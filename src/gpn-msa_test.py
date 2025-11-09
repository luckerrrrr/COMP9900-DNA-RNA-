import os
import re
import datetime
import pandas as pd
import numpy as np
from pathlib import Path
import torch
from sklearn.preprocessing import StandardScaler
from data.loader import GenomeLoader
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from umap import UMAP
import seaborn as sns


# Generate timestamp string formatted as "HH-MM-SS"
timestamp = datetime.datetime.now().strftime("%H-%M-%S")

# Project and environment configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get('USER', 'unknown')
MIDDLE_RESULT_DIR = Path(f"/srv/scratch/{USER}/middle_results")
MIDDLE_RESULT_DIR_OUT = Path(f"/srv/scratch/{USER}/middle_results/{timestamp}")

# Input dataset paths
GTF_PATH = f"{PROJECT_ROOT}/dataset/gencode.v38.basic.annotation.gtf"
WIGFIX_PATH = f"{PROJECT_ROOT}/dataset/chr1.phastCons100way.wigFix"

# Device setup (GPU if available)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", DEVICE)
BATCH_SIZE = 8 


# ---------------------------- Utility Functions ---------------------------- #

def print_section(title: str):
    """Pretty print section titles for better console readability."""
    print("\n" + "═" * 70)
    print(f"{title:^70}")
    print("═" * 70 + "\n")
    

def parse_attr(attr, key):
    """Extract a specific key-value pair from a GTF attribute column."""
    for a in attr.split(";"):
        if key in a:
            parts = a.split('"')
            if len(parts) > 1:
                return parts[1]
    return None


def debug_log(message: str, level: str = "INFO"):
    """
    Print formatted debug messages with log level indicators.

    Args:
        message (str): Text to display in the log.
        level (str): One of ["INFO", "WARN", "ERROR", "DEBUG", "SUCCESS"].
    """
    prefix = {
        "INFO": "ℹ️ ",
        "WARN": "⚠️ ",
        "ERROR": "❌",
        "DEBUG": "🔍",
        "SUCCESS": "✅"
    }.get(level, "  ")
    print(f"{prefix} {message}")


# ---------------------------- GENCODE Window Extraction ---------------------------- #

def extract_gencode_windows(chrom: str, flanking=100, win=512, step=256):
    """
    Extract genome windows from the GENCODE annotation file for a given chromosome.
    Regions include exon/CDS/UTR and lncRNA, each extended by a flanking region.

    Args:
        chrom (str): Chromosome name (e.g., 'chr1').
        flanking (int): Number of base pairs to extend upstream and downstream.
        win (int): Sliding window size.
        step (int): Step size between consecutive windows.

    Returns:
        pd.DataFrame: Table of genomic windows with associated gene annotations.
    """
    csv_path = Path(MIDDLE_RESULT_DIR / f"{chrom}_windows.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        print(f"💾 Loaded {len(df)} windows from cache {csv_path}")
        return df
    
    # 1️⃣ Load the GTF file
    gtf = pd.read_csv(
        GTF_PATH, sep="\t", comment="#", header=None,
        names=["chr", "src", "feature", "start", "end", "score", "strand", "frame", "attr"]
    )

    # Filter target chromosome
    gtf = gtf[gtf["chr"] == chrom]
    print(f"✅ Loaded {len(gtf)} records from {chrom}")

    # 2️⃣ Select relevant genomic features
    target_features = ["exon", "CDS", "UTR", "lncRNA"]
    selected = gtf[gtf["feature"].isin(target_features)].copy()

    if len(selected) == 0:
        print(f"⚠️ No exon/CDS/UTR/lncRNA features found for {chrom}")
        return pd.DataFrame()

    print(f"📌 Found {len(selected)} regions (exon/CDS/UTR/lncRNA combined)")

    # 3️⃣ Generate sliding windows
    windows = []
    for _, r in selected.iterrows():
        s = max(1, int(r["start"]) - flanking)
        e = int(r["end"]) + flanking

        gene_id = parse_attr(r["attr"], "gene_id")
        gene_type = parse_attr(r["attr"], "gene_type")
        region_type = r["feature"]

        for pos in range(s, e - win + 1, step):
            windows.append({
                "chrom": chrom,
                "start": pos,
                "end": pos + win - 1,
                "gene_id": gene_id,
                "gene_type": gene_type,
                "region": region_type
            })

    # 4️⃣ Remove duplicates
    df = pd.DataFrame(windows).drop_duplicates(subset=["chrom", "start", "end", "gene_id", "region"])

    # 5️⃣ Save generated windows to file
    out = MIDDLE_RESULT_DIR_OUT / f"{chrom}_windows.csv"
    df.to_csv(out, index=False)
    print(f"💾 Saved {len(df)} windows → {out}")
    return df
    

# ---------------------------- PhastCons WIGFIX Parser ---------------------------- #

def parse_fixedstep_wigfix(wig_path, chrom_filter=None):
    """
    Parse fixedStep-format WIGFIX files into block-wise arrays.

    Args:
        wig_path (str): Path to the .wigFix file.
        chrom_filter (str, optional): If provided, filter results to this chromosome only.

    Returns:
        dict: Mapping {chromosome -> list of (start, step, np.array(values))}.
    """
    wig_blocks = {}
    cur_chrom = None
    cur_start = None
    cur_step = None
    cur_vals = None
    with open(wig_path, 'rt') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith('fixedStep'):
                # Flush previous block
                if cur_chrom is not None and cur_vals is not None:
                    wig_blocks.setdefault(cur_chrom, []).append((cur_start, cur_step, np.array(cur_vals, dtype=float)))
                m_chrom = re.search(r'chrom=(\S+)', line)
                m_start = re.search(r'start=(\d+)', line)
                m_step = re.search(r'step=(\d+)', line)
                if not (m_chrom and m_start and m_step):
                    raise ValueError(f"Failed to parse fixedStep header: {line}")
                cur_chrom = m_chrom.group(1)
                cur_start = int(m_start.group(1))
                cur_step = int(m_step.group(1))
                cur_vals = []
            elif line.startswith(('variableStep','track','#')):
                continue
            else:
                try:
                    cur_vals.append(float(line))
                except:
                    continue
        # Flush last block
        if cur_chrom is not None and cur_vals is not None:
            wig_blocks.setdefault(cur_chrom, []).append((cur_start, cur_step, np.array(cur_vals, dtype=float)))
    if chrom_filter:
        wig_blocks = {k:v for k,v in wig_blocks.items() if k==chrom_filter}
    return wig_blocks


def mean_phastcons_from_wigfix_blocklist(chrom, start1, end1, wig_blocks):
    """
    Compute the mean phastCons value for a genomic region using pre-parsed wigFix blocks.
    """
    if chrom not in wig_blocks:
        return float('nan')
    total_sum = 0.0
    total_count = 0
    for b_start, b_step, arr in wig_blocks[chrom]:
        if b_step == 1:
            b_end = b_start + len(arr) - 1
            ov_s = max(start1, b_start)
            ov_e = min(end1, b_end)
            if ov_s <= ov_e:
                i0 = ov_s - b_start
                i1 = ov_e - b_start
                seg = arr[i0:i1+1]
                total_sum += np.nansum(seg)
                total_count += np.count_nonzero(~np.isnan(seg))
        else:
            kmin = int(np.ceil((start1 - b_start) / b_step)) if (start1 - b_start) > 0 else 0
            kmax = int(np.floor((end1 - b_start) / b_step))
            if kmax < kmin:
                continue
            kmin = max(kmin, 0)
            kmax = min(kmax, len(arr)-1)
            if kmin <= kmax:
                seg = arr[kmin:kmax+1]
                total_sum += np.nansum(seg)
                total_count += np.count_nonzero(~np.isnan(seg))
    if total_count == 0:
        return float('nan')
    return float(total_sum / total_count)


def inject_phastcons(df_windows, wig_blocks, chrom_col='chrom', start_col='start', end_col='end', out_col='mean_phastCons'):
    """
    Inject mean phastCons scores into each genomic window.

    Args:
        df_windows (pd.DataFrame): DataFrame containing genomic windows.
        wig_blocks (dict): Pre-parsed WIGFIX blocks.
        chrom_col (str): Column containing chromosome name.
        start_col (str): Column containing start position.
        end_col (str): Column containing end position.
        out_col (str): Column name to store computed mean phastCons values.

    Returns:
        pd.DataFrame: Updated DataFrame with an additional column for mean phastCons.
    """
    values = []
    for _, r in df_windows.iterrows():
        chrom = r[chrom_col]
        s = int(r[start_col])
        e = int(r[end_col])
        meanv = mean_phastcons_from_wigfix_blocklist(chrom, s, e, wig_blocks)
        values.append(meanv)
    df = df_windows.copy()
    df[out_col] = values
    return df


def compute_embeddings(df, chrom, sample_size=1000):
    """
    Compute GPN-MSA embeddings for sampled genomic windows.

    This function performs the following steps:
    1. Randomly sample a subset of genomic windows.
    2. Retrieve multiple sequence alignments (MSA) for each window from Multiz100way.
    3. Extract per-window tokenized features (input_ids + auxiliary features).
    4. Forward-pass through the pretrained GPN-MSA model to obtain embeddings.
    5. Mean-pool embeddings across sequence positions to generate fixed-length feature vectors.
    6. Save embeddings and metadata to CSV and Parquet files.

    Args:
        df (pd.DataFrame): DataFrame of genomic windows and associated metadata.
        chrom (str): Chromosome identifier (e.g., "chr1").
        sample_size (int): Number of windows to sample for embedding computation.

    Returns:
        pd.DataFrame: Combined embedding and metadata DataFrame.
    """
    print_section(f"Computing embeddings for {chrom} ({sample_size} sampled windows)")
    chrom_key = chrom.replace("chr", "")
    sampled_df = df.sample(min(sample_size, len(df)), random_state=42).reset_index(drop=True)
    emb_list = []
    meta_list = []

    csv_path = Path(MIDDLE_RESULT_DIR_OUT / f"{chrom}_embeddings_sampled.csv")
    parquet_path = Path(MIDDLE_RESULT_DIR_OUT / f"{chrom}_embeddings_sampled.parquet")
    msas_dir = Path(MIDDLE_RESULT_DIR_OUT / "msas")
    msas_dir.mkdir(parents=True, exist_ok=True)

    # If cached results exist, load directly
    if csv_path.exists() and parquet_path.exists():
        result_df = pd.read_csv(csv_path)
        print(f"💾 Loaded {len(result_df)} windows from cache {csv_path}")
        return result_df

    loader = GenomeLoader()
    msa_ds = loader.load_multiz100way_dataset(streaming=True)
    model_unmasked = loader.load_gpn_msa_sapiens_model(masked=False).to(DEVICE)
    model_unmasked.eval()

    print("model device:", next(model_unmasked.parameters()).device)

    for i, row in sampled_df.iterrows():
        try:
            s = int(row.start)
            e = int(row.end)

            # Add +1 to the end position to handle closed intervals properly
            msa_raw = msa_ds.get_msa(chrom_key, s, e + 1, strand="+", tokenize=True)

            if msa_raw is None:
                debug_log(f"⚠️ No msa for {chrom}:{s}-{e}", "WARN")
                continue

            msa_arr = np.asarray(msa_raw)

            # Normalize MSA array shape across various formats:
            #   (1, L, Nseq) → transpose → (Nseq, L)
            #   (Nseq, L, F) → keep as-is
            if msa_arr.ndim == 3:
                if msa_arr.shape[0] == 1 and msa_arr.shape[2] > msa_arr.shape[1]:
                    msa_arr = msa_arr.transpose(2, 1, 0)
                    if msa_arr.shape[2] == 1:
                        msa_arr = msa_arr.squeeze(-1)

            # Extract input tokens and auxiliary features
            if msa_arr.ndim == 2:
                input_ids_np = msa_arr[0:1, :].astype(np.int64)
                aux_np = None
            elif msa_arr.ndim == 3:
                input_ids_np = msa_arr[:, :, 0].astype(np.int64)[0:1, :]
                if msa_arr.shape[2] > 1:
                    aux_np = msa_arr[:, :, 1:].astype(np.float32)[0:1, :, :]
                else:
                    aux_np = None
            else:
                debug_log(f"⚠️ Unsupported msa ndim={msa_arr.ndim} for {chrom}:{s}-{e}", "WARN")
                continue

            # Convert arrays to PyTorch tensors and push to device
            input_ids = torch.tensor(input_ids_np, dtype=torch.long, device=DEVICE)
            aux = torch.tensor(aux_np, dtype=torch.float32, device=DEVICE) if aux_np is not None else None

            # Forward-pass through the model
            with torch.no_grad():
                out = model_unmasked(input_ids=input_ids, aux_features=aux)
                if hasattr(out, "last_hidden_state"):
                    emb = out.last_hidden_state
                elif isinstance(out, (tuple, list)):
                    emb = out[0]
                else:
                    emb = out

            # Mean-pool across sequence length to obtain a fixed-length embedding
            if emb is None or emb.numel() == 0:
                debug_log(f"⚠️ Empty embedding for {chrom}:{s}-{e}", "WARN")
                continue
            mean_emb = emb.mean(dim=1).cpu().numpy().squeeze()

            # Prepare metadata
            meta = {
                "chrom": chrom,
                "start": s,
                "end": e,
                "gene_id": row.get("gene_id", None),
                "gene_type": row.get("gene_type", None),
                "region": row.get("region", None),
                "mean_phastCons": row.get("mean_phastCons", 0),
            }

            emb_list.append(mean_emb)
            meta_list.append(meta)

        except Exception as e:
            debug_log(f"⚠️ Embedding failed: {row.start}-{row.end} ({e})", "WARN")
            continue

        if len(emb_list) % 200 == 0:
            print(f"   🔹 {len(emb_list)} windows processed...")

    if not emb_list:
        raise RuntimeError("❌ No embeddings computed.")

    # Construct standardized embedding DataFrame
    emb_arr = np.vstack(emb_list)
    D = emb_arr.shape[1]
    scaled = StandardScaler().fit_transform(emb_arr)
    emb_df = pd.DataFrame(scaled, columns=[f"dim_{i}" for i in range(D)])
    meta_df = pd.DataFrame(meta_list).reset_index(drop=True)
    result_df = pd.concat([meta_df, emb_df], axis=1)

    # Save embeddings and metadata
    result_df.to_csv(csv_path, index=False)
    result_df.to_parquet(parquet_path, index=False)
    print(f"💾 Embedding (sampled) saved → {csv_path} and {parquet_path}")
    print(f"💾 Per-window MSA npz files saved under → {msas_dir}")

    return result_df


def run_umap_with_labels(emb_df):
    """
    Run UMAP dimensionality reduction on GPN-MSA embeddings.

    This function projects high-dimensional embeddings into 2D space
    and visualizes them, colored by gene type or region, with lncRNA
    highlighted distinctly.

    Args:
        emb_df (pd.DataFrame): DataFrame containing embeddings (dim_*) and metadata.
    """
    print_section("🧬 Running UMAP visualization with lncRNA labels")

    # 1️⃣ Extract embedding vectors (columns named dim_0, dim_1, ...)
    X = emb_df.filter(regex="^dim_").values

    # 2️⃣ Standardize and slightly perturb data to avoid degenerate eigenvalues
    X_scaled = StandardScaler().fit_transform(X)
    X_noisy = X_scaled + np.random.normal(0, 1e-5, X_scaled.shape)

    # 3️⃣ Initialize UMAP (spectral init improves global structure)
    reducer = UMAP(
        n_neighbors=20,
        min_dist=0.1,
        n_components=2,
        random_state=42,
        init="spectral"
    )

    # 4️⃣ Run UMAP projection
    coords = reducer.fit_transform(X_noisy)

    # 5️⃣ Construct UMAP output DataFrame
    umap_df = pd.DataFrame(coords, columns=["UMAP1", "UMAP2"])
    umap_df["region"] = emb_df["region"]
    umap_df['gene_type'] = emb_df['gene_type'].astype(str).fillna('')
    umap_df['gene_type'] = umap_df['gene_type'].where(
        ~umap_df['gene_type'].str.contains('pseudogene', case=False, na=False),
        'pseudogene'
    )

    print(f"✅ UMAP completed successfully — {len(umap_df)} points projected.")
    print("🔹 Sample of results:")
    print(umap_df.head())

    # Define color palette for visualization
    palette = {
        "protein_coding": "#1f77b4",
        "TEC": "#ff8100",
        "pseudogene": "#9d5549",
        "lncRNA": "#f82224",
        "scaRNA": "#17becf",
        "misc_RNA": "#bcbd22",
        "unknown": "#7f7f7f",
    }

    # 6️⃣ Plot UMAP scatter
    plt.figure(figsize=(9, 7))
    sns.scatterplot(
        data=umap_df,
        x="UMAP1",
        y="UMAP2",
        hue="gene_type",
        s=1.2,
        alpha=0.6,
        linewidth=0,
        edgecolor=None,
        palette=palette,
        rasterized=True
    )

    plt.title("UMAP projection of GPN-MSA embeddings (fine-grained lncRNA scatter)", fontsize=13)
    plt.xlabel("UMAP1")
    plt.ylabel("UMAP2")

    patches = [Patch(facecolor=color, edgecolor='black', label=label) for label, color in palette.items()]
    plt.legend(
        handles=patches,
        title="region",
        loc="best",
        frameon=True,
        handlelength=2,
        handleheight=1.2
    )

    plt.tight_layout()
    out_img = MIDDLE_RESULT_DIR_OUT / f"umap_region_lncRNA_fine.png"
    plt.savefig(out_img, dpi=600, bbox_inches="tight")
    plt.close()

    print(f"✅ Fine-grained UMAP saved → {out_img}")


# ---------------------------- Main Execution Entry ---------------------------- #

if __name__ == "__main__":
    chrom = "chr1"
    os.mkdir(MIDDLE_RESULT_DIR_OUT)
    phasctCon_file = Path(MIDDLE_RESULT_DIR_OUT / "sampled_pos_neg_windows_with_phastcons.csv")
    conversation_file = Path(MIDDLE_RESULT_DIR_OUT / "chr1_window_conservation.csv")

    # Step 1: Extract genomic windows from GENCODE
    windows_df = extract_gencode_windows(chrom)
    if windows_df is None or len(windows_df) == 0:
        print("No windows generated.")
    
    # Step 2: Inject phastCons conservation scores if available
    df = windows_df.copy()
    if os.path.exists(WIGFIX_PATH):
        print("Parsing wigFix file and injecting phastCons values (this may take a while)...")
        wig_blocks = parse_fixedstep_wigfix(WIGFIX_PATH, chrom_filter='chr1')
        combined_with_pc = inject_phastcons(df, wig_blocks)
        combined_with_pc.to_csv(phasctCon_file, index=False)
        print("Saved window set with phastCons scores to:", phasctCon_file)
    else:
        combined_with_pc = df
        print("WIGFIX_PATH not found — skipping phastCons injection step.")
        
    # Step 3: Compute embeddings for all windows and visualize via UMAP
    emb_df = compute_embeddings(combined_with_pc, "chr1", len(combined_with_pc))
    run_umap_with_labels(emb_df)

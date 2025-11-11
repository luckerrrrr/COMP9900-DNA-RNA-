from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path

from src.gpn_msa.backbone import GPNBackbone
from src.gpn_msa.classifier import GPNClassifier
from data.loader import GenomeLoader, MODEL_GPN_MSA_SAPIENS
from gpn.data import Tokenizer

from src.config import MIDDLE_RESULT_DIR, GTF, FASTA, CHROM, CONFIG, PHASTCONS_FILE, MIDDLE_RESULT_DIR_OUT
from data.preprocess import GencodeWindowGenerator
from utils.utils import print_section, debug_log
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from umap import UMAP

# Device setup (GPU if available)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", DEVICE)

# ------------------------------------------------------
# 以下为示例输入构造与 quick-run（可直接执行）
# ------------------------------------------------------
def make_mock_batch(batch_size: int = 2, seq_len: int = 512, aux_dim: int = 5, device: Optional[torch.device] = None):
    """
    生成一个 mock 输入 batch 用于本地测试
    返回:
      input_ids: LongTensor [B, L]  (随机 small vocab)
      aux_features: FloatTensor [B, L, F] (随机)
      attention_mask: LongTensor [B, L] (全1 表示无 padding) 
    说明: 这与实际 MSA tokenization 不同，只用于快速检查模型 forward 是否通顺
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # 词表大小参照 dummy backbone 定义 (vocab_size = 32)
    input_ids = torch.randint(1, 31, (batch_size, seq_len), dtype=torch.long, device=device)
    aux = torch.randn(batch_size, seq_len, aux_dim, device=device)  # per-base features (e.g., phastCons, phyloP etc.)
    attention_mask = torch.ones(batch_size, seq_len, dtype=torch.long, device=device)
    return input_ids, aux, attention_mask

# debug & sanitize input_ids before passing to model
def sanitize_input_ids(input_ids, backbone=None, tokenizer=None):
    # input_ids: tensor on device (可能是 LongTensor 也可能不是)
    if not torch.is_tensor(input_ids):
        input_ids = torch.tensor(input_ids)
    # 打印基本信息
    print(">>> input_ids dtype:", input_ids.dtype, "shape:", input_ids.shape,
          "min:", input_ids.min().item(), "max:", input_ids.max().item())

    # 强制 long
    if input_ids.dtype != torch.long:
        input_ids = input_ids.long()
        print(">>> converted input_ids to long")

    # 尝试获取 vocab_size / pad_id
    vocab_size = None
    pad_id = 0
    try:
        if backbone is not None and hasattr(backbone, "_hf_model"):
            cfg = getattr(backbone._hf_model, "config", None)
            if cfg is not None:
                vocab_size = getattr(cfg, "vocab_size", None)
        # 如果提供 tokenizer，可从 tokenizer 获取 pad_token_id
        if tokenizer is not None:
            pad_id = getattr(tokenizer, "pad_token_id", pad_id)
    except Exception:
        pass
    print(">>> vocab_size:", vocab_size, "pad_id:", pad_id)

    # 检查负值
    if (input_ids < 0).any():
        neg_count = int((input_ids < 0).sum().item())
        print(f"⚠️ Found {neg_count} negative ids in input_ids. Replacing negatives with pad_id={pad_id}")
        input_ids = input_ids.clone()
        input_ids[input_ids < 0] = pad_id

    # 检查是否有值 >= vocab_size（若能拿到 vocab_size）
    if vocab_size is not None and (input_ids >= vocab_size).any():
        bad_count = int((input_ids >= vocab_size).sum().item())
        print(f"⚠️ Found {bad_count} ids >= vocab_size ({vocab_size}). These will be clamped to {vocab_size-1}.")
        input_ids = torch.clamp(input_ids, max=vocab_size-1)

    return input_ids


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
                "mean_phastCons": row.get("mean_phastCons", 0),
                "sequence": row.get("sequence", "")
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
    and visualizes them, colored by gene type, with lncRNA
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
        title="Gene Type",
        loc="best",
        frameon=True,
        handlelength=2,
        handleheight=1.2
    )

    plt.tight_layout()
    out_img = MIDDLE_RESULT_DIR_OUT / f"umap_gene_type.png"
    plt.savefig(out_img, dpi=600, bbox_inches="tight")
    plt.close()

    print(f"✅ Fine-grained UMAP saved → {out_img}")


def example_run():
    """
    快速示例：构建 backbone + classifier，跑一遍前向并打印输出形状与数值样例。
    保存该文件后直接运行: python gpn_backbone_classifier.py
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)

    # 1) 尝试加载真实 backbone（如果不可用会退回到 dummy）
    #    model_name 可以改成你实际想用的 HF 模型
    backbone = GPNBackbone(model_name=MODEL_GPN_MSA_SAPIENS, hidden_size=256, use_dummy_if_failed=True)
    print("Using dummy backbone?" , backbone.using_dummy())

    # 2) 构建 classifier wrapper
    clf = GPNClassifier(backbone=backbone, head_hidden_ratio=0.5, dropout=0.1).to(device)

    # 3) 准备 data
    out_json = Path(f"{MIDDLE_RESULT_DIR}/human_gencode_windows.json")
    window_df = []
    if not out_json.exists():
        flanking = CONFIG["data"]["flanking"]
        win = CONFIG["data"]["window_len"]
        step = CONFIG["data"]["step"]
        gen = GencodeWindowGenerator(GTF, FASTA)
        window_df = gen.run(chrom=CHROM, output_path=out_json, flanking=flanking, win=win, step=step, wig_path=PHASTCONS_FILE)
    else:
        window_df = pd.read_json(out_json)
    
    emb_df = compute_embeddings(window_df, "chr1", len(window_df))
    run_umap_with_labels(emb_df)
    
    # loader = GenomeLoader()
    # msa_ds = loader.load_multiz100way_dataset(streaming=True)
    # msa = msa_ds.get_msa("6", 31575665, 31575793, strand="+", tokenize=True)
    # msa = torch.tensor(np.expand_dims(msa, 0).astype(np.int64))
    # input_ids, aux_features = msa[:, :, 0], msa[:, :, 1:]
    # print(input_ids.shape, aux_features.shape)

    # # 4) forward
    # clf.eval()
    # B, L = input_ids.shape
    # attention_mask = torch.ones(B, L, dtype=torch.long, device=input_ids.device)
    # with torch.no_grad():
    #     logits = clf(input_ids=input_ids, aux_features=aux_features, attention_mask=attention_mask)  # [B]
    #     probs = torch.sigmoid(logits)

    # print("logits shape:", logits.shape)      # 期望: torch.Size([B])
    # print("probs shape:", probs.shape)
    # print("sample logits:", logits[:4].cpu().numpy())
    # print("sample probs:", probs[:4].cpu().numpy())


if __name__ == "__main__":
    example_run()
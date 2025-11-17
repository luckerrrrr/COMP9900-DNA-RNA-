#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------
# This script performs fine-tuning for GPN-MSA on binary conservation prediction.
# The structure is intentionally "static": no dynamic mixing of classifiers.
# Architecture: (MSA tokens) → GPN-MSA backbone → mean pooling → MLP classifier.
# All utility components (scheduler, caching, plotting) are embedded here.
# ------------------------------------------------------

import os
import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    average_precision_score, roc_auc_score,
    roc_curve, precision_recall_curve,
    confusion_matrix, f1_score
)

from torch.cuda.amp import autocast, GradScaler
import h5py

from typing import Dict, List, Optional

from data.wigfix_loader import WigFixLoader

# ------------------------------------------------------
# Project-specific imports:
# - MIDDLE_RESULT_DIR / MIDDLE_RESULT_DIR_OUT: standardized locations for intermediate files.
# - CONFIG carries core hyperparameters (e.g., window length).
# - MSA_BEST_MODEL points to a pre-trained / fine-tuned model checkpoint.
# - GenomeLoader abstracts access to genomic and MSA datasets.
# - GPNBackbone implements the GPN-MSA transformer feature extractor.
# - GPNClassifier is a downstream binary classification head.
# ------------------------------------------------------

from gpn_msa.config import MIDDLE_RESULT_DIR, MIDDLE_RESULT_DIR_OUT, CONFIG, MSA_BEST_MODEL
from data.loader import GenomeLoader
from src.gpn_msa.backbone import GPNBackbone
from src.gpn_msa.classifier import GPNClassifier  # 直接使用该分类器

# ------------------------------------------------------
# Static configuration and output directories
# ------------------------------------------------------
# SET_NAME controls metadata (seq + window) selection for fine-tuning.
# All outputs are written into MIDDLE_RESULT_DIR_OUT/{timestamp}/...
# CACHE_DIR stores HDF5 per-chromosome MSA caches to avoid recomputing alignments.
# ------------------------------------------------------

SET_NAME = "set2"
METADATA_CSV = f"{MIDDLE_RESULT_DIR}/fine_tune_windows_with_seq_{SET_NAME}.csv"
OUT_DIR = f"{MIDDLE_RESULT_DIR_OUT}/ft_out_static"
CACHE_DIR = f"{MIDDLE_RESULT_DIR}/{SET_NAME}/msa_cache"
EPOCH_LOG_DIR = f"{OUT_DIR}/epoch_logs"

# Training on GPU is preferred; CPU fallback supported but slow for MSA-based models.
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ------------------------------------------------------
# Dataset split ratios
# To prevent information leakage, splits are gene-level (handled later).
# Ratios follow typical ML practice: 70/15/15.
# ------------------------------------------------------
TRAIN_FRAC = 0.7
VAL_FRAC = 0.15
TEST_FRAC = 0.15
RANDOM_SEED = 42

# ------------------------------------------------------
# Training hyperparameters
# ------------------------------------------------------
# - LR_HEAD: classifier head learning rate (higher for early-stage training)
# - LR_BACKBONE: used after unfreezing; kept much smaller to avoid catastrophic forgetting
# - WEIGHT_DECAY: stabilizes training
# - CLIP_GRAD prevents gradient explosion, especially during early unfreeze epochs
# ------------------------------------------------------
BATCH_SIZE = 16
EPOCHS = 8
LR_HEAD = 5e-5              # Classifier head LR
LR_BACKBONE = 1e-5          # Backbone LR once unfrozen
WEIGHT_DECAY = 1e-2         # Standard AdamW parameter
CLIP_GRAD = 1.0

# ------------------------------------------------------
# Freezing Strategy
# FREEZE_FIRST = False means we begin training with frozen backbone for stability.
# UNFREEZE_EPOCH defines when to let gradients flow through the backbone.
# ------------------------------------------------------
FREEZE_FIRST = False
UNFREEZE_EPOCH = 3  # Don't unfreeze early → more stable optimization

# ------------------------------------------------------
# Window filtering
# Scientific Note:
# Using at most MAX_WINDOWS_PER_PARENT windows per gene prevents sampling imbalance.
# ------------------------------------------------------
MAX_WINDOWS_PER_PARENT = 1
WINDOW = CONFIG["data"]["window_len"]

# ------------------------------------------------------
# Dataset
# ------------------------------------------------------
# SeqMsasDataset couples:
#   - Metadata/DataFrame describing genomic windows and labels.
#   - GenomeLoader / Multiz MSA dataset to fetch MSAs on demand.
#   - HDF5 caching to avoid recomputing MSAs across epochs.
# It returns (input_ids, aux_features, label) tuples for each window.
# ------------------------------------------------------
class SeqMsasDataset(Dataset):
    def __init__(self, df, msa_ds, cache_dir=CACHE_DIR):
         # Store metadata and references to genome/MSA datasets.
        self.df = df.reset_index(drop=True)
        self.msa_ds = msa_ds
        self.cache_dir = cache_dir
        
        # In-memory dictionary mapping chromosome → open HDF5 file handle.
        # This avoids repeatedly re-opening HDF5 files for every sample.
        self._h5 = {}

    def __len__(self):
        # Standard PyTorch Dataset length: number of windows.
        return len(self.df)

    def __getitem__(self, idx):
        # Retrieve one row from the metadata DataFrame.
        row = self.df.iloc[idx]

        # Normalize chromosome (strip 'chr' prefix if present).
        chrom = row.chrom.replace("chr", "")
        # Start/end coordinates and strand information from metadata.
        s, e, strand = int(row.start), int(row.end), row.strand

        # Construct a unique sample identifier for caching / file keys.
        sample_id = f"{chrom}:{s}-{e}"
        key = f"{sample_id}".replace("/", "_")

        # HDF5 cache file is one per chromosome (e.g. '1.h5', '2.h5', ...).
        h5_path = f"{self.cache_dir}/{chrom}.h5"

        # Lazily open HDF5 bucket for this chromosome.
        if chrom not in self._h5:
            # 'a' mode: read/write, create if not exists.
            self._h5[chrom] = h5py.File(h5_path, "a")
        h5f = self._h5[chrom]

        # Inner helper: recompute MSA when cache is missing or corrupted.
        def recompute():
            try:
                # ======== Fetch MSA from multiz100way dataset ========
                # get_msa returns a numpy array with shape (L, F+1):
                #   column 0: token ids (A/C/G/T/N/... mapped to integers)
                #   columns 1..F: auxiliary alignment features (one per species/track).
                msa = self.msa_ds.get_msa(chrom, s, e+1, strand=strand, tokenize=True)
                # Wrap in extra batch dimension for consistency, then cast to int64.
                msa = torch.tensor(np.expand_dims(msa, 0).astype(np.int64))
                
                # Split tokens and auxiliary features.
                # ids: (L,)
                # aux: (L, F) where F is number of auxiliary channels (e.g., species).
                ids = msa[0, :, 0]          # (L,)
                aux = msa[0, :, 1:].float() # (L, 89) in this particular MSA setting

                # ======== Write MSA into HDF5 cache for reuse ========
                g = h5f.create_group(key)
                g.create_dataset("input_ids", data=ids.numpy())
                if aux is not None:
                    g.create_dataset("aux", data=aux.numpy())
                h5f.flush()

                return ids, aux

            except Exception as err:
                # Any failure in MSA retrieval or shape mismatch is surfaced clearly.
                print("recompute_error:", err)
                raise RuntimeError(
                    f"⛔ MSA shape 无效, coords={chrom}:{s}-{e}, strand={strand}, error={err}"
                )
                return ids, aux

        # ----------------- Cache loading logic -----------------
        if key in h5f:
            # Try to load from cache. If anything fails, the group is deleted and recomputed.
            try:
                ids = h5f[key]["input_ids"][()]
                aux = h5f[key]["aux"][()] if "aux" in h5f[key] else None
            except:
                # Cache entry is corrupted or incomplete → delete and recompute.
                del h5f[key]
                ids, aux = recompute()
        else:
            # First time access: compute MSA and write cache.
            ids, aux = recompute()

        # Convert label to float 0.0 / 1.0 according to several textual representations.
        label = 1.0 if row.label in (1,"1","true","t","True","yes") else 0.0

        # Return tensors suitable for the collate function.
        return (
            torch.tensor(ids).long(),         # Token sequence (L,)
            (torch.tensor(aux).float() if aux is not None else None),  # Aux feats (L,F) or None
            torch.tensor(label).float(),
        )



# ------------------------------------------------------
# collate_fn
# ------------------------------------------------------
# collate_msa pads variable-length MSAs in a batch to a common max length.
# It returns:
#   padded_ids: (B, L_max)
#   aux_pad:    (B, L_max, F) or None
#   labels:     (B,)
# This padding is essential for batched transformer processing.
# ------------------------------------------------------
def collate_msa(batch):
    # Unzip the batch into separate tuples.
    ids, auxs, labels = zip(*batch)

    B = len(ids)
    # Compute maximum length across all windows in the batch.
    maxL = max(t.size(0) for t in ids)

    # Initialize padded token id tensor.
    padded_ids = torch.zeros((B,maxL), dtype=torch.long)

    # Determine feature dimension F (if any aux exists).
    aux_pad = None
    F = next((a.size(1) for a in auxs if a is not None), 0)
    if F > 0:
        # Initialize padded aux tensor with zeros.
        aux_pad = torch.zeros((B,maxL,F), dtype=torch.float32)

    # Fill in the actual sequences and features, leaving trailing zeros as padding.
    for i,(tokens,aux) in enumerate(zip(ids,auxs)):
        L = tokens.size(0)
        padded_ids[i,:L] = tokens
        if aux_pad is not None and aux is not None:
            aux_pad[i,:L] = aux

    # Move everything onto the target device and stack labels.
    return (
        padded_ids.to(DEVICE),                
        (aux_pad.to(DEVICE) if aux_pad is not None else None),
        torch.stack(labels).to(DEVICE)
    )



# ------------------------------------------------------
# split dataset
# ------------------------------------------------------
# split_dataset performs a group-aware train/val/test split, grouping by gene_id
# (or 'id' as fallback). This avoids leakage where multiple windows from the same gene
# end up in different splits. It also enforces that each split contains both classes.
# ------------------------------------------------------
def split_dataset(df, seed=42):
    # Choose group column: prefer 'gene_id', fall back to 'id'.
    group_col = "gene_id" if "gene_id" in df.columns else "id"

    # Aggregate labels per group to define group-level label used for stratification.
    groups = df[group_col].unique()
    gdf = df.groupby(group_col)["label"].agg(["sum","count"])
    gdf["lbl"] = (gdf["sum"]>0).astype(int)

    # Try multiple seeds to obtain non-degenerate splits with both classes present.
    for attempt in range(50):
        rs = seed + attempt

        # First split groups into train vs (val+test), preserving class proportions.
        tr_g, rest_g = train_test_split(
            groups,
            train_size=TRAIN_FRAC,
            random_state=rs,
            stratify=gdf.loc[groups,"lbl"]
        )
        # Then split remaining groups into val and test.
        va_g, te_g = train_test_split(
            rest_g,
            train_size=VAL_FRAC/(VAL_FRAC+TEST_FRAC),
            random_state=rs
        )

        # Materialize DataFrame splits based on group membership.
        tr=df[df[group_col].isin(tr_g)]
        va=df[df[group_col].isin(va_g)]
        te=df[df[group_col].isin(te_g)]

        # Ensure all splits contain both positive and negative labels.
        if (tr.label.nunique()==2 and va.label.nunique()==2 and te.label.nunique()==2):
            print("[SPLIT] OK")
            return tr,va,te

    # If after multiple attempts no valid split is found, fail explicitly.
    raise RuntimeError("Split failed")

def predict_chr1_lncrna(
    gtf_path: str,
    wig_path: str,
    window_size: int = 512,
    window_step: Optional[int] = None,
    out_tsv: Optional[str] = None,
):
    """
    End-to-end pipeline:
      1) Read lncRNA genes from chr1 GTF and generate windows.
      2) Use SeqMsasDataset + GenomeLoader to build MSAs.
      3) Load best.pt and get pred_prob_conserved for each window.
      4) Compute mean phastCons via WigFixLoader.
      5) Plot correlation scatter (and optionally save TSV).
    """
    print("[PRED] Generating windows from GTF ...")

    # Generate fixed-length windows across lncRNA genes on chr1.
    df_windows = generate_windows_from_gtf(
        gtf_path=gtf_path,
        chrom_filter="chr1",
        gene_type_filter="lncRNA",
        window_size=window_size,
        window_step=window_step,
    )
    print(f"[PRED] Total windows on chr1 lncRNA: {len(df_windows)}")

    # SeqMsasDataset expects a 'label' column; we assign dummy zeros for inference.
    df_windows = df_windows.copy()
    df_windows["label"] = 0

    # Build MSA dataset and loader as in training.
    loader = GenomeLoader()
    msa_ds = loader.load_multiz100way_dataset(streaming=True)

    pred_ds = SeqMsasDataset(df_windows, msa_ds)
    pred_loader = DataLoader(
        pred_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        collate_fn=collate_msa,
    )

    # Rebuild model and load the best fine-tuned checkpoint.
    best_model_path = MSA_BEST_MODEL
    print(f"[PRED] Loading best model from {best_model_path}")
    backbone = GPNBackbone()
    model = GPNClassifier(backbone).to(DEVICE)
    state_dict = torch.load(best_model_path, map_location=DEVICE)
    model.load_state_dict(state_dict)
    model.eval()

    # --------------------
    # Forward pass: produce probabilities of "conserved" per window.
    # --------------------
    all_probs: List[float] = []
    with torch.no_grad():
        for x_ids, aux, _labels in tqdm(pred_loader, desc="Predict chr1 windows"):
            # Model returns logits per window; apply sigmoid to convert to probabilities.
            logits = model(input_ids=x_ids, aux_features=aux)
            probs = torch.sigmoid(logits).view(-1)
            all_probs.extend(probs.cpu().numpy().tolist())

    # Attach predicted probabilities to the windows DataFrame.
    df_windows["pred_prob_conserved"] = all_probs

    # --------------------
    # Compute mean phastCons from wigFix file for each window.
    # --------------------
    print("[PRED] Computing mean phastCons ...")
    df_full = add_phastcons_mean(df_windows, wig_path=wig_path)

    # Filter explicitly to chr1 (defensive; should already be chr1).
    df_chr1 = df_full[df_full["chrom"] == "chr1"].copy()

    # Show the top 20 windows ranked by model-predicted conservation probability.
    df_top20 = df_chr1.sort_values("pred_prob_conserved", ascending=False).head(20)
    print("[PRED] Top20 windows:")
    print(df_top20[["chrom", "start", "end", "gene_id", "gene_name",
                    "pred_prob_conserved", "mean_phastcons"]])

    # Optionally dump all chr1 predictions + phastCons to disk for downstream analyses.
    if out_tsv is not None:
        df_full.to_csv(out_tsv, sep="\t", index=False)
        print(f"[PRED] Saved chr1 prediction table to {out_tsv}")

    # --------------------
    # Generate visualizations: dense view over all windows + focused view on top 20.
    # --------------------
    # plot_pred_vs_phastcons(df_chr1, title_prefix="chr1 lncRNA all windows", out_path=PLOTS_DIR)
    plot_all_windows_views(df_chr1, title_prefix="chr1 lncRNA all windows", out_path=PLOTS_DIR)
    plot_pred_vs_phastcons(df_top20, title_prefix="chr1 lncRNA top20", out_path=PLOTS_DIR)

# ======================
# GTF utilities for chr1 prediction
# ======================

# parse_gtf_attributes converts the attributes column (9th field of GTF)
# into a Python dict: keys like 'gene_id', 'gene_name', 'gene_type'.
def parse_gtf_attributes(attr_str: str) -> Dict[str, str]:
    """Parse the 9th column of a GTF line into a dict."""
    attrs: Dict[str, str] = {}
    fields = [f.strip() for f in attr_str.strip().split(";") if f.strip()]
    for f in fields:
        parts = f.split(" ", 1)
        if len(parts) != 2:
            continue
        key, val = parts
        attrs[key] = val.strip().strip('"')
    return attrs


def generate_windows_from_gtf(
    gtf_path: str,
    chrom_filter: str = "chr1",
    gene_type_filter: str = "lncRNA",
    window_size: int = 512,
    window_step: Optional[int] = None,
) -> pd.DataFrame:
    """
    Read a GTF file, keep only gene_type == lncRNA and chrom == chrom_filter,
    then generate sliding windows for each gene.

    GTF uses 1-based inclusive coordinates. We keep the same here.
    window_size should match the WINDOW used in training (512).
    """
    # Default step equals window length (non-overlapping windows) unless overridden.
    if window_step is None:
        window_step = window_size

    records: List[Dict] = []
    with open(gtf_path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            cols = line.split("\t")
            if len(cols) < 9:
                continue

            chrom, source, feature, start, end, score, strand, frame, attrs_str = cols

            # Filter chromosome and focus on gene-level entries.
            if chrom != chrom_filter:
                continue
            if feature.lower() != "gene":
                continue

            # Parse GTF attributes: gene_id, gene_name, gene_type/biotype.
            attrs = parse_gtf_attributes(attrs_str)
            gene_type = attrs.get("gene_type") or attrs.get("gene_biotype")
            if gene_type_filter is not None and gene_type != gene_type_filter:
                continue

            gene_id = attrs.get("gene_id", "")
            gene_name = attrs.get("gene_name", "")

            # Gene coordinates (1-based inclusive).
            gene_start = int(start)
            gene_end = int(end)

            # Slide a fixed-length window across each gene.
            pos = gene_start
            while pos <= gene_end:
                win_start = pos
                win_end = min(pos + window_size - 1, gene_end)

                records.append(
                    {
                        "chrom": chrom,
                        "start": win_start,
                        "end": win_end,
                        "strand": strand,
                        "gene_id": gene_id,
                        "gene_name": gene_name,
                    }
                )

                pos += window_step

    # Convert accumulated records to a DataFrame compatible with SeqMsasDataset.
    df = pd.DataFrame.from_records(records)
    return df


def add_phastcons_mean(df_windows: pd.DataFrame, wig_path: str) -> pd.DataFrame:
    """
    Use WigFixLoader to compute mean phastCons for each window.
    """
    # Initialize and load wigFix data using a dedicated loader.
    loader = WigFixLoader()
    loader.load(wig_path, verbose=False)

    means: List[Optional[float]] = []
    for _, row in df_windows.iterrows():
        chrom = row["chrom"]
        start = int(row["start"])
        end = int(row["end"])
        # Compute mean phastCons over the [start, end] interval for this chromosome.
        m = loader.get_window_mean(chrom, start, end)
        means.append(m if m is not None else np.nan)

    # Attach the mean phastCons as a new column.
    df = df_windows.copy()
    df["mean_phastcons"] = means
    return df


# ------------------------------------------------------
# Plotting utilities
# ------------------------------------------------------
# The following functions help visualize:
#   - Optimization dynamics (loss/AP curves).
#   - Discriminative power (ROC/PR curves).
#   - Error structure (confusion matrix).
#   - Agreement between model scores and conservation (scatter/density plots).
# These provide sanity checks and interpretability for the fine-tuned model.
# ------------------------------------------------------

# -------- Find threshold with best F1 on validation set --------
def find_best_threshold(y_true, probs):
    # Grid-search thresholds in [0.01, 0.99] to maximize F1 score.
    best_thr = 0.5
    best_f1 = -1.0
    for thr in np.linspace(0.01, 0.99, 99):
        preds = (probs >= thr).astype(int)
        f1 = f1_score(y_true, preds)
        if f1 > best_f1:
            best_f1 = f1
            best_thr = thr
    return best_thr, best_f1

# -------- Plot training curves: loss + average precision --------
def plot_training_curves(history, outdir):
    # 'history' holds per-epoch values for train/val loss and AP.
    epochs = np.arange(1, len(history['train_loss'])+1)

    plt.figure(figsize=(8,4))
    # Loss curves
    plt.subplot(1,2,1)
    plt.plot(epochs, history['train_loss'], label='train_loss')
    plt.plot(epochs, history['val_loss'], label='val_loss')
    plt.xlabel("Epoch"); plt.ylabel("Loss"); plt.legend()

    # AP curves
    plt.subplot(1,2,2)
    plt.plot(epochs, history['train_ap'], label='train_ap')
    plt.plot(epochs, history['val_ap'], label='val_ap')
    plt.xlabel("Epoch"); plt.ylabel("AP"); plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "training_curves.png"), dpi=150)
    plt.close()


# -------- Plot ROC and PR curves and save to disk --------
def plot_roc_pr(y_true, probs, outdir, tag="test"):
    # Standard ROC computation.
    fpr, tpr, _ = roc_curve(y_true, probs)
    roc_auc = roc_auc_score(y_true, probs)

    # Precision-recall curve and AP (area under PR).
    precision, recall, _ = precision_recall_curve(y_true, probs)
    ap = average_precision_score(y_true, probs)

    plt.figure(figsize=(10,4))

    # ROC subplot
    plt.subplot(1,2,1)
    plt.plot(fpr, tpr, label=f"AUC={roc_auc:.4f}")
    plt.plot([0,1],[0,1],'k--',alpha=0.5)
    plt.xlabel("FPR"); plt.ylabel("TPR"); plt.title(f"ROC ({tag})"); plt.legend()

    # PR subplot
    plt.subplot(1,2,2)
    plt.plot(recall, precision, label=f"AP={ap:.4f}")
    plt.xlabel("Recall"); plt.ylabel("Precision"); plt.title(f"PR ({tag})"); plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(outdir, f"{tag}_roc_pr.png"), dpi=150)
    plt.close()
    return roc_auc, ap


def plot_confusion(cm, outpath, classes=('neg','pos')):
    # Visualize confusion matrix with counts overlaid.
    plt.figure(figsize=(4,4))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title("Confusion matrix")
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes)
    plt.yticks(tick_marks, classes)

    # Threshold defines text color for better contrast.
    thresh = cm.max() / 2.
    for i, j in np.ndindex(cm.shape):
        plt.text(j, i, format(int(cm[i, j]), 'd'),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    

def plot_pred_vs_phastcons(
    df: pd.DataFrame,
    title_prefix: str = "chr1 lncRNA",
    out_path: Optional[str] = None,
):
    """
    Scatter plot:
        x: mean_phastcons
        y: pred_prob_conserved

    Features:
        ✓ Pearson & Spearman correlations in title
        ✓ 1:1 aspect ratio so diagonal represents perfect prediction
        ✓ Draw y=x reference line
        ✓ Optional saving to PNG
    """
    # Drop rows with missing phastCons or prediction values.
    df_plot = df.dropna(subset=["mean_phastcons", "pred_prob_conserved"])
    if df_plot.empty:
        print("No data to plot (all mean_phastcons are NaN).")
        return

    x = df_plot["mean_phastcons"].values
    y = df_plot["pred_prob_conserved"].values

    # Compute correlation statistics between mean_phastcons and model scores.
    r, p_pearson = pearsonr(x, y)
    rho, p_spearman = spearmanr(x, y)

    plt.figure(figsize=(8, 7))

    # Scatter each window as a point.
    plt.scatter(x, y, alpha=0.4)

    plt.xlabel("mean_phastcons")
    plt.ylabel("pred_prob_conserved")

    # Force 1:1 aspect ratio so the diagonal line indicates perfect match.
    plt.gca().set_aspect('equal', adjustable='box')

    # Reference diagonal y = x (ideal agreement).
    min_lim = min(np.min(x), np.min(y))
    max_lim = max(np.max(x), np.max(y))
    plt.plot([min_lim, max_lim], [min_lim, max_lim], '--', color='red', linewidth=1, alpha=0.6)

    # Use the same range for both axes for comparability.
    plt.xlim(min_lim, max_lim)
    plt.ylim(min_lim, max_lim)

    # Title summarizing correlation coefficients.
    title = (
        f"{title_prefix}: "
        f"r={r:.3f} (p={p_pearson:.1e}), "
        f"rho={rho:.3f} (p={p_spearman:.1e})"
    )
    plt.title(title)
    plt.tight_layout()

    # Persist figure if requested, otherwise show interactively.
    if out_path is not None:
        safe_name = title_prefix.replace(" ", "_")
        save_file = f"{out_path}/{safe_name}.png"
        plt.savefig(save_file, dpi=160)
        print(f"[PRED] Saved scatter plot to {save_file}")
        plt.close()
    else:
        plt.show()
        plt.close()


def plot_all_windows_views(
    df,
    title_prefix="chr1 lncRNA all windows",
    out_path="plots"
):
    """
    Generate 4 visualizations for very large genomic datasets:
        1) scatter (tiny dots, alpha low)
        2) subsample scatter
        3) hexbin density
        4) 2D KDE density (seaborn)
    Automatically computes Pearson and Spearman correlations
    and adds them to the title.

    df must contain columns:
        mean_phastcons, pred_prob_conserved
    """

    # Ensure output directory exists.
    os.makedirs(out_path, exist_ok=True)

    # Clean data: only keep rows where both axes are defined.
    df_plot = df.dropna(subset=["mean_phastcons", "pred_prob_conserved"])
    if df_plot.empty:
        print("[PLOT] No data to plot.")
        return

    x = df_plot["mean_phastcons"].values
    y = df_plot["pred_prob_conserved"].values

    # Global correlation across all windows.
    r, p_pearson = pearsonr(x, y)
    rho, p_spearman = spearmanr(x, y)

    corr_text = f"r={r:.3f} (p={p_pearson:.1e}), rho={rho:.3f} (p={p_spearman:.1e})"
    safe_title = "_".join(title_prefix.split())

    # ==========================================================
    # 1) Dense scatter (tiny points + very low alpha)
    # ==========================================================
    plt.figure(figsize=(8, 7))

    # Force 1:1 aspect ratio for direct comparability.
    plt.gca().set_aspect('equal', adjustable='box')

    # Reference diagonal
    min_lim = min(np.min(x), np.min(y))
    max_lim = max(np.max(x), np.max(y))
    plt.plot([min_lim, max_lim], [min_lim, max_lim], '--', color='red', linewidth=1, alpha=0.6)

    # Match axis ranges.
    plt.xlim(min_lim, max_lim)
    plt.ylim(min_lim, max_lim)

    # Extremely dense scatter visualization (small markers, low alpha) for large datasets.
    plt.scatter(x, y, s=2, alpha=0.05)
    plt.xlabel("mean_phastcons")
    plt.ylabel("pred_prob_conserved")
    plt.title(f"{title_prefix} (scatter) | {corr_text}")
    plt.tight_layout()
    out1 = f"{out_path}/{safe_title}_scatter.png"
    plt.savefig(out1, dpi=160)
    plt.close()
    print(f"[PLOT] saved {out1}")

    # ==========================================================
    # 2) Subsample scatter (e.g. first 1000 points)
    # ==========================================================
    # For interpretability, show a clearer view on a manageable subset of points.
    df_sub = df_plot.head(1000)

    plt.figure(figsize=(8, 7))
    plt.gca().set_aspect('equal', adjustable='box')

    min_lim = min(np.min(x), np.min(y))
    max_lim = max(np.max(x), np.max(y))
    plt.plot([min_lim, max_lim], [min_lim, max_lim], '--', color='red', linewidth=1, alpha=0.6)

    plt.xlim(min_lim, max_lim)
    plt.ylim(min_lim, max_lim)

    plt.scatter(df_sub["mean_phastcons"], df_sub["pred_prob_conserved"],
                s=8, alpha=0.4)
    plt.xlabel("mean_phastcons")
    plt.ylabel("pred_prob_conserved")
    plt.title(f"{title_prefix} (top 1000) | {corr_text}")
    plt.tight_layout()
    out2 = f"{out_path}/{safe_title}_subsample.png"
    plt.savefig(out2, dpi=160)
    plt.close()
    print(f"[PLOT] saved {out2}")

    print("\n[PLOT] All 2 visualizations generated successfully!\n")

# ------------------------------------------------------
# Main training routine
# ------------------------------------------------------
# train_main orchestrates the full fine-tuning pipeline:
#   1) Load annotated windows and labels.
#   2) Group-aware split into train/val/test.
#   3) Construct SeqMsasDataset/DataLoader pipelines (with MSA caching).
#   4) Initialize GPNBackbone + GPNClassifier with staged freezing/unfreezing.
#   5) Train with AMP, AdamW, cosine LR schedule, and early stopping on val AP.
#   6) Evaluate on test set and produce metrics/plots.
# ------------------------------------------------------
def train_main():
    # ----- Load metadata CSV containing windows and labels -----
    meta = pd.read_csv(METADATA_CSV, dtype=str)
    meta["start"] = meta["start"].astype(int)
    meta["end"] = meta["end"].astype(int)
    # Normalize labels into 0/1 integers from multiple string formats.
    meta["label"] = meta["label"].apply(
        lambda x: 1 if str(x).lower() in ("1","true","t","yes") else 0
    ).astype(int)

    # If gene_id is absent, use a coordinate-based surrogate to group windows.
    if "gene_id" not in meta.columns:
        meta["gene_id"] = meta["chrom"]+":"+meta["start"].astype(str)+"-"+meta["end"].astype(str)

    # Limit the number of windows per gene_id to reduce correlation and imbalance.
    if MAX_WINDOWS_PER_PARENT:
        before_n = len(meta)
        meta = meta.groupby("gene_id").head(MAX_WINDOWS_PER_PARENT).reset_index(drop=True)
        after_n = len(meta)
        print(f"[INFO] per-group window cap: MAX_WINDOWS_PER_PARENT={MAX_WINDOWS_PER_PARENT}")
        print(f"[INFO] windows before/after capping: {before_n} -> {after_n}")

    # Perform group-aware stratified splitting.
    train_df,val_df,test_df = split_dataset(meta)
    
    # ----- Print final split statistics -----
    def _count(df):
        pos = int((df.label == 1).sum())
        neg = int((df.label == 0).sum())
        return pos, neg, len(df)

    p_tr, n_tr, m_tr = _count(train_df)
    p_va, n_va, m_va = _count(val_df)
    p_te, n_te, m_te = _count(test_df)

    print(f"[SPLIT] train pos/neg/total = {p_tr}/{n_tr}/{m_tr}")
    print(f"[SPLIT]   val pos/neg/total = {p_va}/{n_va}/{m_va}")
    print(f"[SPLIT]  test pos/neg/total = {p_te}/{n_te}/{m_te}")
    print(f"✅ Split sizes train/val/test: {len(train_df)}/{len(val_df)}/{len(test_df)}")

    # Compute and log positive class ratios for each split.
    train_pos_ratio = p_tr / m_tr if m_tr > 0 else 0.0
    val_pos_ratio   = p_va / m_va if m_va > 0 else 0.0
    test_pos_ratio  = p_te / m_te if m_te > 0 else 0.0

    print(f"[RATIO] train pos_ratio = {train_pos_ratio:.4f} ({train_pos_ratio*100:.2f}%)")
    print(f"[RATIO]   val pos_ratio = {val_pos_ratio:.4f} ({val_pos_ratio*100:.2f}%)")
    print(f"[RATIO]  test pos_ratio = {test_pos_ratio:.4f} ({test_pos_ratio*100:.2f}%)")

    # Persist split definitions for reproducibility and downstream inspection.
    train_df.to_csv(f"{OUT_DIR}/train_meta.csv", index=False)
    val_df.to_csv(f"{OUT_DIR}/val_meta.csv", index=False)
    test_df.to_csv(f"{OUT_DIR}/test_meta.csv", index=False)
    print("[INFO] Saved split CSVs to OUT_DIR")

    # ----- Construct datasets and loaders -----
    loader = GenomeLoader()
    msa_ds = loader.load_multiz100way_dataset(streaming=True)

    train_ds = SeqMsasDataset(train_df, msa_ds)
    val_ds   = SeqMsasDataset(val_df, msa_ds)
    test_ds  = SeqMsasDataset(test_df, msa_ds)

    train_loader = DataLoader(train_ds,BATCH_SIZE,shuffle=True,collate_fn=collate_msa)
    val_loader   = DataLoader(val_ds,BATCH_SIZE,shuffle=False,collate_fn=collate_msa)
    test_loader  = DataLoader(test_ds,BATCH_SIZE,shuffle=False,collate_fn=collate_msa)

    # ----- Build model: GPNBackbone + GPNClassifier head -----
    backbone = GPNBackbone()
    model = GPNClassifier(backbone).to(DEVICE)
    
    # Initially freeze backbone parameters to stabilize head training.
    model.freeze_backbone()
    print(f"[INFO] Backbone frozen for first {UNFREEZE_EPOCH-1} epochs.")

    # ----- Loss with class imbalance handling -----
    n_pos = (train_df.label==1).sum()
    n_neg = (train_df.label==0).sum()
    pos_weight = torch.tensor([n_neg/max(1,n_pos)], device=DEVICE)
    # BCEWithLogitsLoss with pos_weight implements cost-sensitive learning (pos gets higher weight).
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    # ----- Initial optimizer: train classifier head only -----
    optim = torch.optim.AdamW(
        model.classifier.parameters(),
        lr=LR_HEAD,
        weight_decay=WEIGHT_DECAY
    )
    print("[INFO] Optimizer initialized: classifier head ONLY.")

    # ----- Learning rate scheduler: warmup + cosine decay -----
    warmup = 2
    total_steps = EPOCHS*len(train_loader)

    def lr_lambda(step):
        # Linear warmup for the first 'warmup' steps.
        if step < warmup: return step/warmup
        # Cosine decay for the remaining steps.
        progress = (step-warmup)/max(1,total_steps-warmup)
        return 0.5*(1+math.cos(math.pi*progress))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optim, lr_lambda)

    # AMP scaler for mixed-precision training.
    scaler = GradScaler()

    # ----- Training bookkeeping -----
    history = {"train_loss":[], "val_loss":[], "train_ap":[], "val_ap":[]}
    best_val_ap = -1
    no_improve = 0
    patience = 4
    step_global=0

    for epoch in range(1,EPOCHS+1):
        # ======= Optionally unfreeze backbone at a chosen epoch =======
        if epoch == UNFREEZE_EPOCH:
            print(f"[INFO] Unfreezing backbone at epoch {epoch} ...")
            model.unfreeze_backbone()

            # Switch optimizer to include all model parameters.
            optim = torch.optim.AdamW(
                model.parameters(),
                lr=LR_BACKBONE,       # Smaller LR to avoid disrupting pre-training
                weight_decay=WEIGHT_DECAY
            )
            print("[INFO] Optimizer switched: backbone + head.")

            # Recreate scheduler tied to new optimizer.
            scheduler = torch.optim.lr_scheduler.LambdaLR(optim, lr_lambda)

        # =====================
        # Training loop
        # =====================
        model.train()
        tr_loss=[]; tr_y=[]; tr_p=[]
        print_counter = 0

        for x_ids,aux,y in tqdm(train_loader, desc=f"Train E{epoch}"):
            # For the first few batches, print tensor shapes for sanity checking.
            if print_counter < 3:
                print("[train] x_ids:", x_ids.shape)
                if aux is None:
                    print("[train] aux: None")
                else:
                    print("[train] aux:", aux.shape)
                print("[train] labels:", y.shape)
                print_counter += 1

            optim.zero_grad(set_to_none=True)

            # Enable mixed-precision forward/backward passes.
            with autocast():
                logits = model(input_ids=x_ids, aux_features=aux)
                loss = loss_fn(logits, y)

            # Backprop with gradient scaling (AMP).
            scaler.scale(loss).backward()
            scaler.unscale_(optim)
            # Clip gradient norm to stabilize training.
            torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP_GRAD)
            scaler.step(optim); scaler.update()
            scheduler.step()
            step_global+=1

            # Accumulate metrics.
            tr_loss.append(loss.item())
            tr_y.extend(y.cpu().numpy())
            tr_p.extend(torch.sigmoid(logits).detach().cpu().numpy())

        # Save histogram of predicted probabilities (or logits after sigmoid)
        # to monitor possible collapse (all predictions near 0 or 1).
        plt.figure()
        plt.hist(tr_p,bins=40); plt.title(f"logits epoch {epoch}")
        plt.savefig(f"{PLOTS_DIR}/epoch{epoch}_logits.png"); plt.close()

        train_loss=np.mean(tr_loss)
        train_ap=average_precision_score(tr_y,tr_p)

        # =====================
        # Validation loop
        # =====================
        model.eval()
        va_loss=[]; va_y=[]; va_p=[]
        with torch.no_grad():
            for x_ids,aux,y in val_loader:
                with autocast():
                    logits = model(input_ids=x_ids, aux_features=aux)
                    loss=loss_fn(logits,y)
                va_loss.append(loss.item())
                va_y.extend(y.cpu().numpy())
                va_p.extend(torch.sigmoid(logits).cpu().numpy())

        val_loss=np.mean(va_loss)
        val_ap=average_precision_score(va_y,va_p)
        val_auc=roc_auc_score(va_y,va_p)

        print(f"[E{epoch}] train_loss={train_loss:.4f} val_loss={val_loss:.4f} | train_ap={train_ap:.4f} val_ap={val_ap:.4f} | AUC={val_auc:.4f}")

        # Record epoch-level stats.
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_ap"].append(train_ap)
        history["val_ap"].append(val_ap)

        # ====== Early stopping based on validation AP ======
        if val_ap > best_val_ap:
            best_val_ap = val_ap
            no_improve = 0
            torch.save(model.state_dict(), f"{OUT_DIR}/best.pt")
            print("  -> best model saved.")
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"Early stopping at epoch {epoch}")
                break
            
        # ========== Per-epoch logging to text file ==========
        epoch_log_path = f"{EPOCH_LOG_DIR}/epoch_{epoch}.txt"
        with open(epoch_log_path, "w") as f:
            f.write(f"[Epoch {epoch}]\n")
            f.write(f"train_loss={train_loss:.6f}\n")
            f.write(f"val_loss={val_loss:.6f}\n")
            f.write(f"train_ap={train_ap:.6f}\n")
            f.write(f"val_ap={val_ap:.6f}\n")
            f.write(f"val_auc={val_auc:.6f}\n")
            # Current learning rate for debugging and reproducibility.
            current_lr = optim.param_groups[0]["lr"]
            f.write(f"lr={current_lr:.6e}\n")
            # Mark whether this epoch produced a new best model.
            f.write(f"best_model_saved={'YES' if val_ap > best_val_ap else 'NO'}\n")

        print(f"[Epoch {epoch}] log saved to {epoch_log_path}")

    # ------------------------ Save training curves ------------------------
    plot_training_curves(history, PLOTS_DIR)

    # ------------------------ Final test evaluation ------------------------
    best = torch.load(f"{OUT_DIR}/best.pt", map_location=DEVICE)
    model.load_state_dict(best)
    model.eval()

    # Determine best classification threshold from validation set.
    val_probs=[]; val_true=[]
    with torch.no_grad():
        for x_ids,aux,y in val_loader:
            p = torch.sigmoid(model(input_ids=x_ids,aux_features=aux)).cpu().numpy()
            val_probs.extend(p); val_true.extend(y.cpu().numpy())
    best_thr,best_f1 = find_best_threshold(np.array(val_true), np.array(val_probs))
    print(f"[VAL] Best threshold={best_thr:.3f} F1={best_f1:.4f}")

    # Evaluate on test set at this threshold and plot ROC/PR and confusion matrix.
    ts_p=[]; ts_y=[]
    with torch.no_grad():
        for x_ids,aux,y in test_loader:
            p = torch.sigmoid(model(input_ids=x_ids,aux_features=aux)).cpu().numpy()
            ts_p.extend(p); ts_y.extend(y.cpu().numpy())

    ts_p=np.array(ts_p); ts_y=np.array(ts_y)
    auc,ap = plot_roc_pr(ts_y,ts_p,PLOTS_DIR,"test")
    pred=(ts_p>=best_thr).astype(int)
    cm=confusion_matrix(ts_y.astype(int), pred)

    print(f"[TEST] AUC={auc:.4f} AP={ap:.4f}")
    plot_confusion(cm, f"{PLOTS_DIR}/test_confusion.png")


if __name__ == "__main__":
    # Ensure output directories exist.
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    PLOTS_DIR = f"{OUT_DIR}/plots"
    Path(PLOTS_DIR).mkdir(parents=True, exist_ok=True)
    # 1) Run training (produces OUT_DIR/best.pt and plots/metrics).
    Path(EPOCH_LOG_DIR).mkdir(parents=True, exist_ok=True)
    train_main()
    
    # 2) After training, run chr1 lncRNA prediction + phastCons visualization (optional).
    #    Uncomment and configure the following lines to enable the downstream analysis.
    # gtf_chr1 = GTF_LNCRNA         
    # phastcons_wig = PHASTCONS_FILE
    # out_tsv = f"{MIDDLE_RESULT_DIR_OUT}/chr1_lncrna_pred.tsv"

    # predict_chr1_lncrna(
    #     gtf_path=gtf_chr1,
    #     wig_path=phastcons_wig,
    #     window_size=CONFIG["data"]["window_len"],
    #     window_step=CONFIG["data"]["step"],
    #     out_tsv=out_tsv,
    # )
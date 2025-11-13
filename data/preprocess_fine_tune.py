#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate sliding windows from region files and split by parent gene

- Generate 512bp sliding windows with stride 256
- Save windows.bed / windows.csv
- Split by parent (70/15/15) ensuring same parent doesn't cross splits
- Save train/val/test csv and bed files

Static configuration at top - modify paths/parameters as needed
"""
import os
import math
import argparse
import random
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from src.config import MIDDLE_RESULT_DIR, GTF, FASTA, CHROM, CONFIG, PHASTCONS_FILE, MIDDLE_RESULT_DIR_OUT

# ------------------ Static Configuration ------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = f"{PROJECT_ROOT}/dataset/FineTuningSet2.txt"   # Source file (tab or space separated)
OUT_DIR = f"{MIDDLE_RESULT_DIR_OUT}/windows_out"
WINDOW = 512
STRIDE = 256
START_BASE = 0   # If original start is 1-based, change to 1, else keep 0
RANDOM_SEED = 42
FLANK = 0

# Output file names (under OUT_DIR)
OUT_WINDOWS_BED = "windows_FineTuningSet2.bed"     # tab no header: chrom start end gene_id strand label
OUT_WINDOWS_CSV = "windows_FineTuningSet2.csv"     # full csv with gene_id and label
TRAIN_META = "train_meta.csv"
VAL_META = "val_meta.csv"
TEST_META = "test_meta.csv"
TRAIN_BED = "train_windows.bed"
VAL_BED = "val_windows.bed"
TEST_BED = "test_windows.bed"
# --------------------------------------------------------

def ensure_outdir():
    os.makedirs(OUT_DIR, exist_ok=True)

def read_input(path):
    """
    Try reading input file in various ways, return normalized DataFrame
    Output columns: chrom, start, end, gene_id, strand, label
    Special handling: Conservation -> label, ID -> gene_id
    """
    # Try reading with tab separator (common case with header)
    try:
        df = pd.read_csv(path, sep='\t', engine='python', dtype=str)
    except Exception:
        # Fallback: read with any whitespace separator (possibly no header)
        df = pd.read_csv(path, sep=r'\s+', engine='python', header=0, dtype=str)

    cols = list(df.columns)
    lower = [c.lower() for c in cols]

    # Detect required columns (case insensitive)
    # Support chrom or seqid
    chrom_candidates = ['chrom', 'seqid', 'chr', 'chromosome']
    chrom_col = None
    for cand in chrom_candidates:
        if cand in lower:
            chrom_col = cols[lower.index(cand)]
            break
    
    if chrom_col is None or 'start' not in lower or 'end' not in lower:
        raise RuntimeError("Cannot find chrom/seqid/start/end columns in input file, please check header or file format")
    
    start_col = cols[lower.index('start')]
    end_col = cols[lower.index('end')]

    # gene_id column - try common names (note your file has ID)
    gene_candidates = ('gene_id', 'id', 'name', 'gene', 'ID')
    gene_col = None
    for cand in gene_candidates:
        if cand.lower() in lower:
            gene_col = cols[lower.index(cand.lower())]
            break
    # If not found, use 4th column as id
    if gene_col is None:
        gene_col = cols[3] if len(cols) >= 4 else cols[-2]

    # strand column (optional)
    strand_col = None
    for cand in ('strand',):
        if cand in lower:
            strand_col = cols[lower.index(cand)]
            break

    # conservation column -> label (optional)
    cons_col = None
    for cand in ('conservation', 'mean_phastcons'):
        if cand in lower:
            cons_col = cols[lower.index(cand)]
            break

    # Build normalized DataFrame
    df2 = pd.DataFrame()
    # Remove possible 'chr' prefix to keep consistent with downstream processing
    df2['chrom'] = df[chrom_col].astype(str).str.replace('^chr', '', regex=True)
    # Force convert to int
    df2['start'] = df[start_col].astype(int)
    df2['end'] = df[end_col].astype(int)
    df2['gene_id'] = df[gene_col].astype(str)

    # strand - if doesn't exist fill with '.'
    if strand_col is not None:
        df2['strand'] = df[strand_col].astype(str)
    else:
        df2['strand'] = '.'

    # label: try converting Conservation to numeric, else keep as string
    if cons_col is not None:
        cons_series = pd.to_numeric(df[cons_col], errors='coerce')
        if cons_series.notna().any():
            df2['label'] = cons_series
        else:
            df2['label'] = df[cons_col].astype(str)
    else:
        # If no Conservation column, try using last column as label (fallback)
        last_col = cols[-1]
        df2['label'] = pd.to_numeric(df[last_col], errors='coerce').where(
            pd.to_numeric(df[last_col], errors='coerce').notna(),
            df[last_col].astype(str)
        )

    # Return normalized column order
    return df2[['chrom', 'start', 'end', 'gene_id', 'strand', 'label']]

def normalize_label(col):
    """
    Convert 'TRUE'/'FALSE'/'1'/'0' strings to 1/0
    If numeric string (conservative), keep as is
    """
    def conv(x):
        if pd.isna(x):
            return x
        xs = str(x).strip()
        low = xs.lower()
        if low in ('true','t','yes'):
            return 1
        if low in ('false','f','no'):
            return 0
        if low in ('1','0'):
            return int(low)
        # maybe numeric conservation value -> keep as float
        try:
            v = float(xs)
            return v
        except:
            return xs
    return col.apply(conv)

def generate_windows(df, window=512, stride=256, start_base=0, flank=0, chrom_sizes_path=None):
    """
    Generate sliding windows for each parent with flank on both sides (can be 0)
    If chrom_sizes_path provided (two-column chrom\tlen), will clamp to boundaries
    Returns windows DataFrame with columns: chrom, start, end, gene_id, strand, label
    """
    # load chrom sizes if provided
    chromlen = {}
    if chrom_sizes_path and os.path.exists(chrom_sizes_path):
        with open(chrom_sizes_path) as fh:
            for line in fh:
                parts = line.strip().split()
                if len(parts) >= 2:
                    chromlen[parts[0].replace('chr','chr')] = int(parts[1])

    rows = []
    for _, r in df.iterrows():
        chrom = str(r['chrom'])
        st = int(r['start'])
        en = int(r['end'])
        if start_base == 1:
            st -= 1
        if st < 0:
            st = 0
        gene_id = str(r['gene_id'])
        strand = str(r['strand']) if 'strand' in r.index else '.'
        label = r['label']
        region_len = en - st

        def clamp_bounds(ws, we):
            # clamp to [0, chromlen] if known
            if chrom in chromlen:
                L = chromlen[chrom]
                if ws < 0: ws = 0
                if we > L: we = L
                # if after clamp length < window+2*flank, shift ws to keep window size if possible
                if we - ws < window + 2*flank:
                    need = window + 2*flank - (we - ws)
                    ws = max(0, ws - need)
                    we = min(L, ws + window + 2*flank)
            else:
                if ws < 0: ws = 0
            return int(ws), int(we)

        if region_len >= window:
            n_windows = int((region_len - window) // stride) + 1
            if n_windows < 1:
                n_windows = 1
            # Normal sliding windows
            for i in range(n_windows):
                core_ws = st + i * stride
                core_we = core_ws + window
                ws = core_ws - flank
                we = core_we + flank
                ws, we = clamp_bounds(ws, we)
                # append consistent tuple: chrom, start, end, gene_id, strand, label
                rows.append((chrom, ws, we, gene_id, strand, label))
            # Tail window (if last core window didn't cover region end)
            last_core_start = st + (n_windows - 1) * stride
            last_core_end = last_core_start + window
            if last_core_end < en:
                core_ws = max(st, en - window)
                core_we = core_ws + window
                ws = core_ws - flank
                we = core_we + flank
                ws, we = clamp_bounds(ws, we)
                rows.append((chrom, ws, we, gene_id, strand, label))
        else:
            # region shorter than window, center align
            center = (st + en) // 2
            core_ws = center - window // 2
            core_we = core_ws + window
            ws = core_ws - flank
            we = core_we + flank
            ws, we = clamp_bounds(ws, we)
            rows.append((chrom, ws, we, gene_id, strand, label))

    win_df = pd.DataFrame(rows, columns=['chrom', 'start', 'end', 'gene_id', 'strand', 'label'])
    win_df['start'] = win_df['start'].astype(int)
    win_df['end'] = win_df['end'].astype(int)
    return win_df

def save_windows(win_df):
    bed_path = Path(OUT_DIR) / OUT_WINDOWS_BED
    csv_path = Path(OUT_DIR) / OUT_WINDOWS_CSV
    # bed: chrom start end gene_id strand label (no header)
    win_df[['chrom','start','end','gene_id','strand','label']].to_csv(bed_path, sep='\t', index=False, header=False)
    win_df.to_csv(csv_path, index=False)
    print(f"Saved windows: {len(win_df)} rows -> {bed_path}, {csv_path}")

def split_by_parent(win_df, train_frac=0.7, val_frac=0.15, seed=42):
    """
    Split by parent (group split), try to stratify by parent-level label (via parent's mean label)
    Returns train_df, val_df, test_df
    """
    parent_df = win_df.groupby('gene_id')['label'].agg(list).reset_index()
    # convert possible strings to numeric where possible
    def parent_label_from_list(lst):
        vals = []
        for v in lst:
            try:
                if isinstance(v, (int,float)):
                    vals.append(float(v))
                else:
                    sv = str(v).strip().lower()
                    if sv in ('true','t','yes','1'):
                        vals.append(1.0)
                    elif sv in ('false','f','no','0'):
                        vals.append(0.0)
                    else:
                        vals.append(float(sv))
            except:
                pass
        if len(vals) == 0:
            return 0
        if all((x in (0.0,1.0) for x in vals)):
            return int(round(np.mean(vals)))
        med = float(np.median(vals))
        return int((np.mean(vals) >= med))
    parent_df['group_label'] = parent_df['label'].apply(parent_label_from_list)
    parents = parent_df['gene_id'].tolist()
    group_labels = parent_df['group_label'].tolist()

    train_p, tmp_p = train_test_split(parents, train_size=train_frac, random_state=seed, stratify=group_labels)
    val_frac_rel = val_frac / (1.0 - train_frac)
    val_p, test_p = train_test_split(tmp_p, train_size=val_frac_rel, random_state=seed)

    train_df = win_df[win_df['gene_id'].isin(train_p)].reset_index(drop=True)
    val_df = win_df[win_df['gene_id'].isin(val_p)].reset_index(drop=True)
    test_df = win_df[win_df['gene_id'].isin(test_p)].reset_index(drop=True)
    return train_df, val_df, test_df

def save_splits(train_df, val_df, test_df):
    # save csv
    train_df.to_csv(Path(OUT_DIR)/TRAIN_META, index=False)
    val_df.to_csv(Path(OUT_DIR)/VAL_META, index=False)
    test_df.to_csv(Path(OUT_DIR)/TEST_META, index=False)
    # save bed versions (chrom start end gene_id strand label)
    train_df[['chrom','start','end','gene_id','strand','label']].to_csv(Path(OUT_DIR)/TRAIN_BED, sep='\t', index=False, header=False)
    val_df[['chrom','start','end','gene_id','strand','label']].to_csv(Path(OUT_DIR)/VAL_BED, sep='\t', index=False, header=False)
    test_df[['chrom','start','end','gene_id','strand','label']].to_csv(Path(OUT_DIR)/TEST_BED, sep='\t', index=False, header=False)
    print("Saved splits:")
    print(f"  train: {len(train_df)}, val: {len(val_df)}, test: {len(test_df)}")
    print(f"Files in {OUT_DIR}: {TRAIN_META}, {VAL_META}, {TEST_META}")

def main():
    ensure_outdir()
    print("Reading input:", INPUT_PATH)
    df = read_input(INPUT_PATH)
    # normalize labels (TRUE/FALSE -> 1/0 or float)
    df['label'] = normalize_label(df['label'])
    # generate windows
    print("Generating windows: window=", WINDOW, "stride=", STRIDE, "start_base=", START_BASE, "flank=", FLANK)
    win_df = generate_windows(df, window=WINDOW, stride=STRIDE, start_base=START_BASE, flank=FLANK)
    # save windows
    save_windows(win_df)
    # split by parent and save splits as CSV (no JSON)
    # Uncomment the following two lines if you want to immediately save splits
    # train_df, val_df, test_df = split_by_parent(win_df, train_frac=0.7, val_frac=0.15, seed=RANDOM_SEED)
    # save_splits(train_df, val_df, test_df)
    print("Done.")

if __name__ == "__main__":
    main()

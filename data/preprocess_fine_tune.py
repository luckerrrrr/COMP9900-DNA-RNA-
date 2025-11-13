#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_windows_and_splits.py
- 从 region 表（bed/tsv）生成 512bp sliding windows（stride 256）
- 保存 windows.bed / windows.csv
- 按 parent 做 70/15/15 划分（保证同 parent 不会跨 split）
- 保存 train/val/test 的 csv 与 bed
注意：静态配置在文件顶部，运行前按需修改路径或参数
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

# ------------------ 静态配置区（改这里） ------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = f"{PROJECT_ROOT}/dataset/FineTuningSet2.txt"   # 源文件（tab 分隔或空白分隔），可带 header 或无 header
OUT_DIR = f"{MIDDLE_RESULT_DIR_OUT}/windows_out"
WINDOW = 512
STRIDE = 256
START_BASE = 0   # 如果原始 start 是 1-based，改成 1，否则保持 0
RANDOM_SEED = 42
FLANK = 0

# 输出文件名（在 OUT_DIR 下）
OUT_WINDOWS_BED = "windows_FineTuningSet2.bed"     # tab 无 header: chrom start end gene_id strand label
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
    """尝试用多种方式读取输入文件，返回 DataFrame，列规范化：
       输出列为: chrom,start,end,gene_id,strand,label
       特别处理：Conservation -> label, ID -> gene_id
    """
    # 先尝试以 tab 读取（有 header 的常见情况）
    try:
        df = pd.read_csv(path, sep='\t', engine='python', dtype=str)
    except Exception:
        # 兜底：用任意空白分隔读取（可能无 header）
        df = pd.read_csv(path, sep=r'\s+', engine='python', header=0, dtype=str)

    cols = list(df.columns)
    lower = [c.lower() for c in cols]

    # 必要列检测并选择列名（大小写不敏感）
    if 'chrom' in lower and 'start' in lower and 'end' in lower:
        chrom_col = cols[lower.index('chrom')]
        start_col = cols[lower.index('start')]
        end_col = cols[lower.index('end')]
    else:
        raise RuntimeError("无法在输入文件中找到 chrom/start/end 列，请检查 header 或文件格式。")

    # gene_id 列优先匹配常见名称（注意你的文件中是 ID）
    gene_candidates = ('gene_id', 'id', 'name', 'gene', 'ID')
    gene_col = None
    for cand in gene_candidates:
        if cand.lower() in lower:
            gene_col = cols[lower.index(cand.lower())]
            break
    # 如果没找到，使用第4列作为 id
    if gene_col is None:
        gene_col = cols[3] if len(cols) >= 4 else cols[-2]

    # strand 列（可选）
    strand_col = None
    for cand in ('strand',):
        if cand in lower:
            strand_col = cols[lower.index(cand)]
            break

    # conservation 列 -> label（可选）
    cons_col = None
    for cand in ('conservation', 'mean_phastcons'):
        if cand in lower:
            cons_col = cols[lower.index(cand)]
            break

    # 构造规范化的 DataFrame
    df2 = pd.DataFrame()
    # 去掉可能的 'chr' 前缀，保持与后续处理一致
    df2['chrom'] = df[chrom_col].astype(str).str.replace('^chr', '', regex=True)
    # 强制转换为 int
    df2['start'] = df[start_col].astype(int)
    df2['end'] = df[end_col].astype(int)
    df2['gene_id'] = df[gene_col].astype(str)

    # strand 如果不存在则填 '.'
    if strand_col is not None:
        df2['strand'] = df[strand_col].astype(str)
    else:
        df2['strand'] = '.'

    # label：优先把 Conservation 尝试转换为数值，否则保留原字符串
    if cons_col is not None:
        cons_series = pd.to_numeric(df[cons_col], errors='coerce')
        if cons_series.notna().any():
            df2['label'] = cons_series
        else:
            df2['label'] = df[cons_col].astype(str)
    else:
        # 如果没有 Conservation 列，尝试把最后一列作为标签（fallback）
        last_col = cols[-1]
        df2['label'] = pd.to_numeric(df[last_col], errors='coerce').where(
            pd.to_numeric(df[last_col], errors='coerce').notna(),
            df[last_col].astype(str)
        )

    # 返回规范列顺序
    return df2[['chrom', 'start', 'end', 'gene_id', 'strand', 'label']]

def normalize_label(col):
    """把 'TRUE'/'FALSE'/'1'/'0' 等字符串转成 1/0，如果是数值字符串(保守性)保持原样"""
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

# Replace generate_windows with this corrected version:
def generate_windows(df, window=512, stride=256, start_base=0, flank=0, chrom_sizes_path=None):
    """对每个 parent 划窗并在每个 window 两侧加 flank（可为 0）。
       如果提供 chrom_sizes_path（two-column chrom\\tlen），会 clamp 到边界。
       返回 windows DataFrame with columns: chrom,start,end,gene_id,strand,label
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
            # 正常滑窗
            for i in range(n_windows):
                core_ws = st + i * stride
                core_we = core_ws + window
                ws = core_ws - flank
                we = core_we + flank
                ws, we = clamp_bounds(ws, we)
                # append consistent tuple: chrom, start, end, gene_id, strand, label
                rows.append((chrom, ws, we, gene_id, strand, label))
            # tail 窗口（如果最后一个 core window 没覆盖到 region 结尾）
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
            # region 比 window 短，中心对齐
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
    """按 parent 做 group split，尽量按 parent-level label 做 stratify（通过 parent 的 mean label）
       返回 train_df, val_df, test_df
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
    # 如果需要立即保存 split，取消注释下面两行
    # train_df, val_df, test_df = split_by_parent(win_df, train_frac=0.7, val_frac=0.15, seed=RANDOM_SEED)
    # save_splits(train_df, val_df, test_df)
    print("Done.")

if __name__ == "__main__":
    main()

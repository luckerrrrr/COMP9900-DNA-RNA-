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
INPUT_PATH = f"{PROJECT_ROOT}/dataset/FineTuningSet1.head.bed"   # 源文件（tab 分隔或空白分隔），可带 header 或无 header
OUT_DIR = f"{MIDDLE_RESULT_DIR_OUT}/windows_out"
WINDOW = 512
STRIDE = 256
START_BASE = 0   # 如果原始 start 是 1-based，改成 1，否则保持 0
RANDOM_SEED = 42
FLANK = 128   

# 输出文件名（在 OUT_DIR 下）
OUT_WINDOWS_BED = "windows.bed"     # tab 无 header: chrom start end window_id label
OUT_WINDOWS_CSV = "windows.csv"     # full csv with parent_id and label
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
    """尝试用多种方式读取输入文件，返回 DataFrame，列规范化： chrom,start,end,id,label 或 Conservation """
    # 先尝试 tab 读取（常见）
    df = pd.read_csv(path, sep='\t', engine='python', dtype=str)
    cols = list(df.columns)
    lower = [c.lower() for c in cols]
    # detect common header formats
    if 'chrom' in lower and 'start' in lower and 'end' in lower:
        chrom_col = cols[lower.index('chrom')]
        start_col = cols[lower.index('start')]
        end_col = cols[lower.index('end')]
        # id could be 'id' or 'name' or 4th col
        if 'id' in lower:
            id_col = cols[lower.index('id')]
        elif 'name' in lower:
            id_col = cols[lower.index('name')]
        else:
            id_col = cols[3] if len(cols) >= 4 else cols[-2]
        if 'label' in lower:
            label_col = cols[lower.index('label')]
        elif 'conservation' in lower:
            label_col = cols[lower.index('conservation')]
        else:
            label_col = cols[-1]
    else:
        # maybe whitespace-separated without header; try fallback: assume columns:
        # chrom start end id label  OR index chrom start end id label
        df2 = pd.read_csv(path, sep=r'\s+', engine='python', header=None, dtype=str)
        # prefer 5 columns (chrom,start,end,id,label)
        if df2.shape[1] >= 5:
            # if first col is numeric index -> drop it
            if df2.shape[1] >= 6 and all(x.isdigit() for x in df2.iloc[:10,0].astype(str)):
                df2 = df2.drop(columns=[0]).reset_index(drop=True)
            df2.columns = ['chrom','start','end','id','label'] + list(df2.columns[5:])
            return df2[['chrom','start','end','id','label']]
        else:
            raise RuntimeError("无法识别输入文件列，请检查格式或加 header。")
    # build normalized df
    df2 = pd.DataFrame()
    df2['chrom'] = df[chrom_col].astype(str).str.replace('^chr','', regex=True).apply(lambda x: x)
    # numeric
    df2['start'] = df[start_col].astype(int)
    df2['end'] = df[end_col].astype(int)
    df2['id'] = df[id_col].astype(str)
    df2['label'] = df[label_col].astype(str)
    return df2[['chrom','start','end','id','label']]

def normalize_label(col):
    """把 'TRUE'/'FALSE'/'1'/'0' 等字符串转成 1/0，如果是数值字符串(保守性)保持原样"""
    def conv(x):
        if pd.isna(x):
            return x
        xs = str(x).strip()
        low = xs.lower()
        if low in ('true','t','yes','1'):
            return 1
        if low in ('false','f','no','0'):
            return 0
        # maybe numeric conservation value -> keep as float string
        try:
            v = float(xs)
            return v
        except:
            return xs
    return col.apply(conv)

# Replace generate_windows with this version:
def generate_windows(df, window=512, stride=256, start_base=0, flank=0, chrom_sizes_path=None):
    """对每个 parent 划窗并在每个 window 两侧加 flank（可为 0）。
       如果提供 chrom_sizes_path（two-column chrom\\tlen），会 clamp 到边界。
       返回 windows DataFrame with columns: chrom,start,end,window_id,parent_id,label
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
        parent_id = str(r['id'])
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
                    # try to expand on left if possible
                    need = window + 2*flank - (we - ws)
                    ws = max(0, ws - need)
                    # recompute we if still less than L
                    we = min(L, ws + window + 2*flank)
            else:
                if ws < 0: ws = 0
            return int(ws), int(we)

        if region_len >= window:
            n_windows = int((region_len - window) // stride) + 1
            if n_windows < 1:
                n_windows = 1
            for i in range(n_windows):
                core_ws = st + i * stride
                core_we = core_ws + window
                ws = core_ws - flank
                we = core_we + flank
                # clamp
                ws, we = clamp_bounds(ws, we)
                win_id = f"{parent_id}:{i}"
                rows.append((chrom, ws, we, win_id, parent_id, label))
            # tail window
            last_start = st + (n_windows - 1) * stride
            last_end = last_start + window
            if last_end < en:
                core_ws = max(st, en - window)
                core_we = core_ws + window
                ws = core_ws - flank
                we = core_we + flank
                ws, we = clamp_bounds(ws, we)
                win_id = f"{parent_id}:{n_windows}"
                rows.append((chrom, ws, we, win_id, parent_id, label))
        else:
            # short region: center expand core then add flank
            center = (st + en) // 2
            core_ws = center - window // 2
            core_we = core_ws + window
            ws = core_ws - flank
            we = core_we + flank
            ws, we = clamp_bounds(ws, we)
            win_id = f"{parent_id}:0"
            rows.append((chrom, ws, we, win_id, parent_id, label))

    win_df = pd.DataFrame(rows, columns=['chrom','start','end','window_id','parent_id','label'])
    win_df['start'] = win_df['start'].astype(int)
    win_df['end'] = win_df['end'].astype(int)
    return win_df

def save_windows(win_df):
    bed_path = Path(OUT_DIR) / OUT_WINDOWS_BED
    csv_path = Path(OUT_DIR) / OUT_WINDOWS_CSV
    # bed: chrom start end window_id label (no header)
    win_df[['chrom','start','end','window_id','label']].to_csv(bed_path, sep='\t', index=False, header=False)
    win_df.to_csv(csv_path, index=False)
    print(f"Saved windows: {len(win_df)} rows -> {bed_path}, {csv_path}")

def split_by_parent(win_df, train_frac=0.7, val_frac=0.15, seed=42):
    """按 parent 做 group split，尽量按 parent-level label 做 stratify（通过 parent 的 mean label）
       返回 train_df, val_df, test_df
    """
    # 计算 parent-level label（如果 label 是 0/1，则 mean 四舍五入），否则按字符串分布（fallback）
    parent_df = win_df.groupby('parent_id')['label'].agg(list).reset_index()
    # convert possible strings to numeric where possible
    def parent_label_from_list(lst):
        # lst may contain 'TRUE'/'FALSE' or numeric strings or mixed
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
                        # try float
                        vals.append(float(sv))
                # append succeeded
            except:
                # cannot parse -> ignore
                pass
        if len(vals) == 0:
            return 0
        # if values are 0/1 then majority
        if all((x in (0.0,1.0) for x in vals)):
            return int(round(np.mean(vals)))
        # else treat numeric conservation: threshold at median to produce group label
        med = float(np.median(vals))
        return int((np.mean(vals) >= med))
    parent_df['group_label'] = parent_df['label'].apply(parent_label_from_list)
    parents = parent_df['parent_id'].tolist()
    group_labels = parent_df['group_label'].tolist()

    # split parents -> train / tmp
    train_p, tmp_p = train_test_split(parents, train_size=train_frac, random_state=seed, stratify=group_labels)
    # compute relative val fraction inside tmp
    tmp_frac = 1.0 - train_frac
    val_rel = val_frac / (val_frac + (1 - train_frac - val_frac)) if False else val_frac / (val_frac + (1 - train_frac - val_frac))
    # actually simpler: split tmp into val/test equally by desired proportions:
    # desired val_frac and test_frac are relative to total; so val_frac_rel = val_frac / (1-train_frac)
    val_frac_rel = val_frac / (1.0 - train_frac)
    val_p, test_p = train_test_split(tmp_p, train_size=val_frac_rel, random_state=seed)
    # build dfs
    train_df = win_df[win_df['parent_id'].isin(train_p)].reset_index(drop=True)
    val_df = win_df[win_df['parent_id'].isin(val_p)].reset_index(drop=True)
    test_df = win_df[win_df['parent_id'].isin(test_p)].reset_index(drop=True)
    return train_df, val_df, test_df

def save_splits(train_df, val_df, test_df):
    # save csv
    train_df.to_csv(Path(OUT_DIR)/TRAIN_META, index=False)
    val_df.to_csv(Path(OUT_DIR)/VAL_META, index=False)
    test_df.to_csv(Path(OUT_DIR)/TEST_META, index=False)
    # save bed versions (chrom start end window_id label)
    train_df[['chrom','start','end','window_id','label']].to_csv(Path(OUT_DIR)/TRAIN_BED, sep='\t', index=False, header=False)
    val_df[['chrom','start','end','window_id','label']].to_csv(Path(OUT_DIR)/VAL_BED, sep='\t', index=False, header=False)
    test_df[['chrom','start','end','window_id','label']].to_csv(Path(OUT_DIR)/TEST_BED, sep='\t', index=False, header=False)
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
    print("Generating windows: window=", WINDOW, "stride=", STRIDE, "start_base=", START_BASE)
    win_df = generate_windows(df, window=WINDOW, stride=STRIDE, start_base=START_BASE, flank=FLANK)
    # save windows
    save_windows(win_df)
    # split by parent
    # train_df, val_df, test_df = split_by_parent(win_df, train_frac=0.7, val_frac=0.15, seed=RANDOM_SEED)
    # # save splits
    # save_splits(train_df, val_df, test_df)
    print("Done.")

if __name__ == "__main__":
    main()

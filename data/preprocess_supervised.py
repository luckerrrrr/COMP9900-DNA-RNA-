#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preprocess.py

Pipeline:
1) Read conservation txt:
   Columns: Chrom, Start, End, ID, strand, Conservation
2) Rename columns:
   Chrom, Start, End, ID, strand, Conservation
   -> chrom, start, end, gene_id, strand, label
3) Sample 10,000 TRUE + 10,000 FALSE rows (if available).
   Optionally save sampled table as CSV.
4) For each region (chrom, start, end):
   - extend by flanking bp
   - generate sliding windows (win=512, step=256)
5) Annotate each window with sequence from genome FASTA.
6) Save final CSV:
   chrom,start,end,gene_id,strand,label,sequence
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import pandas as pd

from src.config import MIDDLE_RESULT_DIR, GTF, FASTA, CHROM, CONFIG
from utils.utils import norm_chrom_name


# ---------------------------
# FASTA loader (原样保留)
# ---------------------------

class FastaLoader:
    """
    Simple FASTA loader that stores each chromosome sequence in memory.
    Keys are normalized by norm_chrom_name(header).

    Supports FASTA like:
        >chr1 1
        NNNNN...
        >chr2 2
        NNNNN...
    """

    def __init__(self, fasta_path: str):
        self.fasta_path = Path(fasta_path)
        self.sequences = {}  # chrom -> sequence (uppercase)

    def load(self):
        if not self.fasta_path.exists():
            raise FileNotFoundError(f"FASTA not found: {self.fasta_path}")
        cur_chrom = None
        cur_seq_parts = []
        with open(self.fasta_path, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    # flush previous
                    if cur_chrom is not None:
                        seq = "".join(cur_seq_parts).upper()
                        self.sequences[cur_chrom] = seq
                    # parse new header: take first token, e.g. "chr1 1" -> "chr1"
                    header = line[1:].split()[0]
                    cur_chrom = norm_chrom_name(header)
                    cur_seq_parts = []
                else:
                    cur_seq_parts.append(line)
            # flush last
            if cur_chrom is not None:
                seq = "".join(cur_seq_parts).upper()
                self.sequences[cur_chrom] = seq

    def fetch(self, chrom: str, start: int, end: int) -> Optional[str]:
        """
        chrom: '1' or 'chr1' accepted
        start, end: 1-based inclusive
        """
        key = norm_chrom_name(chrom)
        seq = self.sequences.get(key)
        if seq is None:
            return None
        # convert to 0-based slicing
        s0 = max(0, start - 1)
        e0 = end  # inclusive in 1-based -> exclusive in 0-based slice
        if e0 > len(seq):
            return None
        return seq[s0:e0]


# ---------------------------
# Step 1: 从 txt 读数据 + 改列名 + 抽样
# ---------------------------

def load_conservation_txt(txt_path: str) -> pd.DataFrame:
    """
    Load raw conservation txt/tsv file.

    Expected header like:
        Chrom    Start    End    ID    strand    Conservation
    or
        seqid    start    end    ID    strand    Conservation
    """
    p = Path(txt_path)
    if not p.exists():
        raise FileNotFoundError(f"Input txt not found: {p}")

    # 默认用制表符；如果你的文件是空格分隔，可以改成 delim_whitespace=True
    df = pd.read_csv(p, sep="\t")
    return df


def rename_conservation_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns:
        Chrom, Start, End, ID, strand, Conservation
    ->  chrom, start, end, gene_id, strand, label

    Only keep the 6 target columns.
    """
    rename_map = {}

    # chrom
    if "Chrom" in df.columns:
        rename_map["Chrom"] = "chrom"
    elif "seqid" in df.columns:
        rename_map["seqid"] = "chrom"

    # start / end
    if "Start" in df.columns:
        rename_map["Start"] = "start"
    if "End" in df.columns:
        rename_map["End"] = "end"

    # id
    if "ID" in df.columns:
        rename_map["ID"] = "gene_id"

    # strand / Conservation
    if "strand" in df.columns:
        rename_map["strand"] = "strand"
    if "Conservation" in df.columns:
        rename_map["Conservation"] = "label"

    df = df.rename(columns=rename_map)

    required_cols = ["chrom", "start", "end", "gene_id", "strand", "label"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns after rename: {missing}")

    df["start"] = df["start"].astype(int)
    df["end"] = df["end"].astype(int)

    # 保留并按顺序排列
    df = df[required_cols]
    return df


def sample_true_false_balanced(
    df: pd.DataFrame,
    n_true: int = 10000,
    n_false: int = 10000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    From a DataFrame with 'label' column (TRUE/FALSE or bool),
    sample up to n_true rows with label TRUE,
    and up to n_false rows with label FALSE.
    """
    # 统一成字符串再比较
    lab = df["label"].astype(str).str.upper()
    df_true = df[lab == "TRUE"].copy()
    df_false = df[lab == "FALSE"].copy()

    if len(df_true) == 0 or len(df_false) == 0:
        raise ValueError(
            f"No TRUE/FALSE rows found. TRUE={len(df_true)}, FALSE={len(df_false)}"
        )

    n_true_sample = min(n_true, len(df_true))
    n_false_sample = min(n_false, len(df_false))

    df_true_sampled = df_true.sample(n=n_true_sample, random_state=seed)
    df_false_sampled = df_false.sample(n=n_false_sample, random_state=seed)

    df_combined = pd.concat([df_true_sampled, df_false_sampled], axis=0)
    df_combined = (
        df_combined.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    )
    return df_combined


def load_and_sample_labels(
    txt_path: str,
    n_true: int = 10000,
    n_false: int = 10000,
    middle_csv: Optional[str] = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    入口函数：
    1) 从 txt 读原始表
    2) 改列名 -> chrom,start,end,gene_id,strand,label
    3) TRUE/FALSE 各抽样 n_true/n_false
    4) 可选保存中间 CSV
    """
    print(f"[STEP] Load conservation txt: {txt_path}")
    df_raw = load_conservation_txt(txt_path)
    print(f"  Loaded {len(df_raw)} rows")

    print("[STEP] Rename columns → chrom,start,end,gene_id,strand,label")
    df_renamed = rename_conservation_columns(df_raw)
    print(f"  After rename: {len(df_renamed)} rows")

    if n_true is not None and n_false is not None:
        print(
        f"[STEP] Sample TRUE/FALSE: n_true={n_true}, n_false={n_false}, seed={seed}"
        )
        df_sampled = sample_true_false_balanced(
            df_renamed, n_true=n_true, n_false=n_false, seed=seed
        )
        print(f"  Sampled total {len(df_sampled)} rows")
    else:
        df_sampled = df_renamed

    if middle_csv is not None:
        outp = Path(middle_csv)
        outp.parent.mkdir(parents=True, exist_ok=True)
        df_sampled.to_csv(outp, sep="\t", index=False)
        print(f"  Saved sampled labels → {outp}")

    return df_sampled


# ---------------------------
# Step 2: 用 df 做滑动窗口
# ---------------------------

def make_sliding_windows_from_df(
    df: pd.DataFrame,
    flanking: int = 100,
    win: int = 512,
    step: int = 256,
) -> List[Dict]:
    """
    For each row in df (chrom, start, end, gene_id, strand, label),
    extend by flanking on both sides and create sliding windows.

    Returns:
        List[dict] with keys:
            chrom, start, end, gene_id, strand, label
    (no sequence yet)
    """
    windows: List[Dict] = []

    for _, row in df.iterrows():
        chrom = norm_chrom_name(str(row["chrom"]))
        region_start = int(row["start"])
        region_end = int(row["end"])
        gene_id = row["gene_id"]
        strand = row["strand"]
        label = row["label"]

        s = max(1, region_start - flanking)
        e = region_end + flanking

        pos = s
        while pos + win - 1 <= e:
            windows.append(
                {
                    "chrom": chrom,
                    "start": int(pos),
                    "end": int(pos + win - 1),
                    "gene_id": gene_id,
                    "strand": strand,
                    "label": label,
                }
            )
            pos += step

    print(f"[STEP] Sliding windows generated: {len(windows)}")
    return windows


# ---------------------------
# Step 3: 用 FASTA 标注 seq 并存文件
# ---------------------------

class SequenceAnnotator:
    """
    Use FastaLoader to fetch sequence for each window and save final CSV.
    """

    def __init__(self, fasta_path: str):
        self.fasta_loader = FastaLoader(fasta_path)

    def annotate_and_save(
        self,
        windows: List[Dict],
        win: int,
        output_csv: str,
    ) -> pd.DataFrame:
        """
        windows: list of dict (chrom,start,end,gene_id,strand,label)
        win: window length, e.g. 512
        """
        print(f"[STEP] Loading FASTA from {self.fasta_loader.fasta_path}")
        self.fasta_loader.load()
        print(
            f"  Loaded chromosomes: {list(self.fasta_loader.sequences.keys())[:10]} (showing up to 10)"
        )

        results = []
        skipped = 0

        for i, w in enumerate(windows):
            seq = self.fasta_loader.fetch(w["chrom"], w["start"], w["end"])
            if seq is None or len(seq) != win:
                skipped += 1
                continue

            rec = {
                "chrom": w["chrom"],
                "start": w["start"],
                "end": w["end"],
                "gene_id": w["gene_id"],
                "strand": w["strand"],
                "label": w["label"],
                "sequence": seq,
            }
            results.append(rec)

        print(
            f"[STEP] Sequence annotation done: kept={len(results)}, skipped={skipped}"
        )

        df_final = pd.DataFrame(results)
        df_final["chrom"] = df_final["chrom"].apply(lambda x: norm_chrom_name(str(x)))
        outp = Path(output_csv)
        outp.parent.mkdir(parents=True, exist_ok=True)
        df_final.to_csv(outp, index=False)
        print(f"[STEP] Saved final windows with sequence → {outp}")
        return df_final


# ---------------------------
# main: 串起来整个流程
# ---------------------------

if __name__ == "__main__":
    """
    流程：
    1) 把 GTF 当成 txt 路径使用（你现在 GTF 指向的就是 txt）
    2) 从 txt 读 + 改列名 + TRUE/FALSE 各抽 10000，存一个中间 CSV
    3) 用 df 做滑动窗口
    4) 用 FASTA 标 seq，存最终 CSV
    """

    # 1) load + sample labels from txt
    label_txt_path = GTF  # 这里现在应指向你的 txt 文件
    sampled_csv_path = f"{MIDDLE_RESULT_DIR}/conservation_sample_set2.tsv"

    df_labels = load_and_sample_labels(
        txt_path=label_txt_path,
        n_true=None,
        n_false=None,
        middle_csv=sampled_csv_path,
        seed=42,
    )

    # 2) 可选：根据 CHROM 筛选（如果你 config 里 CHROM 不是 'all'）
    chrom_norm = norm_chrom_name(str(CHROM)) if CHROM else None
    if chrom_norm and chrom_norm.lower() not in ("all", "whole", "none"):
        before = len(df_labels)
        df_labels = df_labels[
            df_labels["chrom"].apply(
                lambda x: norm_chrom_name(str(x)) == chrom_norm
            )
        ]
        print(
            f"[STEP] Filter by CHROM={CHROM}: {before} -> {len(df_labels)} regions"
        )

    # 3) sliding windows
    flanking = CONFIG["data"]["flanking"]
    win = CONFIG["data"]["window_len"]
    step = CONFIG["data"]["step"]

    windows_meta = make_sliding_windows_from_df(
        df_labels, flanking=flanking, win=win, step=step
    )

    # 4) sequence annotation + save final CSV
    out_csv = f"{MIDDLE_RESULT_DIR}/fine_tune_windows_with_seq_set2.csv"
    annotator = SequenceAnnotator(FASTA)
    annotator.annotate_and_save(windows_meta, win=win, output_csv=out_csv)

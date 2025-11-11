#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preprocess.py
Generate sliding windows from GENCODE GTF and genome FASTA.
Output records in the structure requested by the user:
{
 "chr": "1",
 "start": 100000,
 "end": 100511,
 "gene_id":"ENSG...",
 "gene_type":"protein_coding",
 "source": "GENCODE",
 "sequence": "ATCG..."
}
Sliding window defaults: flanking=100, win=512, step=256
No masking, no gene_type distribution control.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
from src.config import MIDDLE_RESULT_DIR, GTF, FASTA, CHROM, CONFIG, PHASTCONS_FILE
from utils.utils import norm_chrom_name
from data.wigfix_loader import WigFixLoader

# ---------------------------
# Helpers
# ---------------------------
def parse_attr_value(attr_str: str, key: str) -> Optional[str]:
    """
    从 GTF attribute 字段里解析 key 的值（如 gene_id, gene_type）。
    attr_str 形如: 'gene_id "ENSG..."; gene_type "protein_coding"; ...'
    """
    if not isinstance(attr_str, str):
        return None
    for part in attr_str.split(";"):
        part = part.strip()
        if not part:
            continue
        if part.startswith(key):
            # try "value" pattern
            if '"' in part:
                parts = part.split('"')
                if len(parts) >= 2:
                    return parts[1]
            # fallback: split by whitespace
            toks = part.split()
            if len(toks) >= 2:
                return toks[1]
    return None

# ---------------------------
# FASTA loader
# ---------------------------
class FastaLoader:
    """
    Simple FASTA loader that stores each chromosome sequence in memory.
    Keys are normalized by norm_chrom_name(header).
    """
    def __init__(self, fasta_path: str):
        self.fasta_path = Path(fasta_path)
        self.sequences = {}  # chrom -> sequence (uppercase)
    
    def load(self):
        if not self.fasta_path.exists():
            raise FileNotFoundError(f"FASTA not found: {self.fasta_path}")
        cur_chrom = None
        cur_seq_parts = []
        with open(self.fasta_path, 'r') as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('>'):
                    # flush previous
                    if cur_chrom is not None:
                        seq = "".join(cur_seq_parts).upper()
                        self.sequences[cur_chrom] = seq
                    # parse new header
                    header = line[1:].split()[0]  # take first token
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
        e0 = end  # python slice stops before index, but we want inclusive end so use end
        if e0 > len(seq):
            return None
        return seq[s0:e0]

# ---------------------------
# Main processor
# ---------------------------
class GencodeWindowGenerator:
    def __init__(self, gtf_path: str, fasta_path: str):
        self.gtf_path = Path(gtf_path)
        self.fasta_path = Path(fasta_path)
        if not self.gtf_path.exists():
            raise FileNotFoundError(f"GTF not found: {self.gtf_path}")
        if not self.fasta_path.exists():
            raise FileNotFoundError(f"FASTA not found: {self.fasta_path}")
        self.fasta = FastaLoader(fasta_path)
        self.wig = WigFixLoader()
    
    def parse_gtf(self) -> pd.DataFrame:
        cols = ["chr", "source", "feature", "start", "end", "score", "strand", "frame", "attribute"]
        gtf = pd.read_csv(self.gtf_path, sep="\t", comment="#", header=None, names=cols, dtype={"chr": str})
        return gtf

    def generate_windows_from_features(self,
                                   chrom: str,
                                   flanking: int = 100,
                                   win: int = 512,
                                   step: int = 256
                                  ) -> List[Dict]:
        """
        从 GTF 中指定染色体提取所有注释（不再按 feature 过滤），对每个注释扩展 flanking 并生成滑动窗口。
        返回：list of dict，每个 dict 包含 minimal meta（未包含 sequence）
        """
        gtf = self.parse_gtf()
        # 只选指定染色体的所有注释行（统一 chrom 名称）
        # 先尝试直接包含匹配（避免误匹配），再 fallback 到规范名比较
        chrom_str = str(chrom)
        gtf_chr = gtf[gtf["chr"].astype(str).str.replace("'", "").str.replace('"', '').str.contains(chrom_str, regex=False)]
        if gtf_chr.empty:
            gtf_chr = gtf[gtf["chr"].apply(lambda x: norm_chrom_name(str(x)) == norm_chrom_name(chrom_str))]

        if gtf_chr.empty:
            return []

        windows = []
        for _, row in gtf_chr.iterrows():
            try:
                s = max(1, int(row["start"]) - flanking)
                e = int(row["end"]) + flanking
            except Exception:
                continue

            gene_id = parse_attr_value(row.get("attribute", ""), "gene_id") or ""
            gene_type = parse_attr_value(row.get("attribute", ""), "gene_type") or ""
            src = row.get("source", "GENCODE") or "GENCODE"

            pos = s
            while pos + win - 1 <= e:
                windows.append({
                    "chr": norm_chrom_name(str(row["chr"])),
                    "start": int(pos),
                    "end": int(pos + win - 1),
                    "gene_id": gene_id,
                    "gene_type": gene_type,
                    "source": src
                })
                pos += step

        # 去重 (chr, start, end, gene_id)
        seen = set()
        uniq = []
        for w in windows:
            key = (w["chr"], w["start"], w["end"], w["gene_id"])
            if key not in seen:
                seen.add(key)
                uniq.append(w)
        return uniq


    def run(self,
            chrom: str,
            output_path: str,
            flanking: int = 100,
            win: int = 512,
            step: int = 256,
            wig_path: Optional[str] = None,
           ) -> List[Dict]:
        """
        主运行函数：生成 windows、加载 fasta、填充 sequence 字段并写出 JSON 文件
        """
        print(f"Generating windows for chrom={chrom} (flank={flanking}, win={win}, step={step})")
        windows_meta = self.generate_windows_from_features(chrom=chrom, flanking=flanking, win=win, step=step)
        print(f"Found {len(windows_meta)} candidate windows (before fetch)")

        # load fasta once
        print("Loading FASTA into memory...")
        self.fasta.load()
        if wig_path:
            self.wig.load(wig_path, verbose=True)  
        print(f"Loaded chromosomes: {list(self.fasta.sequences.keys())[:10]} (showing up to 10)")

        results = []
        skipped = 0
        for i, w in enumerate(windows_meta):
            # if i > 11:
            #     break
            seq = self.fasta.fetch(w["chr"], w["start"], w["end"])
            if seq is None or len(seq) != win:
                skipped += 1
                if (i + 1) % 10000 == 0:
                    print(f"  1processed {i+1}/{len(windows_meta)} → kept {len(results)} (skipped {skipped})")
                continue
            rec = {
                "chr": w["chr"],
                "start": w["start"],
                "end": w["end"],
                "gene_id": w.get("gene_id", "") or "",
                "gene_type": w.get("gene_type", "") or "",
                "source": "GENCODE",
                "sequence": seq
            }
            if wig_path:
                mean_val = self.wig.get_window_mean(w["chr"], w["start"], w["end"])
                rec["mean_phastCons"] = 0.0 if mean_val is None else mean_val

            print(rec)
            # optional progress print every 10000
            if (i + 1) % 10000 == 0:
                print(f"  processed {i+1}/{len(windows_meta)} → kept {len(results)} (skipped {skipped})")

        print(f"Total kept windows with sequence: {len(results)} (skipped {skipped} windows)")
        # save to JSON
        outp = Path(output_path)
        outp.parent.mkdir(parents=True, exist_ok=True)
        with open(outp, 'w') as fh:
            json.dump(results, fh, indent=2)
        print(f"Saved {len(results)} records → {outp} (size: {outp.stat().st_size/1024:.1f} KB)")
        return results

# ---------------------------
# CLI
# ---------------------------
if __name__ == "__main__":
    out_json = f"{MIDDLE_RESULT_DIR}/human_gencode_windows.json"
    flanking = CONFIG["data"]["flanking"]
    win = CONFIG["data"]["window_len"]
    step = CONFIG["data"]["step"]
    gen = GencodeWindowGenerator(GTF, FASTA)
    gen.run(chrom=CHROM, output_path=out_json, flanking=flanking, win=win, step=step, wig_path=PHASTCONS_FILE)


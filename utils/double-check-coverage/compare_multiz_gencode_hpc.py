#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compare GENCODE long non-coding RNAs (lncRNAs) with Multiz100way alignment (human only)
Check what fraction of GENCODE annotations exist in Multiz100way hg38.
Designed for HPC environment with streaming access.
"""

import argparse
import gzip
from tqdm import tqdm
import gpn.model  
from gpn.data import GenomeMSA
from pathlib import Path
import pandas as pd


def parse_arguments():
    parser = argparse.ArgumentParser(description="Compare GENCODE GTF with Multiz100way (human subset)")
    parser.add_argument("--gtf", type=str, required=True, help="Path to gencode.v38.long_noncoding_RNAs.gtf")
    parser.add_argument("--msa_version", type=str, default="89", help="Multiz100way version (e.g. 89 or 99)")
    parser.add_argument("--output", type=str, default="coverage_summary.tsv", help="Output file for summary results")
    parser.add_argument("--streaming", type=bool, default=True, help="Use online streaming access (True/False)")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on number of genes to check")
    return parser.parse_args()


def load_multiz_msa(msa_version="89", streaming=True):
    if streaming:
        msa_path = f"zip:///::https://huggingface.co/datasets/songlab/multiz100way/resolve/main/{msa_version}.zarr.zip"
        print(f"[INFO] Using streaming mode for Multiz100way ({msa_version})")
    else:
        msa_path = f"data/{msa_version}.zarr"
        print(f"[INFO] Using local dataset at {msa_path}")

    msa = GenomeMSA(msa_path)
    return msa


def parse_gtf(gtf_path, limit=None):
    print(f"[INFO] Parsing GTF: {gtf_path}")
    features = []
    open_func = gzip.open if gtf_path.endswith(".gz") else open
    with open_func(gtf_path, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 9:
                continue
            chrom, _, feature_type, start, end, _, strand, _, attributes = parts
            if feature_type != "gene":
                continue
            gene_id = attributes.split("gene_id")[1].split(";")[0].replace('"', "").strip()
            features.append((chrom.replace("chr", ""), int(start), int(end), strand, gene_id))
            if limit and len(features) >= limit:
                break
    print(f"[INFO] Parsed {len(features)} gene features from GTF.")
    return features


def compare_coverage(msa, features):
    """
    Only check human (hg38) sequences in Multiz100way
    """
    total = len(features)
    found = 0
    missing = 0
    missing_genes = []

    print(f"[INFO] Checking {total} genes in Multiz100way (hg38 only)...")
    for chrom, start, end, strand, gene_id in tqdm(features, total=total):
        try:
            msa_matrix = msa.get_msa(chrom, start, end)
            seq = msa_matrix[0] if msa_matrix is not None else None
            if seq is not None:
                found += 1
            else:
                missing += 1
                missing_genes.append(gene_id)
        except Exception:
            missing += 1
            missing_genes.append(gene_id)
            continue

    coverage = (found / total) * 100 if total > 0 else 0
    print(f"[RESULT] Found: {found}/{total} ({coverage:.2f}%) | Missing: {missing}/{total} ({100 - coverage:.2f}%)")

    summary = {
        "total_genes": total,
        "found_genes": found,
        "missing_genes": missing,
        "coverage_percent": coverage,
        "missing_percent": 100 - coverage,
    }

    return summary, missing_genes


def main():
    args = parse_arguments()
    msa = load_multiz_msa(msa_version=args.msa_version, streaming=args.streaming)
    features = parse_gtf(args.gtf, limit=args.limit)
    summary, missing_genes = compare_coverage(msa, features)

    out_dir = Path(args.output).parent
    out_dir.mkdir(exist_ok=True, parents=True)
    pd.DataFrame([summary]).to_csv(args.output, sep="\t", index=False)
    print(f"[INFO] Summary written to {args.output}")

    missing_path = str(Path(args.output).with_name("missing_genes.txt"))
    with open(missing_path, "w") as f:
        f.write("\n".join(missing_genes))
    print(f"[INFO] Missing gene IDs written to {missing_path}")


if __name__ == "__main__":
    main()

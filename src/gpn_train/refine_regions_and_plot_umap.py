#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refine window region labels using GTF (CDS, five_prime_UTR, three_prime_UTR, exon, gene)
and plot UMAP with distinct colors: exon, intron, UTR5, UTR3, CDS, intergenic, unknown.

Inputs:
- output/window_embeddings/windows_with_umap.csv (contains umap_x, umap_y, chrom,start,end,...)
- dataset/gencode.v38.basic.annotation.gtf

Outputs:
- output/window_embeddings/windows_with_umap_refined.csv (adds refined_region)
- output/window_embeddings/umap_window_regions_refined.png
"""

import os
import sys
import csv
from pathlib import Path
from collections import defaultdict

import pandas as pd
import matplotlib.pyplot as plt

project_root = Path(__file__).parent.parent.parent


def normalize_chrom(chrom: str) -> str:
    if chrom is None:
        return None
    c = str(chrom).strip()
    if c.lower().startswith('chr'):
        c = c[3:]
    if c.upper() in ('M', 'MT', 'MTR'):
        return 'MT'
    if c.upper() in ('X', 'Y'):
        return c.upper()
    return c


def parse_attrs(attrs: str) -> dict:
    out = {}
    # GTF attributes: key "value"; pairs separated by ;
    for item in attrs.split(';'):
        item = item.strip()
        if item == '':
            continue
        if ' "' in item:
            k, v = item.split(' "', 1)
            v = v.rstrip('"')
            out[k.strip()] = v
        elif ' ' in item:
            k, v = item.split(' ', 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def load_gtf_intervals(gtf_path: Path):
    """Load intervals: CDS, 5'UTR, 3'UTR, exon, gene, plus generic UTR and transcript CDS bounds."""
    cds = defaultdict(list)
    utr5 = defaultdict(list)
    utr3 = defaultdict(list)
    exon = defaultdict(list)
    gene = defaultdict(list)
    utr_generic = defaultdict(list)

    # Per-transcript strand and CDS bounds and exons
    tx_strand = {}
    tx_chr = {}
    tx_cds_min = {}
    tx_cds_max = {}
    tx_exons = defaultdict(list)

    with open(gtf_path, 'r') as f:
        for line in f:
            if not line or line.startswith('#'):
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 9:
                continue
            chrom, source, feature, start, end, score, strand, frame, attrs = parts
            fkey = feature.strip().lower()
            try:
                s = int(start)
                e = int(end)
            except ValueError:
                continue
            c = normalize_chrom(chrom)
            a = parse_attrs(attrs)
            tx = a.get('transcript_id') or a.get('transcriptId')
            if fkey == 'gene':
                gene[c].append((s, e))
            elif fkey == 'exon':
                exon[c].append((s, e))
                if tx:
                    tx_strand[tx] = strand
                    tx_chr[tx] = c
                    tx_exons[tx].append((s, e))
            elif fkey == 'cds':
                cds[c].append((s, e))
                if tx:
                    tx_strand[tx] = strand
                    tx_chr[tx] = c
                    tx_cds_min[tx] = min(s, tx_cds_min.get(tx, s))
                    tx_cds_max[tx] = max(e, tx_cds_max.get(tx, e))
            elif fkey in ('five_prime_utr', 'five_prime-utr'):
                utr5[c].append((s, e))
                if tx:
                    tx_strand[tx] = strand
                    tx_chr[tx] = c
            elif fkey in ('three_prime_utr', 'three_prime-utr'):
                utr3[c].append((s, e))
                if tx:
                    tx_strand[tx] = strand
                    tx_chr[tx] = c
            elif fkey == 'utr':
                utr_generic[c].append((s, e, tx, strand))
                if tx:
                    tx_strand[tx] = strand
                    tx_chr[tx] = c

    # Derive UTRs from exon minus CDS per transcript when explicit UTRs are missing
    for tx, exs in tx_exons.items():
        c = tx_chr.get(tx)
        if not c or tx not in tx_cds_min or tx not in tx_cds_max:
            continue
        cds_min = tx_cds_min[tx]
        cds_max = tx_cds_max[tx]
        strand = tx_strand.get(tx, '+')
        for (s, e) in exs:
            # Left segment before CDS
            if s < cds_min:
                left_s = s
                left_e = min(e, cds_min - 1)
                if left_s <= left_e:
                    if strand == '+':
                        utr5[c].append((left_s, left_e))
                    else:
                        utr3[c].append((left_s, left_e))
            # Right segment after CDS
            if e > cds_max:
                right_s = max(s, cds_max + 1)
                right_e = e
                if right_s <= right_e:
                    if strand == '+':
                        utr3[c].append((right_s, right_e))
                    else:
                        utr5[c].append((right_s, right_e))

    return cds, utr5, utr3, exon, gene, utr_generic, tx_chr, tx_strand, tx_cds_min, tx_cds_max


def any_overlap(s1: int, e1: int, intervals):
    for (s2, e2) in intervals:
        if e1 >= s2 and e2 >= s1:
            return True
    return False


def classify_window(chrom: str, start: int, end: int, cds, utr5, utr3, exon, gene,
                    utr_generic, tx_chr, tx_strand, tx_cds_min, tx_cds_max) -> str:
    c = normalize_chrom(chrom)
    if c is None:
        return 'unknown'

    # Priority: CDS > UTR5 > UTR3 > exon > intron > intergenic > unknown
    if any_overlap(start, end, cds.get(c, [])):
        return 'CDS'
    if any_overlap(start, end, utr5.get(c, [])):
        return 'UTR5'
    if any_overlap(start, end, utr3.get(c, [])):
        return 'UTR3'
    if any_overlap(start, end, exon.get(c, [])):
        return 'exon'
    # Try to split generic UTR using transcript CDS bounds
    for (us, ue, tx, s) in utr_generic.get(c, []):
        if end >= us and ue >= start:
            if not tx or tx not in tx_cds_min or tx not in tx_cds_max:
                continue
            cds_min = tx_cds_min[tx]
            cds_max = tx_cds_max[tx]
            strand = tx_strand.get(tx, '+')
            # Decide relative to CDS bounds
            if strand == '+':
                if end <= cds_min:
                    return 'UTR5'
                if start >= cds_max:
                    return 'UTR3'
            else:  # negative strand
                if start >= cds_max:
                    return 'UTR5'
                if end <= cds_min:
                    return 'UTR3'
    if any_overlap(start, end, gene.get(c, [])):
        return 'intron'
    return 'intergenic'


def plot_umap(df: pd.DataFrame, output_path: Path):
    # Collapse UTR5/UTR3 into UTR for plotting
    df = df.copy()
    df['plot_region'] = df['refined_region']
    df.loc[df['plot_region'].isin(['UTR5', 'UTR3']), 'plot_region'] = 'UTR'

    # Only show requested classes: CDS, UTR, exon, lncRNA. Keep unknown in legend if present.
    colors = {
        'CDS': '#9467bd',
        'UTR': '#2ca02c',
        'exon': '#1f77b4',
        'lncRNA': '#e377c2',
        'unknown': '#000000',
    }

    order = ['CDS', 'UTR', 'exon', 'lncRNA', 'unknown']
    plt.figure(figsize=(10, 8))
    legend_handles = []
    import matplotlib.patches as mpatches
    for label in order:
        sub = df[df['plot_region'] == label]
        if len(sub) > 0:
            plt.scatter(sub['umap_x'], sub['umap_y'], s=6, alpha=0.7, c=colors[label], label=label)
        # Always add a legend handle so categories appear even if empty
        legend_handles.append(mpatches.Patch(color=colors[label], label=label))

    plt.xlabel('UMAP 1')
    plt.ylabel('UMAP 2')
    plt.title('UMAP by refined region')
    plt.legend(handles=legend_handles, markerscale=2, frameon=False)
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def main():
    windows_umap_csv = project_root / 'output' / 'window_embeddings' / 'windows_with_umap.csv'
    gtf_path = project_root / 'dataset' / 'gencode.v38.basic.annotation.gtf'
    out_dir = project_root / 'output' / 'window_embeddings'
    out_dir.mkdir(parents=True, exist_ok=True)

    if not windows_umap_csv.exists():
        print(f'Missing input: {windows_umap_csv}')
        return 1
    if not gtf_path.exists():
        print(f'Missing GTF: {gtf_path}')
        return 1

    print('Loading windows with UMAP...')
    df = pd.read_csv(windows_umap_csv)
    # Ensure required columns
    for col in ['chrom', 'start', 'end', 'umap_x', 'umap_y']:
        if col not in df.columns:
            print(f'Missing column in {windows_umap_csv}: {col}')
            return 1

    print('Loading GTF intervals...')
    cds, utr5, utr3, exon, gene, utr_generic, tx_chr, tx_strand, tx_cds_min, tx_cds_max = load_gtf_intervals(gtf_path)

    print('Classifying windows...')
    refined = []
    for _, row in df.iterrows():
        # Priority override: lncRNA as its own region if gene_type says so
        gtype = str(row.get('gene_type', '')).lower()
        if gtype == 'lncrna':
            refined.append('lncRNA')
            continue
        label = classify_window(row['chrom'], int(row['start']), int(row['end']),
                                cds, utr5, utr3, exon, gene,
                                utr_generic, tx_chr, tx_strand, tx_cds_min, tx_cds_max)
        refined.append(label)
    df['refined_region'] = refined

    # Save refined CSV
    refined_csv = out_dir / 'windows_with_umap_refined.csv'
    df.to_csv(refined_csv, index=False)
    print(f'Saved: {refined_csv}')

    # Plot UMAP
    plot_path = out_dir / 'umap_window_regions_refined.png'
    plot_umap(df, plot_path)
    print(f'Saved: {plot_path}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())



#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate chr1_windows.csv for Mouse (similar to human)
Extract windows from mouse GTF annotation file
"""

import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def parse_attr(attr_str: str, key: str) -> str:
    """Parse GTF attribute string to extract value by key"""
    if not attr_str:
        return "unknown"
    
    for item in attr_str.split(';'):
        item = item.strip()
        if item.startswith(key):
            # Extract value (handle both "key value" and "key \"value\"" formats)
            if ' "' in item:
                value = item.split(' "', 1)[1].rstrip('"')
            elif ' ' in item:
                value = item.split(' ', 1)[1].strip('"')
            else:
                value = "unknown"
            return value
    
    return "unknown"


def extract_gencode_windows(chrom: str, gtf_path: Path, output_path: Path, 
                           flanking=100, win=512, step=256):
    """
    Extract windows from GENCODE annotation file for specified chromosome
    Includes exon / CDS / 5'/3'UTR regions
    Each region extends flanking bp upstream/downstream, and generates windows with win/step sliding
    
    Args:
        chrom: Chromosome name (e.g., "chr1")
        gtf_path: GTF file path
        output_path: Output CSV path
        flanking: Upstream/downstream extension in bp
        win: Window size in bp
        step: Sliding step in bp
    """
    # If already exists, load directly
    if output_path.exists():
        df = pd.read_csv(output_path)
        print(f"Loaded {len(df)} windows from cache {output_path}")
        return df
    
    print(f"\nGenerating windows from GTF: {gtf_path}")
    print(f"   Chromosome: {chrom}")
    print(f"   Window size: {win}bp, Step: {step}bp, Flanking: {flanking}bp")
    
    # 1. Read GTF file
    print("   Reading GTF file...")
    gtf = pd.read_csv(
        gtf_path, sep="\t", comment="#", header=None,
        names=["chr", "src", "feature", "start", "end", "score", "strand", "frame", "attr"]
    )
    
    print(f"   Loaded {len(gtf)} total records from GTF")
    
    # Filter for target chromosome
    gtf = gtf[gtf["chr"] == chrom]
    print(f"   Found {len(gtf)} records for {chrom}")
    
    if len(gtf) == 0:
        print(f"   Warning: No records found for {chrom}")
        return pd.DataFrame()
    
    # 2. Match all interested features
    # Note: Mouse GTF may not have "UTR", need to find "five_prime_utr" and "three_prime_utr"
    target_features = ["exon", "CDS", "CDS", "five_prime_utr", "three_prime_utr", "UTR"]
    
    # Try matching (case-insensitive)
    selected = gtf[gtf["feature"].str.lower().isin([f.lower() for f in target_features])].copy()
    
    if len(selected) == 0:
        print(f"   Warning: No exon/CDS/UTR features found for {chrom}")
        print(f"   Available features: {gtf['feature'].unique()[:10]}")
        return pd.DataFrame()
    
    print(f"   Found {len(selected)} regions (exon/CDS/UTR combined)")
    print(f"   Feature distribution:")
    print(selected["feature"].value_counts())
    
    # 3. Generate windows
    print(f"   Generating sliding windows...")
    windows = []
    
    for idx, r in selected.iterrows():
        # Add upstream/downstream flanking
        s = max(1, int(r["start"]) - flanking)
        e = int(r["end"]) + flanking
        
        # Ensure region is large enough
        if e - s < win:
            continue
        
        gene_id = parse_attr(r["attr"], "gene_id")
        gene_type = parse_attr(r["attr"], "gene_type")
        region_type = r["feature"].lower()
        
        # Normalize region type
        if region_type in ["five_prime_utr", "three_prime_utr"]:
            region_type = "UTR"
        elif region_type == "cds":
            region_type = "CDS"
        
        # Sliding windows
        for pos in range(s, e - win + 1, step):
            windows.append({
                "chrom": chrom,
                "start": pos,
                "end": pos + win - 1,
                "gene_id": gene_id,
                "gene_type": gene_type,
                "region": region_type
            })
    
    if not windows:
        print(f"   Warning: No windows generated!")
        return pd.DataFrame()
    
    # 4. Remove duplicates (keep only one occurrence per window)
    df = pd.DataFrame(windows)
    original_len = len(df)
    df = df.drop_duplicates(subset=["chrom", "start", "end", "gene_id", "region"])
    print(f"   Generated {original_len} windows, {len(df)} unique windows")
    
    # 5. Save output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"   Saved {len(df)} windows -> {output_path}")
    
    # Print statistics
    print(f"\n   Window Statistics:")
    print(f"      Total windows: {len(df)}")
    print(f"      Region distribution:")
    print(df["region"].value_counts())
    print(f"      Gene type distribution (top 5):")
    print(df["gene_type"].value_counts().head(5))
    
    return df


def main():
    """Main function to generate mouse chr1_windows.csv"""
    # File paths
    chrom = "chr1"
    gtf_path = project_root / "dataset" / "mouse" / "gencode.vM38.basic.annotation.gtf"
    output_path = project_root / "mouse_chr1_windows.csv"  # Different filename to avoid overwriting human version
    
    # Check GTF file
    if not gtf_path.exists():
        print(f"Error: GTF file not found: {gtf_path}")
        return 1
    
    # Generate windows
    df = extract_gencode_windows(
        chrom=chrom,
        gtf_path=gtf_path,
        output_path=output_path,
        flanking=100,
        win=512,
        step=256
    )
    
    if df.empty:
        print(f"\nFailed to generate windows")
        return 1
    
    print(f"\nSuccessfully generated {len(df)} windows for {chrom}")
    return 0


if __name__ == "__main__":
    exit(main())

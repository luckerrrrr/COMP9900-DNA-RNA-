#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENCODE lncRNA Extraction Tool

Function: Extract lncRNA data from GTF files and display
"""

import pandas as pd
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# Constants Definition
# ═══════════════════════════════════════════════════════════════

GTF_COLUMNS = ["chr", "src", "feature", "start", "end", "score", "strand", "frame", "attr"]


# ═══════════════════════════════════════════════════════════════
# Core Classes
# ═══════════════════════════════════════════════════════════════

class GencodeExtractor:
    """GENCODE Data Extractor"""
    
    def __init__(self, gtf_path: str):
        self.gtf_path = gtf_path
    
    @staticmethod
    def _parse_attr(attr: str, key: str) -> Optional[str]:
        """Extract fields from GTF attributes"""
        for part in attr.split(";"):
            if key in part and '"' in part:
                return part.split('"')[1]
        return None
    
    def _read_chrom(self, chrom: str) -> pd.DataFrame:
        """Read specified chromosome data in chunks"""
        chunks = []
        for chunk in pd.read_csv(self.gtf_path, sep="\t", comment="#", header=None,
                                 names=GTF_COLUMNS, chunksize=100000):
            filtered = chunk[chunk["chr"] == chrom]
            if not filtered.empty:
                chunks.append(filtered)
        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    
    def extract_lncrna(self, chrom: str = "chr1") -> pd.DataFrame:
        """
        Extract lncRNA data
        
        Args:
            chrom: Chromosome name, default 'chr1'
            
        Returns:
            DataFrame, columns: chr, src, feature, start, end, score, strand, frame, attr, gene_type
        """
        print(f"📖 Reading: {self.gtf_path}")
        print(f"   Chromosome: {chrom}")
        
        gtf = self._read_chrom(chrom)
        
        if gtf.empty:
            print(f"⚠️  No data for {chrom}")
            return pd.DataFrame()
        
        # Parse gene_type and filter lncRNA
        gtf['gene_type'] = gtf['attr'].apply(lambda x: self._parse_attr(x, 'gene_type'))
        result = gtf[gtf['gene_type'] == 'lncRNA'].copy()
        
        print(f"✅ Extracted {len(result):,} lncRNA records\n")
        
        # Statistics of feature type distribution
        if not result.empty:
            print("📊 Feature types found:")
            unique_features = result['feature'].unique()
            for feat in sorted(unique_features):
                count = (result['feature'] == feat).sum()
                pct = count / len(result) * 100
                print(f"   • {feat}: {count:,} ({pct:.1f}%)")
        
        print()
        return result
    
    def print_preview(self, df: pd.DataFrame, n: int = 20) -> None:
        """Print data preview"""
        if df.empty:
            print("⚠️  No data to preview")
            return
        
        print(f"💡 First {min(n, len(df))} rows:")
        print("─" * 100)
        cols = ['chr', 'feature', 'start', 'end', 'gene_type']
        print(df[cols].head(n).to_string(index=False))
        print()


# ═══════════════════════════════════════════════════════════════
# Main Program
# ═══════════════════════════════════════════════════════════════

def main():
    """Example usage"""
    
    # Initialize extractor
    extractor = GencodeExtractor("dataset/gencode.v38.basic.annotation.gtf")
    
    # Extract lncRNA
    lncrna_df = extractor.extract_lncrna(chrom="chr1")
    
    # Display first 20 rows
    extractor.print_preview(lncrna_df, n=20)


if __name__ == "__main__":
    main()
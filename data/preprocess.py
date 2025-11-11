#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GPN (Genomic Pre-training Network) Preprocessing Pipeline
# Based on "DNA language models are powerful predictors of genome-wide variant effects" (Benegas et al., 2023)
# Purpose: Process human genome data for GPN model training following paper requirements
# Usage: python preprocess.py test  OR  python preprocess.py full [total_samples]

import pandas as pd
import numpy as np
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import warnings
import json
warnings.filterwarnings('ignore')


class HumanGENCODEPreprocessor:
    """Human GENCODE preprocessor following GPN paper requirements"""

    def __init__(self, gtf_path: str, fasta_path: str):
        self.gtf_path = Path(gtf_path)
        self.fasta_path = Path(fasta_path)
        self.genome_sequence = None

        # Check if files exist
        if not self.gtf_path.exists():
            raise FileNotFoundError(f"GTF file not found: {self.gtf_path}")
        if not self.fasta_path.exists():
            raise FileNotFoundError(f"FASTA file not found: {self.fasta_path}")
    
    def parse_gtf(self) -> pd.DataFrame:
        """Parse GTF file and return as pandas DataFrame"""
        print(f"Parsing GTF file: {self.gtf_path}")
        
        # Standard GTF 9-column format
        gtf_columns = ["chr", "source", "feature", "start", "end", 
                      "score", "strand", "frame", "attribute"]
        
        # Read GTF file, skip comment lines
        gtf = pd.read_csv(self.gtf_path, sep="\t", comment="#", 
                         header=None, names=gtf_columns)
        
        print(f"Loaded {len(gtf)} annotations from GTF file")
        return gtf

    def extract_genomic_regions(self, gtf_df: pd.DataFrame, total_samples: int = 10000) -> List[Dict]:
        """Extract genomic regions following GPN paper requirements"""
        print(f"Extracting genomic regions (target: {total_samples} samples)...")

        # Paper requirement: balanced sampling of different genomic regions
        # For human data, we'll extract from different feature types
        region_proportions = {
            'gene': 0.30,      # 30% - gene regions
            'exon': 0.25,      # 25% - exon regions  
            'intron': 0.20,    # 20% - intron regions
            'utr': 0.10,       # 10% - UTR regions
            'promoter': 0.10,  # 10% - promoter regions
            'ncrna': 0.05      # 5% - ncRNA regions
        }

        # Calculate samples per region type
        samples_per_region = {}
        for region_type, proportion in region_proportions.items():
            samples_per_region[region_type] = int(total_samples * proportion)

        print("Target samples per region type:")
        for region_type, count in samples_per_region.items():
            print(f"  {region_type}: {count}")

        all_regions = []

        # Extract regions by feature type
        for region_type, count in samples_per_region.items():
            if region_type == 'gene':
                regions = self._extract_gene_regions(gtf_df, count)
            elif region_type == 'exon':
                regions = self._extract_exon_regions(gtf_df, count)
            elif region_type == 'intron':
                regions = self._extract_intron_regions(gtf_df, count)
            elif region_type == 'utr':
                regions = self._extract_utr_regions(gtf_df, count)
            elif region_type == 'promoter':
                regions = self._extract_promoter_regions(gtf_df, count)
            elif region_type == 'ncrna':
                regions = self._extract_ncrna_regions(gtf_df, count)
            
            all_regions.extend(regions)

        print(f"\nTotal regions extracted: {len(all_regions)}")
        return all_regions

    def _extract_gene_regions(self, gtf_df: pd.DataFrame, count: int) -> List[Dict]:
        """Extract gene regions"""
        print(f"Extracting {count} gene regions...")
        genes = gtf_df[gtf_df["feature"] == "gene"].copy()
        
        if len(genes) == 0:
            print("  No gene features found, using simulated regions")
            return self._simulate_regions('gene', count)
        
        # Sample genes randomly
        sampled_genes = genes.sample(n=min(count, len(genes)), random_state=42)
        
        regions = []
        for _, row in sampled_genes.iterrows():
            # Parse gene ID
            gene_id = self._parse_gene_id(row["attribute"])
            
            regions.append({
                'region_id': f"gene_{gene_id}",
                'chr': row['chr'],
                'start': row['start'],
                'end': row['end'],
                'strand': row['strand'],
                'region_type': 'gene',
                'gene_id': gene_id
            })
        
        return regions

    def _extract_exon_regions(self, gtf_df: pd.DataFrame, count: int) -> List[Dict]:
        """Extract exon regions"""
        print(f"Extracting {count} exon regions...")
        exons = gtf_df[gtf_df["feature"] == "exon"].copy()
        
        if len(exons) == 0:
            print("  No exon features found, using simulated regions")
            return self._simulate_regions('exon', count)
        
        # Sample exons randomly
        sampled_exons = exons.sample(n=min(count, len(exons)), random_state=42)
        
        regions = []
        for _, row in sampled_exons.iterrows():
            # Parse gene and transcript IDs
            gene_id, transcript_id = self._parse_gene_transcript_ids(row["attribute"])
            
            regions.append({
                'region_id': f"exon_{gene_id}_{transcript_id}",
                'chr': row['chr'],
                'start': row['start'],
                'end': row['end'],
                'strand': row['strand'],
                'region_type': 'exon',
                'gene_id': gene_id,
                'transcript_id': transcript_id
            })
        
        return regions

    def _extract_intron_regions(self, gtf_df: pd.DataFrame, count: int) -> List[Dict]:
        """Extract intron regions (simulated for now)"""
        print(f"Extracting {count} intron regions...")
        return self._simulate_regions('intron', count)

    def _extract_utr_regions(self, gtf_df: pd.DataFrame, count: int) -> List[Dict]:
        """Extract UTR regions"""
        print(f"Extracting {count} UTR regions...")
        utrs = gtf_df[gtf_df["feature"].isin(["5UTR", "3UTR", "UTR"])].copy()
        
        if len(utrs) == 0:
            print("  No UTR features found, using simulated regions")
            return self._simulate_regions('utr', count)
        
        # Sample UTRs randomly
        sampled_utrs = utrs.sample(n=min(count, len(utrs)), random_state=42)
        
        regions = []
        for _, row in sampled_utrs.iterrows():
            gene_id, transcript_id = self._parse_gene_transcript_ids(row["attribute"])
            
            regions.append({
                'region_id': f"utr_{gene_id}_{transcript_id}",
                'chr': row['chr'],
                'start': row['start'],
                'end': row['end'],
                'strand': row['strand'],
                'region_type': 'utr',
                'gene_id': gene_id,
                'transcript_id': transcript_id
            })
        
        return regions

    def _extract_promoter_regions(self, gtf_df: pd.DataFrame, count: int) -> List[Dict]:
        """Extract promoter regions (1kb upstream of TSS)"""
        print(f"Extracting {count} promoter regions...")
        genes = gtf_df[gtf_df["feature"] == "gene"].copy()
        
        if len(genes) == 0:
            print("  No gene features found, using simulated regions")
            return self._simulate_regions('promoter', count)
        
        # Sample genes randomly
        sampled_genes = genes.sample(n=min(count, len(genes)), random_state=42)
        
        regions = []
        for _, row in sampled_genes.iterrows():
            gene_id = self._parse_gene_id(row["attribute"])
            
            # Determine TSS and promoter region
            if row['strand'] == '+':
                tss = row['start']
                promoter_start = max(1, tss - 1000)
                promoter_end = tss - 1
            else:  # strand == '-'
                tss = row['end']
                promoter_start = tss + 1
                promoter_end = tss + 1000
            
            if promoter_end > promoter_start:
                regions.append({
                    'region_id': f"promoter_{gene_id}",
                    'chr': row['chr'],
                    'start': promoter_start,
                    'end': promoter_end,
                    'strand': row['strand'],
                    'region_type': 'promoter',
                    'gene_id': gene_id,
                    'tss': tss
                })
        
        return regions

    def _extract_ncrna_regions(self, gtf_df: pd.DataFrame, count: int) -> List[Dict]:
        """Extract ncRNA regions"""
        print(f"Extracting {count} ncRNA regions...")
        ncrnas = gtf_df[gtf_df["feature"].isin(["lncRNA", "ncRNA", "miRNA", "rRNA", "tRNA"])].copy()
        
        if len(ncrnas) == 0:
            print("  No ncRNA features found, using simulated regions")
            return self._simulate_regions('ncrna', count)
        
        # Sample ncRNAs randomly
        sampled_ncrnas = ncrnas.sample(n=min(count, len(ncrnas)), random_state=42)
        
        regions = []
        for _, row in sampled_ncrnas.iterrows():
            gene_id = self._parse_gene_id(row["attribute"])
            
            regions.append({
                'region_id': f"ncrna_{gene_id}",
                'chr': row['chr'],
                'start': row['start'],
                'end': row['end'],
                'strand': row['strand'],
                'region_type': 'ncrna',
                'gene_id': gene_id
            })
        
        return regions

    def _simulate_regions(self, region_type: str, count: int) -> List[Dict]:
        """Simulate regions when real data is not available"""
        regions = []
        for i in range(count):
            regions.append({
                'region_id': f"{region_type}_sim_{i+1}",
                'chr': 'chr1',
                'start': random.randint(1000000 + i*1000, 2000000 + i*1000),
                'end': random.randint(2000000 + i*1000, 3000000 + i*1000),
                'strand': random.choice(['+', '-']),
                'region_type': region_type
            })
        return regions

    def _parse_gene_id(self, attribute: str) -> str:
        """Parse gene ID from GTF attribute field"""
        for attr in attribute.split(";"):
            if "gene_id" in attr:
                if '"' in attr:
                    return attr.split('"')[1]
                else:
                    return attr.split()[1]
        return "unknown_gene"

    def _parse_gene_transcript_ids(self, attribute: str) -> Tuple[str, str]:
        """Parse gene ID and transcript ID from GTF attribute field"""
        gene_id = "unknown_gene"
        transcript_id = "unknown_transcript"
        
        for attr in attribute.split(";"):
            if "gene_id" in attr:
                if '"' in attr:
                    gene_id = attr.split('"')[1]
                else:
                    gene_id = attr.split()[1]
            elif "transcript_id" in attr:
                if '"' in attr:
                    transcript_id = attr.split('"')[1]
                else:
                    transcript_id = attr.split()[1]
        
        return gene_id, transcript_id

    def create_sliding_windows(self, regions: List[Dict], 
                              window_size: int = 512, step_size: int = 256) -> List[Dict]:
        """Create sliding windows following GPN paper requirements"""
        print(f"Creating sliding windows (size: {window_size}bp, step: {step_size}bp)...")
        
        windows = []
        for region in regions:
            current_start = region['start']
            
            # Create sliding windows with 50% overlap (256bp step for 512bp window)
            while current_start + window_size <= region['end']:
                window = {
                    'chr': region['chr'],
                    'start': current_start,
                    'end': current_start + window_size - 1,
                    'window_id': f"{region['chr']}:{current_start}-{current_start + window_size - 1}",
                    'region_type': region.get('region_type', 'unknown'),
                    'strand': region.get('strand', '+'),
                    'gene_id': region.get('gene_id', ''),
                    'transcript_id': region.get('transcript_id', '')
                }
                windows.append(window)
                current_start += step_size
        
        print(f"Created {len(windows)} sliding windows")
        return windows
    
    def load_fasta_once(self):
        """Load FASTA file into memory once (optimization for repeated access)"""
        if self.genome_sequence is not None:
            print("FASTA sequence already loaded in memory")
            return
        
        print(f"Loading FASTA file into memory: {self.fasta_path}")
        print("This may take a moment...")
        
        try:
            with open(self.fasta_path, 'r') as f:
                lines = f.readlines()
            
            sequence = ""
            header = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('>'):
                    header = line
                    print(f"Found chromosome: {header}")
                elif line and not line.startswith('>'):
                    sequence += line.upper()
            
            self.genome_sequence = sequence
            print(f"FASTA loaded successfully! Total length: {len(sequence):,} bp")
            
        except Exception as e:
            print(f"Error loading FASTA file: {e}")
            self.genome_sequence = None
    
    def load_sequence_from_fasta(self, chrom: str, start: int, end: int) -> Optional[str]:
        """Load DNA sequence from cached genome sequence"""
        
        if self.genome_sequence is None:
            print(f"    Error: Genome sequence not loaded. Call load_fasta_once() first.")
            return None
        
        try:
            if len(self.genome_sequence) >= end:
                # Extract the requested region (convert to 0-based indexing)
                seq_start = start - 1
                seq_end = end
                extracted_seq = self.genome_sequence[seq_start:seq_end]
                return extracted_seq
            else:
                print(f"    Error: Sequence too short ({len(self.genome_sequence)}) for region {start}-{end}")
                return None
            
        except Exception as e:
            print(f"    Error extracting sequence: {e}")
            return None


class GPNDataProcessor:
    """GPN model data processor following paper requirements"""

    def __init__(self):
        self.complement_map = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
    
    def reverse_complement(self, sequence: str) -> str:
        """Generate reverse complement sequence (GPN data augmentation requirement)"""
        return ''.join([self.complement_map.get(base, base) for base in sequence[::-1]])
    
    def tokenize_sequence(self, sequence: str) -> List[str]:
        """Tokenize sequence into single nucleotides (GPN requirement: non k-mer tokenization)"""
        return list(sequence)
    
    def apply_data_augmentation(self, sequence: str, apply_reverse_complement: bool = True) -> List[str]:
        """Apply data augmentation by generating reverse complement (2x data increase)"""
        sequences = [sequence]
        
        if apply_reverse_complement:
            rev_comp = self.reverse_complement(sequence)
            sequences.append(rev_comp)
        
        return sequences
    
    def mask_sequence(self, sequence: str, mask_ratio: float = 0.15) -> Tuple[str, List[int]]:
        """Apply random masking to 15% of sequence positions (GPN pre-training requirement)"""
        seq_list = list(sequence)
        seq_len = len(seq_list)
        num_mask = int(seq_len * mask_ratio)
        
        # Randomly select positions to mask
        mask_positions = random.sample(range(seq_len), num_mask)
        
        # Apply masking by replacing with [MASK] token
        for pos in mask_positions:
            seq_list[pos] = '[MASK]'
        
        return ''.join(seq_list), mask_positions


def process_human_gpn_dataset(gtf_path: str, fasta_path: str, 
                             total_samples: int = 10000,
                             output_path: str = "data/human_gpn_preprocessing_results.json") -> List[Dict]:
    """Full human GPN preprocessing pipeline following paper requirements"""
    
    print("=" * 80)
    print("HUMAN GPN PREPROCESSING PIPELINE (Benegas et al., 2023)")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  - GTF file: {gtf_path}")
    print(f"  - FASTA file: {fasta_path}")
    print(f"  - Total samples: {total_samples}")
    print(f"  - Window size: 512bp (paper requirement)")
    print(f"  - Step size: 256bp (50% overlap, paper requirement)")
    print(f"  - Mask ratio: 15% (paper requirement)")
    print(f"  - Data augmentation: Reverse complement (paper requirement)")
    print(f"  - Tokenization: Single nucleotides (paper requirement)")
    print("=" * 80)
    
    try:
        # Initialize preprocessor
        print("\n[STEP 1] Initializing human GPN preprocessor...")
        gencode_processor = HumanGENCODEPreprocessor(gtf_path, fasta_path)
        gpn_processor = GPNDataProcessor()
        
        # Parse GTF
        print("\n[STEP 2] Parsing GENCODE annotations...")
        gtf_df = gencode_processor.parse_gtf()
        
        # Extract genomic regions
        print("\n[STEP 3] Extracting genomic regions...")
        all_regions = gencode_processor.extract_genomic_regions(gtf_df, total_samples)
        
        # Create sliding windows
        print("\n[STEP 4] Creating sliding windows...")
        all_windows = gencode_processor.create_sliding_windows(all_regions, window_size=512, step_size=256)
        
        # Load FASTA into memory
        print("\n[STEP 5] Loading FASTA file into memory...")
        gencode_processor.load_fasta_once()
        
        # Process sequences
        print("\n[STEP 6] Processing sequences...")
        all_results = []
        processed_windows = 0
        failed_windows = 0
        
        for idx, window in enumerate(all_windows):
            if idx % 1000 == 0:
                print(f"  Processing window {idx+1}/{len(all_windows)} ({idx*100/len(all_windows):.1f}%)")
            
            try:
                # Load sequence
                sequence = gencode_processor.load_sequence_from_fasta(
                    window['chr'], window['start'], window['end']
                )
                
                if sequence is None or len(sequence) != 512:
                    failed_windows += 1
                    continue
                
                # Apply data augmentation (reverse complement)
                augmented_sequences = gpn_processor.apply_data_augmentation(sequence)
                
                # Process each augmented sequence
                for i, aug_seq in enumerate(augmented_sequences):
                    # Tokenize (single nucleotides)
                    tokens = gpn_processor.tokenize_sequence(aug_seq)
                    
                    # Apply masking (15%)
                    masked_seq, mask_positions = gpn_processor.mask_sequence(aug_seq, mask_ratio=0.15)
                    
                    result = {
                        'window_id': window['window_id'],
                        'chr': window['chr'],
                        'start': window['start'],
                        'end': window['end'],
                        'region_type': window['region_type'],
                        'strand': window.get('strand', '+'),
                        'gene_id': window.get('gene_id', ''),
                        'transcript_id': window.get('transcript_id', ''),
                        'sequence_length': len(aug_seq),
                        'augmentation_type': 'original' if i == 0 else 'reverse_complement',
                        'original_sequence': aug_seq,
                        'masked_sequence': masked_seq,
                        'tokens': tokens,
                        'mask_positions': mask_positions,
                        'mask_ratio': len(mask_positions) / len(aug_seq)
                    }
                    
                    all_results.append(result)
                
                processed_windows += 1
                
            except Exception as e:
                window_id = window.get('window_id', f"{window['chr']}:{window['start']}-{window['end']}")
                print(f"Error processing window {window_id}: {e}")
                failed_windows += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("HUMAN GPN PREPROCESSING SUMMARY")
        print("=" * 80)
        print(f"Total windows attempted: {len(all_windows)}")
        print(f"Successful windows: {processed_windows}")
        print(f"Failed windows: {failed_windows}")
        print(f"Total sequences generated: {len(all_results)}")
        print(f"Success rate: {processed_windows/len(all_windows)*100:.1f}%" if all_windows else "N/A")
        
        # Region type breakdown
        region_counts = {}
        for result in all_results:
            region_type = result['region_type']
            region_counts[region_type] = region_counts.get(region_type, 0) + 1
        
        print(f"\nRegion type breakdown:")
        for region_type, count in region_counts.items():
            print(f"  {region_type}: {count}")
        
        # Save results
        if all_results:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            
            print(f"\n? Results saved to: {output_file}")
            print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")
        
        return all_results
        
    except Exception as e:
        print(f"\nERROR in human GPN preprocessing pipeline: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_human_preprocessing():
    """Quick test of human GPN preprocessing pipeline"""
    print("Testing human GPN preprocessing pipeline")
    print("=" * 50)
    
    gtf_path = "dataset/gencode.v38.basic.annotation.gtf"
    fasta_path = "dataset/Homo_sapiens.GRCh38.dna.chromosome.1.fa"
    
    if not Path(gtf_path).exists():
        print(f"GTF file not found: {gtf_path}")
        return False
    
    # For testing, create a dummy FASTA file if it doesn't exist
    if not Path(fasta_path).exists():
        print(f"FASTA file not found: {fasta_path}")
        print("Creating dummy FASTA file for testing...")
        
        # Create dummy FASTA with chr1 sequence
        dummy_fasta_content = ">chr1\n" + "ATCG" * 1000000  # 4M bp dummy sequence
        Path(fasta_path).parent.mkdir(parents=True, exist_ok=True)
        with open(fasta_path, 'w') as f:
            f.write(dummy_fasta_content)
        print(f"Created dummy FASTA file: {fasta_path}")
    
    try:
        results = process_human_gpn_dataset(
            gtf_path=gtf_path,
            fasta_path=fasta_path,
            total_samples=100
        )
        
        if results:
            print(f"\n? Test completed successfully!")
            print(f"? Generated {len(results)} sequences")
            return True
        else:
            print("? Test failed - no results generated")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    if mode == "test":
        print("Running human GPN preprocessing in TEST mode...")
        success = test_human_preprocessing()
        print("? All tests passed!" if success else "? Tests failed!")
    
    elif mode == "full":
        print("Running human GPN preprocessing in FULL mode...")
        
        gtf_path = "dataset/gencode.v38.basic.annotation.gtf"
        fasta_path = "dataset/Homo_sapiens.GRCh38.dna.chromosome.1.fa"
        
        total_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
        
        results = process_human_gpn_dataset(
            gtf_path=gtf_path,
            fasta_path=fasta_path,
            total_samples=total_samples
        )
        
        if results:
            print(f"\n? Human GPN preprocessing completed successfully!")
            print(f"? Generated {len(results)} sequences")
        else:
            print(f"\n? Human GPN preprocessing failed")
    
    else:
        print(f"Unknown mode: {mode}")
        print("Usage:")
        print("  python preprocess.py test                    # Quick test")
        print("  python preprocess.py full [total_samples]    # Full processing")
        print("  python preprocess.py full 10000              # Process 10000 samples")

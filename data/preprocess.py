#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class GENCODEPreprocessor:
    """GENCODE data preprocessor for GPN model (PNAS 2023)"""
    
    def __init__(self, gtf_path: str, fasta_path: str):
        self.gtf_path = Path(gtf_path)
        self.fasta_path = Path(fasta_path)
        
        if not self.gtf_path.exists():
            raise FileNotFoundError(f"GTF file not found: {self.gtf_path}")
        if not self.fasta_path.exists():
            raise FileNotFoundError(f"FASTA file not found: {self.fasta_path}")
    
    def parse_gtf(self) -> pd.DataFrame:
        """Parse GTF file and extract gene annotation information"""
        print(f"Parsing GTF file: {self.gtf_path}")
        
        gtf_columns = ["chr", "source", "feature", "start", "end", 
                      "score", "strand", "frame", "attribute"]
        
        gtf = pd.read_csv(self.gtf_path, sep="\t", comment="#", 
                         header=None, names=gtf_columns)
        
        print(f"Loaded {len(gtf)} annotations from GTF file")
        return gtf
    
    def extract_exons_with_flanking(self, gtf_df: pd.DataFrame, 
                                  flanking_size: int = 100) -> List[Dict]:
        """Extract exons with flanking introns (GPN requirement)"""
        print(f"Extracting exons with {flanking_size}bp flanking introns...")
        
        # Filter exon features
        exons = gtf_df[gtf_df["feature"] == "exon"].copy()
        
        exon_regions = []
        for _, row in exons.iterrows():
            # Parse attribute field
            gene_id = None
            transcript_id = None
            
            for attr in row["attribute"].split(";"):
                if "gene_id" in attr:
                    gene_id = attr.split('"')[1] if '"' in attr else attr.split()[1]
                elif "transcript_id" in attr:
                    transcript_id = attr.split('"')[1] if '"' in attr else attr.split()[1]
            
            if gene_id and transcript_id:
                # Add flanking regions
                start_with_flank = max(1, row['start'] - flanking_size)
                end_with_flank = row['end'] + flanking_size
                
                exon_regions.append({
                    'gene_id': gene_id,
                    'transcript_id': transcript_id,
                    'chr': row['chr'],
                    'start': start_with_flank,
                    'end': end_with_flank,
                    'strand': row['strand'],
                    'exon_start': row['start'],
                    'exon_end': row['end'],
                    'flanking_size': flanking_size,
                    'region_type': 'exon_with_flanking'
                })
        
        print(f"Found {len(exon_regions)} exons with flanking regions")
        return exon_regions
    
    def extract_promoter_regions(self, gtf_df: pd.DataFrame, 
                               promoter_size: int = 1000) -> List[Dict]:
        """Extract promoter regions (TSS upstream 1000bp, GPN requirement)"""
        print(f"Extracting promoter regions ({promoter_size}bp upstream of TSS)...")
        
        # Filter gene features
        genes = gtf_df[gtf_df["feature"] == "gene"].copy()
        
        promoter_regions = []
        for _, row in genes.iterrows():
            gene_id = None
            gene_name = None
            
            for attr in row["attribute"].split(";"):
                if "gene_id" in attr:
                    gene_id = attr.split('"')[1] if '"' in attr else attr.split()[1]
                elif "gene_name" in attr:
                    gene_name = attr.split('"')[1] if '"' in attr else attr.split()[1]
            
            if gene_id:
                # Determine TSS based on strand
                if row['strand'] == '+':
                    tss = row['start']
                    promoter_start = max(1, tss - promoter_size)
                    promoter_end = tss - 1
                else:  # strand == '-'
                    tss = row['end']
                    promoter_start = tss + 1
                    promoter_end = tss + promoter_size
                
                # Only add if promoter region is valid
                if promoter_end > promoter_start:
                    promoter_regions.append({
                        'gene_id': gene_id,
                        'gene_name': gene_name,
                        'chr': row['chr'],
                        'start': promoter_start,
                        'end': promoter_end,
                        'strand': row['strand'],
                        'tss': tss,
                        'promoter_size': promoter_size,
                        'region_type': 'promoter'
                    })
        
        print(f"Found {len(promoter_regions)} promoter regions")
        return promoter_regions
    
    def generate_random_genome_windows(self, num_windows: int, 
                                     window_size: int = 512) -> List[Dict]:
        """Generate random genome windows (GPN requirement: equal amount)"""
        print(f"Generating {num_windows} random genome windows...")
        
        # Human genome sizes (approximate)
        genome_sizes = {
            'chr1': 248956422, 'chr2': 242193529, 'chr3': 198295559,
            'chr4': 190214555, 'chr5': 181538259, 'chr6': 170805979,
            'chr7': 159345973, 'chr8': 145138636, 'chr9': 138394717,
            'chr10': 133797422, 'chr11': 135086622, 'chr12': 133275309,
            'chr13': 114364328, 'chr14': 107043718, 'chr15': 101991189,
            'chr16': 90338345, 'chr17': 83257441, 'chr18': 80373285,
            'chr19': 58617616, 'chr20': 64444167, 'chr21': 46709983,
            'chr22': 50818468, 'chrX': 156040895, 'chrY': 57227415
        }
        
        random_windows = []
        for _ in range(num_windows):
            # Randomly select chromosome
            chrom = random.choice(list(genome_sizes.keys()))
            max_start = genome_sizes[chrom] - window_size
            
            # Random start position
            start = random.randint(1, max_start)
            end = start + window_size - 1
            
            random_windows.append({
                'chr': chrom,
                'start': start,
                'end': end,
                'window_size': window_size,
                'region_type': 'random_genome'
            })
        
        print(f"Generated {len(random_windows)} random genome windows")
        return random_windows
    
    def create_gpn_windows(self, regions: List[Dict], 
                          window_size: int = 512, step_size: int = 256) -> List[Dict]:
        """Create 512bp sliding windows with 256bp step (GPN requirement)"""
        windows = []
        
        for region in regions:
            current_start = region['start']
            
            while current_start + window_size <= region['end']:
                window = {
                    'chr': region['chr'],
                    'start': current_start,
                    'end': current_start + window_size - 1,
                    'window_id': f"{region['chr']}:{current_start}-{current_start + window_size - 1}",
                    'region_type': region.get('region_type', 'unknown'),
                    'gene_id': region.get('gene_id', ''),
                    'gene_name': region.get('gene_name', ''),
                    'strand': region.get('strand', '+')
                }
                windows.append(window)
                current_start += step_size
        
        return windows
    
    def load_sequence_from_fasta(self, chrom: str, start: int, end: int) -> Optional[str]:
        """Load DNA sequence from FASTA file"""
        try:
            print(f"    Loading sequence for {chrom}:{start}-{end}")
            
            # Simple FASTA parser for single chromosome
            with open(self.fasta_path, 'r') as f:
                lines = f.readlines()
            
            sequence = ""
            in_target_chrom = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('>'):
                    # Check if this is our target chromosome
                    if chrom in line or chrom.replace('chr', '') in line:
                        in_target_chrom = True
                        print(f"    Found target chromosome in FASTA: {line}")
                    else:
                        in_target_chrom = False
                elif in_target_chrom and line and not line.startswith('>'):
                    sequence += line.upper()
            
            print(f"    Total sequence length: {len(sequence)}")
            
            if sequence and len(sequence) >= end:
                # Extract the requested region (convert to 0-based indexing)
                seq_start = start - 1
                seq_end = end
                extracted_seq = sequence[seq_start:seq_end]
                print(f"    Extracted sequence length: {len(extracted_seq)}")
                return extracted_seq
            else:
                print(f"    Error: Sequence too short ({len(sequence)}) for region {start}-{end}")
                return None
            
        except Exception as e:
            print(f"    Error loading sequence from FASTA: {e}")
            return None


class GPNDataProcessor:
    """GPN model data processor"""
    
    def __init__(self):
        self.complement_map = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
    
    def reverse_complement(self, sequence: str) -> str:
        """Generate reverse complement sequence (GPN data augmentation)"""
        return ''.join([self.complement_map.get(base, base) for base in sequence[::-1]])
    
    def tokenize_sequence(self, sequence: str) -> List[str]:
        """Tokenize sequence into single nucleotides (GPN requirement: non k-mer)"""
        return list(sequence)
    
    def apply_data_augmentation(self, sequence: str, apply_reverse_complement: bool = True) -> List[str]:
        """Apply data augmentation: reverse complement (GPN requirement)"""
        sequences = [sequence]
        
        if apply_reverse_complement:
            rev_comp = self.reverse_complement(sequence)
            sequences.append(rev_comp)
        
        return sequences
    
    def mask_sequence(self, sequence: str, mask_ratio: float = 0.15) -> Tuple[str, List[int]]:
        """Apply 15% masking (GPN requirement)"""
        seq_list = list(sequence)
        seq_len = len(seq_list)
        num_mask = int(seq_len * mask_ratio)
        
        # Randomly select positions to mask
        mask_positions = random.sample(range(seq_len), num_mask)
        
        # Apply masking
        for pos in mask_positions:
            seq_list[pos] = '[MASK]'
        
        return ''.join(seq_list), mask_positions


def process_gpn_dataset(gtf_path: str, fasta_path: str, 
                       max_exons: int = 1000, max_promoters: int = 1000,
                       random_windows: int = 1000,
                       output_path: str = "data/gpn_preprocessing_results.json") -> List[Dict]:
    """Full GPN preprocessing pipeline following PNAS 2023 requirements"""
    
    print("=" * 80)
    print("GPN PREPROCESSING PIPELINE (PNAS 2023)")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  - GTF file: {gtf_path}")
    print(f"  - FASTA file: {fasta_path}")
    print(f"  - Max exons: {max_exons}")
    print(f"  - Max promoters: {max_promoters}")
    print(f"  - Random windows: {random_windows}")
    print(f"  - Window size: 512bp (GPN requirement)")
    print(f"  - Step size: 256bp (50% overlap)")
    print("=" * 80)
    
    try:
        # Initialize preprocessor
        print("\n[STEP 1] Initializing GPN preprocessor...")
        gencode_processor = GENCODEPreprocessor(gtf_path, fasta_path)
        gpn_processor = GPNDataProcessor()
        
        # Parse GTF
        print("\n[STEP 2] Parsing GENCODE annotations...")
        gtf_df = gencode_processor.parse_gtf()
        
        # Extract regions following GPN requirements
        print("\n[STEP 3] Extracting regions...")
        
        # 1. Exons with flanking introns
        exon_regions = gencode_processor.extract_exons_with_flanking(gtf_df, flanking_size=100)
        exon_regions = exon_regions[:max_exons]
        
        # 2. Promoter regions (TSS upstream 1000bp)
        promoter_regions = gencode_processor.extract_promoter_regions(gtf_df, promoter_size=1000)
        promoter_regions = promoter_regions[:max_promoters]
        
        # 3. Random genome windows (equal amount)
        random_regions = gencode_processor.generate_random_genome_windows(random_windows, window_size=512)
        
        print(f"  - Exon regions: {len(exon_regions)}")
        print(f"  - Promoter regions: {len(promoter_regions)}")
        print(f"  - Random regions: {len(random_regions)}")
        
        # Create windows
        print("\n[STEP 4] Creating 512bp windows...")
        all_windows = []
        
        # Windows from exons
        exon_windows = gencode_processor.create_gpn_windows(exon_regions, window_size=512, step_size=256)
        all_windows.extend(exon_windows)
        
        # Windows from promoters
        promoter_windows = gencode_processor.create_gpn_windows(promoter_regions, window_size=512, step_size=256)
        all_windows.extend(promoter_windows)
        
        # Random windows (already 512bp)
        all_windows.extend(random_regions)
        
        print(f"  Total windows created: {len(all_windows)}")
        
        # Process sequences
        print("\n[STEP 5] Processing sequences...")
        all_results = []
        processed_windows = 0
        failed_windows = 0
        
        for window in all_windows:
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
                        'gene_id': window.get('gene_id', ''),
                        'gene_name': window.get('gene_name', ''),
                        'strand': window.get('strand', '+'),
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
        print("GPN PREPROCESSING SUMMARY")
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
            import json
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            
            print(f"\n? Results saved to: {output_file}")
            print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")
        
        return all_results
        
    except Exception as e:
        print(f"\nERROR in GPN preprocessing pipeline: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_gpn_preprocessing():
    """Quick test of GPN preprocessing pipeline"""
    print("Testing GPN preprocessing pipeline")
    print("=" * 50)
    
    gtf_path = "data/Dark Matter of the Genome data/gencode.v38.basic.annotation.gtf"
    fasta_path = "data/Dark Matter of the Genome data/Homo_sapiens.GRCh38.dna.chromosome.1.fa"
    
    if not Path(gtf_path).exists():
        print(f"GTF file not found: {gtf_path}")
        return False
    if not Path(fasta_path).exists():
        print(f"FASTA file not found: {fasta_path}")
        return False
    
    try:
        results = process_gpn_dataset(
            gtf_path=gtf_path,
            fasta_path=fasta_path,
            max_exons=10,
            max_promoters=10,
            random_windows=10
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
        return False


if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    if mode == "test":
        print("Running GPN preprocessing in TEST mode...")
        success = test_gpn_preprocessing()
        print("? All tests passed!" if success else "? Tests failed!")
    
    elif mode == "full":
        print("Running GPN preprocessing in FULL mode...")
        
        gtf_path = "data/Dark Matter of the Genome data/gencode.v38.basic.annotation.gtf"
        fasta_path = "data/Dark Matter of the Genome data/Homo_sapiens.GRCh38.dna.chromosome.1.fa"
        
        max_exons = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        max_promoters = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
        random_windows = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
        
        results = process_gpn_dataset(
            gtf_path=gtf_path,
            fasta_path=fasta_path,
            max_exons=max_exons,
            max_promoters=max_promoters,
            random_windows=random_windows
        )
        
        if results:
            print(f"\n? GPN preprocessing completed successfully!")
            print(f"? Generated {len(results)} sequences")
        else:
            print(f"\n? GPN preprocessing failed")
    
    else:
        print(f"Unknown mode: {mode}")
        print("Usage:")
        print("  python preprocess_gpn.py test                           # Quick test")
        print("  python preprocess_gpn.py full [exons] [promoters] [random]  # Full processing")
        print("  python preprocess_gpn.py full 1000 1000 1000            # Process 1000 of each type")

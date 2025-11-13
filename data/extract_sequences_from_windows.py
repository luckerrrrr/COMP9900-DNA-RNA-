#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract DNA sequences from window coordinates and generate training JSON

Reads windows CSV file (from preprocess_fine_tune.py), extracts DNA sequences,
and outputs JSON format for gpn_supervised.py training.
"""

import pandas as pd
import json
import argparse
from pathlib import Path
from typing import List, Dict
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


# ============================================================================
# FastaLoader - inline to avoid encoding issues in imports
# ============================================================================

class FastaLoader:
    """
    Simple FASTA loader that stores each chromosome sequence in memory.
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
                    # Normalize: remove 'chr' prefix if present
                    cur_chrom = header.replace('chr', '').replace('Chr', '').replace('CHR', '')
                    cur_seq_parts = []
                else:
                    cur_seq_parts.append(line)
            # flush last
            if cur_chrom is not None:
                seq = "".join(cur_seq_parts).upper()
                self.sequences[cur_chrom] = seq
    
    def fetch(self, chrom: str, start: int, end: int, zero_based: bool = False) -> str:
        """
        chrom: '1' or 'chr1' accepted
        start, end: coordinates (0-based or 1-based depending on zero_based flag)
        zero_based: If True, treat as 0-based [start, end); If False, treat as 1-based [start, end]
        """
        # Normalize chromosome name
        key = str(chrom).replace('chr', '').replace('Chr', '').replace('CHR', '')
        seq = self.sequences.get(key)
        if seq is None:
            return None
        
        # convert to 0-based slicing for Python
        if zero_based:
            # Already 0-based, use directly
            s0 = max(0, start)
            e0 = end
        else:
            # 1-based, convert to 0-based
            s0 = max(0, start - 1)
            e0 = end
        
        if e0 > len(seq):
            return None
        return seq[s0:e0]


def extract_sequences_from_windows(
    windows_csv: str,
    fasta_files: List[str],
    output_json: str,
    max_samples: int = None,
    verbose: bool = True
) -> None:
    """
    Extract DNA sequences for windows and save as JSON
    
    Args:
        windows_csv: Path to windows CSV file (from preprocess_fine_tune.py)
        fasta_files: List of FASTA file paths
        output_json: Output JSON file path
        max_samples: Maximum number of samples to process (for testing)
        verbose: Print progress messages
    """
    if verbose:
        print("=" * 80)
        print("Extracting DNA Sequences from Windows")
        print("=" * 80)
        print()
    
    # 1. Read windows CSV
    if verbose:
        print(f"? Reading windows CSV: {windows_csv}")
    
    windows_path = Path(windows_csv)
    if not windows_path.exists():
        raise FileNotFoundError(f"Windows CSV not found: {windows_csv}")
    
    df = pd.read_csv(windows_path)
    if verbose:
        print(f"   Loaded {len(df):,} windows")
        print(f"   Columns: {df.columns.tolist()}")
    
    # Verify required columns
    required_cols = ['chrom', 'start', 'end', 'gene_id', 'label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Limit samples if specified
    if max_samples and max_samples < len(df):
        if verbose:
            print(f"   Limiting to {max_samples:,} samples for testing")
        df = df.head(max_samples)
    
    # 2. Load FASTA sequences
    if verbose:
        print(f"\n? Loading FASTA files...")
    
    fasta_loader = FastaLoader(fasta_files[0])
    
    # Load all FASTA files
    for fasta_file in fasta_files:
        fasta_path = Path(fasta_file)
        if fasta_path.exists():
            if verbose:
                print(f"   Loading: {fasta_path.name}")
            temp_loader = FastaLoader(str(fasta_path))
            temp_loader.load()
            fasta_loader.sequences.update(temp_loader.sequences)
    
    if verbose:
        print(f"   Loaded {len(fasta_loader.sequences)} chromosomes")
        chrom_names = list(fasta_loader.sequences.keys())[:10]
        print(f"   Chromosomes: {chrom_names}...")
    
    # 3. Extract sequences for each window
    if verbose:
        print(f"\n??  Extracting sequences...")
    
    processed_records = []
    skipped_records = []
    
    # Statistics
    label_counts = df['label'].value_counts()
    if verbose:
        print(f"   Label distribution in input:")
        for label, count in label_counts.items():
            print(f"      Label {label}: {count:,}")
    
    for idx, row in df.iterrows():
        chrom = str(row['chrom'])
        start = int(row['start'])
        end = int(row['end'])
        gene_id = str(row['gene_id'])
        strand = str(row.get('strand', '.'))
        label_raw = row['label']
        
        # Convert label to int (0 or 1)
        try:
            if isinstance(label_raw, (int, float)):
                label = int(label_raw)
            else:
                label_str = str(label_raw).strip().lower()
                if label_str in ('true', 't', 'yes', '1', '1.0'):
                    label = 1
                elif label_str in ('false', 'f', 'no', '0', '0.0'):
                    label = 0
                else:
                    label = int(float(label_str))
        except:
            skipped_records.append({
                'reason': 'invalid_label',
                'chrom': chrom,
                'start': start,
                'end': end,
                'label': label_raw
            })
            continue
        
        # Extract sequence (windows CSV uses 0-based coordinates)
        sequence = fasta_loader.fetch(chrom, start, end, zero_based=True)
        
        if sequence is None:
            skipped_records.append({
                'reason': 'sequence_not_found',
                'chrom': chrom,
                'start': start,
                'end': end
            })
            continue
        
        # Check sequence length
        expected_length = end - start
        if len(sequence) != expected_length:
            skipped_records.append({
                'reason': 'length_mismatch',
                'chrom': chrom,
                'start': start,
                'end': end,
                'expected': expected_length,
                'actual': len(sequence)
            })
            continue
        
        # Check for invalid bases
        valid_bases = set('ATCGN')
        sequence_upper = sequence.upper()
        invalid_bases = set(sequence_upper) - valid_bases
        if invalid_bases:
            skipped_records.append({
                'reason': 'invalid_bases',
                'chrom': chrom,
                'start': start,
                'end': end,
                'invalid': list(invalid_bases)
            })
            continue
        
        # Save record
        record = {
            'chrom': chrom,
            'start': start,
            'end': end,
            'sequence': sequence_upper,
            'label': label,
            'gene_id': gene_id,
            'strand': strand
        }
        
        processed_records.append(record)
        
        # Progress display
        if verbose and (idx + 1) % 100000 == 0:
            print(f"   Processed {idx + 1:,}/{len(df):,} windows, "
                  f"kept {len(processed_records):,}, "
                  f"skipped {len(skipped_records):,}")
    
    # 4. Statistics and save
    if verbose:
        print(f"\n? Processing Summary:")
        print(f"   Total input windows: {len(df):,}")
        print(f"   Successfully processed: {len(processed_records):,}")
        print(f"   Skipped: {len(skipped_records):,}")
    
    if skipped_records:
        skip_reasons = {}
        for rec in skipped_records:
            reason = rec['reason']
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        
        if verbose:
            print(f"\n   Skip reasons:")
            for reason, count in skip_reasons.items():
                print(f"      {reason}: {count:,}")
    
    # Statistics on processed labels
    if processed_records:
        processed_label_dist = {}
        for rec in processed_records:
            label = rec['label']
            processed_label_dist[label] = processed_label_dist.get(label, 0) + 1
        
        if verbose:
            print(f"\n   Final label distribution:")
            for label, count in processed_label_dist.items():
                label_name = "conserved" if label == 1 else "non-conserved"
                pct = 100 * count / len(processed_records)
                print(f"      Label {label} ({label_name}): {count:,} ({pct:.2f}%)")
    
    # 5. Save to JSON
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(processed_records, f, indent=2)
    
    if verbose:
        file_size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"\n? Data saved to: {output_path}")
        print(f"   File size: {file_size_mb:.2f} MB")
        print(f"   Records: {len(processed_records):,}")
        print(f"\n{'=' * 80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract DNA sequences from window coordinates"
    )
    parser.add_argument(
        '--windows',
        required=True,
        help='Input windows CSV file (from preprocess_fine_tune.py)'
    )
    parser.add_argument(
        '--fasta',
        nargs='+',
        required=True,
        help='FASTA file(s) for genome reference'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output JSON file'
    )
    parser.add_argument(
        '--max-samples',
        type=int,
        default=None,
        help='Maximum number of samples to process (for testing)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )
    
    args = parser.parse_args()
    
    extract_sequences_from_windows(
        windows_csv=args.windows,
        fasta_files=args.fasta,
        output_json=args.output,
        max_samples=args.max_samples,
        verbose=not args.quiet
    )


if __name__ == '__main__':
    main()


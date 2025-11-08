#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract GPN Embeddings from Windows CSV
Directly use chr1_windows.csv to extract embeddings from GPN model
"""

import os
import sys
import pandas as pd
import numpy as np
import torch
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from gpn.model import ConvNetForMaskedLM
    from gpn.data import Tokenizer
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure running in container environment")
    sys.exit(1)

class WindowEmbeddingExtractor:
    def __init__(self, model_path, fasta_path, windows_csv, output_dir):
        self.model_path = model_path
        self.fasta_path = fasta_path
        self.windows_csv = windows_csv
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load FASTA sequences
        self.sequences = self.load_fasta()
        
    def normalize_chrom(self, chrom):
        """Normalize chromosome naming between CSV (e.g., 'chr1') and FASTA keys (e.g., '1')."""
        if chrom is None:
            return None
        c = str(chrom).strip()
        # Remove common prefixes like 'chr'
        if c.lower().startswith('chr'):
            c = c[3:]
        # Normalize mitochondrial naming
        if c.upper() in ('M', 'MT', 'MTR'):  # be forgiving
            c = 'MT'
        # Uppercase X/Y, keep numeric as-is
        if c.upper() in ('X', 'Y'):
            c = c.upper()
        return c

    def load_fasta(self):
        """Load FASTA sequences into memory"""
        print("Loading FASTA sequences...")
        sequences = {}
        current_chr = None
        current_seq = []
        
        with open(self.fasta_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if current_chr:
                        sequences[current_chr] = ''.join(current_seq)
                    current_chr = line[1:].split()[0]  # Extract chromosome name
                    current_seq = []
                else:
                    current_seq.append(line)
            
            # Add last sequence
            if current_chr:
                sequences[current_chr] = ''.join(current_seq)
        
        print(f"Loaded {len(sequences)} chromosomes")
        return sequences
    
    def load_model_and_tokenizer(self):
        """Load GPN model and tokenizer"""
        print("Loading GPN model and tokenizer...")
        try:
            self.model = ConvNetForMaskedLM.from_pretrained(self.model_path)
            self.tokenizer = Tokenizer()
            
            # Ensure model is on correct device
            if torch.cuda.is_available():
                self.model = torch.nn.DataParallel(self.model)
                self.model = self.model.to(self.device)
            
            print(f"Model loaded from: {self.model_path}")
            print(f"Using device: {self.device}")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def load_windows(self, max_windows=None):
        """Load windows from CSV"""
        print(f"Loading windows from: {self.windows_csv}")
        df = pd.read_csv(self.windows_csv)
        
        if max_windows and len(df) > max_windows:
            df = df.head(max_windows)
            print(f"Limited to {max_windows} windows")
        
        print(f"Loaded {len(df)} windows")
        print("Window distribution by region:")
        print(df['region'].value_counts())
        
        return df
    
    def extract_sequence_from_window(self, row):
        """Extract DNA sequence for a window"""
        chrom = self.normalize_chrom(row['chrom'])
        start = row['start'] - 1  # Convert to 0-based indexing
        end = row['end']
        
        if chrom not in self.sequences:
            # Attempt alternative: sometimes FASTA uses '1' while CSV has 'chr1'
            # After normalization above, if still missing, skip
            return None
        
        # Guard against out-of-bound indices
        chrom_seq = self.sequences[chrom]
        if start < 0:
            start = 0
        if end > len(chrom_seq):
            end = len(chrom_seq)
        if start >= end:
            return None
        seq = chrom_seq[start:end]
        return seq
    
    def extract_embeddings(self, df, batch_size=256):
        """Extract embeddings for all windows"""
        print(f"Extracting embeddings (batch_size={batch_size})...")
        
        all_embeddings = []
        all_metadata = []
        
        self.model.eval()
        with torch.no_grad():
            for i in tqdm(range(0, len(df), batch_size), desc="Processing batches"):
                batch_df = df.iloc[i:i+batch_size]
                batch_sequences = []
                batch_metadata = []
                
                # Extract sequences for this batch
                for _, row in batch_df.iterrows():
                    seq = self.extract_sequence_from_window(row)
                    if seq and len(seq) > 0:
                        batch_sequences.append(seq)
                        batch_metadata.append({
                            'chrom': row['chrom'],
                            'start': row['start'],
                            'end': row['end'],
                            'gene_id': row['gene_id'],
                            'gene_type': row['gene_type'],
                            'region': row['region']
                        })
                
                if not batch_sequences:
                    continue
                
                # Tokenize sequences
                batch_tokens = []
                for seq in batch_sequences:
                    seq_array = np.array(list(seq))
                    tokens = self.tokenizer(seq_array)
                    if isinstance(tokens, np.ndarray):
                        tokens = tokens.tolist()
                    batch_tokens.append(tokens)
                
                # Padding
                max_len = max(len(tokens) for tokens in batch_tokens)
                padded_tokens = np.zeros((len(batch_tokens), max_len), dtype=np.int64)
                attention_masks = np.zeros((len(batch_tokens), max_len), dtype=np.int64)
                
                for j, tokens in enumerate(batch_tokens):
                    seq_len = len(tokens)
                    padded_tokens[j, :seq_len] = tokens
                    attention_masks[j, :seq_len] = 1
                
                # Convert to tensors
                input_ids = torch.from_numpy(padded_tokens).long().to(self.device)
                attention_mask = torch.from_numpy(attention_masks).long().to(self.device)
                
                # Get embeddings
                if hasattr(self.model, 'module'):
                    base_model = self.model.module.model
                else:
                    base_model = self.model.model
                
                outputs = base_model(input_ids, attention_mask=attention_mask)
                batch_embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
                
                all_embeddings.append(batch_embeddings)
                all_metadata.extend(batch_metadata)
        
        if all_embeddings:
            embeddings = np.vstack(all_embeddings)
            print(f"Extracted {embeddings.shape[0]} embeddings, dimension: {embeddings.shape[1]}")
            return embeddings, all_metadata
        else:
            print("No embeddings extracted!")
            return None, []
    
    def save_results(self, embeddings, metadata):
        """Save embeddings and metadata"""
        print("Saving results...")
        
        # Save embeddings
        embeddings_path = os.path.join(self.output_dir, 'window_embeddings.npy')
        np.save(embeddings_path, embeddings)
        print(f"Embeddings saved: {embeddings_path}")
        
        # Save metadata
        metadata_path = os.path.join(self.output_dir, 'window_metadata.json')
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved: {metadata_path}")
        
        # Save as CSV for easy viewing
        metadata_df = pd.DataFrame(metadata)
        csv_path = os.path.join(self.output_dir, 'window_metadata.csv')
        metadata_df.to_csv(csv_path, index=False)
        print(f"Metadata CSV saved: {csv_path}")
        
        return embeddings_path, metadata_path, csv_path
    
    def run_extraction(self, max_windows=10000):
        """Run complete embedding extraction"""
        print("Starting window embedding extraction...")
        
        try:
            # Load model
            self.load_model_and_tokenizer()
            
            # Load windows
            df = self.load_windows(max_windows)
            
            if df.empty:
                print("No windows loaded!")
                return False
            
            # Extract embeddings
            embeddings, metadata = self.extract_embeddings(df)
            
            if embeddings is None:
                print("No embeddings extracted!")
                return False
            
            # Save results
            self.save_results(embeddings, metadata)
            
            print(f"\nExtraction completed successfully!")
            print(f"Results saved in: {self.output_dir}")
            
            return True
            
        except Exception as e:
            print(f"Error during extraction: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function"""
    # File paths
    model_path = project_root / "output" / "human_gpn_pretrained_real_gpn"
    fasta_path = project_root / "dataset" / "Homo_sapiens.GRCh38.dna.chromosome.1.fa"
    windows_csv = project_root / "chr1_windows.csv"
    output_dir = project_root / "output" / "window_embeddings"
    
    # Check input files
    if not model_path.exists():
        print(f"Error: Model not found: {model_path}")
        return 1
    
    if not fasta_path.exists():
        print(f"Error: FASTA file not found: {fasta_path}")
        return 1
    
    if not windows_csv.exists():
        print(f"Error: Windows CSV not found: {windows_csv}")
        return 1
    
    # Run extraction
    extractor = WindowEmbeddingExtractor(model_path, fasta_path, windows_csv, output_dir)
    
    success = extractor.run_extraction(max_windows=None)  # Process all windows
    
    if success:
        print("\nWindow embedding extraction completed!")
    else:
        print("\nWindow embedding extraction failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())


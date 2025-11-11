#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate UMAP visualization for Mouse GPN Model
Extract embeddings from mouse model and create UMAP
Uses refined region classification (CDS, UTR, exon, lncRNA) to match human model
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import matplotlib.patches as mpatches
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
import umap
import warnings
warnings.filterwarnings('ignore')

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    import torch
    from gpn.model import ConvNetForMaskedLM
    from gpn.data import Tokenizer
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure running in container environment")
    sys.exit(1)


# ========== GTF Parsing and Region Classification ==========

def normalize_chrom(chrom: str) -> str:
    """Normalize chromosome naming"""
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
    """Parse GTF attributes"""
    out = {}
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
    """Load intervals: CDS, UTR, exon, gene from GTF"""
    cds = defaultdict(list)
    utr5 = defaultdict(list)
    utr3 = defaultdict(list)
    exon = defaultdict(list)
    gene = defaultdict(list)
    utr_generic = defaultdict(list)
    
    # Per-transcript info
    tx_strand = {}
    tx_chr = {}
    tx_cds_min = {}
    tx_cds_max = {}
    tx_exons = defaultdict(list)
    
    print(f"Loading GTF intervals from: {gtf_path}")
    
    # Handle both .gtf and .gtf.gz files
    import gzip
    if str(gtf_path).endswith('.gz'):
        f = gzip.open(gtf_path, 'rt')
    else:
        f = open(gtf_path, 'r')
    
    try:
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
            elif fkey in ('three_prime_utr', 'three_prime-utr'):
                utr3[c].append((s, e))
            elif fkey == 'utr':
                utr_generic[c].append((s, e, tx, strand))
    finally:
        f.close()
    
    # Derive UTRs from exon minus CDS
    for tx, exs in tx_exons.items():
        c = tx_chr.get(tx)
        if not c or tx not in tx_cds_min or tx not in tx_cds_max:
            continue
        cds_min = tx_cds_min[tx]
        cds_max = tx_cds_max[tx]
        strand = tx_strand.get(tx, '+')
        for (s, e) in exs:
            if s < cds_min:
                left_s = s
                left_e = min(e, cds_min - 1)
                if left_s <= left_e:
                    if strand == '+':
                        utr5[c].append((left_s, left_e))
                    else:
                        utr3[c].append((left_s, left_e))
            if e > cds_max:
                right_s = max(s, cds_max + 1)
                right_e = e
                if right_s <= right_e:
                    if strand == '+':
                        utr3[c].append((right_s, right_e))
                    else:
                        utr5[c].append((right_s, right_e))
    
    print(f"? Loaded GTF intervals")
    return cds, utr5, utr3, exon, gene, utr_generic, tx_chr, tx_strand, tx_cds_min, tx_cds_max


def any_overlap(s1: int, e1: int, intervals):
    """Check if window overlaps any interval"""
    for (s2, e2) in intervals:
        if e1 >= s2 and e2 >= s1:
            return True
    return False


def classify_window(chrom: str, start: int, end: int, gene_type: str,
                    cds, utr5, utr3, exon, gene, 
                    utr_generic, tx_chr, tx_strand, tx_cds_min, tx_cds_max) -> str:
    """Classify genomic window into refined region category"""
    # Priority override: lncRNA as its own region
    if str(gene_type).lower() == 'lncrna':
        return 'lncRNA'
    
    c = normalize_chrom(chrom)
    if c is None:
        return 'unknown'
    
    # Priority: CDS > UTR > exon > intron > intergenic
    if any_overlap(start, end, cds.get(c, [])):
        return 'CDS'
    if any_overlap(start, end, utr5.get(c, [])):
        return 'UTR'
    if any_overlap(start, end, utr3.get(c, [])):
        return 'UTR'
    if any_overlap(start, end, exon.get(c, [])):
        return 'exon'
    
    # Handle generic UTR
    for (us, ue, tx, s) in utr_generic.get(c, []):
        if end >= us and ue >= start:
            if not tx or tx not in tx_cds_min or tx not in tx_cds_max:
                continue
            cds_min = tx_cds_min[tx]
            cds_max = tx_cds_max[tx]
            strand = tx_strand.get(tx, '+')
            if strand == '+':
                if end <= cds_min or start >= cds_max:
                    return 'UTR'
            else:
                if start >= cds_max or end <= cds_min:
                    return 'UTR'
    
    if any_overlap(start, end, gene.get(c, [])):
        return 'intron'
    
    return 'intergenic'


def group_gene_type(gene_type: str) -> str:
    """
    Group gene types into main categories for UMAP visualization.
    According to supervisor's suggestion: use gene_type from GTF instead of refined_region.
    
    Main categories:
    - protein_coding: Protein-coding genes
    - lncRNA: Long non-coding RNA
    - TEC: To be experimentally confirmed
    - pseudogene: All types of pseudogenes (merged)
    - other: Small categories (misc_RNA, miRNA, scaRNA, etc.)
    """
    gt = str(gene_type).lower().strip()
    
    # Pseudogenes (merge all types)
    if 'pseudogene' in gt:
        return 'pseudogene'
    
    # Main functional categories
    if gt == 'protein_coding':
        return 'protein_coding'
    if gt == 'lncrna':
        return 'lncRNA'
    if gt == 'tec':
        return 'TEC'
    
    # Small categories grouped as 'other'
    # Includes: misc_RNA, miRNA, scaRNA, snoRNA, snRNA, rRNA, etc.
    return 'other'


# ========== Main UMAP Generator Class ==========

class MouseUMAPGenerator:
    def __init__(self, model_path, fasta_path, windows_csv, gtf_path, output_dir):
        self.model_path = model_path
        self.fasta_path = fasta_path
        self.windows_csv = windows_csv
        self.gtf_path = gtf_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # FASTA sequences and GTF intervals (loaded once)
        self.sequences = {}
        self.gtf_data = None
        
    def load_fasta(self):
        """Load FASTA sequences into memory"""
        print(f"\nLoading FASTA sequences from: {self.fasta_path}")
        current_chr = None
        current_seq = []
        
        with open(self.fasta_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if current_chr:
                        self.sequences[current_chr] = ''.join(current_seq)
                    current_chr = line[1:].split()[0]
                    current_seq = []
                else:
                    current_seq.append(line)
            
            if current_chr:
                self.sequences[current_chr] = ''.join(current_seq)
        
        print(f"? Loaded {len(self.sequences)} chromosomes")
    
    def load_model_and_tokenizer(self):
        """Load trained Mouse GPN model and tokenizer"""
        print(f"\nLoading Mouse GPN model from: {self.model_path}")
        print(f"Using device: {self.device}")
        
        try:
            self.model = ConvNetForMaskedLM.from_pretrained(self.model_path)
            self.tokenizer = Tokenizer()
            
            # Move model to device
            if torch.cuda.is_available():
                self.model = torch.nn.DataParallel(self.model)
                self.model = self.model.to(self.device)
            
            print(f"? Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def load_windows(self, max_windows=None):
        """Load windows from CSV"""
        print(f"\nLoading windows from: {self.windows_csv}")
        df = pd.read_csv(self.windows_csv)
        
        print(f"Loaded {len(df)} windows")
        
        if max_windows and len(df) > max_windows:
            df = df.head(max_windows)
            print(f"Limited to {max_windows} windows")
        
        print(f"\nWindow distribution by region:")
        if 'region' in df.columns:
            print(df['region'].value_counts())
        
        return df
    
    def extract_sequence_from_window(self, row):
        """Extract DNA sequence for a window"""
        chrom = normalize_chrom(row['chrom'])
        start = row['start'] - 1  # Convert to 0-based
        end = row['end']
        
        if chrom not in self.sequences:
            # Try alternative chromosome naming
            if chrom.startswith('chr'):
                chrom_alt = chrom[3:]
            else:
                chrom_alt = f'chr{chrom}'
            if chrom_alt in self.sequences:
                chrom = chrom_alt
            else:
                return None
        
        chrom_seq = self.sequences[chrom]
        if start < 0:
            start = 0
        if end > len(chrom_seq):
            end = len(chrom_seq)
        if start >= end:
            return None
        
        return chrom_seq[start:end]
    
    
    def extract_embeddings(self, df, batch_size=256):
        """Extract embeddings for all windows"""
        print(f"\nExtracting embeddings (batch_size={batch_size})...")
        
        all_embeddings = []
        all_metadata = []
        
        self.model.eval()
        with torch.no_grad():
            total_batches = (len(df) + batch_size - 1) // batch_size
            for i in range(0, len(df), batch_size):
                if i % 1000 == 0:
                    print(f"Processing batch {i//batch_size + 1}/{total_batches}...")
                
                batch_df = df.iloc[i:i+batch_size]
                batch_sequences = []
                batch_metadata = []
                
                for _, row in batch_df.iterrows():
                    seq = self.extract_sequence_from_window(row)
                    if seq and len(seq) > 0:
                        batch_sequences.append(seq)
                        batch_metadata.append({
                            'chrom': row['chrom'],
                            'start': row['start'],
                            'end': row['end'],
                            'gene_id': row.get('gene_id', 'unknown'),
                            'gene_type': row.get('gene_type', 'unknown'),
                            'region': row.get('region', 'unknown')
                        })
                
                if not batch_sequences:
                    continue
                
                # Tokenize
                batch_tokens = []
                for seq in batch_sequences:
                    seq_array = np.array(list(seq))
                    tokens = self.tokenizer(seq_array)
                    if isinstance(tokens, np.ndarray):
                        tokens = tokens.tolist()
                    batch_tokens.append(tokens)
                
                # Pad
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
            print(f"? Extracted {embeddings.shape[0]} embeddings, dimension: {embeddings.shape[1]}")
            return embeddings, all_metadata
        else:
            print("No embeddings extracted!")
            return None, []
    
    def refine_regions(self, metadata):
        """Refine region classification using GTF"""
        print(f"\nRefining region classification using GTF...")
        
        # Load GTF if not already loaded
        if self.gtf_data is None:
            self.gtf_data = load_gtf_intervals(self.gtf_path)
        
        cds, utr5, utr3, exon, gene, utr_generic, tx_chr, tx_strand, tx_cds_min, tx_cds_max = self.gtf_data
        
        # Classify each window
        refined_regions = []
        for meta in metadata:
            chrom = meta.get('chrom', 'unknown')
            start = meta.get('start', 0)
            end = meta.get('end', 0)
            gene_type = meta.get('gene_type', 'unknown')
            
            refined_region = classify_window(
                chrom, start, end, gene_type,
                cds, utr5, utr3, exon, gene,
                utr_generic, tx_chr, tx_strand, tx_cds_min, tx_cds_max
            )
            refined_regions.append(refined_region)
        
        print(f"? Classified {len(refined_regions)} windows")
        return refined_regions
    
    def create_umap(self, embeddings, metadata):
        """Create UMAP visualization with gene types (supervisor's suggestion)"""
        print(f"\nPerforming UMAP dimensionality reduction...")
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)
        
        # Perform UMAP
        mapper = umap.UMAP(
            n_neighbors=20,
            min_dist=0.1,
            n_components=2,
            random_state=42,
            init='spectral',
            verbose=True,
            n_jobs=-1
        )
        
        umap_coords = mapper.fit_transform(embeddings_scaled)
        print(f"? UMAP coordinates shape: {umap_coords.shape}")
        
        # Create DataFrame with UMAP coordinates
        df = pd.DataFrame(metadata)
        df['umap_x'] = umap_coords[:, 0]
        df['umap_y'] = umap_coords[:, 1]
        
        # Use gene_type from GTF (supervisor's suggestion)
        # Group gene types into main categories
        df['grouped_gene_type'] = df['gene_type'].apply(group_gene_type)
        
        # Also keep refined_region for reference (optional)
        refined_regions = self.refine_regions(metadata)
        df['refined_region'] = refined_regions
        
        print(f"\nGene type distribution:")
        print(df['grouped_gene_type'].value_counts())
        print(f"\n(Refined region distribution for reference):")
        print(df['refined_region'].value_counts())
        
        # Create visualization
        print(f"\nCreating UMAP visualization by gene type...")
        
        # Color scheme for gene types (unified with group style)
        gene_type_colors = {
            'protein_coding': '#1f77b4',  # Blue - most common
            'lncRNA': '#f82224',          # Red - distinct non-coding
            'TEC': '#ff8100',             # Orange - experimental
            'pseudogene': '#9d5549',      # Brown - non-functional
            'other': '#7f7f7f'            # Gray - small categories (unknown)
        }
        
        gene_type_order = ['protein_coding', 'lncRNA', 'TEC', 'pseudogene', 'other']
        
        # Create figure (single plot like human model)
        plt.figure(figsize=(9, 7))
        
        for label in gene_type_order:
            sub = df[df['grouped_gene_type'] == label]
            if len(sub) > 0:
                plt.scatter(
                    sub['umap_x'], sub['umap_y'], 
                    s=1.2, 
                    alpha=0.6, 
                    c=gene_type_colors[label], 
                    linewidth=0,
                    edgecolor=None,
                    rasterized=True,
                    label=label
                )
        
        plt.xlabel('UMAP 1')
        plt.ylabel('UMAP 2')
        plt.title('UMAP projection of GPN embeddings (fine-grained IncRNA scatter)')
        
        # Create legend with Patch style
        patches = [
            mpatches.Patch(facecolor=gene_type_colors[label], edgecolor='black', label=label)
            for label in gene_type_order
        ]
        plt.legend(
            handles=patches,
            title='region',
            loc='best',
            frameon=True,
            handlelength=2,
            handleheight=1.2
        )
        plt.grid(alpha=0.2)
        
        # Set coordinate interval to 2.5
        ax = plt.gca()
        ax.xaxis.set_major_locator(MultipleLocator(2.5))
        ax.yaxis.set_major_locator(MultipleLocator(2.5))
        
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.output_dir, 'mouse_umap_visualization.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"? UMAP plot saved: {plot_path}")
        
        return plot_path, embeddings, umap_coords, df
    
    def save_results(self, embeddings, umap_coords, df):
        """Save all results"""
        print(f"\nSaving results...")
        
        # Save embeddings
        emb_path = os.path.join(self.output_dir, 'window_embeddings.npy')
        np.save(emb_path, embeddings)
        print(f"? Embeddings saved: {emb_path}")
        
        # Save UMAP coordinates
        umap_path = os.path.join(self.output_dir, 'umap_coordinates.npy')
        np.save(umap_path, umap_coords)
        print(f"? UMAP coordinates saved: {umap_path}")
        
        # Save complete data
        df_path = os.path.join(self.output_dir, 'windows_with_umap_refined.csv')
        df.to_csv(df_path, index=False)
        print(f"? Complete data saved: {df_path}")
        
        # Save summary
        summary = {
            'total_windows': len(df),
            'embedding_dimension': embeddings.shape[1],
            'umap_range_x': [float(df['umap_x'].min()), float(df['umap_x'].max())],
            'umap_range_y': [float(df['umap_y'].min()), float(df['umap_y'].max())],
            'gene_type_counts': df['grouped_gene_type'].value_counts().to_dict(),
            'refined_region_counts': df['refined_region'].value_counts().to_dict(),
        }
        
        summary_path = os.path.join(self.output_dir, 'umap_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"? Summary saved: {summary_path}")
        
        return emb_path, umap_path, df_path, summary_path
    
    def run_pipeline(self, max_windows=None):
        """Run complete integrated pipeline"""
        print("=" * 80)
        print("Mouse GPN Model - Integrated UMAP Generation")
        print("=" * 80)
        
        try:
            # Step 1: Load resources
            self.load_fasta()
            self.load_model_and_tokenizer()
            df = self.load_windows(max_windows)
            
            if df.empty:
                print("Error: No windows loaded!")
                return False
            
            # Step 2: Extract embeddings
            embeddings, metadata = self.extract_embeddings(df)
            
            if embeddings is None:
                print("Error: No embeddings extracted!")
                return False
            
            # Step 3: Generate UMAP with refined regions
            plot_path, embeddings, umap_coords, df = self.create_umap(embeddings, metadata)
            
            # Step 4: Save results
            self.save_results(embeddings, umap_coords, df)
            
            print("\n" + "=" * 80)
            print("? Mouse UMAP generation completed successfully!")
            print(f"? Results saved in: {self.output_dir}")
            print("=" * 80)
            
            return True
            
        except Exception as e:
            print(f"\nError during UMAP generation: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function"""
    # File paths
    model_path = project_root / "output" / "mouse_gpn_finetuned"
    fasta_path = project_root / "dataset" / "mouse" / "GRCm39.chr1.fa"
    windows_csv = project_root / "mouse_chr1_windows.csv"  # Generated from mouse GTF
    gtf_path = project_root / "dataset" / "mouse" / "gencode.vM38.basic.annotation.gtf"
    output_dir = project_root / "output" / "mouse_umap"
    
    # Check input files
    if not model_path.exists():
        print(f"Error: Model not found: {model_path}")
        return 1
    
    if not fasta_path.exists():
        print(f"Error: FASTA not found: {fasta_path}")
        return 1
    
    if not windows_csv.exists():
        print(f"Error: Windows CSV not found: {windows_csv}")
        print(f"  Please generate it first using: python src/gpn_train/create_mouse_windows.py")
        return 1
    
    if not gtf_path.exists():
        # Check if .gz version exists
        if Path(str(gtf_path) + ".gz").exists():
            gtf_path = Path(str(gtf_path) + ".gz")
        else:
            print(f"Error: GTF not found: {gtf_path}")
            return 1
    
    # Run UMAP generation
    generator = MouseUMAPGenerator(model_path, fasta_path, windows_csv, gtf_path, output_dir)
    
    success = generator.run_pipeline(max_windows=None)  # Process all windows
    
    if success:
        print("\n? Mouse UMAP generation completed!")
        return 0
    else:
        print("\n? Mouse UMAP generation failed!")
        return 1


if __name__ == "__main__":
    exit(main())


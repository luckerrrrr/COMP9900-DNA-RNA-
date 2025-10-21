#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# lncRNA Validation Analysis - UMAP Visualization
# Purpose: Validate GENCODE lncRNA information in GPN-MSA training data
# Usage: python lncrna_analysis.py

import os
import sys
import json
import argparse
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple, Optional

class UMAPAnalyzer:
    # UMAP dimensionality reduction analyzer for GPN-MSA data with GENCODE labels
    
    def __init__(self, gencode_path: str, output_dir: str = "."):
        self.gencode_path = gencode_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def load_gpn_msa_data(self, sample_size: int = 10000):
        # Load GPN-MSA dataset from Hugging Face
        try:
            from datasets import load_dataset
            print(f"Loading GPN-MSA dataset (sample size: {sample_size})...")
            
            dataset = load_dataset('songlab/gpn-msa-sapiens-dataset', cache_dir='../../cache/datasets')
            train_data = dataset['train']
            
            # Sample data to speed up processing
            if len(train_data) > sample_size:
                indices = list(range(0, len(train_data), len(train_data) // sample_size))[:sample_size]
                sampled_data = [train_data[i] for i in indices]
            else:
                sampled_data = list(train_data)
            
            print(f"Loaded {len(sampled_data)} samples")
            return sampled_data
            
        except Exception as e:
            print(f"Error loading GPN-MSA data: {e}")
            return None
    
    def get_gencode_labels(self, windows):
        # Get label information from GENCODE GTF file
        print("Loading GENCODE annotations for labeling...")
        
        try:
            gencode_regions = []
            with open(self.gencode_path, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    
                    parts = line.strip().split('\t')
                    if len(parts) < 9:
                        continue
                    
                    chrom, source, feature, start, end, score, strand, frame, attribute = parts
                    
                    if feature == 'gene':
                        # Parse gene type from attributes
                        gene_type = 'unknown'
                        gene_name = 'unknown'
                        
                        for attr in attribute.split(';'):
                            if 'gene_type' in attr:
                                gene_type = attr.split('"')[1] if '"' in attr else attr.split()[1]
                            elif 'gene_name' in attr:
                                gene_name = attr.split('"')[1] if '"' in attr else attr.split()[1]
                        
                        gencode_regions.append({
                            'chrom': chrom,
                            'start': int(start),
                            'end': int(end),
                            'gene_type': gene_type,
                            'gene_name': gene_name
                        })
            
            print(f"Loaded {len(gencode_regions)} GENCODE regions")
            
            # Assign labels to each window
            window_labels = []
            for window in windows:
                label = 'intergenic'  # Default label
                
                for region in gencode_regions:
                    if (region['chrom'] == window['chrom'] and 
                        not (window['end'] <= region['start'] or region['end'] <= window['start'])):
                        label = region['gene_type']
                        break
                
                window_labels.append(label)
            
            return window_labels
            
        except Exception as e:
            print(f"Error loading GENCODE labels: {e}")
            return ['unknown'] * len(windows)
    
    def extract_features(self, windows):
        # Extract features from GPN-MSA windows using phyloP and phastCons
        print("Extracting features from GPN-MSA windows...")
        
        features = []
        for window in windows:
            # Use phyloP and phastCons as features
            phylop = window.get('phyloP', [])
            phastcons = window.get('phastCons', [])
            
            if phylop and phastcons and len(phylop) > 0 and len(phastcons) > 0:
                # Calculate statistical features
                try:
                    feature_vector = [
                        sum(phylop) / len(phylop),  # Mean phyloP
                        max(phylop),                # Max phyloP
                        min(phylop),                # Min phyloP
                        sum(phastcons) / len(phastcons),  # Mean phastCons
                        max(phastcons),             # Max phastCons
                        min(phastcons),             # Min phastCons
                        window['start'] % 1000000,  # Genomic position feature
                    ]
                    features.append(feature_vector)
                except (TypeError, ValueError):
                    # If calculation fails, use default features
                    features.append([0.0] * 7)
            else:
                # If no phyloP/phastCons, use default features
                features.append([0.0] * 7)
        
        return features
    
    def generate_umap(self, features, labels, output_path):
        # Generate UMAP dimensionality reduction plot
        try:
            import umap
            import matplotlib.pyplot as plt
            import numpy as np
            
            print("Generating UMAP embedding...")
            
            # Create UMAP embedding
            reducer = umap.UMAP(n_components=2, random_state=42)
            embedding = reducer.fit_transform(features)
            
            # Create label color mapping
            unique_labels = list(set(labels))
            colors = plt.cm.Set3(np.linspace(0, 1, len(unique_labels)))
            label_colors = dict(zip(unique_labels, colors))
            
            # Plot UMAP figure
            plt.figure(figsize=(12, 8))
            
            for label in unique_labels:
                mask = np.array(labels) == label
                plt.scatter(embedding[mask, 0], embedding[mask, 1], 
                           c=[label_colors[label]], label=label, alpha=0.6, s=20)
            
            plt.title('UMAP Visualization of GPN-MSA Training Windows\nColored by GENCODE Gene Types', 
                     fontsize=14, fontweight='bold')
            plt.xlabel('UMAP 1', fontsize=12)
            plt.ylabel('UMAP 2', fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"UMAP visualization saved to: {output_path}")
            
            # Count label distribution
            label_counts = Counter(labels)
            print("\nLabel distribution:")
            for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {label}: {count} ({count/len(labels)*100:.1f}%)")
            
            return True
            
        except ImportError as e:
            print(f"Error: Required packages not available: {e}")
            print("Please install: pip install umap-learn matplotlib")
            return False
        except Exception as e:
            print(f"Error generating UMAP: {e}")
            return False
    
    def run_umap_analysis(self, sample_size: int = 10000):
        # Run complete UMAP analysis
        print("=" * 60)
        print("UMAP ANALYSIS - GPN-MSA Data with GENCODE Labels")
        print("=" * 60)
        
        # 1. Load GPN-MSA data
        windows = self.load_gpn_msa_data(sample_size)
        if not windows:
            return False
        
        # 2. Get GENCODE labels
        labels = self.get_gencode_labels(windows)
        
        # 3. Extract features
        features = self.extract_features(windows)
        
        # 4. Generate UMAP plot
        output_path = self.output_dir / "gpn_msa_umap.png"
        success = self.generate_umap(features, labels, output_path)
        
        if success:
            print("\nUMAP analysis completed successfully!")
            return True
        else:
            print("\nUMAP analysis failed!")
            return False


def main():
    parser = argparse.ArgumentParser(description="lncRNA Validation Analysis with UMAP")
    parser.add_argument("--gencode", default="../../dataset/gencode.v38.basic.annotation.gtf", 
                       help="Path to GENCODE GTF file")
    parser.add_argument("--sample-size", type=int, default=10000, 
                       help="Sample size for UMAP analysis")
    parser.add_argument("--output-dir", default=".", 
                       help="Output directory")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.gencode).exists():
        print(f"Error: GENCODE file not found: {args.gencode}")
        return 1
    
    # Run UMAP analysis
    try:
        print("Starting lncRNA validation analysis...")
        print(f"GENCODE file: {args.gencode}")
        print(f"Sample size: {args.sample_size}")
        print(f"Output directory: {args.output_dir}")
        
        analyzer = UMAPAnalyzer(args.gencode, args.output_dir)
        success = analyzer.run_umap_analysis(args.sample_size)
        
        if success:
            print("\nAnalysis completed successfully!")
            return 0
        else:
            print("\nAnalysis failed!")
            return 1
            
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
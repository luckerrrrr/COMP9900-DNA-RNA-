#!/usr/bin/env python3
"""
Conservation Score Data Download and Analysis Tool
Supports downloading, parsing and statistical analysis of phyloP and phastCons data
"""

import gzip
import urllib.request
import os
from collections import defaultdict
import statistics
import numpy as np


class ConservationScoreAnalyzer:
    """Conservation score data analysis class"""
    
    def __init__(self, chrom='chr1'):
        """
        Initialize analyzer
        
        Args:
            chrom: Chromosome number, default is 'chr1'
        """
        self.chrom = chrom
        self.phylop_url = f"https://hgdownload.cse.ucsc.edu/goldenPath/hg38/phyloP100way/hg38.100way.phyloP100way/{chrom}.phyloP100way.wigFix.gz"
        self.phastcons_url = f"https://hgdownload.cse.ucsc.edu/goldenpath/hg38/phastCons100way/hg38.100way.phastCons/{chrom}.phastCons100way.wigFix.gz"
        
        # Set dataset directory path (relative to utils directory)
        self.dataset_dir = os.path.join(os.path.dirname(__file__), '..', 'dataset')
        os.makedirs(self.dataset_dir, exist_ok=True)  # Create dataset directory
        
        self.phylop_file = os.path.join(self.dataset_dir, f"{chrom}.phyloP100way.wigFix.gz")
        self.phastcons_file = os.path.join(self.dataset_dir, f"{chrom}.phastCons100way.wigFix.gz")
        
        self.phylop_scores = np.array([])
        self.phastcons_scores = np.array([])
        self.phylop_start = None
        self.phylop_step = 1
        self.phastcons_start = None
        self.phastcons_step = 1
    
    def download_file(self, url, filename):
        """Download file"""
        if os.path.exists(filename):
            print(f"File {filename} already exists, skipping download")
            return
        
        print(f"Downloading: {url}")
        try:
            urllib.request.urlretrieve(url, filename)
            print(f"Download complete: {filename}")
        except Exception as e:
            print(f"Download failed: {e}")
            raise
    
    def download_data(self):
        """Download phyloP and phastCons data"""
        print(f"\n=== Starting download of {self.chrom} chromosome data ===\n")
        self.download_file(self.phylop_url, self.phylop_file)
        self.download_file(self.phastcons_url, self.phastcons_file)
        print("\nData download complete\n")
    
    def parse_wigfix(self, filename):
        """
        Parse wigFix format file (optimized version)
        
        Returns:
            tuple: (score data array, start position, step size)
        """
        print(f"Parsing: {filename}")
        
        scores = []
        batch_size = 1000000  # Process 1 million lines per batch
        batch = []
        line_count = 0
        start_pos = None
        step = 1
        
        with gzip.open(filename, 'rt') as f:
            for line in f:
                line = line.strip()
                
                # Parse header to get start position
                if line.startswith('fixedStep'):
                    parts = line.split()
                    for part in parts:
                        if part.startswith('start='):
                            start_pos = int(part.split('=')[1])
                        elif part.startswith('step='):
                            step = int(part.split('=')[1])
                    continue
                
                if not line:
                    continue
                
                try:
                    batch.append(float(line))
                    line_count += 1
                    
                    # Batch processing
                    if len(batch) >= batch_size:
                        scores.extend(batch)
                        batch = []
                            
                except ValueError:
                    continue
            
            # Process remaining data
            if batch:
                scores.extend(batch)
        
        scores_array = np.array(scores, dtype=np.float32)  # Use float32 to save memory
        print(f"Parsing complete, total {len(scores_array):,} sites (start position: {start_pos}, step size: {step})")
        return scores_array, start_pos, step
    
    def load_data(self):
        """Load and parse data files"""
        print(f"\n=== Starting parsing of {self.chrom} chromosome data ===\n")
        self.phylop_scores, self.phylop_start, self.phylop_step = self.parse_wigfix(self.phylop_file)
        self.phastcons_scores, self.phastcons_start, self.phastcons_step = self.parse_wigfix(self.phastcons_file)
        print("\nData parsing complete\n")
    
    def calculate_statistics(self, scores, score_type):
        """
        Calculate statistical metrics
        
        Args:
            scores: Score array
            score_type: Score type name
        """
        if len(scores) == 0:
            print(f"{score_type}: No data")
            return
        
        print(f"\n--- {score_type} Statistics ---")
        print(f"Total sites: {len(scores):,}")
        print(f"Minimum: {np.min(scores):.4f}")
        print(f"Maximum: {np.max(scores):.4f}")
        print(f"Mean: {np.mean(scores):.4f}")
        print(f"Median: {np.median(scores):.4f}")
        print(f"Standard deviation: {np.std(scores):.4f}")
        
        # Conservation distribution statistics
        if score_type == "phyloP":
            # phyloP: Positive values indicate conservation, negative values indicate rapid evolution
            conserved = np.sum(scores > 0)
            neutral = np.sum(scores == 0)
            fast_evolving = np.sum(scores < 0)
            
            print(f"\nConservation distribution:")
            print(f"  Conserved sites (>0): {conserved:,} ({conserved/len(scores)*100:.2f}%)")
            print(f"  Neutral sites (=0): {neutral:,} ({neutral/len(scores)*100:.2f}%)")
            print(f"  Fast evolving (<0): {fast_evolving:,} ({fast_evolving/len(scores)*100:.2f}%)")
            
            # Highly conserved sites
            highly_conserved = np.sum(scores > 2)
            print(f"  Highly conserved (>2): {highly_conserved:,} ({highly_conserved/len(scores)*100:.2f}%)")
        
        else:  # phastCons
            # phastCons: Between 0-1, closer to 1 means more conserved
            high_conservation = np.sum(scores > 0.9)
            moderate = np.sum((scores > 0.5) & (scores <= 0.9))
            low = np.sum(scores <= 0.5)
            
            print(f"\nConservation distribution:")
            print(f"  High conservation (>0.9): {high_conservation:,} ({high_conservation/len(scores)*100:.2f}%)")
            print(f"  Moderate conservation (0.5-0.9): {moderate:,} ({moderate/len(scores)*100:.2f}%)")
            print(f"  Low conservation (≤0.5): {low:,} ({low/len(scores)*100:.2f}%)")
    
    def analyze(self):
        """Execute complete data analysis"""
        print(f"\n{'='*60}")
        print(f"  {self.chrom} Chromosome Conservation Score Analysis")
        print(f"{'='*60}")
        
        # Display position information
        print(f"\nPosition information:")
        print(f"phyloP   - Start position: {self.phylop_start:,}, Step size: {self.phylop_step}")
        print(f"phastCons - Start position: {self.phastcons_start:,}, Step size: {self.phastcons_step}")
        
        self.calculate_statistics(self.phylop_scores, "phyloP")
        self.calculate_statistics(self.phastcons_scores, "phastCons")
        
        # Data comparison
        print(f"\n{'='*60}")
        print("  Comparison of Two Scoring Methods")
        print(f"{'='*60}")
        print(f"\nphyloP site count: {len(self.phylop_scores):,}")
        print(f"phastCons site count: {len(self.phastcons_scores):,}")
        
        if len(self.phylop_scores) != len(self.phastcons_scores):
            print("\n⚠️  Note: Site counts differ between the two methods")
    
    def run(self):
        """Execute complete workflow"""
        self.download_data()
        self.load_data()
        self.analyze()


def main():
    """Main function"""
    # Default analysis chr1
    analyzer = ConservationScoreAnalyzer(chrom='chr1')
    analyzer.run()


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# lncRNA Validation Analysis - Simplified Version
#
# This script validates whether GENCODE lncRNA information appears in GPN-MSA training data.
# Implements both analysis pathways from the project plan.
#
# Usage:
#     python lncrna_analysis.py --gencode gencode.gtf --gpn-msa data.json --output output/
#     python lncrna_analysis.py --config config.json
#
# Author: Capstone Project Team

import os
import sys
import json
import argparse
import logging
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GenomicRegion:
    # Represents a genomic region with coordinates and metadata
    def __init__(self, chrom, start, end, gene_id, gene_name, gene_type, strand='+'):
        self.chrom = chrom
        self.start = start
        self.end = end
        self.gene_id = gene_id
        self.gene_name = gene_name
        self.gene_type = gene_type
        self.strand = strand
        
        if self.start >= self.end:
            raise ValueError(f"Invalid coordinates: start ({self.start}) >= end ({self.end})")
    
    def overlaps(self, other):
        # Check if this region overlaps with another region
        if self.chrom != other.chrom:
            return False
        return not (self.end <= other.start or other.end <= self.start)

class TrainingWindow:
    # Represents a GPN-MSA training window
    def __init__(self, chrom, start, end, window_id, sequence=None, label=None, embedding=None):
        self.chrom = chrom
        self.start = start
        self.end = end
        self.window_id = window_id
        self.sequence = sequence
        self.label = label
        self.embedding = embedding
        
        if self.start >= self.end:
            raise ValueError(f"Invalid coordinates: start ({self.start}) >= end ({self.end})")

class lncRNAAnalyzer:
    # Main analyzer class for lncRNA validation
    
    def __init__(self, gencode_path, gpn_msa_path, output_dir="output"):
        self.gencode_path = gencode_path
        self.gpn_msa_path = gpn_msa_path
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Data storage
        self.gencode_regions = []
        self.lncrna_regions = []
        self.training_windows = []
        self.intersections = []
    
    def parse_gencode_gtf(self):
        # Parse GENCODE GTF file and extract gene regions
        logger.info(f"Parsing GENCODE GTF: {self.gencode_path}")
        
        regions = []
        with open(self.gencode_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.startswith('#'):
                    continue
                
                try:
                    region = self._parse_gtf_line(line.strip())
                    if region:
                        regions.append(region)
                except Exception as e:
                    logger.warning(f"Error parsing line {line_num}: {e}")
                    continue
        
        self.gencode_regions = regions
        self.lncrna_regions = [r for r in regions if 'lncRNA' in r.gene_type.lower()]
        
        logger.info(f"Parsed {len(regions)} total regions, {len(self.lncrna_regions)} lncRNA regions")
        return regions
    
    def _parse_gtf_line(self, line):
        # Parse a single GTF line
        fields = line.split('\t')
        if len(fields) < 9 or fields[2] != 'gene':
            return None
        
        chrom = fields[0]
        start = int(fields[3]) - 1  # Convert to 0-based
        end = int(fields[4])
        strand = fields[6]
        
        # Parse attributes
        attributes = {}
        for attr in fields[8].split(';'):
            attr = attr.strip()
            if ' ' in attr:
                key, value = attr.split(' ', 1)
                value = value.strip('"')
                attributes[key] = value
        
        return GenomicRegion(
            chrom=chrom,
            start=start,
            end=end,
            gene_id=attributes.get('gene_id', 'unknown'),
            gene_name=attributes.get('gene_name', 'unknown'),
            gene_type=attributes.get('gene_type', 'unknown'),
            strand=strand
        )
    
    def parse_gpn_msa_data(self, window_size=150):
        # Parse GPN-MSA training data and extract windows
        logger.info(f"Parsing GPN-MSA data: {self.gpn_msa_path}")
        
        windows = []
        
        if self.gpn_msa_path.endswith('.json'):
            windows = self._parse_json_data(window_size)
        elif self.gpn_msa_path.endswith('.bed'):
            windows = self._parse_bed_data(window_size)
        else:
            logger.warning(f"Unknown data format for {self.gpn_msa_path}")
        
        self.training_windows = windows
        logger.info(f"Parsed {len(windows)} training windows")
        return windows
    
    def _parse_json_data(self, window_size):
        # Parse JSON format training data
        try:
            with open(self.gpn_msa_path, 'r') as f:
                data = json.load(f)
            
            windows = []
            for i, item in enumerate(data):
                chrom = item.get('chromosome', 'chr1')
                start = item.get('start', i * window_size)
                end = start + window_size
                
                window = TrainingWindow(
                    chrom=chrom,
                    start=start,
                    end=end,
                    window_id=f"window_{i}",
                    sequence=item.get('sequence'),
                    label=item.get('label'),
                    embedding=item.get('embedding')
                )
                windows.append(window)
            
            return windows
        except Exception as e:
            logger.error(f"Error parsing JSON data: {e}")
            return []
    
    def _parse_bed_data(self, window_size):
        # Parse BED format training data
        try:
            windows = []
            with open(self.gpn_msa_path, 'r') as f:
                for i, line in enumerate(f):
                    if line.startswith('#'):
                        continue
                    
                    fields = line.strip().split('\t')
                    if len(fields) >= 3:
                        chrom = fields[0]
                        start = int(fields[1])
                        end = int(fields[2])
                        
                        window = TrainingWindow(
                            chrom=chrom,
                            start=start,
                            end=end,
                            window_id=f"window_{i}",
                            label=fields[3] if len(fields) > 3 else None
                        )
                        windows.append(window)
            
            return windows
        except Exception as e:
            logger.error(f"Error parsing BED data: {e}")
            return []
    
    def find_intersections(self):
        # Find intersections between GENCODE regions and training windows
        logger.info("Finding genomic intersections...")
        
        intersections = []
        for region in self.gencode_regions:
            for window in self.training_windows:
                if self._regions_overlap(region, window):
                    intersections.append((region, window))
        
        self.intersections = intersections
        logger.info(f"Found {len(intersections)} intersections")
        return intersections
    
    def _regions_overlap(self, region, window):
        # Check if a genomic region overlaps with a training window
        if region.chrom != window.chrom:
            return False
        return not (region.end <= window.start or window.end <= region.start)
    
    def get_lncrna_coverage(self):
        # Get lncRNA coverage statistics
        lncrna_intersections = [(r, w) for r, w in self.intersections if 'lncRNA' in r.gene_type.lower()]
        
        coverage_stats = {
            'total_lncrna_regions': len(self.lncrna_regions),
            'lncrna_regions_with_windows': len(set(r.gene_id for r, w in lncrna_intersections)),
            'total_intersections': len(lncrna_intersections),
            'coverage_percentage': (len(set(r.gene_id for r, w in lncrna_intersections)) / 
                                  len(self.lncrna_regions) * 100) if self.lncrna_regions else 0
        }
        
        return coverage_stats
    
    def generate_visualizations(self, coverage_stats):
        # Generate visualizations for the analysis
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Create figure with subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. lncRNA Coverage Pie Chart
            covered = coverage_stats['lncrna_regions_with_windows']
            not_covered = coverage_stats['total_lncrna_regions'] - covered
            
            ax1.pie([covered, not_covered], 
                    labels=['Covered by Windows', 'Not Covered'],
                    autopct='%1.1f%%',
                    colors=['#2E8B57', '#FF6B6B'])
            ax1.set_title('lncRNA Coverage by Training Windows')
            
            # 2. Coverage Bar Chart
            categories = ['Total lncRNAs', 'Covered lncRNAs', 'Total Intersections']
            values = [coverage_stats['total_lncrna_regions'], 
                     coverage_stats['lncrna_regions_with_windows'],
                     coverage_stats['total_intersections']]
            
            bars = ax2.bar(categories, values, color=['#4169E1', '#2E8B57', '#FF8C00'])
            ax2.set_title('lncRNA Coverage Statistics')
            ax2.set_ylabel('Count')
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(value), ha='center', va='bottom')
            
            # 3. Gene Type Distribution
            gene_types = [r.gene_type for r in self.gencode_regions]
            type_counts = Counter(gene_types)
            top_types = dict(type_counts.most_common(10))
            
            ax3.bar(range(len(top_types)), list(top_types.values()))
            ax3.set_xticks(range(len(top_types)))
            ax3.set_xticklabels(list(top_types.keys()), rotation=45, ha='right')
            ax3.set_title('Distribution of Gene Types in GENCODE Data')
            ax3.set_ylabel('Count')
            
            # 4. Chromosome Distribution
            chrom_counts = Counter(r.chrom for r, w in self.intersections)
            top_chroms = dict(chrom_counts.most_common(10))
            
            ax4.bar(range(len(top_chroms)), list(top_chroms.values()))
            ax4.set_xticks(range(len(top_chroms)))
            ax4.set_xticklabels(list(top_chroms.keys()), rotation=45, ha='right')
            ax4.set_title('Intersections by Chromosome')
            ax4.set_ylabel('Count')
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'lncrna_analysis.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Visualizations saved to {self.output_dir}/lncrna_analysis.png")
            
        except ImportError:
            logger.warning("matplotlib not available, skipping visualizations")
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
    
    def generate_report(self, coverage_stats):
        # Generate comprehensive analysis report
        # Count gene types in intersections
        intersection_gene_types = Counter()
        for region, window in self.intersections:
            intersection_gene_types[region.gene_type] += 1
        
        # Calculate additional statistics
        total_windows = len(self.training_windows)
        windows_with_genes = len(set(w.window_id for r, w in self.intersections))
        
        # Get top intersected genes
        gene_counts = Counter()
        for region, window in self.intersections:
            gene_counts[region.gene_name] += 1
        
        top_genes = []
        for gene_name, count in gene_counts.most_common(10):
            region = next((r for r in self.gencode_regions if r.gene_name == gene_name), None)
            if region:
                top_genes.append({
                    'gene_name': gene_name,
                    'gene_id': region.gene_id,
                    'gene_type': region.gene_type,
                    'intersection_count': count,
                    'chromosome': region.chrom,
                    'coordinates': f"{region.start}-{region.end}"
                })
        
        # Get chromosome distribution
        chrom_counts = Counter(r.chrom for r, w in self.intersections)
        
        report = {
            'summary': {
                'total_gencode_regions': len(self.gencode_regions),
                'total_lncrna_regions': coverage_stats['total_lncrna_regions'],
                'total_training_windows': total_windows,
                'lncrna_coverage_percentage': coverage_stats['coverage_percentage'],
                'windows_with_gene_overlap': windows_with_genes,
                'total_intersections': len(self.intersections)
            },
            'lncrna_coverage': coverage_stats,
            'gene_type_intersections': dict(intersection_gene_types),
            'top_intersected_genes': top_genes,
            'chromosome_distribution': dict(chrom_counts)
        }
        
        # Save report to JSON
        report_path = os.path.join(self.output_dir, 'lncrna_analysis_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Analysis report saved to: {report_path}")
        return report
    
    def run_analysis(self, window_size=150):
        # Run the complete lncRNA validation analysis
        logger.info("Starting lncRNA validation analysis...")
        
        # Step 1: Parse GENCODE data
        self.parse_gencode_gtf()
        
        # Step 2: Parse GPN-MSA training data
        self.parse_gpn_msa_data(window_size)
        
        # Step 3: Find intersections
        self.find_intersections()
        
        # Step 4: Get coverage statistics
        coverage_stats = self.get_lncrna_coverage()
        
        # Step 5: Generate visualizations
        self.generate_visualizations(coverage_stats)
        
        # Step 6: Generate report
        results = self.generate_report(coverage_stats)
        
        logger.info("Analysis completed successfully!")
        return results

def load_config(config_path):
    # Load configuration from JSON file
    with open(config_path, 'r') as f:
        return json.load(f)

def validate_paths(gencode_path, gpn_msa_path):
    # Validate that input files exist
    if not os.path.exists(gencode_path):
        logger.error(f"GENCODE file not found: {gencode_path}")
        return False
    
    if not os.path.exists(gpn_msa_path):
        logger.error(f"GPN-MSA data file not found: {gpn_msa_path}")
        return False
    
    return True

def print_summary(results):
    # Print analysis summary
    print("\n" + "="*60)
    print("lncRNA VALIDATION ANALYSIS SUMMARY")
    print("="*60)
    
    summary = results['summary']
    print(f"Total GENCODE regions: {summary['total_gencode_regions']:,}")
    print(f"Total lncRNA regions: {summary['total_lncrna_regions']:,}")
    print(f"Total training windows: {summary['total_training_windows']:,}")
    print(f"lncRNA coverage: {summary['lncrna_coverage_percentage']:.2f}%")
    print(f"Windows with gene overlap: {summary['windows_with_gene_overlap']:,}")
    print(f"Total intersections: {summary['total_intersections']:,}")
    
    print(f"\nTop gene types in intersections:")
    for gene_type, count in list(results['gene_type_intersections'].items())[:5]:
        print(f"  {gene_type}: {count}")
    
    print(f"\nTop intersected genes:")
    for gene in results['top_intersected_genes'][:5]:
        print(f"  {gene['gene_name']} ({gene['gene_type']}): {gene['intersection_count']} intersections")
    
    print("="*60)

def main():
    # Main function
    parser = argparse.ArgumentParser(description='lncRNA Validation Analysis')
    
    # Input file arguments
    parser.add_argument('--gencode', type=str, help='Path to GENCODE GTF file')
    parser.add_argument('--gpn-msa', type=str, help='Path to GPN-MSA training data file')
    parser.add_argument('--config', type=str, help='Path to configuration JSON file')
    
    # Analysis parameters
    parser.add_argument('--window-size', type=int, default=150, help='Training window size (default: 150)')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory (default: output)')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = load_config(args.config)
        gencode_path = config.get('gencode_path')
        gpn_msa_path = config.get('gpn_msa_path')
        window_size = config.get('window_size', args.window_size)
        output_dir = config.get('output_dir', args.output_dir)
    else:
        gencode_path = args.gencode
        gpn_msa_path = args.gpn_msa
        window_size = args.window_size
        output_dir = args.output_dir
    
    # Validate inputs
    if not gencode_path or not gpn_msa_path:
        logger.error("Please provide either --config file or both --gencode and --gpn-msa paths")
        parser.print_help()
        return 1
    
    if not validate_paths(gencode_path, gpn_msa_path):
        return 1
    
    # Run analysis
    try:
        logger.info("Starting lncRNA validation analysis...")
        logger.info(f"GENCODE file: {gencode_path}")
        logger.info(f"GPN-MSA file: {gpn_msa_path}")
        logger.info(f"Window size: {window_size}")
        logger.info(f"Output directory: {output_dir}")
        
        analyzer = lncRNAAnalyzer(gencode_path, gpn_msa_path, output_dir)
        results = analyzer.run_analysis(window_size)
        
        # Print summary
        print_summary(results)
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

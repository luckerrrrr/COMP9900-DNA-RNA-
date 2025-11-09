#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized Conservation Score Visualization Module
✨ New Optimizations:
1. Vectorized Queries: Use np.searchsorted for batch lookups (replacing Python loops)
2. Decompression Cache: First decompress .gz files and save as .wig, then directly read
3. Correlation Analysis: phastCons vs GPN entropy scores (modified)
"""

import gzip
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from scipy import stats
from dataclasses import dataclass


@dataclass
class Block:
    """Conservation data block"""
    start: int
    end: int
    step: int
    scores: np.ndarray


class ConservationVisualizer:
    """Optimized conservation score visualization (vectorized queries + decompression cache)"""
    
    def __init__(self, output_dir: str, dataset_dir: str = 'dataset'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_dir = Path(dataset_dir)
        
        # Use NumPy arrays to store starting positions (supports vectorized queries)
        self.phylop_blocks: List[Block] = []
        self.phastcons_blocks: List[Block] = []
        self.phylop_starts: np.ndarray = None
        self.phastcons_starts: np.ndarray = None
        
        # Set plotting style
        sns.set_style("whitegrid")
        plt.rcParams['font.size'] = 10
        plt.rcParams['figure.dpi'] = 150
    
    def _decompress_if_needed(self, gz_path: Path) -> Path:
        """
        Decompress .gz file and cache (if cache doesn't exist)
        
        Args:
            gz_path: .gz file path
            
        Returns:
            Decompressed file path
        """
        wig_path = gz_path.with_suffix('')  # Remove .gz suffix
        
        # If decompressed file exists, use it directly
        if wig_path.exists():
            print(f"  ✓ Using cached: {wig_path.name}")
            return wig_path
        
        # Otherwise decompress and save
        print(f"  → Decompressing: {gz_path.name} ...")
        with gzip.open(gz_path, 'rb') as f_in:
            with open(wig_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"  ✓ Saved to: {wig_path.name}")
        
        return wig_path
    
    def _ensure_conservation_file(self, chrom: str, data_type: str) -> Optional[Path]:
        """
        Ensure conservation data file exists (prioritize existing files, download if not present)
        
        Args:
            chrom: Chromosome name (e.g., 'chr1')
            data_type: 'phyloP' or 'phastCons'
            
        Returns:
            File path (.wig or .wigFix), None on failure
        """
        base_name = f"{chrom}.{data_type}100way.wigFix"
        
        # Priority 1: Already decompressed .wigFix file
        wig_path = self.dataset_dir / base_name
        if wig_path.exists():
            print(f"  ✓ Found: {wig_path.name}")
            return wig_path
        
        # Priority 2: Compressed .wigFix.gz file
        gz_path = self.dataset_dir / f"{base_name}.gz"
        if gz_path.exists():
            print(f"  ✓ Found compressed: {gz_path.name}")
            return self._decompress_if_needed(gz_path)
        
        # Priority 3: Download file
        print(f"  → {data_type} data not found, downloading...")
        return self._download_conservation_file(chrom, data_type)
    
    def _download_conservation_file(self, chrom: str, data_type: str) -> Optional[Path]:
        """
        Download conservation data from UCSC
        
        Args:
            chrom: Chromosome name (e.g., 'chr1')
            data_type: 'phyloP' or 'phastCons'
            
        Returns:
            Decompressed file path, None on failure
        """
        import urllib.request
        
        # UCSC download link
        base_url = "http://hgdownload.soe.ucsc.edu/goldenPath/hg38/phyloP100way"
        if data_type == "phastCons":
            base_url = "http://hgdownload.soe.ucsc.edu/goldenPath/hg38/phastCons100way"
        
        file_name = f"{chrom}.{data_type}100way.wigFix.gz"
        url = f"{base_url}/hg38.100way.{data_type}/{file_name}"
        gz_path = self.dataset_dir / file_name
        
        try:
            print(f"  → Downloading from: {url}")
            print(f"  → This may take several minutes...")
            
            # Download file (with progress)
            def _progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 / total_size)
                    mb = downloaded / (1024**2)
                    total_mb = total_size / (1024**2)
                    print(f"\r    Progress: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)", end='')
            
            urllib.request.urlretrieve(url, gz_path, reporthook=_progress)
            print(f"\n  ✓ Downloaded: {gz_path.name}")
            
            # Decompress
            return self._decompress_if_needed(gz_path)
            
        except Exception as e:
            print(f"\n  ✗ Download failed: {e}")
            if gz_path.exists():
                gz_path.unlink()
            return None
    
    def load_conservation_data(self, chrom: str) -> bool:
        """Load phyloP and phastCons data (auto-download + decompression cache)"""
        print(f"\n→ Loading conservation data for {chrom}...")
        
        # Ensure dataset directory exists
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Get phyloP file
        phylop_file = self._ensure_conservation_file(chrom, "phyloP")
        if phylop_file is None:
            print(f"⚠️  Failed to obtain phyloP data")
            return False
        
        # Get phastCons file
        phastcons_file = self._ensure_conservation_file(chrom, "phastCons")
        if phastcons_file is None:
            print(f"⚠️  Failed to obtain phastCons data")
            return False
        
        # Parse data
        self.phylop_blocks, self.phylop_starts = self._parse_wigfix_optimized(phylop_file)
        self.phastcons_blocks, self.phastcons_starts = self._parse_wigfix_optimized(phastcons_file)
        
        print(f"✓ phyloP: {len(self.phylop_blocks)} blocks loaded")
        print(f"✓ phastCons: {len(self.phastcons_blocks)} blocks loaded")
        
        return True
    
    def _parse_wigfix_optimized(self, filepath: Path) -> Tuple[List[Block], np.ndarray]:
        """
        Parse WigFix file (supports .wig and .gz)
        
        Returns:
            (blocks, sorted_starts_array)
        """
        blocks = []
        current_start = None
        current_step = 1
        current_scores = []
        
        # Auto-detect if compressed
        open_func = gzip.open if filepath.suffix == '.gz' else open
        mode = 'rt' if filepath.suffix == '.gz' else 'r'
        
        with open_func(filepath, mode) as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('fixedStep'):
                    # Save previous block
                    if current_start is not None and current_scores:
                        scores_array = np.array(current_scores, dtype=np.float32)
                        blocks.append(Block(
                            start=current_start,
                            end=current_start + len(scores_array) * current_step,
                            step=current_step,
                            scores=scores_array
                        ))
                    
                    # Parse new block
                    current_scores = []
                    parts = line.split()
                    for part in parts:
                        if part.startswith('start='):
                            current_start = int(part.split('=')[1])
                        elif part.startswith('step='):
                            current_step = int(part.split('=')[1])
                    continue
                
                if line and not line.startswith('#'):
                    try:
                        current_scores.append(float(line))
                    except ValueError:
                        pass
            
            # Save last block
            if current_start is not None and current_scores:
                scores_array = np.array(current_scores, dtype=np.float32)
                blocks.append(Block(
                    start=current_start,
                    end=current_start + len(scores_array) * current_step,
                    step=current_step,
                    scores=scores_array
                ))
        
        # Sort by start position
        blocks.sort(key=lambda b: b.start)
        sorted_starts = np.array([b.start for b in blocks], dtype=np.int32)
        
        total_sites = sum(len(b.scores) for b in blocks)
        print(f"  Parsed {filepath.name}: {len(blocks)} blocks, {total_sites:,} total sites")
        
        return blocks, sorted_starts
    
    # ========== Core Optimization: Vectorized Queries ==========
    def _get_scores_vectorized(self, blocks: List[Block], 
                               sorted_starts: np.ndarray, 
                               positions: np.ndarray) -> np.ndarray:
        """
        Vectorized batch score queries (replacing individual queries)
        
        Algorithm:
        1. Use np.searchsorted to find block index for each position
        2. Vectorized calculation of array offsets
        3. Batch extract scores
        
        Complexity: O(m + n·log(k)), where:
            m = len(positions)
            n = average sites per block
            k = len(blocks)
        
        Args:
            blocks: Conservation block list
            sorted_starts: Sorted start position array
            positions: Positions to query array
            
        Returns:
            Score array (unfound positions are NaN)
        """
        scores = np.full(len(positions), np.nan, dtype=np.float32)
        
        # Batch binary search: find block index for each position
        block_indices = np.searchsorted(sorted_starts, positions, side='right') - 1
        
        # Process by block grouping (avoid repeated access to same block)
        for block_idx in np.unique(block_indices):
            if block_idx < 0 or block_idx >= len(blocks):
                continue
            
            block = blocks[block_idx]
            
            # Find all positions belonging to this block
            mask = (block_indices == block_idx)
            pos_in_block = positions[mask]
            
            # Check if within block range
            valid_mask = (pos_in_block >= block.start) & (pos_in_block < block.end)
            valid_positions = pos_in_block[valid_mask]
            
            if len(valid_positions) == 0:
                continue
            
            # Vectorized calculation of array indices
            array_indices = (valid_positions - block.start) // block.step
            
            # Batch extract scores
            valid_scores = block.scores[array_indices]
            
            # Fill back to result array
            result_indices = np.where(mask)[0][valid_mask]
            scores[result_indices] = valid_scores
        
        return scores
    
    def add_conservation_scores_to_df(self, gene_results: pd.DataFrame) -> pd.DataFrame:
        """
        Vectorized addition of conservation scores (optimized version)
        """
        abs_positions = gene_results['abs_position'].values
        
        # Vectorized queries (replacing Python loops)
        phylop_scores = self._get_scores_vectorized(
            self.phylop_blocks, 
            self.phylop_starts, 
            abs_positions
        )
        
        phastcons_scores = self._get_scores_vectorized(
            self.phastcons_blocks, 
            self.phastcons_starts, 
            abs_positions
        )
        
        gene_results['phylop_score'] = phylop_scores
        gene_results['phastcons_score'] = phastcons_scores
        
        # Alignment statistics
        n_valid_phylop = np.sum(~np.isnan(phylop_scores))
        n_valid_phastcons = np.sum(~np.isnan(phastcons_scores))
        n_total = len(gene_results)
        
        print(f"  ✓ Alignment: phyloP {n_valid_phylop}/{n_total} ({n_valid_phylop/n_total*100:.1f}%), "
              f"phastCons {n_valid_phastcons}/{n_total} ({n_valid_phastcons/n_total*100:.1f}%)")
        
        return gene_results
    
    def plot_gene_conservation(self, gene_results: pd.DataFrame, gene_id: str):
        """Plot conservation comparison chart for single gene"""
        print(f"  → Aligning conservation scores for {gene_id}...")
        
        import time
        t0 = time.time()
        gene_results = self.add_conservation_scores_to_df(gene_results)
        print(f"  ⏱️  Alignment took {time.time() - t0:.2f}s")
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 10), 
                                gridspec_kw={'height_ratios': [2, 1, 1.5]})
        
        self._plot_conservation_curves(axes[0], gene_results)
        self._plot_gene_structure(axes[1], gene_results)
        self._plot_correlation(axes[2], gene_results)
        
        plt.suptitle(f"Conservation Analysis: {gene_id}", fontsize=14, fontweight='bold')
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        output_path = self.output_dir / f"{gene_id}_conservation.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Saved: {output_path.name}")
    
    def _plot_conservation_curves(self, ax, gene_results: pd.DataFrame):
        """Plot two conservation curves: GPN vs phastCons"""
        positions = gene_results['abs_position'].values
        gpn_scores = gene_results['conservation_score'].values
        phastcons_scores = gene_results['phastcons_score'].values
        
        # GPN entropy score
        ax.plot(positions, gpn_scores, 
               color='#2E86AB', linewidth=2, alpha=0.9, label='GPN Entropy Score')
        
        # phastCons
        phastcons_valid = ~np.isnan(phastcons_scores)
        if phastcons_valid.any():
            ax.plot(positions[phastcons_valid], phastcons_scores[phastcons_valid], 
                   color='#F18F01', linewidth=2, alpha=0.8, label='phastCons')
        
        ax.set_ylabel('Conservation Score', fontweight='bold')
        ax.set_ylim(-0.05, 1.05)
        ax.legend(loc='upper right', framealpha=0.9, fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_title('Panel A: Conservation Scores Comparison (GPN vs phastCons)', loc='left', fontsize=11)
    
    def _plot_gene_structure(self, ax, gene_results: pd.DataFrame):
        """Plot gene structure annotation"""
        positions = gene_results['abs_position'].values
        feature_types = gene_results['feature_types'].values
        
        y_mapping = {'gene': 0.7, 'transcript': 0.5, 'exon': 0.3}
        colors = {'gene': '#084C61', 'transcript': '#177E89', 'exon': '#FFC857'}
        
        for feature_name, y_pos in y_mapping.items():
            mask = np.array([feature_name in str(ft) for ft in feature_types])
            if mask.any():
                ax.scatter(positions[mask], [y_pos]*mask.sum(), 
                          c=colors[feature_name], s=1, alpha=0.6, label=feature_name)
        
        ax.set_yticks([0.3, 0.5, 0.7])
        ax.set_yticklabels(['exon', 'transcript', 'gene'])
        ax.set_ylim(0.2, 0.8)
        ax.set_ylabel('Feature Type', fontweight='bold')
        ax.set_xlabel('Genomic Position', fontweight='bold')
        ax.grid(True, alpha=0.2)
        ax.legend(loc='upper right', framealpha=0.9, fontsize=9)
        ax.set_title('Panel B: Gene Structure Annotation', loc='left', fontsize=11)
    
    def _plot_correlation(self, ax, gene_results: pd.DataFrame):
        """Plot correlation scatter plot: phastCons vs GPN Entropy (enhanced version)"""
        gpn_scores = gene_results['conservation_score'].values
        phylop_scores = gene_results['phylop_score'].values
        phastcons_scores = gene_results['phastcons_score'].values
        
        # Modified: use phastCons as main comparison target
        valid_mask = ~np.isnan(phastcons_scores)
        
        if valid_mask.sum() > 10:
            gpn_valid = gpn_scores[valid_mask]
            phastcons_valid = phastcons_scores[valid_mask]
            phylop_valid = phylop_scores[valid_mask]  # For coloring
            
            # Spearman correlation coefficient: phastCons vs GPN
            rho, p_value = stats.spearmanr(phastcons_valid, gpn_valid)
            
            # Scatter plot (phyloP coloring, if available)
            if np.sum(~np.isnan(phylop_valid)) > 0:
                # Normalize phyloP for coloring
                phylop_min = np.nanmin(phylop_valid)
                phylop_max = np.nanmax(phylop_valid)
                phylop_norm = (phylop_valid - phylop_min) / (phylop_max - phylop_min + 1e-9)
                
                scatter = ax.scatter(phastcons_valid, gpn_valid, 
                                    c=phylop_norm, cmap='viridis', 
                                    s=10, alpha=0.5, edgecolors='none')
                
                cbar = plt.colorbar(scatter, ax=ax, pad=0.01)
                cbar.set_label(f'phyloP (norm.)', rotation=270, labelpad=15)
            else:
                # If no phyloP data, use single color
                ax.scatter(phastcons_valid, gpn_valid, 
                          c='#2E86AB', s=10, alpha=0.5, edgecolors='none')
            
            # Add trend line
            z = np.polyfit(phastcons_valid, gpn_valid, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(phastcons_valid.min(), phastcons_valid.max(), 100)
            ax.plot(x_trend, p(x_trend), 'r--', linewidth=1, alpha=0.6, label='Linear fit')
            
            ax.set_xlabel('phastCons Score', fontweight='bold')
            ax.set_ylabel('GPN Entropy Score', fontweight='bold')
            ax.set_title(f'Panel C: Correlation (Spearman ρ = {rho:.3f}, p = {p_value:.2e}, n = {valid_mask.sum()})', 
                        loc='left', fontsize=11)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left', fontsize=9)
            
        else:
            ax.text(0.5, 0.5, f'Insufficient aligned data\n({valid_mask.sum()} valid points, need ≥10)', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_xlabel('phastCons Score', fontweight='bold')
            ax.set_ylabel('GPN Entropy Score', fontweight='bold')
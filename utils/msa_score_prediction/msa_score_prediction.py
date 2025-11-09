#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPN-MSA Inference and Conservation Prediction (Optimized + Real-time Visualization)

Core Functions:
1. Import lncRNA interval data
2. Intelligently merge overlapping intervals to avoid redundant computation
3. Batch inference (512bp window, non-overlapping)
4. Data compression to optimize memory
5. Calculate conservation scores (binary logarithmic entropy)
6. Generate visualization immediately after processing each gene
7. Check existing visualizations before starting to avoid duplication
8. Save results uniformly at the end
"""

import os
import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, List

import torch
import torch.nn.functional as F

from data.loader import GenomeLoader
from gpn.data import Tokenizer
from utils.msa_score_prediction.monitor import MemoryMonitor
from utils.msa_score_prediction.gencode_extracter import GencodeExtractor
from utils.msa_score_prediction.conservation_visualizer import ConservationVisualizer


# ==================== Global Configuration Parameters ====================
# Inference window and batch
WIN = 512
BATCH_SIZE = 64

# Path configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get("USER", "unknown")
CACHE_DIR = f"/srv/scratch/{USER}/hf_cache"
GTF_PATH = "dataset/gencode.v38.basic.annotation.gtf"
OUTPUT_DIR = PROJECT_ROOT / "results"
OUTPUT_FILE = "lncrna_predictions.parquet"
VIS_OUTPUT_DIR = PROJECT_ROOT / "results" / "conservation_test"

# Inference parameters
DEFAULT_CHROM = "1"
MAX_DEBUG_GENES = None
PREVIEW_ROWS = 30

# Data type optimization mapping
DTYPE_OPTIMIZATION = {
    'gene_id': 'category',
    'feature_types': 'category',
    'transcript_ids': 'category',
    'position': 'int16',
    'batch_id': 'int16',
    'batch_start': 'int32',
    'batch_end': 'int32',
    'abs_position': 'int32',
    'predicted_token': 'int8',
    'max_prob': 'float32',
    'conservation_score': 'float32',
}


# ==================== Core Inference Class ====================
class GPNInference:
    """GPN-MSA Inference Engine: Unified management of model loading, inference and result processing"""
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        """Initialize model and data resources"""
        self._load_resources(cache_dir)
        self._setup_device()
        self._cache_token_ids()
        self._detect_chrom_format()
    
    # ---------- Initialization Related ----------
    def _load_resources(self, cache_dir: str):
        """Load model and dataset"""
        loader = GenomeLoader(cache_dir=cache_dir)
        self.model_masked = loader.load_gpn_msa_sapiens_model(masked=True)
        self.genome_msa = loader.load_multiz100way_dataset(streaming=True)
        self.tokenizer = Tokenizer()
    
    def _setup_device(self):
        """Configure compute device"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if torch.cuda.is_available():
            self.model_masked = self.model_masked.to(self.device)
            print(f"✓ Device: {self.device} ({torch.cuda.get_device_name(0)})")
        else:
            print(f"✓ Device: {self.device}")
    
    def _cache_token_ids(self):
        """Cache commonly used token IDs"""
        for name in ["pad_token_id", "mask_token_id"]:
            val = getattr(self.tokenizer, name, None)
            setattr(self, f"_{name}", val() if callable(val) else val)
    
    def _detect_chrom_format(self):
        """Detect dataset chromosome format"""
        sample_chrom = list(self.genome_msa.data.keys())[0]
        self.chrom_has_prefix = sample_chrom.startswith("chr")
        print(f"✓ Chromosome format: {'chr+number' if self.chrom_has_prefix else 'number only'}")
    
    def _normalize_chrom(self, chrom: str) -> str:
        """Standardize chromosome name"""
        chrom = str(chrom)
        return (chrom if chrom.startswith("chr") else f"chr{chrom}") if self.chrom_has_prefix \
               else (chrom[3:] if chrom.startswith("chr") else chrom)
    
    # ---------- Data Retrieval ----------
    def get_msa_window(self, chrom: str, start: int, win: int = WIN) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get MSA window data, returns (input_ids, aux_features)"""
        chrom = self._normalize_chrom(chrom)
        arr = self.genome_msa.get_msa(chrom, start, start + win, strand="+", tokenize=True)
        assert arr is not None and arr.shape[0] == win, f"Invalid MSA: {chrom}:{start}-{start+win}"
        
        arr = torch.tensor(arr, dtype=torch.long).unsqueeze(0)
        return arr[:, :, 0], arr[:, :, 1:]
    
    def _build_attention_mask(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Build attention mask"""
        return torch.ones_like(input_ids, dtype=torch.long) if self._pad_token_id is None \
               else (input_ids != int(self._pad_token_id)).long()
    
    # ---------- Core Inference ----------
    def run_masked_batch(self, input_ids: torch.Tensor, aux_features: torch.Tensor,
                        positions: List[int]) -> torch.Tensor:
        """Batch inference for multiple positions, returns [len(positions), vocab_size]"""
        self.model_masked.eval()
        
        input_ids = input_ids.to(self.device)
        aux_features = aux_features.to(self.device)
        attn = self._build_attention_mask(input_ids).to(self.device)
        
        all_logits = []
        with torch.no_grad():
            for pos in positions:
                masked_ids = input_ids.clone()
                masked_ids[0, pos] = int(self._mask_token_id)
                out = self.model_masked(input_ids=masked_ids, aux_features=aux_features, attention_mask=attn)
                all_logits.append(out.logits[0, pos])
        
        return torch.stack(all_logits)
    
    # ========== Conservation Calculation ==========
    @staticmethod
    def compute_conservation_score(probs: torch.Tensor, eps: float = 1e-12) -> float:
        """
        Calculate site conservation score (binary logarithmic entropy)
        
        Formula: S = 1 - H2(P)/2, where H2(P) = -Σ p_b * log2(p_b)
        
        Args:
            probs: Probability distribution of four bases (shape: [4])
            eps: Numerical stability clipping value
            
        Returns:
            Conservation score S ∈ [0, 1], closer to 1 means more conserved
        """
        # Normalize and clip
        p = probs / torch.clamp(probs.sum(), min=eps)
        p = torch.clamp(p, min=eps, max=1.0)
        
        # Calculate binary entropy
        H2 = -(p * torch.log2(p)).sum()
        
        # Normalize to [0, 1]
        S = 1.0 - H2 / 2.0
        
        return S.item()
    
    def predict_region(self, input_ids: torch.Tensor, aux_features: torch.Tensor, 
                      start_pos: int, end_pos: int) -> pd.DataFrame:
        """Batch inference for specified region (including conservation scores)"""
        positions = list(range(start_pos, end_pos))
        all_logits = self.run_masked_batch(input_ids, aux_features, positions)
        
        # Calculate probabilities and predictions
        results = []
        for i, pos in enumerate(positions):
            probs = F.softmax(all_logits[i], dim=-1)
            max_prob, predicted_id = torch.max(probs, dim=0)
            
            # Calculate conservation score
            conservation_score = self.compute_conservation_score(probs)
            
            results.append({
                'position': pos,
                'predicted_token': predicted_id.item(),
                'max_prob': max_prob.item(),
                'conservation_score': conservation_score,
                'probs': probs.cpu().numpy(),
                'logits': all_logits[i].cpu().numpy()
            })
        
        return pd.DataFrame(results)
    
    # ---------- lncRNA Batch Inference ----------
    def predict_lncrna_genes(self, lncrna_df: pd.DataFrame, chrom: str,
                            max_genes: Optional[int] = None,
                            visualizer: Optional[ConservationVisualizer] = None) -> pd.DataFrame:
        """
        Batch inference for all lncRNA genes
        
        Args:
            lncrna_df: lncRNA interval data
            chrom: Chromosome number
            max_genes: Maximum number of genes to process (for debugging)
            visualizer: Visualizer (if provided, real-time plotting per gene)
        """
        print(f"\n{'='*80}\n  Starting lncRNA Batch Inference\n{'='*80}")
        
        overall_start = time.time()
        
        # Prepare gene list
        lncrna_df['gene_id_parsed'] = lncrna_df['attr'].apply(lambda x: self._parse_attr(x, 'gene_id'))
        unique_genes = lncrna_df['gene_id_parsed'].unique()
        if max_genes:
            unique_genes = unique_genes[:max_genes]
        
        lncrna_df_filtered = lncrna_df[lncrna_df['gene_id_parsed'].isin(unique_genes)]
        
        print(f"📊 Total genes: {len(unique_genes)}, intervals: {len(lncrna_df_filtered)}\n")
        
        # Inference per gene
        all_results = []
        gene_timings = []
        
        for gene_idx, gene_id in enumerate(unique_genes):
            gene_data = lncrna_df_filtered[lncrna_df_filtered['gene_id_parsed'] == gene_id]
            gene_start_time = time.time()
            
            print(f"→ [{gene_idx+1}/{len(unique_genes)}] {gene_id} "
                  f"({len(gene_data)} features, {int(gene_data['start'].min())}-{int(gene_data['end'].max())} bp)")
            
            try:
                # Modified: pass visualizer parameter
                gene_results = self._predict_single_gene(gene_data, chrom, visualizer=visualizer)
                all_results.append(gene_results)
                
                gene_elapsed = time.time() - gene_start_time
                gene_timings.append(gene_elapsed)
                
                # Modified: output includes visualization status
                vis_status = " (visualized)" if visualizer is not None else ""
                print(f"  ✓ Completed in {gene_elapsed:.2f}s ({len(gene_results)} predictions){vis_status}")
                
                # Estimate remaining time
                if gene_idx > 0:
                    avg_time = np.mean(gene_timings)
                    remaining = (len(unique_genes) - gene_idx - 1) * avg_time
                    print(f"  📈 Progress: {(gene_idx+1)/len(unique_genes)*100:.1f}% | "
                          f"Avg: {avg_time:.1f}s/gene | ETA: {remaining/60:.1f} min\n")
                else:
                    print()
                    
            except Exception as e:
                print(f"  ✗ Error: {e}\n")
                continue
        
        # Merge results
        print(f"\n{'='*80}\n  Merging results...\n{'='*80}")
        final_df = pd.concat(all_results, ignore_index=True)
        final_df = self._optimize_dtypes(final_df)
        
        total_elapsed = time.time() - overall_start
        print(f"✓ Total predictions: {len(final_df):,}")
        print(f"✓ Memory usage: {final_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        print(f"\n⏱️  Performance: {total_elapsed:.2f}s ({total_elapsed/60:.2f} min) | "
              f"Avg: {np.mean(gene_timings):.2f}s/gene | "
              f"Throughput: {len(final_df)/total_elapsed:.1f} pos/sec\n")
        
        return final_df
    
    def _predict_single_gene(self, gene_intervals: pd.DataFrame, chrom: str, 
                            visualizer: Optional[ConservationVisualizer] = None) -> pd.DataFrame:
        """
        Predict all intervals for a single gene + immediate visualization (if visualizer provided)
        
        Args:
            gene_intervals: Gene interval data
            chrom: Chromosome number
            visualizer: Visualizer (if provided, plot immediately)
        """
        total_start = int(gene_intervals['start'].min())
        total_end = int(gene_intervals['end'].max())
        gene_id = self._parse_attr(gene_intervals.iloc[0]['attr'], 'gene_id')
        
        print(f"  → Range: {total_start}-{total_end} ({total_end - total_start} bp)")
        
        # Batch inference
        batches = self._split_to_batches(total_start, total_end)
        print(f"  → Batches: {len(batches)}")
        
        all_results = []
        for batch_idx, (batch_start, batch_end) in enumerate(batches):
            batch_length = batch_end - batch_start
            
            # MSA data loading
            input_ids, aux_features = self.get_msa_window(chrom, batch_start, win=batch_length)
            
            # Model inference
            batch_results = self.predict_region(input_ids, aux_features, 0, batch_length)
            
            # Add batch information
            batch_results['batch_id'] = batch_idx
            batch_results['batch_start'] = batch_start
            batch_results['batch_end'] = batch_end
            batch_results['abs_position'] = batch_start + batch_results['position']
            batch_results['gene_id'] = gene_id
            
            all_results.append(batch_results)
        
        # Merge and associate feature information
        full_results = pd.concat(all_results, ignore_index=True)
        print(f"  → Annotating features...")
        full_results = self._annotate_features(full_results, gene_intervals)
        
        # ========== New: Immediate Visualization ==========
        if visualizer is not None:
            print(f"  → Generating visualization...")
            try:
                visualizer.plot_gene_conservation(full_results, gene_id)
            except Exception as e:
                print(f"  ⚠️  Visualization failed: {e}")
        
        return full_results
    
    @staticmethod
    def _split_to_batches(start: int, end: int, window: int = WIN) -> List[Tuple[int, int]]:
        """Split large interval into multiple non-overlapping windows"""
        batches = []
        current = start
        while current < end:
            batch_end = min(current + window, end)
            batches.append((current, batch_end))
            current = batch_end
        return batches
    
    def _annotate_features(self, results_df: pd.DataFrame, 
                          gene_intervals: pd.DataFrame) -> pd.DataFrame:
        """Vectorized way to associate feature information"""
        for col in ['feature_types', 'transcript_ids', 'exon_ids', 'exon_numbers']:
            results_df[col] = ''
        
        for _, interval in gene_intervals.iterrows():
            start, end = int(interval['start']), int(interval['end'])
            feature = interval['feature']
            attr = interval['attr']
            
            mask = (results_df['abs_position'] >= start) & (results_df['abs_position'] <= end)
            
            results_df.loc[mask, 'feature_types'] = results_df.loc[mask, 'feature_types'].apply(
                lambda x: f"{x},{feature}" if x else feature
            )
            
            if feature == 'transcript':
                transcript_id = self._parse_attr(attr, 'transcript_id')
                if transcript_id:
                    results_df.loc[mask, 'transcript_ids'] = results_df.loc[mask, 'transcript_ids'].apply(
                        lambda x: f"{x},{transcript_id}" if x else transcript_id
                    )
            elif feature == 'exon':
                exon_id = self._parse_attr(attr, 'exon_id')
                exon_number = self._parse_attr(attr, 'exon_number')
                if exon_id:
                    results_df.loc[mask, 'exon_ids'] = results_df.loc[mask, 'exon_ids'].apply(
                        lambda x: f"{x},{exon_id}" if x else exon_id
                    )
                if exon_number:
                    results_df.loc[mask, 'exon_numbers'] = results_df.loc[mask, 'exon_numbers'].apply(
                        lambda x: f"{x},{exon_number}" if x else exon_number
                    )
        
        return results_df
    
    # ---------- Helper Methods ----------
    @staticmethod
    def _parse_attr(attr: str, key: str) -> Optional[str]:
        """Extract field from GTF attributes"""
        for part in attr.split(";"):
            if key in part and '"' in part:
                return part.split('"')[1]
        return None
    
    @staticmethod
    def _optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """Data type optimization to reduce memory usage"""
        for col, dtype in DTYPE_OPTIMIZATION.items():
            if col in df.columns:
                df[col] = df[col].astype(dtype)
        
        for col in ['probs', 'logits']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: x.astype('float32'))
        
        return df
    
    @staticmethod
    def format_results_preview(df: pd.DataFrame, n_rows: int = PREVIEW_ROWS):
        """Elegantly output prediction results table"""
        print(f"\n{'='*100}")
        print(f"  Preview: First {min(n_rows, len(df))} Predictions")
        print(f"{'='*100}")
        print(f"{'Gene ID':<18} {'Abs.Pos':<10} {'Feature Types':<25} {'Token':<6} {'Prob':<8} {'Conservation':<12}")
        print(f"{'-'*100}")
        
        for _, row in df.head(n_rows).iterrows():
            gene_id = row['gene_id'][:16] if pd.notna(row.get('gene_id')) else 'N/A'
            abs_pos = int(row['abs_position'])
            features = row.get('feature_types', 'N/A')
            token = int(row['predicted_token'])
            prob = float(row['max_prob'])
            conservation = float(row['conservation_score'])
            
            print(f"{gene_id:<18} {abs_pos:<10} {features:<25} {token:<6} {prob:.4f}   {conservation:.4f}")
        
        print(f"{'='*100}\n")


# ==================== Main Process ====================
def main():
    """Main process: Load resources → Extract intervals → Inference + Real-time visualization → Save results"""
    start_time = time.time()
    timings = {}
    
    # Initialize monitoring
    monitor = MemoryMonitor()
    monitor.print_diagnostics()
    memory_snapshots = {'start': monitor.snapshot()}
    
    # Print task header
    monitor.print_task_header(
        title="GPN-MSA lncRNA Batch Inference + Real-time Conservation Visualization",
        region=f"chr{DEFAULT_CHROM} (all lncRNA intervals)",
        initial_snapshot=memory_snapshots['start']
    )
    print(f"⚙️  Batch Size: {BATCH_SIZE}\n")
    
    # Step 1: Load GPN resources
    print("\n→ Loading GPN resources...")
    t0 = time.time()
    gpn = GPNInference(CACHE_DIR)
    timings['load_gpn'] = time.time() - t0
    memory_snapshots['after_load_gpn'] = monitor.snapshot()
    
    # Step 2: Extract lncRNA intervals
    print("\n→ Extracting lncRNA intervals...")
    t0 = time.time()
    extractor = GencodeExtractor(GTF_PATH)
    lncrna_df = extractor.extract_lncrna(chrom=f"chr{DEFAULT_CHROM}")
    timings['extract_lncrna'] = time.time() - t0
    memory_snapshots['after_extract'] = monitor.snapshot()
    
    if lncrna_df.empty:
        print("⚠️  No lncRNA data found. Exiting.")
        return
    
    # Step 3: Filter processed genes
    print("\n→ Filtering genes with existing visualizations...")
    lncrna_df['gene_id_parsed'] = lncrna_df['attr'].apply(
        lambda x: GPNInference._parse_attr(x, 'gene_id')
    )
    unique_genes = lncrna_df['gene_id_parsed'].unique()
    
    # Check which genes already have visualizations
    genes_to_process = []
    genes_skipped = []
    
    for gene_id in unique_genes:
        output_path = VIS_OUTPUT_DIR / f"{gene_id}_conservation.png"
        if output_path.exists():
            genes_skipped.append(gene_id)
        else:
            genes_to_process.append(gene_id)
    
    print(f"✓ Total genes: {len(unique_genes)}")
    print(f"  - To process: {len(genes_to_process)}")
    print(f"  - Skipped (already exists): {len(genes_skipped)}")
    
    if not genes_to_process:
        print("\n✓ All genes already processed. Exiting.")
        return
    
    # Limit processing count (for debugging)
    if MAX_DEBUG_GENES and len(genes_to_process) > MAX_DEBUG_GENES:
        genes_to_process = genes_to_process[:MAX_DEBUG_GENES]
        print(f"  - Debug mode: limiting to {MAX_DEBUG_GENES} genes")
    
    # Only keep genes to be processed
    lncrna_df_filtered = lncrna_df[lncrna_df['gene_id_parsed'].isin(genes_to_process)]
    print(f"  - Intervals to process: {len(lncrna_df_filtered)}\n")
    
    # Step 4: Initialize visualizer (before inference)
    print("\n→ Initializing conservation visualizer...")
    t0 = time.time()
    visualizer = ConservationVisualizer(output_dir=str(VIS_OUTPUT_DIR))
    
    # Try to load conservation data
    if not visualizer.load_conservation_data(chrom=f"chr{DEFAULT_CHROM}"):
        print("⚠️  Conservation data not available, will skip visualization")
        visualizer = None  # Set to None to skip visualization
    else:
        print("✓ Conservation data loaded successfully")
    
    timings['init_visualizer'] = time.time() - t0
    
    # Step 5: Batch inference + real-time visualization (modified: pass visualizer)
    print("\n→ Running batch inference + real-time visualization...")
    t0 = time.time()
    results_df = gpn.predict_lncrna_genes(
        lncrna_df_filtered,
        chrom=DEFAULT_CHROM,
        max_genes=None,
        visualizer=visualizer  # New: pass visualizer
    )
    timings['batch_inference_and_visualization'] = time.time() - t0
    memory_snapshots['after_inference'] = monitor.snapshot()
    
    # Step 6: Preview results
    gpn.format_results_preview(results_df)
    
    # Step 7: Save results
    output_path = OUTPUT_DIR / OUTPUT_FILE
    print(f"\n→ Saving results to {output_path}...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_parquet(str(output_path), compression='gzip')
    print(f"✓ Saved {len(results_df):,} predictions to: {output_path.relative_to(PROJECT_ROOT)}\n")
    
    # Step 8: Performance statistics
    stage_map = {
        'load_gpn': ('after_load_gpn', 'Load GPN'),
        'extract_lncrna': ('after_extract', 'Extract lncRNA'),
        'init_visualizer': ('after_extract', 'Init Visualizer'),
        'batch_inference_and_visualization': ('after_inference', 'Inference + Visualization')
    }
    monitor.print_performance_summary(start_time, timings, memory_snapshots, stage_map)
    
    # Output visualization path
    if visualizer is not None:
        print(f"\n✓ Visualizations saved to: {VIS_OUTPUT_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
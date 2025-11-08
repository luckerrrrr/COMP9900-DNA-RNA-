"""
GPN-MSA 基因组分析完整流程（增强版）
新增功能：
1. GENCODE 注释匹配
2. 详细调试日志
3. 参数自动校验
4. 中间结果导出
"""

import os
import torch
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from umap import UMAP
from matplotlib.gridspec import GridSpec
from PIL import Image

# 配置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

from data.loader import GenomeLoader
from gpn.data import Tokenizer
from ncrna_predict import (
    mlm_logp_true_per_base, 
    smooth_signal, 
    call_candidate_ncrnas,
    GENCODEAnnotator,  # 🆕 导入注释器
    debug_log  # 🆕 导入日志函数
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 全局配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

USER = os.environ.get("USER", "unknown")
CACHE_DIR = f"/srv/scratch/{USER}/hf_cache"

# 🆕 GENCODE GTF 路径（根据实际情况修改）
GENCODE_GTF = PROJECT_ROOT / "dataset" / "gencode.v38.basic.annotation.gtf"

# 分析参数
CHROM = "1"
START_POS = 100000
END_POS = 100512  # 🔍 改为 110000 以测试大窗口
WINDOW_SIZE = END_POS - START_POS

# 🎯 智能参数配置
if WINDOW_SIZE < 1000:
    MIN_LEN = max(50, WINDOW_SIZE // 10)
    TOP_QUANTILE = 0.90
    SMOOTH_WINDOW = 11  # 🔧 缩小平滑窗口
    debug_log(f"Small window mode: min_len={MIN_LEN}bp, quantile={TOP_QUANTILE}, smooth={SMOOTH_WINDOW}", "INFO")
elif WINDOW_SIZE < 10000:
    MIN_LEN = 100
    TOP_QUANTILE = 0.95
    SMOOTH_WINDOW = 51
    debug_log(f"Medium window mode: min_len={MIN_LEN}bp, quantile={TOP_QUANTILE}", "INFO")
else:
    MIN_LEN = 200
    TOP_QUANTILE = 0.995
    SMOOTH_WINDOW = 51
    debug_log(f"Large window mode: min_len={MIN_LEN}bp, quantile={TOP_QUANTILE}", "INFO")

# 可视化配置
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10
plt.rcParams['figure.dpi'] = 100


def print_section(title: str, char: str = "=", width: int = 70):
    """打印格式化章节标题"""
    print(f"\n{char * width}\n{title:^{width}}\n{char * width}\n")


def print_step(step_num: int, description: str):
    """打印步骤日志"""
    print(f"[Step {step_num}] {description}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 数据加载与模型推理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_data_and_models():
    """加载基因组数据和 GPN-MSA 模型"""
    print_step(1, "Initialize GenomeLoader")
    loader = GenomeLoader(cache_dir=CACHE_DIR)
    print("✅ GenomeLoader ready\n")
    
    print_step(2, "Load GPN-MSA model (songlab/gpn-msa-sapiens)")
    model = loader.load_gpn_msa_sapiens_model(masked=False)
    model.eval()
    print("✅ Model loaded\n")
    
    print_step(3, "Load Multiz100way MSA dataset (streaming)")
    genome_msa = loader.load_multiz100way_dataset(streaming=True)
    if genome_msa is None:
        raise RuntimeError("❌ MSA dataset loading failed")
    print("✅ MSA dataset ready\n")
    
    # 🆕 加载 GENCODE 注释
    print_step(4, "Load GENCODE annotations")
    annotator = None
    if GENCODE_GTF.exists():
        try:
            annotator = GENCODEAnnotator(str(GENCODE_GTF))
            print("✅ GENCODE annotator ready\n")
        except Exception as e:
            debug_log(f"Failed to load GENCODE: {e}", "WARN")
    else:
        debug_log(f"GENCODE file not found: {GENCODE_GTF}", "WARN")
        debug_log("Will proceed without annotation validation\n", "WARN")
    
    return loader, model, genome_msa, annotator


def extract_and_process_msa(genome_msa):
    """提取并处理目标区域 MSA"""
    print_step(5, f"Extract MSA for chr{CHROM}:{START_POS}-{END_POS}")
    
    raw_msa = genome_msa.get_msa(CHROM, START_POS, END_POS, strand="+", tokenize=False)
    print(f"✅ Raw MSA: {raw_msa.shape}, sample: {raw_msa[0, :10]}\n")
    
    # 🔍 检查 MSA 质量
    gap_ratio = np.mean(raw_msa == b'-')
    debug_log(f"MSA gap ratio: {gap_ratio:.2%}", "DEBUG")
    
    print_step(6, "Tokenize MSA")
    msa = genome_msa.get_msa(CHROM, START_POS, END_POS, strand="+", tokenize=True)
    msa = torch.tensor(np.expand_dims(msa, 0).astype(np.int64))
    input_ids, aux_features = msa[:, :, 0], msa[:, :, 1:]
    print(f"✅ input_ids: {input_ids.shape}, aux: {aux_features.shape}\n")
    
    return input_ids, aux_features


def compute_embeddings(model, input_ids, aux_features):
    """计算序列嵌入向量"""
    print_step(7, "Compute sequence embeddings")
    with torch.no_grad():
        embedding = model(input_ids=input_ids, aux_features=aux_features).last_hidden_state
    
    print(f"✅ Embedding: {embedding.shape}")
    
    embedding_df = pd.DataFrame(
        StandardScaler().fit_transform(embedding[0].numpy()),
        columns=[f"Dim_{i}" for i in range(embedding.shape[2])]
    )
    embedding_df.index.name = "Position"
    print(f"✅ DataFrame: {embedding_df.shape[0]} x {embedding_df.shape[1]}\n")
    
    # 🔍 导出中间结果
    embedding_file = RESULTS_DIR / f"embedding_chr{CHROM}_{START_POS}_{END_POS}.npz"
    np.savez_compressed(embedding_file, embedding=embedding[0].numpy())
    debug_log(f"Saved embedding to: {embedding_file}", "DEBUG")
    
    return embedding, embedding_df


def perform_umap_reduction(embedding):
    """UMAP 降维 (768D → 2D)"""
    print_step(8, "Perform UMAP dimensionality reduction")
    scaled = StandardScaler().fit_transform(embedding[0].numpy())
    
    umap_model = UMAP(n_neighbors=15, min_dist=0.1, n_components=2, random_state=42)
    umap_coords = umap_model.fit_transform(scaled)
    
    umap_df = pd.DataFrame(umap_coords, columns=["UMAP1", "UMAP2"])
    umap_df["Position"] = range(len(umap_coords))
    print(f"✅ UMAP: {umap_df.shape}\n")
    
    return umap_df


def predict_conservation_scores(loader, input_ids, aux_features):
    """基于 MLM 预测保守性得分"""
    print_step(9, "Load MLM and predict conservation scores")
    
    model_mlm = loader.load_gpn_msa_sapiens_model(masked=True)
    model_mlm.eval()
    tokenizer = Tokenizer()
    
    pos1 = np.arange(START_POS, END_POS, dtype=np.int64)
    scores = mlm_logp_true_per_base(
        model_mlm, input_ids, aux_features, tokenizer, batch_chunk=64
    )
    
    # 🔧 使用动态平滑窗口
    scores_smoothed = smooth_signal(scores, window=SMOOTH_WINDOW)
    
    print(f"✅ Valid sites: {np.isfinite(scores).sum()}/{len(scores)}")
    
    # 📊 详细统计
    valid_scores = scores_smoothed[np.isfinite(scores_smoothed)]
    if len(valid_scores) > 0:
        print(f"   Score range: [{np.min(valid_scores):.4f}, {np.max(valid_scores):.4f}]")
        print(f"   Score mean±std: {np.mean(valid_scores):.4f} ± {np.std(valid_scores):.4f}")
        
        # 🔍 显示多个分位数（帮助选择阈值）
        for q in [0.80, 0.85, 0.90, 0.95, 0.99]:
            threshold = np.quantile(valid_scores, q)
            high_count = np.sum(valid_scores >= threshold)
            print(f"   {q*100:.0f}% quantile: {threshold:.4f} ({high_count} sites)")
        print()
    
    # 🔍 导出得分数据
    scores_file = RESULTS_DIR / f"scores_chr{CHROM}_{START_POS}_{END_POS}.csv"
    pd.DataFrame({
        'position': pos1,
        'score_raw': scores,
        'score_smoothed': scores_smoothed
    }).to_csv(scores_file, index=False)
    debug_log(f"Saved scores to: {scores_file}", "DEBUG")
    
    return pos1, scores, scores_smoothed


def identify_ncrna_candidates(pos1, scores_smoothed, annotator=None):
    """识别候选 ncRNA 区域（增强版）"""
    print_step(10, "Identify candidate ncRNA regions")
    
    # 🔍 参数验证
    debug_log(f"Current parameters:", "INFO")
    debug_log(f"  - Window size: {WINDOW_SIZE} bp", "INFO")
    debug_log(f"  - Min length: {MIN_LEN} bp ({MIN_LEN/WINDOW_SIZE*100:.1f}% of window)", "INFO")
    debug_log(f"  - Top quantile: {TOP_QUANTILE}", "INFO")
    debug_log(f"  - Smooth window: {SMOOTH_WINDOW} bp", "INFO")
    
    # 🆕 智能设置合并距离
    merge_gap = min(50, WINDOW_SIZE // 20)  # 小窗口用小合并距离
    debug_log(f"  - Merge gap: {merge_gap} bp (auto-adjusted)", "INFO")
    
    calls_df = call_candidate_ncrnas(
        chrom=CHROM, pos1=pos1, scores_smoothed=scores_smoothed,
        min_len=MIN_LEN, top_quantile=TOP_QUANTILE, filter_periodicity=True,
        merge_gap=merge_gap,  # 🆕 传入合并参数
        annotator=annotator
    )
    
    if calls_df.empty:
        print("⚠️  No candidates found")
        print(f"   💡 Diagnostic suggestions:")
        print(f"      1. Check score distribution (see quantile table above)")
        print(f"      2. Try lower quantile: TOP_QUANTILE = 0.80 or 0.85")
        print(f"      3. Try shorter min length: MIN_LEN = {max(20, WINDOW_SIZE//20)}")
        print(f"      4. Try larger merge gap: merge_gap = {merge_gap*2}")
        print(f"      5. Or use larger window: 10000-50000 bp\n")
    else:
        print(f"✅ Found {len(calls_df)} candidate regions\n")
        for idx, row in calls_df.iterrows():
            print(f"   Region {idx+1}: chr{row['chrom']}:{row['start']}-{row['end']} "
                  f"({row['length']}bp, score={row['score_mean']:.4f})")
            
            # 🆕 显示 GENCODE 注释
            if 'has_gene_overlap' in row:
                if row['has_gene_overlap']:
                    print(f"      ⚠️  Overlaps with {row['num_overlapping_genes']} known genes")
                if row['has_exon_overlap']:
                    print(f"      ⚠️  Contains {row['exon_coverage_bp']}bp of exons (likely coding)")
                if not row['has_gene_overlap']:
                    print(f"      ✨ Novel intergenic region!")
        print()
    
    return calls_df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 可视化模块（保持原有逻辑）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def save_embedding_heatmap(embedding_df):
    """保存嵌入热图"""
    plt.figure(figsize=(10, 6))
    sns.heatmap(
        embedding_df.T, center=0, vmin=-3, vmax=3, cmap="coolwarm",
        square=False, xticklabels=100, yticklabels=100
    )
    plt.title("GPN-MSA Embedding Heatmap (768D)", fontweight='bold')
    plt.xlabel("Genomic Position")
    plt.ylabel("Embedding Dimension")
    
    output = RESULTS_DIR / "embedding_heatmap.png"
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"💾 Heatmap saved: {output}")


def save_umap_plot(umap_df):
    """保存 UMAP 可视化"""
    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(
        umap_df["UMAP1"], umap_df["UMAP2"],
        c=umap_df["Position"], cmap="viridis", s=15, alpha=0.8
    )
    plt.colorbar(scatter, label="Genomic Position")
    plt.title(f"UMAP Projection (chr{CHROM}:{START_POS}-{END_POS})", fontweight='bold')
    plt.xlabel("UMAP1")
    plt.ylabel("UMAP2")
    plt.grid(alpha=0.3)
    
    output = RESULTS_DIR / "embedding_umap.png"
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"💾 UMAP saved: {output}")


def create_comprehensive_visualization(pos1, scores, scores_smoothed, calls_df):
    """生成综合分析报告（6 子图）"""
    print_section("Generate comprehensive visualization", char="─")
    
    fig = plt.figure(figsize=(18, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)
    fig.suptitle('GPN-MSA ncRNA Analysis Report', fontsize=18, fontweight='bold', y=0.98)
    
    # [A] 嵌入热图
    ax_heat = fig.add_subplot(gs[0, :2])
    if (img_path := RESULTS_DIR / "embedding_heatmap.png").exists():
        ax_heat.imshow(Image.open(img_path))
        ax_heat.axis('off')
        ax_heat.set_title('(A) GPN-MSA Embedding Heatmap (768D)', fontweight='bold')
    
    # [B] UMAP 投影
    ax_umap = fig.add_subplot(gs[0, 2])
    if (img_path := RESULTS_DIR / "embedding_umap.png").exists():
        ax_umap.imshow(Image.open(img_path))
        ax_umap.axis('off')
        ax_umap.set_title('(B) UMAP Projection\n(768D -> 2D)', fontweight='bold')
    
    # [C] 原始保守性得分
    ax_raw = fig.add_subplot(gs[1, :2])
    ax_raw.plot(pos1, scores, color='#2E86AB', alpha=0.6, linewidth=1.2, label='Raw Scores')
    mean_score = np.nanmean(scores)
    ax_raw.axhline(mean_score, color='red', linestyle='--', linewidth=1.5, alpha=0.7,
                   label=f"Mean = {mean_score:.3f}")
    ax_raw.fill_between(pos1, scores, alpha=0.2, color='#2E86AB')
    ax_raw.set_ylabel('Log P(true base)', fontweight='bold')
    ax_raw.set_title('(C) Raw MLM Conservation Scores', fontweight='bold')
    ax_raw.legend(loc='lower right', fontsize=9)
    ax_raw.grid(True, alpha=0.3, linestyle='--')
    
    valid_cnt = np.isfinite(scores).sum()
    ax_raw.text(0.02, 0.97, 
               f'Valid: {valid_cnt}/{len(scores)}\nMean: {mean_score:.4f}\nStd: {np.nanstd(scores):.4f}',
               transform=ax_raw.transAxes, fontsize=9, va='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # [D] 得分分布箱线图
    ax_box = fig.add_subplot(gs[1, 2])
    valid_raw = scores[np.isfinite(scores)]
    valid_smooth = scores_smoothed[np.isfinite(scores_smoothed)]
    bp = ax_box.boxplot([valid_raw, valid_smooth], tick_labels=['Raw', 'Smoothed'],
                        patch_artist=True, widths=0.6)
    for patch, color in zip(bp['boxes'], ['lightblue', 'lightcoral']):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax_box.set_ylabel('Score Value', fontweight='bold')
    ax_box.set_title('(D) Score Distribution', fontweight='bold')
    ax_box.grid(True, alpha=0.3, axis='y', linestyle='--')
    
    # [E] 平滑得分 + 候选区域
    ax_smooth = fig.add_subplot(gs[2, :2])
    ax_smooth.plot(pos1, scores_smoothed, color='#A23B72', linewidth=2, 
                   label='Smoothed Scores', zorder=2)
    ax_smooth.fill_between(pos1, scores_smoothed, alpha=0.3, color='#A23B72', zorder=1)
    
    # 显示阈值线
    valid_smooth = scores_smoothed[np.isfinite(scores_smoothed)]
    if len(valid_smooth) > 0:
        threshold = np.quantile(valid_smooth, TOP_QUANTILE)
        ax_smooth.axhline(threshold, color='orange', linestyle=':', linewidth=2, 
                         label=f'Threshold ({TOP_QUANTILE*100:.1f}%)', zorder=3)
    
    if not calls_df.empty:
        for idx, row in calls_df.iterrows():
            ax_smooth.axvspan(row['start'], row['end'], color='#F18F01', alpha=0.4, zorder=0,
                            label='Candidate ncRNA' if idx == 0 else '')
            mid = (row['start'] + row['end']) / 2
            
            # 🆕 显示 GENCODE 注释状态
            annotation = f"R{idx+1}\n{row['length']}bp\n{row['score_mean']:.3f}"
            if 'has_gene_overlap' in row:
                if row['has_gene_overlap']:
                    annotation += "\n⚠️Gene"
                else:
                    annotation += "\n✨Novel"
            
            ax_smooth.annotate(
                annotation,
                xy=(mid, row['score_mean']), xytext=(mid, ax_smooth.get_ylim()[1]*0.85),
                fontsize=8, ha='center',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5)
            )
    else:
        ax_smooth.text(0.5, 0.5, 
                      f'No candidate found\n'
                      f'Window: {WINDOW_SIZE}bp, min_len={MIN_LEN}bp, quantile={TOP_QUANTILE}\n'
                      f'Try: larger window or lower threshold',
                      transform=ax_smooth.transAxes, fontsize=10, ha='center', va='center',
                      bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
    
    ax_smooth.set_xlabel(f'Genomic Position (chr{CHROM})', fontweight='bold')
    ax_smooth.set_ylabel('Smoothed Score', fontweight='bold')
    ax_smooth.set_title('(E) Candidate ncRNA Regions (Smoothed + Thresholded)', fontweight='bold')
    ax_smooth.legend(loc='upper right', fontsize=9)
    ax_smooth.grid(True, alpha=0.3, linestyle='--')
    
    # [F] 统计摘要
    ax_stats = fig.add_subplot(gs[2, 2])
    ax_stats.axis('off')
    
    valid_smooth = scores_smoothed[np.isfinite(scores_smoothed)]
    stats_text = [
        "=== ANALYSIS SUMMARY ===\n",
        f"Region: chr{CHROM}:{START_POS}-{END_POS}",
        f"Window: {WINDOW_SIZE} bp",
        f"Valid sites: {np.isfinite(scores).sum()}\n",
        "Score Statistics:",
        f"  Mean: {np.nanmean(valid_smooth):.4f}",
        f"  Median: {np.nanmedian(valid_smooth):.4f}",
        f"  Range: [{np.nanmin(valid_smooth):.3f}, {np.nanmax(valid_smooth):.3f}]\n",
        "Search Parameters:",
        f"  min_len: {MIN_LEN} bp",
        f"  quantile: {TOP_QUANTILE}",
        f"  smooth_window: {SMOOTH_WINDOW} bp\n",
        "Candidate Regions:",
    ]
    
    if calls_df.empty:
        stats_text.extend([
            "  Count: 0",
            "\n⚠️ No candidates found!",
            "  Suggestions:",
            f"  - Use quantile: 0.80-0.85",
            f"  - Use min_len: {max(20, WINDOW_SIZE//20)}",
            "  - Or window: 10k-50k bp"
        ])
    else:
        stats_text.extend([
            f"  Count: {len(calls_df)}",
            f"  Total: {calls_df['length'].sum()} bp",
            f"  Avg: {calls_df['length'].mean():.0f} bp",
            f"  Max score: {calls_df['score_mean'].max():.4f}"
        ])
        
        # 🆕 GENCODE 统计
        if 'has_gene_overlap' in calls_df.columns:
            novel_count = (~calls_df['has_gene_overlap']).sum()
            stats_text.extend([
                f"\nGENCODE Annotation:",
                f"  Novel regions: {novel_count}",
                f"  Gene overlaps: {calls_df['has_gene_overlap'].sum()}",
                f"  Exon overlaps: {calls_df['has_exon_overlap'].sum()}"
            ])
    
    ax_stats.text(0.1, 0.95, '\n'.join(stats_text), transform=ax_stats.transAxes,
                 fontsize=9, va='top', family='monospace',
                 bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    ax_stats.set_title('(F) Summary Statistics', fontsize=12, fontweight='bold')
    
    output = RESULTS_DIR / "ncrna_comprehensive_analysis.png"
    plt.savefig(output, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"💾 Comprehensive plot saved: {output}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 结果保存
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def save_results(pos1, scores, scores_smoothed, calls_df):
    """保存分析结果文件"""
    print_section("Save result files", char="─")
    
    prefix = f"ncrna_chr{CHROM}_{START_POS}_{END_POS}"
    
    # BED 格式
    bed_file = RESULTS_DIR / f"{prefix}_candidates.bed"
    if not calls_df.empty:
        bed_cols = ["chrom", "start", "end", "score_mean", "length"]
        calls_df[bed_cols].to_csv(bed_file, sep="\t", header=False, index=False)
    
    # CSV 格式（完整信息）
    csv_file = RESULTS_DIR / f"{prefix}_candidates.csv"
    calls_df.to_csv(csv_file, index=False)
    
    # 保守性轨道文件
    track_file = RESULTS_DIR / f"{prefix}_conservation_track.tsv"
    pd.DataFrame({
        "chrom": CHROM,
        "pos1": pos1,
        "score": scores,
        "score_smoothed": scores_smoothed
    }).to_csv(track_file, sep="\t", index=False)
    
    print(f"✅ BED file: {bed_file}")
    print(f"✅ CSV file: {csv_file}")
    print(f"✅ Track file: {track_file}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主流程
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """主分析流程"""
    print_section("GPN-MSA Genome Analysis Pipeline (Enhanced)", char="═")
    print(f"Target region: chr{CHROM}:{START_POS}-{END_POS} ({WINDOW_SIZE} bp)\n")
    
    # 数据加载
    loader, model, genome_msa, annotator = load_data_and_models()
    
    # MSA 处理
    input_ids, aux_features = extract_and_process_msa(genome_msa)
    
    # 嵌入计算与可视化
    embedding, embedding_df = compute_embeddings(model, input_ids, aux_features)
    umap_df = perform_umap_reduction(embedding)
    save_embedding_heatmap(embedding_df)
    save_umap_plot(umap_df)
    
    # 保守性预测
    pos1, scores, scores_smoothed = predict_conservation_scores(
        loader, input_ids, aux_features
    )
    
    # ncRNA 识别（🆕 传入 annotator）
    calls_df = identify_ncrna_candidates(pos1, scores_smoothed, annotator)
    
    # 综合可视化与结果保存
    create_comprehensive_visualization(pos1, scores, scores_smoothed, calls_df)
    save_results(pos1, scores, scores_smoothed, calls_df)
    
    print_section("🎯 Analysis Complete", char="═")


if __name__ == "__main__":
    main()
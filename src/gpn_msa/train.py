#!/usr/bin/env python3
# train_finetune_static.py
# 静态配置版本：把所有超参写成静态变量（无命令行参数）
# 需要：torch, numpy, pandas, scikit-learn, matplotlib, tqdm

import os
import random
import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    average_precision_score, roc_auc_score, roc_curve,
    precision_recall_curve, confusion_matrix, f1_score
)
from sklearn.model_selection import StratifiedGroupKFold

from src.config import MIDDLE_RESULT_DIR, GTF, FASTA, CHROM, CONFIG, PHASTCONS_FILE, MIDDLE_RESULT_DIR_OUT

# -------- 静态配置区（全部写这里） --------
# 输入 / 输出 路径（请根据你的文件实际位置修改）
# PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METADATA_CSV = f"{MIDDLE_RESULT_DIR}/windows_FineTuningSet2.csv"  # 或者 .tsv/.csv，下面会自动尝试读取
# METADATA_CSV = f"{MIDDLE_RESULT_DIR}/FineTuningSet1.head.bed"
# METADATA_CSV = f"{MIDDLE_RESULT_DIR}/human_gencode_windows.json"  
OUT_DIR = f"{MIDDLE_RESULT_DIR_OUT}/ft_out_static"

# 标签生成方法： 'gmm' 或 'kmeans' 或 'percentile'
LABEL_METHOD = "gmm"
PERCENTILE_THRESHOLD = 90  # 当 LABEL_METHOD == 'percentile' 时使用

# 数据集划分比例（固定 70/15/15）
TRAIN_FRAC = 0.70
VAL_FRAC = 0.15
TEST_FRAC = 0.15
RANDOM_SEED = 42

# 训练超参
BATCH_SIZE = 8
EPOCHS = 8
LR_HEAD = 2e-4            # head 学习率（stage1）
LR_BACKBONE = 2e-5        # backbone 微调学习率（stage2）
BACKBONE_LR_FACTOR = 0.1  # 相对 head lr 的比例（备用）
WEIGHT_DECAY = 1e-5
CLIP_GRAD_NORM = 1.0

# 两阶段训练设置
FREEZE_FIRST = True       # 是否先冻结 backbone
UNFREEZE_EPOCH = 2        # 训练到第几 epoch 后解冻 backbone（从 1 开始计数）

# 资源设置
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NUM_WORKERS = 2

# 其它
CACHE_DIR = f"{MIDDLE_RESULT_DIR}/msa_cache"   # SeqMsasDataset 缓存目录
PLOTS_DIR = os.path.join(OUT_DIR, "plots")
MODEL_PATH = os.path.join(OUT_DIR, "best.pt")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# -------- 导入项目内模块（根据你的 repo 结构调整 import path）--------
# 下面 import 语句假定你的项目路径与之前一致；如路径不同请修改导入
try:
    from data.loader import GenomeLoader
    from src.gpn_msa.backbone import GPNBackbone
    from src.gpn_msa.classifier import GPNClassifier
except Exception as e:
    raise RuntimeError(f"Import project modules failed: {e}")

# -------- 工具函数：把连续 Conservation 变为二分类 --------
def compute_binary_labels(df: pd.DataFrame, method: str = "gmm"):
    """
    输入 dataframe，必须包含一列 'Conservation'（数值）。
    返回：df 带新增列 'label'（0/1），并返回一些信息用于可视化/记录。
    method: 'gmm'|'kmeans'|'percentile'
    """
    if 'mean_phastCons' not in df.columns:
        raise RuntimeError("metadata must contain 'mean_phastCons' column to compute labels")

    vals = df['mean_phastCons'].astype(float).values.reshape(-1, 1)
    info = {}

    if method == "gmm":
        gmm = GaussianMixture(n_components=2, random_state=RANDOM_SEED)
        gmm.fit(vals)
        comp_means = gmm.means_.reshape(-1)
        # 高均值成分视为保守（positive）
        pos_comp = int(np.argmax(comp_means))
        labels = gmm.predict(vals)
        bin_labels = (labels == pos_comp).astype(int)
        info['method'] = 'gmm'
        info['comp_means'] = comp_means.tolist()
        info['pos_comp'] = int(pos_comp)
    elif method == "kmeans":
        k = KMeans(n_clusters=2, random_state=RANDOM_SEED)
        k.fit(vals)
        centers = k.cluster_centers_.reshape(-1)
        pos_comp = int(np.argmax(centers))
        labels = k.predict(vals)
        bin_labels = (labels == pos_comp).astype(int)
        info['method'] = 'kmeans'
        info['centers'] = centers.tolist()
        info['pos_comp'] = int(pos_comp)
    elif method == "percentile":
        thr = np.percentile(vals, PERCENTILE_THRESHOLD)
        bin_labels = (vals.flatten() >= thr).astype(int)
        info['method'] = 'percentile'
        info['threshold'] = float(thr)
    else:
        raise ValueError("Unknown label method")

    df2 = df.copy()
    df2['label'] = bin_labels
    return df2, info

# 可视化 conservation 分布 & 聚类结果
def plot_conservation_and_clusters(df, info, outpath):
    x = df['mean_phastCons'].astype(float).values
    plt.figure(figsize=(6,4))
    plt.hist(x, bins=80, alpha=0.7, label='Conservation', density=True)
    if info.get('method') == 'gmm' and 'comp_means' in info:
        # 在 histogram 上标记两个高斯均值
        for m in info['comp_means']:
            plt.axvline(m, color='C1', linestyle='--', label=f"comp_mean={m:.3f}")
    if info.get('method') == 'kmeans' and 'centers' in info:
        for c in info['centers']:
            plt.axvline(c, color='C2', linestyle='--', label=f"center={c:.3f}")
    if info.get('method') == 'percentile':
        plt.axvline(info['threshold'], color='C3', linestyle='--', label=f"thr={info['threshold']:.3f}")
    plt.legend()
    plt.xlabel("Conservation")
    plt.ylabel("Density")
    plt.title(f"Conservation distribution ({info.get('method')})")
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

# -------- Dataset & collate （复用你提供的实现） --------
class SeqMsasDataset(Dataset):
    def __init__(self, meta_df: pd.DataFrame, genome_loader: GenomeLoader, msa_ds, cache_dir=CACHE_DIR):
        self.df = meta_df.reset_index(drop=True)
        self.loader = genome_loader
        self.msa_ds = msa_ds
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        chrom = str(row.chrom).replace("chr", "")
        s = int(row.start)
        e = int(row.end)
        key = f"{row.id}_{chrom}_{s}_{e}.npz"
        keypath = os.path.join(self.cache_dir, key)
        if os.path.exists(keypath):
            data = np.load(keypath, allow_pickle=False)
            input_ids = torch.from_numpy(data['input_ids']).long()
            aux = torch.from_numpy(data['aux']).float() if 'aux' in data else None
        else:
            msa = self.msa_ds.get_msa(chrom, s, e, strand="+", tokenize=True)
            msa_arr = np.asarray(msa)
            if msa_arr.ndim == 3:
                # 常见：(N_seqs, L, C) -> 取第0条序列，channel0 为 token id
                input_ids_np = msa_arr[0, :, 0].astype(np.int64)        # (L,)
                aux_np = msa_arr[0, :, 1:].astype(np.float32) if msa_arr.shape[2] > 1 else None  # (L, C-1)
            elif msa_arr.ndim == 2:
                # 可能是 (L, C) 形式
                input_ids_np = msa_arr[:, 0].astype(np.int64)          # (L,)
                aux_np = msa_arr[:, 1:].astype(np.float32) if msa_arr.shape[1] > 1 else None   # (L, C-1)
            else:
                # 兜底
                input_ids_np = np.zeros((0,), dtype=np.int64)
                aux_np = None

            input_ids = torch.from_numpy(input_ids_np).long()          # (L,)
            aux = torch.from_numpy(aux_np).float() if aux_np is not None else None  # (L, aux_dim) or None
            # print(input_ids.shape, None if aux is None else aux.shape)
            # if msa_raw is None:
            #     input_ids = torch.zeros((1,1), dtype=torch.long)
            #     aux = None
            # else:
            #     msa_arr = np.asarray(msa_raw)
            #     if msa_arr.ndim == 3:
            #         input_ids_np = msa_arr[:, :, 0].astype(np.int64)[0:1, :]
            #         aux_np = msa_arr[:, :, 1:].astype(np.float32)[0:1, :, :] if msa_arr.shape[2] > 1 else None
            #         input_ids = torch.from_numpy(input_ids_np[0]).long()
            #         aux = torch.from_numpy(aux_np[0]).float() if aux_np is not None else None
            #     elif msa_arr.ndim == 2:
            #         input_ids_np = msa_arr[0:1, :].astype(np.int64)
            #         input_ids = torch.from_numpy(input_ids_np[0]).long()
            #         aux = None
            #     else:
            #         input_ids = torch.zeros((1,), dtype=torch.long)
            #         aux = None
            save_dict = {'input_ids': input_ids.cpu().numpy()}
            if aux is not None:
                save_dict['aux'] = aux.cpu().numpy()
            np.savez_compressed(keypath, **save_dict)
        label = 1.0 if str(row.label).lower() in ("1","true","t","yes") else 0.0
        return input_ids, aux, torch.tensor(label, dtype=torch.float32), row.id

def collate_msa(batch):
    """
    Robust collate: accept per-sample input_ids either (L,) or (1,L) or other shapes,
    and aux either (L,F) or (1,L,F). Normalize to (L,) and (L,F) before padding.
    """
    ids = [b[0] for b in batch]
    auxs = [b[1] for b in batch]
    labels = torch.stack([b[2] for b in batch]).to(DEVICE)

    # ---- normalize ids: ensure each t is 1D (L,) ----
    norm_ids = []
    for t in ids:
        if t is None:
            norm_ids.append(torch.zeros((0,), dtype=torch.long))
            continue
        # if tensor has batch-like first dim 1, squeeze it
        if t.dim() == 2 and t.size(0) == 1:
            t = t.squeeze(0)        # (1,L) -> (L,)
        elif t.dim() > 1:
            t = t.view(-1)          # fallback -> flatten to 1D
        norm_ids.append(t)

    # ---- normalize aux: ensure each a is (L, F) or None ----
    norm_auxs = []
    for a in auxs:
        if a is None:
            norm_auxs.append(None)
            continue
        # if shape (1, L, F) -> squeeze first dim
        if a.dim() == 3 and a.size(0) == 1:
            a = a.squeeze(0)       # (1,L,F) -> (L,F)
        # if shape (L, F) ok; if shape (F, L) try transpose? (not expected)
        norm_auxs.append(a)

    # ---- compute padding sizes ----
    maxL = 0 if len(norm_ids) == 0 else max([t.size(0) for t in norm_ids])
    B = len(norm_ids)
    padded = torch.zeros((B, maxL), dtype=torch.long)
    attn = torch.zeros((B, maxL), dtype=torch.long)

    # aux padding if any non-None
    if any(a is not None for a in norm_auxs):
        first_idx = next(i for i,a in enumerate(norm_auxs) if a is not None)
        F = norm_auxs[first_idx].size(1)
        aux_p = torch.zeros((B, maxL, F), dtype=torch.float32)
    else:
        aux_p = None

    for i, (t, a) in enumerate(zip(norm_ids, norm_auxs)):
        L = t.size(0)
        if L > 0:
            padded[i, :L] = t
            attn[i, :L] = 1
            if aux_p is not None and a is not None:
                # a may be (L,F) or accidentally (F,L) - we assume (L,F)
                aux_p[i, :L, :] = a

    return padded.to(DEVICE), (None if aux_p is None else aux_p.to(DEVICE)), attn.to(DEVICE), labels


# -------- 划分数据集（70/15/15），支持按 group split（防泄露） --------
def split_dataset(df: pd.DataFrame, seed=RANDOM_SEED, max_retry: int = 50, verbose: bool = True):
    """
    拆分 70/15/15：
    - 若存在 parent_id：按组拆分 + 组分层（group-level stratify），避免泄露并尽量保持类比例；
      同时保证 train/val/test 都至少有 1 个正类与 1 个负类（多次重试，不行则最小调组兜底）。
    - 若不存在 parent_id：使用标签分层的常规拆分。
    需要 df['label'] 为 0/1。
    """
    def has_both_classes(d: pd.DataFrame) -> bool:
        if len(d) == 0: 
            return False
        y = d['label'].values
        return (y == 0).any() and (y == 1).any()

    def report_split(tr, va, te):
        if not verbose: 
            return
        def cnt(d):
            y = d['label'].values
            return int((y==1).sum()), int((y==0).sum()), len(d)
        p_tr, n_tr, m_tr = cnt(tr)
        p_va, n_va, m_va = cnt(va)
        p_te, n_te, m_te = cnt(te)
        print(f"[SPLIT] train pos/neg/total = {p_tr}/{n_tr}/{m_tr}")
        print(f"[SPLIT]   val pos/neg/total = {p_va}/{n_va}/{m_va}")
        print(f"[SPLIT]  test pos/neg/total = {p_te}/{n_te}/{m_te}")

    # ------------- 情况一：有 parent_id -> 按组 + 分层 -------------
    if 'parent_id' in df.columns:
        # 组级标签：只要该组内有正样本，就把该组标成 1（更稳，避免小样本 GMM 导致全负）
        g = df.groupby('parent_id')['label'].agg(['sum','count'])
        g['group_label'] = (g['sum'] > 0).astype(int)  # has-positive-as-1 策略
        groups = g.index.to_numpy()
        y_group = g['group_label'].to_numpy()

        # 多次重试直到三份子集都含正负类
        for attempt in range(max_retry):
            rng = seed + attempt
            # 先按组 stratify 切出 train vs remain
            train_groups, remain_groups = train_test_split(
                groups, train_size=TRAIN_FRAC, random_state=rng,
                stratify=y_group
            )
            # remain 再切 val/test，以组级标签作为 stratify
            y_remain = g.loc[remain_groups, 'group_label'].to_numpy()
            val_ratio_in_remain = VAL_FRAC / (VAL_FRAC + TEST_FRAC)
            val_groups, test_groups = train_test_split(
                remain_groups, train_size=val_ratio_in_remain, random_state=rng,
                stratify=y_remain
            )

            train_df = df[df['parent_id'].isin(train_groups)].reset_index(drop=True)
            val_df   = df[df['parent_id'].isin(val_groups)].reset_index(drop=True)
            test_df  = df[df['parent_id'].isin(test_groups)].reset_index(drop=True)

            if has_both_classes(train_df) and has_both_classes(val_df) and has_both_classes(test_df):
                report_split(train_df, val_df, test_df)
                return train_df, val_df, test_df

        # ---- 兜底：最小调组，把缺类的集合里“借”一个有该类的组 ----
        if verbose:
            print("[SPLIT] strict retry exhausted; applying minimal group rebalance...")

        # 先取最后一次切分的结果（用原 seed）
        rng = seed
        train_groups, remain_groups = train_test_split(
            groups, train_size=TRAIN_FRAC, random_state=rng, stratify=y_group
        )
        y_remain = g.loc[remain_groups, 'group_label'].to_numpy()
        val_ratio_in_remain = VAL_FRAC / (VAL_FRAC + TEST_FRAC)
        val_groups, test_groups = train_test_split(
            remain_groups, train_size=val_ratio_in_remain, random_state=rng,
            stratify=y_remain
        )

        def build(tr_g, va_g, te_g):
            tr = df[df['parent_id'].isin(tr_g)].reset_index(drop=True)
            va = df[df['parent_id'].isin(va_g)].reset_index(drop=True)
            te = df[df['parent_id'].isin(te_g)].reset_index(drop=True)
            return tr, va, te

        train_df, val_df, test_df = build(train_groups, val_groups, test_groups)

        # 从某个子集中缺少的类别，去其他子集中“借”一个拥有该类别的 group（优先选择样本数最少的那一个组，动得最小）
        def borrow_group(want_pos: bool, src_groups, dst_groups):
            # 从 src 中挑一个满足 want_pos 的组，且该组样本数最少
            cand = []
            for gid in src_groups:
                lab = int(g.loc[gid, 'group_label'])
                if (want_pos and lab == 1) or ((not want_pos) and lab == 0):
                    cand.append((gid, int(g.loc[gid, 'count'])))
            if not cand:
                return src_groups, dst_groups  # 借不到
            cand.sort(key=lambda x: x[1])  # 按组大小升序
            gid_to_move = cand[0][0]
            src = [x for x in src_groups if x != gid_to_move]
            dst = list(dst_groups) + [gid_to_move]
            return np.array(src), np.array(dst)

        # 依次保证 train/val/test 都有正负类；最多做几次小调整
        for _ in range(10):
            changed = False
            if not has_both_classes(train_df):
                # 如果 train 缺正（或缺负），优先从 val 借，再不行从 test 借
                want_pos = (train_df['label'].sum() == 0)
                val_groups, train_groups = borrow_group(want_pos, val_groups, train_groups)
                test_groups, train_groups = borrow_group(want_pos, test_groups, train_groups)
                train_df, val_df, test_df = build(train_groups, val_groups, test_groups)
                changed = True

            if not has_both_classes(val_df):
                want_pos = (val_df['label'].sum() == 0)
                train_groups, val_groups = borrow_group(want_pos, train_groups, val_groups)
                test_groups,  val_groups = borrow_group(want_pos, test_groups,  val_groups)
                train_df, val_df, test_df = build(train_groups, val_groups, test_groups)
                changed = True

            if not has_both_classes(test_df):
                want_pos = (test_df['label'].sum() == 0)
                train_groups, test_groups = borrow_group(want_pos, train_groups, test_groups)
                val_groups,   test_groups = borrow_group(want_pos, val_groups,   test_groups)
                train_df, val_df, test_df = build(train_groups, val_groups, test_groups)
                changed = True

            if not changed:
                break

        report_split(train_df, val_df, test_df)
        return train_df, val_df, test_df

    # ------------- 情况二：无 parent_id -> 常规分层 -------------
    else:
        tmp_frac = VAL_FRAC + TEST_FRAC
        train_df, tmp_df = train_test_split(df, train_size=TRAIN_FRAC, stratify=df['label'], random_state=seed)
        val_frac_rel = VAL_FRAC / tmp_frac
        val_df, test_df = train_test_split(tmp_df, train_size=val_frac_rel, stratify=tmp_df['label'], random_state=seed)
        train_df = train_df.reset_index(drop=True)
        val_df = val_df.reset_index(drop=True)
        test_df = test_df.reset_index(drop=True)

        # 兜底：如仍有单类，改变随机种子重试几次
        if (not has_both_classes(train_df)) or (not has_both_classes(val_df)) or (not has_both_classes(test_df)):
            for attempt in range(1, max_retry+1):
                rs = seed + attempt
                train_df, tmp_df = train_test_split(df, train_size=TRAIN_FRAC, stratify=df['label'], random_state=rs)
                val_df, test_df = train_test_split(tmp_df, train_size=val_frac_rel, stratify=tmp_df['label'], random_state=rs)
                train_df = train_df.reset_index(drop=True)
                val_df = val_df.reset_index(drop=True)
                test_df = test_df.reset_index(drop=True)
                if has_both_classes(train_df) and has_both_classes(val_df) and has_both_classes(test_df):
                    break

        report_split(train_df, val_df, test_df)
        return train_df, val_df, test_df


def stratified_group_split_via_kfold(df, group_col, label_col,
                                     n_splits=5,  # 折数越大越容易匹配到相近比例
                                     train_ratio=0.7, val_ratio=0.15, test_ratio=0.15,
                                     n_bins=10, random_state=42):
    rng = np.random.RandomState(random_state)

    # 1) 以 parent_id 聚合，得到每个组的正例比例
    g = df.groupby(group_col)[label_col].agg(['sum', 'count']).rename(columns={'sum':'pos','count':'tot'})
    g['pos_ratio'] = g['pos'] / g['tot']
    # 大小也会影响平衡，顺便把组大小也做个桶
    g['size_bin'] = pd.qcut(g['tot'], q=min(5, g['tot'].nunique()), duplicates='drop', labels=False)
    # 用“正例比例桶 + 组大小桶”拼成分层标签
    g['ratio_bin'] = pd.qcut(g['pos_ratio'], q=min(n_bins, g['pos_ratio'].nunique()),
                             duplicates='drop', labels=False)
    g['strata'] = g['ratio_bin'].astype(str) + "_" + g['size_bin'].astype(str)

    groups = g.index.to_numpy()
    y_strata = g['strata'].to_numpy()

    # 2) StratifiedGroupKFold 产生折号
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    fold_ids = {}
    for fold_id, (_, test_g_idx) in enumerate(sgkf.split(X=np.zeros(len(groups)),
                                                         y=y_strata,
                                                         groups=groups)):
        fold_ids.update({groups[i]: fold_id for i in test_g_idx})

    # 3) 按目标比例合并若干折 -> train/val/test
    #    简单贪心：随机打乱折顺序，按比例分配
    fold_order = list(range(n_splits))
    rng.shuffle(fold_order)
    want_train = int(round(train_ratio * n_splits))
    want_val   = int(round(val_ratio   * n_splits))
    # 剩下给 test
    train_folds = set(fold_order[:want_train])
    val_folds   = set(fold_order[want_train:want_train+want_val])
    test_folds  = set(fold_order[want_train+want_val:])

    df = df.copy()
    df['_fold'] = df[group_col].map(fold_ids)
    train_df = df[df['_fold'].isin(train_folds)].drop(columns=['_fold'])
    val_df   = df[df['_fold'].isin(val_folds)].drop(columns=['_fold'])
    test_df  = df[df['_fold'].isin(test_folds)].drop(columns=['_fold'])

    def stats(name, part):
        pos = int(part[label_col].sum()); neg = len(part)-pos
        print(f"[{name}] pos/neg/total = {pos}/{neg}/{len(part)}  "
              f"pos_ratio={pos/len(part):.3f}")

    stats("ALL ", df)
    stats("TRAIN", train_df)
    stats("VAL  ", val_df)
    stats("TEST ", test_df)
    return train_df, val_df, test_df

# -------- 找到在 val 上最佳阈值（最大 F1） --------
def find_best_threshold(y_true, probs):
    best_thr = 0.5
    best_f1 = -1.0
    for thr in np.linspace(0.01, 0.99, 99):
        preds = (probs >= thr).astype(int)
        f1 = f1_score(y_true, preds)
        if f1 > best_f1:
            best_f1 = f1
            best_thr = thr
    return best_thr, best_f1

# -------- 绘图：训练曲线、ROC、PR、混淆矩阵 --------
def plot_training_curves(history, outdir):
    epochs = np.arange(1, len(history['train_loss'])+1)
    plt.figure(figsize=(8,4))
    plt.subplot(1,2,1)
    plt.plot(epochs, history['train_loss'], label='train_loss')
    plt.plot(epochs, history['val_loss'], label='val_loss')
    plt.xlabel("Epoch"); plt.ylabel("Loss"); plt.legend()
    plt.subplot(1,2,2)
    plt.plot(epochs, history['train_ap'], label='train_ap')
    plt.plot(epochs, history['val_ap'], label='val_ap')
    plt.xlabel("Epoch"); plt.ylabel("AP"); plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "training_curves.png"), dpi=150)
    plt.close()

def plot_roc_pr(y_true, probs, outdir, tag="test"):
    fpr, tpr, _ = roc_curve(y_true, probs)
    roc_auc = roc_auc_score(y_true, probs)
    precision, recall, _ = precision_recall_curve(y_true, probs)
    ap = average_precision_score(y_true, probs)

    plt.figure(figsize=(10,4))
    plt.subplot(1,2,1)
    plt.plot(fpr, tpr, label=f"AUC={roc_auc:.4f}")
    plt.plot([0,1],[0,1],'k--',alpha=0.5)
    plt.xlabel("FPR"); plt.ylabel("TPR"); plt.title(f"ROC ({tag})"); plt.legend()
    plt.subplot(1,2,2)
    plt.plot(recall, precision, label=f"AP={ap:.4f}")
    plt.xlabel("Recall"); plt.ylabel("Precision"); plt.title(f"PR ({tag})"); plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, f"{tag}_roc_pr.png"), dpi=150)
    plt.close()
    return roc_auc, ap

def plot_confusion(cm, outpath, classes=('neg','pos')):
    plt.figure(figsize=(4,4))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title("Confusion matrix")
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes)
    plt.yticks(tick_marks, classes)
    thresh = cm.max() / 2.
    for i, j in np.ndindex(cm.shape):
        plt.text(j, i, format(int(cm[i, j]), 'd'),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

# -------- 训练主流程 --------
def train_main():
    # 1) 读取 metadata（兼容 tsv/csv/bed）
    # 假设文件包含 header，且有 columns: chrom,start,end,id,Conservation 或已经有 label
    if METADATA_CSV.endswith(".bed") or METADATA_CSV.endswith(".tsv") or METADATA_CSV.endswith(".txt"):
        # 以 tab 读取
        meta = pd.read_csv(METADATA_CSV, sep='\t', dtype=str)
    elif METADATA_CSV.endswith(".json"):
        meta = pd.read_json(METADATA_CSV)
    else:
        meta = pd.read_csv(METADATA_CSV, dtype=str)
        
    meta = meta[:10000]
    # return
    # 强制列名小写化处理列名相似问题
    cols = {c: c.strip() for c in meta.columns}
    meta.rename(columns=cols, inplace=True)
    # ensure required numeric columns
    if 'start' in meta.columns:
        meta['start'] = meta['start'].astype(int)
    if 'end' in meta.columns:
        meta['end'] = meta['end'].astype(int)
    # 如果已经有 label 列就直接使用；否则尝试用 Conservation 生成 label
    if 'label' not in meta.columns or meta['label'].isnull().all():
        # if 'Conservation' not in meta.columns and 'conservation' in meta.columns:
        #     meta.rename(columns={'conservation': 'Conservation'}, inplace=True)
        # if 'Conservation' not in meta.columns:
        #     raise RuntimeError("metadata must contain 'Conservation' column or 'label' column")
        meta['mean_phastCons'] = meta['mean_phastCons'].astype(float)
        meta2, info = compute_binary_labels(meta, method=LABEL_METHOD)
        meta = meta2
        # plot distribution
        plot_conservation_and_clusters(meta, info, os.path.join(PLOTS_DIR, "conservation_dist.png"))
        # 保存 info
        with open(os.path.join(OUT_DIR, "label_info.txt"), "w") as f:
            f.write(str(info))
    else:
        # ensure binary 0/1 numeric
        meta['label'] = meta['label'].apply(lambda x: 1 if str(x).lower() in ("1","true","t","yes") else 0)
    # ensure id column exists
    if 'id' not in meta.columns:
        # try to build id from chrom:start-end
        meta['id'] = meta.apply(lambda r: f"{r['chrom']}:{r['start']}-{r['end']}", axis=1)
        
    # 做 70/15/15 划分
    # train_df, val_df, test_df = split_dataset(meta, seed=RANDOM_SEED)
    # # 保存划分表
    # train_df.to_csv(os.path.join(OUT_DIR, "train_meta.csv"), index=False)
    # val_df.to_csv(os.path.join(OUT_DIR, "val_meta.csv"), index=False)
    # test_df.to_csv(os.path.join(OUT_DIR, "test_meta.csv"), index=False)
    # print(f"Split sizes train/val/test: {len(train_df)}/{len(val_df)}/{len(test_df)}")
    
    train_df, val_df, test_df = stratified_group_split_via_kfold(
        df=meta,
        group_col="gene_id",    # ← 用于按组不打散
        label_col="label",        # ← 用于计算正负比例
        n_splits=8,               # 可调，更多折=分布更平衡
        train_ratio=0.7,          # 训练集比例
        val_ratio=0.15,           # 验证集比例
        test_ratio=0.15,          # 测试集比例
        n_bins=10,                # 分层精度
        random_state=RANDOM_SEED
    )

    # 保存结果
    train_df.to_csv(os.path.join(OUT_DIR, "train_meta.csv"), index=False)
    val_df.to_csv(os.path.join(OUT_DIR, "val_meta.csv"), index=False)
    test_df.to_csv(os.path.join(OUT_DIR, "test_meta.csv"), index=False)

    print(f"✅ Split sizes train/val/test: {len(train_df)}/{len(val_df)}/{len(test_df)}")

    # 2) dataset / dataloader
    loader = GenomeLoader()
    msa_ds = loader.load_multiz100way_dataset(streaming=True)
    train_ds = SeqMsasDataset(train_df, loader, msa_ds, cache_dir=CACHE_DIR)
    val_ds = SeqMsasDataset(val_df, loader, msa_ds, cache_dir=CACHE_DIR)
    test_ds = SeqMsasDataset(test_df, loader, msa_ds, cache_dir=CACHE_DIR)


    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, collate_fn=collate_msa)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0, collate_fn=collate_msa)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0, collate_fn=collate_msa)
    
    # import time
    
    # # ---------- 1️⃣ 预取一批，验证 DataLoader ----------
    # print("\n[CHECK 1] Prefetch one batch from train_loader ...")
    # t0 = time.time()
    # x_ids, x_aux, attn, y = next(iter(train_loader))
    # dt = time.time() - t0
    # print(f"Batch fetched in {dt:.2f}s")
    # print(f"  input_ids shape: {tuple(x_ids.shape)}")
    # print(f"  aux shape      : {None if x_aux is None else tuple(x_aux.shape)}")
    # print(f"  attention_mask : {tuple(attn.shape)}")
    # print(f"  labels mean    : {float(y.mean()):.4f}")

    # # ---------- 2️⃣ 模型前向传播 ----------
    # print("\n[CHECK 2] Forward pass test ...")
    # backbone = GPNBackbone()
    # model = GPNClassifier(backbone=backbone).to(DEVICE)

    # with torch.no_grad():
    #     logits = model(input_ids=x_ids, aux_features=x_aux, attention_mask=attn)
    # print("Forward OK ✅")
    # print(f"  logits shape: {tuple(logits.shape)}  mean={float(logits.mean()):.4f}")

    # # ---------- 3️⃣ 单步反向传播 ----------
    # print("\n[CHECK 3] Backward (one step) ...")
    # loss_fn = nn.BCEWithLogitsLoss()
    # optim = torch.optim.AdamW(model.parameters(), lr=1e-4)

    # optim.zero_grad()
    # logits = model(input_ids=x_ids, aux_features=x_aux, attention_mask=attn)
    # loss = loss_fn(logits, y.to(DEVICE))
    # loss.backward()
    # optim.step()
    # print(f"Backward OK ✅ | loss = {float(loss.item()):.4f}")

    # print("\n✅ All pipeline checks passed — DataLoader + Model + GPU ready to train!\n")

    # 3) model 构造
    backbone = GPNBackbone()   # 会尝试加载 HF，否则回退 dummy
    model = GPNClassifier(backbone=backbone).to(DEVICE)

    # 4) 损失与优化器（初始：如果冻结 backbone, 只训练 head）
    pos_weight = max(1.0, (len(train_df) - int((train_df.label==1).sum())) / max(1, int((train_df.label==1).sum())))
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight], device=DEVICE))
    if FREEZE_FIRST:
        model.freeze_backbone()
    # optim = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=LR_HEAD, weight_decay=WEIGHT_DECAY)
    non_backbone_params = [p for n, p in model.named_parameters() if not n.startswith('backbone.')]
    optim = torch.optim.AdamW(non_backbone_params, lr=LR_HEAD, weight_decay=WEIGHT_DECAY)

    # 5) training loop（记录 history）
    history = {'train_loss':[], 'val_loss':[], 'train_ap':[], 'val_ap':[], 'val_auc':[]}
    best_val_ap = -1.0
    for epoch in range(1, EPOCHS+1):
        model.train()
        train_losses = []
        train_trues = []; train_preds = []
        for x_ids, x_aux, attn, y in tqdm(train_loader, desc=f"Train E{epoch}"):
            optim.zero_grad()
            logits = model(input_ids=x_ids, aux_features=x_aux, attention_mask=attn)
            loss = loss_fn(logits, y.to(DEVICE))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP_GRAD_NORM)
            optim.step()
            train_losses.append(loss.item())
            probs = torch.sigmoid(logits).detach().cpu().numpy()
            train_preds.extend(probs.tolist()); train_trues.extend(y.cpu().numpy().tolist())
        train_loss = float(np.mean(train_losses)) if len(train_losses)>0 else float('nan')
        train_ap = float(average_precision_score(train_trues, train_preds)) if len(train_trues)>0 else float('nan')
        history['train_loss'].append(train_loss); history['train_ap'].append(train_ap)

        # validation
        model.eval()
        val_losses = []; val_trues = []; val_preds = []
        with torch.no_grad():
            for x_ids, x_aux, attn, y in tqdm(val_loader, desc="Val"):
                logits = model(input_ids=x_ids, aux_features=x_aux, attention_mask=attn)
                loss = loss_fn(logits, y.to(DEVICE))
                val_losses.append(loss.item())
                probs = torch.sigmoid(logits).cpu().numpy()
                val_preds.extend(probs.tolist()); val_trues.extend(y.cpu().numpy().tolist())
        val_loss = float(np.mean(val_losses)) if len(val_losses)>0 else float('nan')
        val_ap = float(average_precision_score(val_trues, val_preds)) if len(val_trues)>0 else float('nan')
        try:
            val_auc = float(roc_auc_score(val_trues, val_preds))
        except Exception:
            val_auc = float('nan')
        history['val_loss'].append(val_loss); history['val_ap'].append(val_ap); history['val_auc'].append(val_auc)

        print(f"Epoch {epoch}: train_loss={train_loss:.4f} train_ap={train_ap:.4f} val_loss={val_loss:.4f} val_ap={val_ap:.4f} val_auc={val_auc:.4f}")

        # save best
        if val_ap > best_val_ap:
            best_val_ap = val_ap
            torch.save(model.state_dict(), MODEL_PATH)
            print("Saved best model.")

        # 解冻策略
        if FREEZE_FIRST and epoch >= UNFREEZE_EPOCH:
            if hasattr(model, 'unfreeze_backbone'):
                print(f"Epoch {epoch}: unfreezing backbone and reinit optimizer with smaller backbone lr.")
                model.unfreeze_backbone()
                # 重新分组：backbone 用小 lr，其余（分类层等）用大 lr
                backbone_params     = [p for n, p in model.named_parameters() if n.startswith('backbone.')]
                non_backbone_params = [p for n, p in model.named_parameters() if not n.startswith('backbone.')]
                
                # 打印一下参数分组规模，确保没分错
                nb = sum(p.numel() for p in backbone_params)
                nh = sum(p.numel() for p in non_backbone_params)
                print(f"[DEBUG] param split -> backbone: {nb:,} | non-backbone: {nh:,}")

                optim = torch.optim.AdamW([
                    {'params': backbone_params,     'lr': LR_BACKBONE},
                    {'params': non_backbone_params, 'lr': LR_HEAD},
                ], weight_decay=WEIGHT_DECAY)

    # 保存训练曲线
    plot_training_curves(history, PLOTS_DIR)

    # 6) 测试：用 best model，在 val 集上找最佳阈值，再在 test 上评估并绘图
    best_state = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(best_state)
    model.eval()

    # 在 val 上找到最佳阈值（F1）
    val_probs = []; val_trues = []
    with torch.no_grad():
        for x_ids, x_aux, attn, y in tqdm(val_loader, desc="Val predict"):
            logits = model(input_ids=x_ids, aux_features=x_aux, attention_mask=attn)
            val_probs.extend(torch.sigmoid(logits).cpu().numpy().tolist()); val_trues.extend(y.cpu().numpy().tolist())
    best_thr, best_f1 = find_best_threshold(np.array(val_trues), np.array(val_probs))
    print(f"Best threshold on val (max F1): {best_thr:.3f}, F1={best_f1:.4f}")

    # test evaluation
    test_probs = []; test_trues = []
    with torch.no_grad():
        for x_ids, x_aux, attn, y in tqdm(test_loader, desc="Test predict"):
            logits = model(input_ids=x_ids, aux_features=x_aux, attention_mask=attn)
            test_probs.extend(torch.sigmoid(logits).cpu().numpy().tolist()); test_trues.extend(y.cpu().numpy().tolist())
    test_probs = np.array(test_probs); test_trues = np.array(test_trues)
    # ROC/PR
    roc_auc, ap = plot_roc_pr(test_trues, test_probs, PLOTS_DIR, tag="test")
    # threshold -> confusion
    test_preds = (test_probs >= best_thr).astype(int)
    cm = confusion_matrix(test_trues.astype(int), test_preds)
    plot_confusion(cm, os.path.join(PLOTS_DIR, "test_confusion.png"))
    # 保存 final metrics
    metrics = {
        "best_val_ap": float(best_val_ap),
        "val_best_thr": float(best_thr),
        "val_best_f1": float(best_f1),
        "test_ap": float(ap),
        "test_auc": float(roc_auc),
        "test_counts": {"n_test": int(len(test_trues)), "pos": int(test_trues.sum()), "neg": int(len(test_trues)-test_trues.sum())}
    }
    with open(os.path.join(OUT_DIR, "final_metrics.txt"), "w") as f:
        f.write(str(metrics))
    print("Final metrics:", metrics)
    print("Plots saved to:", PLOTS_DIR)
    print("Model saved to:", MODEL_PATH)

if __name__ == "__main__":
    train_main()

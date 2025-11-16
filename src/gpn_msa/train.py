#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_finetune_static.py
---------------------------------
使用 GPN-MSA Backbone + GPNClassifier 进行二分类微调。
本版本不使用 CombinedClassifier，只使用 embedding → mean pooling → MLP。
包含以下增强功能：
  ✓ AMP 自动混合精度
  ✓ Early Stopping
  ✓ Cosine Warmup Learning Rate Scheduler
  ✓ Logits Histogram（监控 collapse）
  ✓ HDF5 MSA 缓存
  ✓ ROC/PR 曲线、混淆矩阵
"""

import os
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

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    average_precision_score, roc_auc_score,
    roc_curve, precision_recall_curve,
    confusion_matrix, f1_score
)

from torch.cuda.amp import autocast, GradScaler
import h5py

# ------------------------------------------------------
# 项目路径
# ------------------------------------------------------
from src.config import MIDDLE_RESULT_DIR, MIDDLE_RESULT_DIR_OUT
from data.loader import GenomeLoader
from src.gpn_msa.backbone import GPNBackbone
from src.gpn_msa.classifier import GPNClassifier  # 直接使用该分类器

# ------------------------------------------------------
# 静态配置
# ------------------------------------------------------
SET_NAME = "set2"
METADATA_CSV = f"{MIDDLE_RESULT_DIR}/fine_tune_windows_with_seq_{SET_NAME}.csv"
OUT_DIR = f"{MIDDLE_RESULT_DIR_OUT}/ft_out_static"
CACHE_DIR = f"{MIDDLE_RESULT_DIR}/{SET_NAME}/msa_cache"
EPOCH_LOG_DIR = f"{OUT_DIR}/epoch_logs"

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
PLOTS_DIR = f"{OUT_DIR}/plots"
Path(PLOTS_DIR).mkdir(parents=True, exist_ok=True)
Path(EPOCH_LOG_DIR).mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TRAIN_FRAC = 0.7
VAL_FRAC = 0.15
TEST_FRAC = 0.15
RANDOM_SEED = 42

# 训练参数
BATCH_SIZE = 16
EPOCHS = 8
LR_HEAD = 5e-5              # 从 2e-4 → 5e-5，绝对稳
LR_BACKBONE = 1e-5          # backbone 更小更稳
WEIGHT_DECAY = 1e-2         # 稍微大一点更防止过拟合
CLIP_GRAD = 1.0             # OK，不动

FREEZE_FIRST = False
UNFREEZE_EPOCH = 10   # 不解冻，让你单测分类头效果

MAX_WINDOWS_PER_PARENT = 5
WINDOW = 512

# ------------------------------------------------------
# Dataset
# ------------------------------------------------------
class SeqMsasDataset(Dataset):
    def __init__(self, df, genome_loader, msa_ds, cache_dir=CACHE_DIR):
        self.df = df.reset_index(drop=True)
        self.msa_ds = msa_ds
        self.cache_dir = cache_dir
        self._h5 = {}

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        chrom = row.chrom.replace("chr", "")
        s, e, strand = int(row.start), int(row.end), row.strand
        sample_id = f"{chrom}:{s}-{e}"
        key = f"{sample_id}".replace("/", "_")
        h5_path = f"{self.cache_dir}/{chrom}.h5"

        # load h5 bucket
        if chrom not in self._h5:
            self._h5[chrom] = h5py.File(h5_path, "a")
        h5f = self._h5[chrom]

        def recompute():
            try:
                # ======== 获得 MSA ========
                msa = self.msa_ds.get_msa(chrom, s, e+1, strand=strand, tokenize=True)
                # msa = self.msa_ds.get_msa("6", 31575665, 31575793, strand="+", tokenize=True)
                msa = torch.tensor(np.expand_dims(msa, 0).astype(np.int64))
                
                # ids, aux = msa[:, :, 0], msa[:, :, 1:]
                
                ids = msa[0, :, 0]          # (L,)
                aux = msa[0, :, 1:].float() # (L, 89)
                # print("msa fix", msa, chrom, s, e+1, strand, ids.shape, aux.shape)

                # ======== 写入 cache ========
                g = h5f.create_group(key)
                g.create_dataset("input_ids", data=ids.numpy())
                if aux is not None:
                    g.create_dataset("aux", data=aux.numpy())
                h5f.flush()

                return ids, aux

            except Exception as err:
                print("recompute_error:", err)
                raise RuntimeError(
                    f"⛔ MSA shape 无效, coords={chrom}:{s}-{e}, strand={strand}, error={err}"
                )
                return ids, aux

        # load / recompute cache
        if key in h5f:
            try:
                ids = h5f[key]["input_ids"][()]
                aux = h5f[key]["aux"][()] if "aux" in h5f[key] else None
            except:
                del h5f[key]
                ids, aux = recompute()
        else:
            ids, aux = recompute()

        label = 1.0 if row.label in (1,"1","true","t","True","yes") else 0.0
        return (
            torch.tensor(ids).long(),         # (L)
            (torch.tensor(aux).float() if aux is not None else None),  # (L,F)
            torch.tensor(label).float(),
        )


# ------------------------------------------------------
# collate_fn
# ------------------------------------------------------
def collate_msa(batch):
    ids, auxs, labels = zip(*batch)
    B = len(ids)
    maxL = max(t.size(0) for t in ids)

    padded_ids = torch.zeros((B,maxL), dtype=torch.long)
    aux_pad = None
    F = next((a.size(1) for a in auxs if a is not None), 0)
    if F > 0:
        aux_pad = torch.zeros((B,maxL,F), dtype=torch.float32)

    for i,(tokens,aux) in enumerate(zip(ids,auxs)):
        L = tokens.size(0)
        padded_ids[i,:L] = tokens
        if aux_pad is not None and aux is not None:
            aux_pad[i,:L] = aux

    return (
        padded_ids.to(DEVICE),                
        (aux_pad.to(DEVICE) if aux_pad is not None else None),
        torch.stack(labels).to(DEVICE)
    )



# ------------------------------------------------------
# split dataset
# ------------------------------------------------------
def split_dataset(df, seed=42):
    group_col = "gene_id" if "gene_id" in df.columns else "id"
    groups = df[group_col].unique()
    gdf = df.groupby(group_col)["label"].agg(["sum","count"])
    gdf["lbl"] = (gdf["sum"]>0).astype(int)

    for attempt in range(50):
        rs = seed + attempt
        tr_g, rest_g = train_test_split(
            groups,
            train_size=TRAIN_FRAC,
            random_state=rs,
            stratify=gdf.loc[groups,"lbl"]
        )
        va_g, te_g = train_test_split(
            rest_g,
            train_size=VAL_FRAC/(VAL_FRAC+TEST_FRAC),
            random_state=rs
        )
        tr=df[df[group_col].isin(tr_g)]
        va=df[df[group_col].isin(va_g)]
        te=df[df[group_col].isin(te_g)]

        if (tr.label.nunique()==2 and va.label.nunique()==2 and te.label.nunique()==2):
            print("[SPLIT] OK")
            return tr,va,te

    raise RuntimeError("Split failed")


# ------------------------------------------------------
# 绘图辅助函数
# ------------------------------------------------------
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


# ------------------------------------------------------
# 主训练流程
# ------------------------------------------------------
def train_main():
    # ----- load metadata -----
    meta = pd.read_csv(METADATA_CSV, dtype=str)
    meta["start"] = meta["start"].astype(int)
    meta["end"] = meta["end"].astype(int)
    meta["label"] = meta["label"].apply(
        lambda x: 1 if str(x).lower() in ("1","true","t","yes") else 0
    ).astype(int)

    if "gene_id" not in meta.columns:
        meta["gene_id"] = meta["chrom"]+":"+meta["start"].astype(str)+"-"+meta["end"].astype(str)

    if MAX_WINDOWS_PER_PARENT:
        before_n = len(meta)
        meta = meta.groupby("gene_id").head(MAX_WINDOWS_PER_PARENT).reset_index(drop=True)
        after_n = len(meta)
        print(f"[INFO] per-group window cap: MAX_WINDOWS_PER_PARENT={MAX_WINDOWS_PER_PARENT}")
        print(f"[INFO] windows before/after capping: {before_n} -> {after_n}")

    train_df,val_df,test_df = split_dataset(meta)
    
    # ----- Print final split summary -----
    def _count(df):
        pos = int((df.label == 1).sum())
        neg = int((df.label == 0).sum())
        return pos, neg, len(df)

    p_tr, n_tr, m_tr = _count(train_df)
    p_va, n_va, m_va = _count(val_df)
    p_te, n_te, m_te = _count(test_df)

    print(f"[SPLIT] train pos/neg/total = {p_tr}/{n_tr}/{m_tr}")
    print(f"[SPLIT]   val pos/neg/total = {p_va}/{n_va}/{m_va}")
    print(f"[SPLIT]  test pos/neg/total = {p_te}/{n_te}/{m_te}")
    print(f"✅ Split sizes train/val/test: {len(train_df)}/{len(val_df)}/{len(test_df)}")

    # 新增：各 split 中正类比例
    train_pos_ratio = p_tr / m_tr if m_tr > 0 else 0.0
    val_pos_ratio   = p_va / m_va if m_va > 0 else 0.0
    test_pos_ratio  = p_te / m_te if m_te > 0 else 0.0

    print(f"[RATIO] train pos_ratio = {train_pos_ratio:.4f} ({train_pos_ratio*100:.2f}%)")
    print(f"[RATIO]   val pos_ratio = {val_pos_ratio:.4f} ({val_pos_ratio*100:.2f}%)")
    print(f"[RATIO]  test pos_ratio = {test_pos_ratio:.4f} ({test_pos_ratio*100:.2f}%)")

    
    train_df.to_csv(f"{OUT_DIR}/train_meta.csv", index=False)
    val_df.to_csv(f"{OUT_DIR}/val_meta.csv", index=False)
    test_df.to_csv(f"{OUT_DIR}/test_meta.csv", index=False)
    print("[INFO] Saved split CSVs to OUT_DIR")

    # ----- dataset -----
    loader = GenomeLoader()
    msa_ds = loader.load_multiz100way_dataset(streaming=True)

    train_ds = SeqMsasDataset(train_df, loader, msa_ds)
    val_ds   = SeqMsasDataset(val_df, loader, msa_ds)
    test_ds  = SeqMsasDataset(test_df, loader, msa_ds)

    train_loader = DataLoader(train_ds,BATCH_SIZE,shuffle=True,collate_fn=collate_msa)
    val_loader   = DataLoader(val_ds,BATCH_SIZE,shuffle=False,collate_fn=collate_msa)
    test_loader  = DataLoader(test_ds,BATCH_SIZE,shuffle=False,collate_fn=collate_msa)

    # ----- model -----
    backbone = GPNBackbone()
    model = GPNClassifier(backbone).to(DEVICE)
    
    # ----- freeze backbone at start -----
    model.freeze_backbone()
    print(f"[INFO] Backbone frozen for first {UNFREEZE_EPOCH-1} epochs.")

    # ----- loss -----
    n_pos = (train_df.label==1).sum()
    n_neg = (train_df.label==0).sum()
    pos_weight = torch.tensor([n_neg/max(1,n_pos)], device=DEVICE)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    # ----- initial optimizer: only classifier head -----
    optim = torch.optim.AdamW(
        model.classifier.parameters(),
        lr=LR_HEAD,
        weight_decay=WEIGHT_DECAY
    )
    print("[INFO] Optimizer initialized: classifier head ONLY.")

    # ----- scheduler -----
    warmup = 2
    total_steps = EPOCHS*len(train_loader)
    def lr_lambda(step):
        if step < warmup: return step/warmup
        progress = (step-warmup)/max(1,total_steps-warmup)
        return 0.5*(1+math.cos(math.pi*progress))
    scheduler = torch.optim.lr_scheduler.LambdaLR(optim, lr_lambda)

    scaler = GradScaler()

    # ----- training loop -----
    history = {"train_loss":[], "val_loss":[], "train_ap":[], "val_ap":[]}
    best_val_ap = -1
    no_improve = 0
    patience = 4
    step_global=0

    for epoch in range(1,EPOCHS+1):
        # ======= 解冻 backbone =======
        if epoch == UNFREEZE_EPOCH:
            print(f"[INFO] Unfreezing backbone at epoch {epoch} ...")
            model.unfreeze_backbone()

            # 新的 optimizer：训练全模型（backbone + head）
            optim = torch.optim.AdamW(
                model.parameters(),
                lr=LR_BACKBONE,       # backbone 用更小 lr
                weight_decay=WEIGHT_DECAY
            )
            print("[INFO] Optimizer switched: backbone + head.")

            # scheduler 也要重置
            scheduler = torch.optim.lr_scheduler.LambdaLR(optim, lr_lambda)
        # ---- Train ----
        model.train()
        tr_loss=[]; tr_y=[]; tr_p=[]
        print_counter = 0
        for x_ids,aux,y in tqdm(train_loader, desc=f"Train E{epoch}"):
            if print_counter < 3:
                print("[train] x_ids:", x_ids.shape)
                if aux is None:
                    print("[train] aux: None")
                else:
                    print("[train] aux:", aux.shape)
                print("[train] labels:", y.shape)
                print_counter += 1
            optim.zero_grad(set_to_none=True)
            with autocast():
                logits = model(input_ids=x_ids, aux_features=aux)
                loss = loss_fn(logits, y)
            scaler.scale(loss).backward()
            scaler.unscale_(optim)
            torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP_GRAD)
            scaler.step(optim); scaler.update()
            scheduler.step()
            step_global+=1

            tr_loss.append(loss.item())
            tr_y.extend(y.cpu().numpy())
            tr_p.extend(torch.sigmoid(logits).detach().cpu().numpy())

        # save logits histogram
        plt.figure()
        plt.hist(tr_p,bins=40); plt.title(f"logits epoch {epoch}")
        plt.savefig(f"{PLOTS_DIR}/epoch{epoch}_logits.png"); plt.close()

        train_loss=np.mean(tr_loss)
        train_ap=average_precision_score(tr_y,tr_p)

        # ---- Validation ----
        model.eval()
        va_loss=[]; va_y=[]; va_p=[]
        with torch.no_grad():
            for x_ids,aux,y in val_loader:
                with autocast():
                    logits = model(input_ids=x_ids, aux_features=aux)
                    loss=loss_fn(logits,y)
                va_loss.append(loss.item())
                va_y.extend(y.cpu().numpy())
                va_p.extend(torch.sigmoid(logits).cpu().numpy())

        val_loss=np.mean(va_loss)
        val_ap=average_precision_score(va_y,va_p)
        val_auc=roc_auc_score(va_y,va_p)

        print(f"[E{epoch}] train_loss={train_loss:.4f} val_loss={val_loss:.4f} | train_ap={train_ap:.4f} val_ap={val_ap:.4f} | AUC={val_auc:.4f}")

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_ap"].append(train_ap)
        history["val_ap"].append(val_ap)

        # early stopping
        if val_ap > best_val_ap:
            best_val_ap = val_ap
            no_improve = 0
            torch.save(model.state_dict(), f"{OUT_DIR}/best.pt")
            print("  -> best model saved.")
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"Early stopping at epoch {epoch}")
                break
            
        # ========== per-epoch logging ==========
        epoch_log_path = f"{EPOCH_LOG_DIR}/epoch_{epoch}.txt"
        with open(epoch_log_path, "w") as f:
            f.write(f"[Epoch {epoch}]\n")
            f.write(f"train_loss={train_loss:.6f}\n")
            f.write(f"val_loss={val_loss:.6f}\n")
            f.write(f"train_ap={train_ap:.6f}\n")
            f.write(f"val_ap={val_ap:.6f}\n")
            f.write(f"val_auc={val_auc:.6f}\n")
            # 当前 lr
            current_lr = optim.param_groups[0]["lr"]
            f.write(f"lr={current_lr:.6e}\n")
            # 是否保存 best
            f.write(f"best_model_saved={'YES' if val_ap > best_val_ap else 'NO'}\n")

        print(f"[Epoch {epoch}] log saved to {epoch_log_path}")

    # ------------------------ 保存训练曲线 ------------------------
    plot_training_curves(history, PLOTS_DIR)

    # ------------------------ 测试评估 ------------------------
    best = torch.load(f"{OUT_DIR}/best.pt", map_location=DEVICE)
    model.load_state_dict(best)
    model.eval()

    # best threshold from val
    val_probs=[]; val_true=[]
    with torch.no_grad():
        for x_ids,aux,y in val_loader:
            p = torch.sigmoid(model(input_ids=x_ids,aux_features=aux)).cpu().numpy()
            val_probs.extend(p); val_true.extend(y.cpu().numpy())
    best_thr,best_f1 = find_best_threshold(np.array(val_true), np.array(val_probs))
    print(f"[VAL] Best threshold={best_thr:.3f} F1={best_f1:.4f}")

    # test
    ts_p=[]; ts_y=[]
    with torch.no_grad():
        for x_ids,aux,y in test_loader:
            p = torch.sigmoid(model(input_ids=x_ids,aux_features=aux)).cpu().numpy()
            ts_p.extend(p); ts_y.extend(y.cpu().numpy())

    ts_p=np.array(ts_p); ts_y=np.array(ts_y)
    auc,ap = plot_roc_pr(ts_y,ts_p,PLOTS_DIR,"test")
    pred=(ts_p>=best_thr).astype(int)
    cm=confusion_matrix(ts_y.astype(int), pred)

    print(f"[TEST] AUC={auc:.4f} AP={ap:.4f}")
    plot_confusion(cm, f"{PLOTS_DIR}/test_confusion.png")


if __name__ == "__main__":
    train_main()

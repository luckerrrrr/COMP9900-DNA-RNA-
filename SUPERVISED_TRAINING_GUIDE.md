# GPN监督训练完整指南
# GPN Supervised Fine-tuning Complete Guide

## ? 概览 | Overview

使用Hugging Face Transformers对GPN模型进行监督学习，预测lncRNA保守性。

- **数据集1 (FineTuningSet1)**: 246个样本，高质量筛选
- **数据集2 (FineTuningSet2)**: 17,945个样本，完整数据集  
- **任务**: 二分类 - 保守(conserved) vs 非保守(non-conserved)
- **方法**: Hugging Face AutoModelForSequenceClassification

---

## ?? 文件结构

```
项目根目录/
├── dataset/finetuning/
│   ├── FineTuningSet1.txt          # 原始数据1 (246 samples)
│   └── FineTuningSet2.txt          # 原始数据2 (17,945 samples)
│
├── data/
│   ├── prepare_finetuning_data.py  # 数据预处理脚本
│   ├── FineTuningSet1_processed.json  # 处理后的数据1
│   └── FineTuningSet2_processed.json  # 处理后的数据2
│
└── src/gpn_train/
    ├── gpn_supervised.py           # ? 核心训练脚本（整合所有代码）
    ├── finetune_set1.pbs           # PBS提交脚本 - Set1
    └── finetune_set2.pbs           # PBS提交脚本 - Set2
```

---

## ? 完整训练流程

### Step 1: 数据预处理

首先需要从基因组坐标提取DNA序列。

#### Set1 预处理（246个样本）

```bash
python3 data/prepare_finetuning_data.py \
    --input dataset/finetuning/FineTuningSet1.txt \
    --fasta dataset/GRCh38_reference_genome/GRCh38.primary.chr*.fa \
    --output data/FineTuningSet1_processed.json \
    --window-size 512
```

#### Set2 预处理（17,945个样本）

```bash
python3 data/prepare_finetuning_data.py \
    --input dataset/finetuning/FineTuningSet2.txt \
    --fasta dataset/GRCh38_reference_genome/GRCh38.primary.chr*.fa \
    --output data/FineTuningSet2_processed.json \
    --window-size 512
```

**预期输出**:
- JSON文件包含: `chrom`, `start`, `end`, `sequence`, `label`, `gene_id`, `strand`
- 标签: `1` = conserved (保守), `0` = non-conserved (非保守)

---

### Step 2: 提交训练任务

数据预处理完成后，提交训练任务到HPC。

#### 训练 Set1

```bash
cd /home/z5618581/capstone-project-25t3-9900-f09c-donut
qsub src/gpn_train/finetune_set1.pbs
```

#### 训练 Set2

```bash
cd /home/z5618581/capstone-project-25t3-9900-f09c-donut
qsub src/gpn_train/finetune_set2.pbs
```

---

### Step 3: 监控训练进度

#### 查看任务状态

```bash
qstat -u $USER
```

#### 查看训练日志

```bash
# Set1日志
tail -f finetune_set1.log

# Set2日志
tail -f finetune_set2.log
```

#### TensorBoard可视化（可选）

```bash
# 在本地或远程查看训练曲线
tensorboard --logdir output/finetuning_set1/logs
tensorboard --logdir output/finetuning_set2/logs
```

---

### Step 4: 查看训练结果

训练完成后，结果保存在输出目录中。

#### Set1 结果

```bash
# 测试集结果
cat output/finetuning_set1/test_results.json

# 详细分类报告
cat output/finetuning_set1/classification_report.txt

# 训练日志
cat output/finetuning_set1/logs/*/events.out.tfevents.*
```

#### Set2 结果

```bash
# 测试集结果
cat output/finetuning_set2/test_results.json

# 详细分类报告
cat output/finetuning_set2/classification_report.txt
```

---

## ? 输出文件说明

训练完成后，每个输出目录包含以下文件：

```
output/finetuning_setX/
├── final_model/              # 最终训练好的模型
│   ├── config.json
│   ├── pytorch_model.bin
│   └── ...
│
├── checkpoint-XXX/           # 训练过程中的checkpoints
│   └── ...
│
├── test_results.json         # 测试集结果
│   {
│     "eval_accuracy": 0.85,
│     "eval_f1": 0.84,
│     "eval_precision": 0.83,
│     "eval_recall": 0.85,
│     "eval_auc": 0.90
│   }
│
├── classification_report.txt # 详细分类报告
│   ? Precision/Recall/F1 per class
│   ? Confusion Matrix
│
└── logs/                     # TensorBoard日志
    └── events.out.tfevents.*
```

---

## ?? 训练参数说明

### `gpn_supervised.py` 主要参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--data` | 必需 | 预处理后的JSON数据文件 |
| `--pretrained-model` | 必需 | GPN预训练模型路径 |
| `--output` | `output/gpn_supervised` | 输出目录 |
| `--num-labels` | 2 | 分类类别数 |
| `--max-length` | 512 | 最大序列长度 |
| `--freeze-backbone` | False | 是否冻结GPN backbone |
| `--epochs` | 20 | 训练轮数 |
| `--batch-size` | 16 | 训练batch size |
| `--lr` | 2e-5 | 学习率 |
| `--fp16` | False | 混合精度训练（提速2x） |
| `--early-stopping-patience` | 3 | Early stopping耐心值 |

### PBS脚本资源配置

- **Set1**: 8小时，1 GPU，32GB RAM
- **Set2**: 12小时，1 GPU，32GB RAM（数据量更大）

---

## ? 模型架构说明

```
DNA序列 (512bp)
    ↓
GPN Encoder (ConvNet)
    ↓
Embeddings (512 × 768)
    ↓
Mean Pooling
    ↓
Pooled Representation (768)
    ↓
Classification Head
    ? Dropout(0.1)
    ? Linear(768 → 384)
    ? ReLU
    ? Dropout(0.1)
    ? Linear(384 → 2)
    ↓
Logits (2) → Softmax → Prediction
```

---

## ? 训练策略

### 1. 冻结 vs 全模型Fine-tuning

**选项A: 冻结backbone（推荐先尝试）**
```bash
--freeze-backbone
```
- 只训练分类头
- 训练更快
- 适合数据量较小的情况（Set1）

**选项B: 全模型fine-tuning**
```bash
# 不加 --freeze-backbone
```
- 训练整个模型
- 效果可能更好
- 需要更多数据和时间（Set2）

### 2. 数据分割

- **训练集**: 70% (Set1) / 70% (Set2)
- **验证集**: 15% (Set1) / 15% (Set2)
- **测试集**: 15% (Set1) / 15% (Set2)

### 3. 评估指标

主要关注：
- **F1 Score**: 平衡精确率和召回率
- **AUC**: 整体分类性能
- **Accuracy**: 总体准确率

---

## ? 性能优化

### 混合精度训练（FP16）

```bash
--fp16
```
- **提速**: 2倍训练速度
- **显存**: 减少50%显存使用
- **精度**: 几乎无损失

### 梯度累积

```bash
--gradient-accumulation-steps 2
```
- 等效于更大的batch size
- 不增加显存使用

---

## ? 常见问题

### Q1: CUDA out of memory

**解决方案**:
```bash
--batch-size 8        # 减小batch size
--fp16                # 启用混合精度
```

### Q2: 训练太慢

**解决方案**:
```bash
--fp16                           # 混合精度
--gradient-accumulation-steps 2  # 梯度累积
--eval-steps 200                 # 减少评估频率
```

### Q3: 过拟合（train loss下降但val loss上升）

**解决方案**:
```bash
--freeze-backbone                # 冻结backbone
--early-stopping-patience 3      # 更严格的early stopping
--weight-decay 0.01              # 增加正则化
```

### Q4: 数据不平衡

如果conserved和non-conserved数量差异很大，可以在代码中添加：
```python
# 在GPNForSequenceClassification的forward中
loss_fct = nn.CrossEntropyLoss(weight=class_weights)
```

---

## ? 结果比较

训练完成后，比较两个数据集的结果：

```bash
# 快速比较
echo "=== Set1 Results ===" && cat output/finetuning_set1/test_results.json
echo ""
echo "=== Set2 Results ===" && cat output/finetuning_set2/test_results.json
```

**预期差异**:
- **Set1** (246样本): 可能过拟合风险，但高质量
- **Set2** (17,945样本): 更好的泛化能力

---

## ? 重新训练或调参

如果需要修改参数重新训练：

1. **修改PBS脚本**中的参数
2. **重新提交**任务
3. 结果会保存到同一目录（覆盖旧结果）

---

## ? 检查清单

训练前确认：
- [ ] 数据预处理完成（JSON文件存在）
- [ ] GPN预训练模型存在 (`output/mouse_gpn_finetuned`)
- [ ] 有可用的GPU资源
- [ ] Container镜像存在 (`/srv/scratch/$USER/images/p3.sif`)

训练后检查：
- [ ] 训练日志无错误
- [ ] `test_results.json` 存在且合理
- [ ] `classification_report.txt` 显示详细指标
- [ ] `final_model/` 目录包含模型文件

---

## ? 联系方式

如有问题，请查看：
- 训练日志: `finetune_setX.log`
- 项目README
- GPN官方文档

---

**Good luck with your training! ?**


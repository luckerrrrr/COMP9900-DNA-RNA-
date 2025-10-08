#!/bin/bash
# ============================================================
# Katana 训练任务启动脚本 | Katana Training Launcher
#
# 功能 / Features:
#   1. 可选指定 Git 分支（不指定则使用本地）  
#      Optional Git branch pull (use local if not specified)
#   2. 可选单一模型或全部模型  
#      Specify a single model or run all models
#   3. 自动生成容器入口配置文件 container_run.txt  
#      Auto-generate container entry config file
#   4. 调用 run.pbs 提交 Katana HPC 任务  
#      Submit PBS job to Katana using run.pbs
# ============================================================

set -euo pipefail

# ---------- 3️⃣ 日志目录 | Log Directory ----------
mkdir -p logs
mkdir -p logs/launcher_logs
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LAUNCH_LOG="logs/launcher_logs/launcher_${TIMESTAMP}.log"
exec > >(tee -a "$LAUNCH_LOG") 2>&1
PBS_SCRIPT="./run.pbs"

# ---------- 参数解析 | Argument Parsing ----------
BRANCH="local"
MODEL="both"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    *)
      echo "❌ Unknown argument: $1"
      echo "Usage: $0 [--branch <branch_name>] [--model <gpn|gpn-msa|both>]"
      exit 1
      ;;
  esac
done

echo "=============================="
echo "[INFO] Katana training launcher started"
echo "[INFO] Git branch : $BRANCH"
echo "[INFO] Model name : $MODEL"
echo "[INFO] Logging to: $LAUNCH_LOG"
echo "=============================="

# ---------- 1️⃣ Git 分支管理 | Git Branch Management ----------
if [[ "$BRANCH" != "local" ]]; then
  echo "[GIT] Pulling branch '$BRANCH' ..."
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
else
  echo "[GIT] Using local code (no pull)"
fi

# ---------- 2️⃣ 模型选择 | Model Selection ----------
AVAILABLE_MODELS=("gpn" "gpn-msa")

case "$MODEL" in
  gpn)
    SELECTED_MODELS=("gpn")
    ;;
  gpn-msa)
    SELECTED_MODELS=("gpn-msa")
    ;;
  both|all)
    SELECTED_MODELS=("${AVAILABLE_MODELS[@]}")
    ;;
  *)
    echo "❌ Invalid model option: $MODEL"
    echo "Please use --model gpn | gpn-msa | both"
    exit 1
    ;;
esac

echo "[INFO] Models to train: ${SELECTED_MODELS[*]}"

# ---------- 清空旧的 configs 目录 | Reset config directory ----------
CONFIG_DIR="configs"
if [[ -d "$CONFIG_DIR" ]]; then
  echo "[CLEANUP] Removing old container_run_*.txt files in $CONFIG_DIR/"
  rm -f "$CONFIG_DIR"/container_run_*.txt
else
  echo "[SETUP] Creating config directory: $CONFIG_DIR/"
  mkdir -p "$CONFIG_DIR"
fi

# ---------- 4️⃣ 循环提交任务 | Submit Jobs for Each Model ----------
for M in "${SELECTED_MODELS[@]}"; do
  JOB_NAME="train-${M}-$(date +%H%M%S)"
  LOG_FILE="logs/training_logs/"
  CONFIG_FILE="configs/container_run_${M}.txt"
  ENTRY_FILE="src/${M}_test.py"

  mkdir -p "$LOG_FILE"
  mkdir -p "$(dirname "$CONFIG_FILE")"

  # ---------- 检查入口文件是否存在 | Check entry file existence ----------
  if [[ ! -f "$ENTRY_FILE" ]]; then
    echo "❌ ERROR: Entry file not found for model '$M'"
    echo "Expected path: $ENTRY_FILE"
    echo "Please create this file before submitting the job."
    exit 1
  fi

    # ---------- 写入模型专属配置文件 ----------
  echo "$ENTRY_FILE" > "$CONFIG_FILE"
  echo "[CONFIG] Generated: $CONFIG_FILE (entry = $ENTRY_FILE)"

  # ---------- 提交 PBS 任务 ----------
  # 提交到 Katana 队列并传入模型名称变量
  # Submit job to Katana PBS queue with model name variable
  echo "[PBS] Submitting job '$JOB_NAME'..."
  echo "$PBS_SCRIPT"
  JOB_LOG=$(qsub -N "$JOB_NAME" \
       -o "$LOG_FILE" \
       -v MODEL_NAME="$M",RUNCONF="$CONFIG_FILE" \
       "$PBS_SCRIPT")
  JOB_ID=${JOB_LOG%%.*}
  echo "[PBS] Submitted job with ID: $JOB_ID"
  echo "Once Completed, See result in file $JOB_LOG"
done

echo "=============================="
echo "[DONE] All jobs submitted successfully!"
echo "=============================="

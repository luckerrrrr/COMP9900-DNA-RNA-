#!/bin/bash
# ============================================================
# Katana Training Launcher
#
# Features:
#   1. Optional Git branch pull (use local if not specified)
#   2. Specify a single model or run all models
#   3. Auto-generate container entry config file
#   4. Submit PBS job to Katana using run.pbs
# ============================================================

set -euo pipefail

# ---------- Log Directory ----------
mkdir -p logs
mkdir -p logs/launcher_logs
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LAUNCH_LOG="logs/launcher_logs/launcher_${TIMESTAMP}.log"
exec > >(tee -a "$LAUNCH_LOG") 2>&1
PBS_SCRIPT="./run.pbs"

# ---------- Default Arguments ----------
BRANCH="local"
declare -a MODELS_TO_RUN=()  # dynamic list of models
INCLUDE_DATA_LOADER=false
INCLUDE_DATA_PREPROCESS=false

# ---------- Parse Command-line Arguments ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --model)
      shift
      # collect all following words until next flag (starts with --)
      while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
        MODELS_TO_RUN+=("$1")
        shift
      done

      # 🧩 Handle the case when no model was provided
      if [[ ${#MODELS_TO_RUN[@]} -eq 0 ]]; then
        echo "[WARN] No models specified after --model → defaulting to both (gpn, gpn-msa)"
        MODELS_TO_RUN=("gpn" "gpn-msa")
      fi
      ;;
    --data-loader)
      INCLUDE_DATA_LOADER=true
      shift
      ;;
    --data-preprocess)
      INCLUDE_DATA_PREPROCESS=true
      shift
      ;;
    *)
      echo "❌ Unknown argument: $1"
      echo "Usage: $0 [--branch <branch>] [--model <m1> <m2> ...] [--data-loader] [--data-preprocess]"
      exit 1
      ;;
  esac
done

# ---------- Auto-enable data-loader when no args ----------
if [[ ${#MODELS_TO_RUN[@]} -eq 0 && "$INCLUDE_DATA_LOADER" == false && "$INCLUDE_DATA_PREPROCESS" == false ]]; then
  echo ""
  echo "[INFO] No specific model or flags provided → defaulting to ALL (including data-loader)"
  INCLUDE_DATA_LOADER=true
  # 🧩 Handle the case when no model was provided
  if [[ ${#MODELS_TO_RUN[@]} -eq 0 ]]; then
    echo "[WARN] No models specified after --model → defaulting to both (gpn, gpn-msa)"
    MODELS_TO_RUN=("gpn" "gpn-msa")
  fi
fi


echo ""
echo "=============================="
echo "[INFO] Katana launcher started"
echo "[INFO] Branch : $BRANCH"
echo "[INFO] Models : ${MODELS_TO_RUN[*]:-(all)}"
echo "[INFO] Data-loader : $INCLUDE_DATA_LOADER"
echo "[INFO] Data-preprocess : $INCLUDE_DATA_PREPROCESS"
echo "[INFO] Log    : $LAUNCH_LOG"
echo "=============================="
echo ""

# ---------- Git Branch Management ----------
if [[ "$BRANCH" != "local" ]]; then
  echo "[GIT] Pulling branch '$BRANCH' ..."
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
else
  echo "[GIT] Using local code (no pull)"
  echo ""
fi


# ---------- Config File Discovery ----------
CONFIG_DIR="configs"
mkdir -p "$CONFIG_DIR"
declare -a CONFIG_FILES

# Case 1️⃣: If no models given → run all configs
if [[ ${#MODELS_TO_RUN[@]} -eq 0 && "$INCLUDE_DATA_LOADER" == false && "$INCLUDE_DATA_PREPROCESS" == false ]]; then
  echo "[SCAN] No specific models provided → running all container_run_*.txt"
  mapfile -t CONFIG_FILES < <(find "$CONFIG_DIR" -maxdepth 1 -type f -name "container_run_*.txt" | sort)
else
  echo "[SELECT] Adding specific model configs..."

  # Add each model's config file
  for M in "${MODELS_TO_RUN[@]}"; do
    CONFIG_PATH="$CONFIG_DIR/container_run_${M}.txt"
    if [[ -f "$CONFIG_PATH" ]]; then
      CONFIG_FILES+=("$CONFIG_PATH")
    else
      echo ""
      echo "⚠️  Warning: Config not found for model '$M' ($CONFIG_PATH)"
    fi
  done

  # Include data-loader if requested
  if [[ "$INCLUDE_DATA_LOADER" == true ]]; then
    DL_CONFIG="$CONFIG_DIR/container_run_data-loader.txt"
    if [[ -f "$DL_CONFIG" ]]; then
      CONFIG_FILES+=("$DL_CONFIG")
    else
      echo "⚠️  Warning: Data-loader config not found ($DL_CONFIG)"
    fi
  fi

  if [[ "$INCLUDE_DATA_PREPROCESS" == true ]]; then
    DL_CONFIG="$CONFIG_DIR/container_run_data-preprocess.txt"
    if [[ -f "$DL_CONFIG" ]]; then
      CONFIG_FILES+=("$DL_CONFIG")
    else
      echo "⚠️  Warning: Data-preprocess config not found ($DL_CONFIG)"
    fi
  fi
fi

# ---------- Validate config existence ----------
if [[ ${#CONFIG_FILES[@]} -eq 0 ]]; then
  echo "❌ No configuration files found to run."
  exit 1
fi

echo "[INFO] Found ${#CONFIG_FILES[@]} config(s) to execute:"
printf '  %s\n' "${CONFIG_FILES[@]}"
echo "" 

# ---------- Submit Jobs ----------
for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
  ENTRY_FILE=$(cat "$CONFIG_FILE" | tr -d '\r\n')  # Python entry path
  JOB_BASENAME=$(basename "$CONFIG_FILE" .txt)
  CONFIG_CLEAN_NAME="${JOB_BASENAME#container_}"
  JOB_NAME="${CONFIG_CLEAN_NAME}-$(date +%H%M%S)"

  echo "[INFO] Submitting job: $JOB_NAME"
  echo "  → Config : $CONFIG_FILE"
  echo "  → Entry  : $ENTRY_FILE"
  echo ""

  if [[ ! -f "$ENTRY_FILE" ]]; then
    echo "❌ ERROR: Entry file not found: $ENTRY_FILE"
    continue
  fi

  LOG_DIR="logs/training_logs"
  mkdir -p "$LOG_DIR"

  # Define config name variable
  CONFIG_BASENAME=$(basename "$CONFIG_FILE")

  JOB_LOG=$(qsub -N "$JOB_NAME" \
      -o "$LOG_DIR" \
      -v RUNCONF="$CONFIG_FILE" \
      "$PBS_SCRIPT")

  JOB_ID=${JOB_LOG%%.*}
  echo "[PBS] Submitted job $JOB_NAME (ID: $JOB_ID)"
done

echo ""
echo "=============================="
echo "[DONE] All jobs submitted successfully!"
echo "=============================="
echo ""


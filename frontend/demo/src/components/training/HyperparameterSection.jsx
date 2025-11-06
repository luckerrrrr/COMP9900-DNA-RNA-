import { motion } from "framer-motion";
import HyperparameterCard from "./HyperparameterCard";

const hyperparameters = [
  {
    id: 1,
    category: "Label-related",
    name: "LABEL_MODE / PHAST_THRESH / TOP_QUANTILE",
    why: "Different thresholds/quantiles change sample definition, greatly affecting signal and AP/ROC",
    recommendation:
      "Use TOP_QUANTILE=0.7-0.95, 0.8 is reasonable. Lower quantile = more positives (↑recall, ↓precision); Higher quantile = stricter (↑precision, but too few samples cause training difficulty)",
    suggestion:
      "If doing small grid search: TOP_QUANTILE ∈ {0.7, 0.8, 0.9}. If train set has few lncRNA (<500), consider lowering threshold or augmenting data",
    priority: "Extremely high (confirm label first, then tune other params)",
    color: "#ff6b9d",
    icon: "🏷️",
  },
  {
    id: 2,
    category: "Imbalance Handling",
    name: "pos_weight / WeightedRandomSampler / loss type",
    why: "For imbalanced data (pos vs neg), loss/gradient/output directly affected. Using pos_weight = n_neg / n_pos is standard, but large values make loss unstable",
    recommendation:
      "Calculate pos_weight, but clip to upper limit (e.g., max_pos_weight = 50 or 100) to avoid excessive imbalance. Or use WeightedRandomSampler in DataLoader to resample positives (oversample) for more stable training",
    suggestion:
      "Another option: Focal Loss (gamma=1.5-2) works well for high imbalance. Practice: Use pos_weight (clip ≤50) first. If training still unstable or loss too high, switch to WeightedRandomSampler resampling (preserve true prevalence for evaluation)",
    priority: "High",
    color: "#ffd700",
    icon: "⚖️",
  },
  {
    id: 3,
    category: "Learning Rate",
    name: "LR_HEAD & LR_ENCODER",
    why: "Head (linear layer) and encoder (pre-trained GPN) converge at different speeds. Too large LR causes divergence; too small LR prevents learning new signals",
    recommendation:
      "LR_HEAD (head-only stage): 1e-4 to 1e-3 (reasonable 1e-4 is safe). LR_ENCODER (fine-tune stage): 1e-6 to 5e-5 (commonly 2e-5, 5e-5 if previously 2e-5 is safe)",
    tuningStrategy:
      "1. Use LR_HEAD in head-only for quick validation (grid: [1e-3, 5e-4, 1e-4]). 2. After fixing head, unfreeze encoder and try LR_ENCODER ∈ {1e-5, 2e-5, 5e-5}. Note: If training loss surges during finetune, LR_ENCODER is too large",
    priority: "High",
    color: "#00d4ff",
    icon: "📈",
  },
  {
    id: 4,
    category: "Epochs & Early Stopping",
    name: "NUM_EPOCHS_HEAD, NUM_EPOCHS_FINETUNE",
    why: "Head stage is shorter; finetune needs more epochs. Over-training causes overfitting, especially with few samples",
    recommendation:
      "NUM_EPOCHS_HEAD: 1-5 (observe val_AP growth). NUM_EPOCHS_FINETUNE: 3-20, combined with ReduceLROnPlateau + early stopping (patience 2). Monitor val_AP, val_ROC, precision@k; if multiple epochs show no improvement, early-stop",
    priority: "Medium-High",
    color: "#00ff88",
    icon: "⏱️",
  },
  {
    id: 5,
    category: "Batch Size",
    name: "BATCH_SIZE",
    why: "Affects gradient stability and memory. Too small causes noisy gradients; too large may reduce generalization",
    recommendation:
      "Typical range: 16-64. If dataset is small or imbalanced, use smaller batch (16-32) for more frequent updates. If dataset is large, use 64-128 for stability",
    priority: "Medium",
    color: "#9d7cff",
    icon: "📦",
  },
];

export default function HyperparameterSection() {
  return (
    <div>
      {/* Title */}
      <motion.h3
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          fontSize: "28px",
          color: "#ffd700",
          marginBottom: "40px",
          textAlign: "center",
        }}
      >
        ⚙️ Fine-tuning: Hyperparameter Impact
      </motion.h3>

      {/* Introduction */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          maxWidth: "1000px",
          margin: "0 auto 60px",
          background: "rgba(255, 215, 0, 0.05)",
          borderRadius: "16px",
          padding: "30px",
          border: "1px solid rgba(255, 215, 0, 0.2)",
        }}
      >
        <p
          style={{
            fontSize: "14px",
            color: "rgba(255, 255, 255, 0.8)",
            lineHeight: "1.8",
            textAlign: "center",
            margin: 0,
          }}
        >
          Fine-tuning hyperparameters significantly impact model performance.
          Below are the key parameters ranked by importance, along with their
          effects and tuning strategies based on empirical results.
        </p>
      </motion.div>

      {/* Hyperparameter cards */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "30px",
          maxWidth: "1200px",
          margin: "0 auto",
        }}
      >
        {hyperparameters.map((param, index) => (
          <HyperparameterCard
            key={param.id}
            param={param}
            delay={index * 0.1}
          />
        ))}
      </div>

      {/* Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        style={{
          maxWidth: "1000px",
          margin: "60px auto 0",
          padding: "30px",
          background: "rgba(0, 212, 255, 0.05)",
          border: "1px solid rgba(0, 212, 255, 0.2)",
          borderRadius: "12px",
        }}
      >
        <h3
          style={{
            fontSize: "18px",
            color: "#00d4ff",
            marginBottom: "16px",
          }}
        >
          💡 Tuning Strategy Summary
        </h3>
        <div
          style={{
            fontSize: "14px",
            color: "rgba(255, 255, 255, 0.8)",
            lineHeight: "1.8",
          }}
        >
          <p style={{ marginBottom: "12px" }}>
            <strong>Priority Order:</strong>
          </p>
          <ol
            style={{
              paddingLeft: "24px",
              margin: "0 0 16px 0",
            }}
          >
            <li style={{ marginBottom: "8px" }}>
              <strong style={{ color: "#ff6b9d" }}>Labels</strong> - Confirm
              thresholds/quantiles first
            </li>
            <li style={{ marginBottom: "8px" }}>
              <strong style={{ color: "#ffd700" }}>Imbalance handling</strong> -
              pos_weight or resampling
            </li>
            <li style={{ marginBottom: "8px" }}>
              <strong style={{ color: "#00d4ff" }}>Learning rates</strong> -
              Grid search LR_HEAD and LR_ENCODER
            </li>
            <li style={{ marginBottom: "8px" }}>
              <strong style={{ color: "#00ff88" }}>Epochs</strong> - Use early
              stopping
            </li>
            <li>
              <strong style={{ color: "#9d7cff" }}>Batch size</strong> - Adjust
              based on dataset size
            </li>
          </ol>
          <p style={{ margin: 0 }}>
            Start with conservative values, monitor validation metrics (AP, ROC,
            precision@k), and iterate. Avoid over-tuning on validation set to
            maintain generalization.
          </p>
        </div>
      </motion.div>
    </div>
  );
}

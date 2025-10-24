import { motion } from "framer-motion";
import MetricCard from "./MetricCard";

export default function TrainingDetailSection({ stage }) {
  return (
    <div>
      {/* Title */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          marginBottom: "24px",
        }}
      >
        <div style={{ fontSize: "40px" }}>{stage.icon}</div>
        <div>
          <h3
            style={{
              fontSize: "28px",
              color: "#00d4ff",
              margin: 0,
              marginBottom: "4px",
            }}
          >
            {stage.title}
          </h3>
          <p
            style={{
              fontSize: "14px",
              color: "rgba(255, 255, 255, 0.6)",
              margin: 0,
            }}
          >
            {stage.description}
          </p>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ marginBottom: "30px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "8px",
          }}
        >
          <span style={{ fontSize: "14px", color: "rgba(255, 255, 255, 0.7)" }}>
            Progress
          </span>
          <span
            style={{ fontSize: "18px", fontWeight: "bold", color: "#00d4ff" }}
          >
            {stage.progress}%
          </span>
        </div>
        <div
          style={{
            width: "100%",
            height: "24px",
            background: "rgba(255, 255, 255, 0.1)",
            borderRadius: "12px",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${stage.progress}%` }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            style={{
              height: "100%",
              background:
                stage.status === "completed"
                  ? "linear-gradient(90deg, #00ff88, #00cc66)"
                  : stage.status === "training"
                  ? "linear-gradient(90deg, #00d4ff, #0099cc)"
                  : "rgba(100, 100, 100, 0.5)",
              borderRadius: "12px",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Animated shine effect for training */}
            {stage.status === "training" && (
              <motion.div
                animate={{ x: ["-100%", "200%"] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "50%",
                  height: "100%",
                  background:
                    "linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent)",
                }}
              />
            )}
          </motion.div>
        </div>
      </div>

      {/* Metrics (only for training stage) */}
      {stage.status === "training" && stage.epoch && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "16px",
            marginBottom: "30px",
          }}
        >
          <MetricCard label="Epoch" value={stage.epoch} />
          <MetricCard label="Loss" value={stage.loss} trend="down" />
          <MetricCard label="Accuracy" value={stage.accuracy} trend="up" />
          <MetricCard label="ETA" value={stage.eta} />
        </div>
      )}

      {/* Details list */}
      <div>
        <h4
          style={{
            fontSize: "16px",
            color: "rgba(255, 255, 255, 0.8)",
            marginBottom: "16px",
          }}
        >
          Key Features:
        </h4>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {stage.details.map((detail, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "12px",
                background: "rgba(255, 255, 255, 0.05)",
                borderRadius: "8px",
                border: "1px solid rgba(255, 255, 255, 0.1)",
              }}
            >
              <div
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  background: "#00d4ff",
                }}
              />
              <span
                style={{ fontSize: "14px", color: "rgba(255, 255, 255, 0.9)" }}
              >
                {detail}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

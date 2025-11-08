import { motion } from "framer-motion";
import FeatureItem from "../FeatureItem";

export default function LearningFeaturesStage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "30px",
      }}
    >
      {/* Title */}
      <div
        style={{
          fontSize: "20px",
          color: "#ffd700",
          fontWeight: "600",
          textAlign: "center",
        }}
      >
        🧠 What Features Does Classifier Learn?
      </div>

      {/* Feature comparison */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: "20px",
        }}
      >
        {/* Conserved lncRNA features */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          style={{
            padding: "24px",
            background: "rgba(0, 255, 136, 0.08)",
            border: "2px solid rgba(0, 255, 136, 0.3)",
            borderRadius: "16px",
          }}
        >
          <div
            style={{
              fontSize: "32px",
              textAlign: "center",
              marginBottom: "16px",
            }}
          >
            ✅
          </div>
          <div
            style={{
              fontSize: "18px",
              color: "#00ff88",
              fontWeight: "600",
              textAlign: "center",
              marginBottom: "20px",
            }}
          >
            Conserved lncRNA (Class 1)
          </div>

          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <FeatureItem
              label="Cross-species Similarity"
              value="High"
              stars={5}
              color="#00ff88"
              delay={0.4}
            />
            <FeatureItem
              label="Evolutionary Pressure"
              value="Strong"
              icon="🔒"
              color="#00ff88"
              delay={0.6}
            />
            <FeatureItem
              label="Sequence Pattern"
              value="Preserved"
              icon="✓"
              color="#00ff88"
              delay={0.8}
            />
          </div>
        </motion.div>

        {/* Non-conserved lncRNA features */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          style={{
            padding: "24px",
            background: "rgba(255, 107, 157, 0.08)",
            border: "2px solid rgba(255, 107, 157, 0.3)",
            borderRadius: "16px",
          }}
        >
          <div
            style={{
              fontSize: "32px",
              textAlign: "center",
              marginBottom: "16px",
            }}
          >
            ❌
          </div>
          <div
            style={{
              fontSize: "18px",
              color: "#ff6b9d",
              fontWeight: "600",
              textAlign: "center",
              marginBottom: "20px",
            }}
          >
            Non-conserved lncRNA (Class 0)
          </div>

          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <FeatureItem
              label="Cross-species Similarity"
              value="Low"
              stars={1}
              color="#ff6b9d"
              delay={0.4}
            />
            <FeatureItem
              label="Evolutionary Pressure"
              value="Weak"
              icon="🔓"
              color="#ff6b9d"
              delay={0.6}
            />
            <FeatureItem
              label="Sequence Pattern"
              value="Variable"
              icon="~"
              color="#ff6b9d"
              delay={0.8}
            />
          </div>
        </motion.div>
      </div>

      {/* Learning insight */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 1.2 }}
        style={{
          padding: "24px",
          background:
            "linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(255, 215, 0, 0.1))",
          border: "2px solid #ffd700",
          borderRadius: "16px",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: "40px", marginBottom: "12px" }}>💡</div>
        <div
          style={{
            fontSize: "18px",
            fontWeight: "600",
            color: "#ffd700",
            marginBottom: "12px",
          }}
        >
          Classifier Learns:
        </div>
        <div
          style={{
            fontSize: "16px",
            color: "#fff",
            lineHeight: "1.7",
          }}
        >
          <strong style={{ color: "#00ff88" }}>
            High Cross-species Similarity
          </strong>{" "}
          + <strong style={{ color: "#00ff88" }}>Preserved Patterns</strong> ={" "}
          <strong style={{ color: "#00ff88" }}>lncRNA Conserved</strong>
        </div>
      </motion.div>
    </motion.div>
  );
}

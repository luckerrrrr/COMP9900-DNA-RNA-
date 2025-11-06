import { motion } from "framer-motion";
import LearnedFeature from "../LearnedFeature";

export default function ResultsStage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "30px",
        alignItems: "center",
      }}
    >
      {/* Title */}
      <div
        style={{
          fontSize: "20px",
          color: "#00ff88",
          fontWeight: "600",
          textAlign: "center",
        }}
      >
        ✅ Classifier Can Now Predict Conservation!
      </div>

      {/* Before / After */}
      <div
        style={{
          display: "flex",
          gap: "30px",
          alignItems: "center",
        }}
      >
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          style={{
            padding: "24px",
            background: "rgba(255, 107, 157, 0.08)",
            border: "2px solid rgba(255, 107, 157, 0.3)",
            borderRadius: "16px",
            textAlign: "center",
            minWidth: "180px",
          }}
        >
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>😕</div>
          <div
            style={{
              fontSize: "14px",
              color: "#ff6b9d",
              marginBottom: "8px",
            }}
          >
            Before
          </div>
          <div style={{ fontSize: "32px", fontWeight: "bold", color: "#fff" }}>
            50%
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          style={{ fontSize: "36px", color: "#00d4ff" }}
        >
          →
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          style={{
            padding: "24px",
            background: "rgba(0, 255, 136, 0.1)",
            border: "2px solid #00ff88",
            borderRadius: "16px",
            textAlign: "center",
            minWidth: "180px",
            boxShadow: "0 0 30px rgba(0, 255, 136, 0.3)",
          }}
        >
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🎉</div>
          <div
            style={{
              fontSize: "14px",
              color: "#00ff88",
              marginBottom: "8px",
            }}
          >
            After
          </div>
          <div style={{ fontSize: "32px", fontWeight: "bold", color: "#fff" }}>
            92%
          </div>
        </motion.div>
      </div>

      {/* What it learned */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        style={{
          width: "100%",
          padding: "24px",
          background: "rgba(0, 212, 255, 0.05)",
          borderRadius: "16px",
          border: "1px solid rgba(0, 212, 255, 0.2)",
        }}
      >
        <div
          style={{
            fontSize: "16px",
            color: "#00d4ff",
            fontWeight: "600",
            marginBottom: "16px",
            textAlign: "center",
          }}
        >
          🎯 What Classifier Learned
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "12px",
          }}
        >
          <LearnedFeature
            icon="⭐"
            text="Recognize"
            detail="High conservation"
          />
          <LearnedFeature icon="🔍" text="Identify" detail="Coding ability" />
          <LearnedFeature icon="✅" text="Classify" detail="lncRNA vs mRNA" />
        </div>
      </motion.div>
    </motion.div>
  );
}

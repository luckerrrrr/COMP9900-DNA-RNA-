import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function ClassifierAnimation() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStage((prev) => (prev >= 3 ? 0 : prev + 1));
    }, 2500);
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      style={{
        padding: "30px",
        background: "rgba(0, 212, 255, 0.03)",
        borderRadius: "12px",
        border: "1px solid rgba(0, 212, 255, 0.1)",
      }}
    >
      {/* Stage indicator */}
      <div
        style={{
          textAlign: "center",
          marginBottom: "30px",
          fontSize: "15px",
          color: "#00d4ff",
          fontWeight: "500",
        }}
      >
        {stage === 0 && "Stage 1: Input DNA Sequence"}
        {stage === 1 && "Stage 2: Frozen Encoder Extracts Features"}
        {stage === 2 && "Stage 3: Linear Head Processes Features"}
        {stage === 3 && "Stage 4: Output Classification Result"}
      </div>

      {/* Pipeline visualization */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "20px",
        }}
      >
        {/* Input */}
        <motion.div
          animate={{
            scale: stage === 0 ? 1.1 : 1,
            borderColor: stage === 0 ? "#00d4ff" : "rgba(255, 255, 255, 0.1)",
          }}
          style={{
            flex: 1,
            padding: "20px",
            background: "rgba(255, 255, 255, 0.05)",
            borderRadius: "12px",
            border: "2px solid rgba(255, 255, 255, 0.1)",
            textAlign: "center",
            transition: "all 0.3s ease",
          }}
        >
          <div style={{ fontSize: "32px", marginBottom: "8px" }}>🧬</div>
          <div style={{ fontSize: "13px", color: "rgba(255, 255, 255, 0.8)" }}>
            DNA Sequence
          </div>
          <div
            style={{
              fontSize: "11px",
              color: "rgba(255, 255, 255, 0.5)",
              marginTop: "4px",
            }}
          >
            512bp window
          </div>
        </motion.div>

        {/* Arrow 1 */}
        <motion.div
          animate={{
            opacity: stage >= 1 ? 1 : 0.3,
            x: stage >= 1 ? [0, 5, 0] : 0,
          }}
          transition={{ duration: 0.5 }}
          style={{ fontSize: "24px", color: "#00d4ff" }}
        >
          →
        </motion.div>

        {/* Encoder (Frozen) */}
        <motion.div
          animate={{
            scale: stage === 1 ? 1.1 : 1,
            borderColor: stage === 1 ? "#00d4ff" : "rgba(0, 212, 255, 0.3)",
          }}
          style={{
            flex: 1,
            padding: "20px",
            background: "rgba(0, 212, 255, 0.1)",
            borderRadius: "12px",
            border: "2px solid rgba(0, 212, 255, 0.3)",
            textAlign: "center",
            position: "relative",
            transition: "all 0.3s ease",
          }}
        >
          {/* Frozen badge */}
          <div
            style={{
              position: "absolute",
              top: "-10px",
              right: "10px",
              padding: "4px 12px",
              background: "#00d4ff",
              borderRadius: "12px",
              fontSize: "10px",
              fontWeight: "bold",
              color: "#000",
            }}
          >
            🔒 FROZEN
          </div>
          <div style={{ fontSize: "32px", marginBottom: "8px" }}>🔷</div>
          <div style={{ fontSize: "13px", color: "rgba(255, 255, 255, 0.8)" }}>
            Encoder
          </div>
          <div
            style={{
              fontSize: "11px",
              color: "rgba(255, 255, 255, 0.5)",
              marginTop: "4px",
            }}
          >
            Pre-trained GPN
          </div>
        </motion.div>

        {/* Arrow 2 */}
        <motion.div
          animate={{
            opacity: stage >= 2 ? 1 : 0.3,
            x: stage >= 2 ? [0, 5, 0] : 0,
          }}
          transition={{ duration: 0.5 }}
          style={{ fontSize: "24px", color: "#00d4ff" }}
        >
          →
        </motion.div>

        {/* Linear Head (Trainable) */}
        <motion.div
          animate={{
            scale: stage === 2 ? 1.1 : 1,
            borderColor: stage === 2 ? "#00ff88" : "rgba(0, 255, 136, 0.3)",
          }}
          style={{
            flex: 1,
            padding: "20px",
            background: "rgba(0, 255, 136, 0.1)",
            borderRadius: "12px",
            border: "2px solid rgba(0, 255, 136, 0.3)",
            textAlign: "center",
            position: "relative",
            transition: "all 0.3s ease",
          }}
        >
          {/* Trainable badge */}
          <div
            style={{
              position: "absolute",
              top: "-10px",
              right: "10px",
              padding: "4px 12px",
              background: "#00ff88",
              borderRadius: "12px",
              fontSize: "10px",
              fontWeight: "bold",
              color: "#000",
            }}
          >
            🔥 TRAINABLE
          </div>
          <div style={{ fontSize: "32px", marginBottom: "8px" }}>📊</div>
          <div style={{ fontSize: "13px", color: "rgba(255, 255, 255, 0.8)" }}>
            Linear Head
          </div>
          <div
            style={{
              fontSize: "11px",
              color: "rgba(255, 255, 255, 0.5)",
              marginTop: "4px",
            }}
          >
            Binary classifier
          </div>
        </motion.div>

        {/* Arrow 3 */}
        <motion.div
          animate={{
            opacity: stage >= 3 ? 1 : 0.3,
            x: stage >= 3 ? [0, 5, 0] : 0,
          }}
          transition={{ duration: 0.5 }}
          style={{ fontSize: "24px", color: "#00d4ff" }}
        >
          →
        </motion.div>

        {/* Output */}
        <motion.div
          animate={{
            scale: stage === 3 ? 1.1 : 1,
            borderColor: stage === 3 ? "#ffd700" : "rgba(255, 215, 0, 0.3)",
          }}
          style={{
            flex: 1,
            padding: "20px",
            background: "rgba(255, 215, 0, 0.1)",
            borderRadius: "12px",
            border: "2px solid rgba(255, 215, 0, 0.3)",
            textAlign: "center",
            transition: "all 0.3s ease",
          }}
        >
          <div style={{ fontSize: "32px", marginBottom: "8px" }}>
            {stage === 3 ? "✅" : "📋"}
          </div>
          <div style={{ fontSize: "13px", color: "rgba(255, 255, 255, 0.8)" }}>
            Prediction
          </div>
          <div
            style={{
              fontSize: "11px",
              color: "rgba(255, 255, 255, 0.5)",
              marginTop: "4px",
            }}
          >
            {stage === 3 ? "lncRNA (0.94)" : "lncRNA / mRNA"}
          </div>
        </motion.div>
      </div>

      {/* Explanation text */}
      <motion.div
        key={stage}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          marginTop: "24px",
          padding: "16px",
          background: "rgba(0, 212, 255, 0.05)",
          borderRadius: "8px",
          fontSize: "13px",
          color: "rgba(255, 255, 255, 0.8)",
          textAlign: "center",
          lineHeight: "1.6",
        }}
      >
        {stage === 0 && "Input: 512bp DNA sequence from genome"}
        {stage === 1 &&
          "Frozen encoder extracts conservation features (no weight updates)"}
        {stage === 2 &&
          "Linear head learns to classify based on encoder features (trainable)"}
        {stage === 3 &&
          "Output: Binary prediction (lncRNA vs. protein-coding) with confidence score"}
      </motion.div>
    </div>
  );
}

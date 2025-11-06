import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { FcBookmark, FcGenealogy } from "react-icons/fc";

export default function TrainingStage() {
  const [epoch, setEpoch] = useState(1);

  useEffect(() => {
    const timer = setInterval(() => {
      setEpoch((prev) => (prev >= 5 ? 1 : prev + 1));
    }, 700);
    return () => clearInterval(timer);
  }, []);

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
          color: "#ffd700",
          fontWeight: "600",
          textAlign: "center",
        }}
      >
        🔥 Training Classifier on Labeled Data
      </div>

      {/* Training flow */}
      <div
        style={{
          width: "100%",
          padding: "30px",
          background: "rgba(255, 215, 0, 0.05)",
          borderRadius: "16px",
          border: "1px solid rgba(255, 215, 0, 0.2)",
        }}
      >
        <div
          style={{
            fontSize: "16px",
            color: "#ffd700",
            marginBottom: "20px",
            textAlign: "center",
            fontWeight: "600",
          }}
        >
          Training with 2000 labeled samples
        </div>

        {/* Flow diagram */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "20px",
            marginBottom: "30px",
          }}
        >
          <div
            style={{
              padding: "16px",
              background: "rgba(0, 255, 136, 0.1)",
              border: "2px solid #00ff88",
              borderRadius: "12px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "24px", marginBottom: "8px" }}>
              <FcBookmark />
            </div>
            <div style={{ fontSize: "13px", color: "#fff" }}>Labeled Data</div>
          </div>

          <div style={{ fontSize: "24px", color: "#ffd700" }}>→</div>

          <motion.div
            animate={{
              boxShadow: [
                "0 0 20px rgba(255, 215, 0, 0.3)",
                "0 0 40px rgba(255, 215, 0, 0.6)",
                "0 0 20px rgba(255, 215, 0, 0.3)",
              ],
            }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{
              padding: "16px",
              background: "rgba(255, 215, 0, 0.1)",
              border: "2px solid #ffd700",
              borderRadius: "12px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "24px", marginBottom: "8px" }}>
              <FcGenealogy />
            </div>
            <div
              style={{ fontSize: "13px", color: "#ffd700", fontWeight: "600" }}
            >
              Classifier Data
            </div>
            <div
              style={{
                fontSize: "11px",
                color: "rgba(255, 255, 255, 0.6)",
                marginTop: "4px",
              }}
            >
              Learning...
            </div>
          </motion.div>

          <div style={{ fontSize: "24px", color: "#ffd700" }}>→</div>

          <div
            style={{
              padding: "16px",
              background: "rgba(0, 212, 255, 0.1)",
              border: "2px solid #00d4ff",
              borderRadius: "12px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "24px", marginBottom: "8px" }}>✅</div>
            <div style={{ fontSize: "13px", color: "#fff" }}>Predictions</div>
          </div>
        </div>

        {/* Epoch progress */}
        <div
          style={{
            textAlign: "center",
            fontSize: "18px",
            color: "#ffd700",
            fontWeight: "600",
            marginBottom: "12px",
          }}
        >
          Epoch {epoch} / 5
        </div>

        <div
          style={{
            width: "100%",
            height: "8px",
            background: "rgba(255, 255, 255, 0.1)",
            borderRadius: "4px",
            overflow: "hidden",
          }}
        >
          <motion.div
            animate={{ width: `${(epoch / 5) * 100}%` }}
            style={{
              height: "100%",
              background: "linear-gradient(90deg, #ffd700, #ffaa00)",
              borderRadius: "4px",
            }}
          />
        </div>
      </div>

      {/* Caption */}
      <motion.div
        style={{
          padding: "16px",
          background: "rgba(0, 212, 255, 0.05)",
          borderRadius: "10px",
          textAlign: "center",
          fontSize: "14px",
          color: "rgba(255, 255, 255, 0.8)",
          lineHeight: "1.6",
        }}
      >
        💡 Only classifier is trained (1-5 epochs). Encoder stays frozen to keep
        DNA understanding.
      </motion.div>
    </motion.div>
  );
}

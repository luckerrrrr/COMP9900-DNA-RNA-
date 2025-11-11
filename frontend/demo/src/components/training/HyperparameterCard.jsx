import { motion } from "framer-motion";
import { useState } from "react";

export default function HyperparameterCard({ param, delay }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      whileHover={{ scale: 1.02 }}
      onClick={() => setIsExpanded(!isExpanded)}
      style={{
        padding: "24px",
        background: `linear-gradient(135deg, ${param.color}10, rgba(255, 255, 255, 0.03))`,
        borderRadius: "16px",
        border: `2px solid ${param.color}40`,
        cursor: "pointer",
        position: "relative",
      }}
    >
      {/* Priority badge */}
      <div
        style={{
          position: "absolute",
          top: "-12px",
          right: "20px",
          padding: "6px 16px",
          background: param.color,
          borderRadius: "20px",
          fontSize: "11px",
          fontWeight: "bold",
          color: "#000",
        }}
      >
        Priority: {param.priority}
      </div>

      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "16px",
          marginBottom: "20px",
        }}
      >
        {/* Icon */}
        <div
          style={{
            fontSize: "40px",
            minWidth: "50px",
          }}
        >
          {param.icon}
        </div>

        {/* Title */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontSize: "12px",
              color: param.color,
              marginBottom: "6px",
              fontWeight: "600",
              textTransform: "uppercase",
            }}
          >
            {param.category}
          </div>
          <div
            style={{
              fontSize: "18px",
              fontWeight: "bold",
              color: "#fff",
              marginBottom: "12px",
            }}
          >
            {param.name}
          </div>
        </div>

        {/* Expand indicator */}
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          style={{
            fontSize: "24px",
            color: param.color,
            transition: "transform 0.3s ease",
          }}
        >
          ▼
        </motion.div>
      </div>

      {/* Why important */}
      <div
        style={{
          padding: "16px",
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: "12px",
          marginBottom: "16px",
        }}
      >
        <div
          style={{
            fontSize: "13px",
            color: param.color,
            marginBottom: "8px",
            fontWeight: "600",
          }}
        >
          ❓ Why Important:
        </div>
        <div
          style={{
            fontSize: "14px",
            color: "rgba(255, 255, 255, 0.85)",
            lineHeight: "1.7",
          }}
        >
          {param.why}
        </div>
      </div>

      {/* Expandable details */}
      <motion.div
        initial={false}
        animate={{
          height: isExpanded ? "auto" : 0,
          opacity: isExpanded ? 1 : 0,
        }}
        style={{
          overflow: "hidden",
        }}
      >
        {/* Recommendation */}
        <div
          style={{
            padding: "16px",
            background: "rgba(0, 255, 136, 0.05)",
            borderRadius: "12px",
            marginBottom: "16px",
            border: "1px solid rgba(0, 255, 136, 0.1)",
          }}
        >
          <div
            style={{
              fontSize: "13px",
              color: "#00ff88",
              marginBottom: "8px",
              fontWeight: "600",
            }}
          >
            ✅ Recommendation:
          </div>
          <div
            style={{
              fontSize: "14px",
              color: "rgba(255, 255, 255, 0.85)",
              lineHeight: "1.7",
            }}
          >
            {param.recommendation}
          </div>
        </div>

        {/* Suggestion/Strategy */}
        {(param.suggestion || param.tuningStrategy) && (
          <div
            style={{
              padding: "16px",
              background: "rgba(0, 212, 255, 0.05)",
              borderRadius: "12px",
              border: "1px solid rgba(0, 212, 255, 0.1)",
            }}
          >
            <div
              style={{
                fontSize: "13px",
                color: "#00d4ff",
                marginBottom: "8px",
                fontWeight: "600",
              }}
            >
              💡 {param.tuningStrategy ? "Tuning Strategy:" : "Suggestion:"}
            </div>
            <div
              style={{
                fontSize: "14px",
                color: "rgba(255, 255, 255, 0.85)",
                lineHeight: "1.7",
              }}
            >
              {param.suggestion || param.tuningStrategy}
            </div>
          </div>
        )}
      </motion.div>

      {/* Click hint */}
      {!isExpanded && (
        <div
          style={{
            textAlign: "center",
            fontSize: "12px",
            color: "rgba(255, 255, 255, 0.4)",
            marginTop: "12px",
          }}
        >
          Click to see recommendations ↓
        </div>
      )}
    </motion.div>
  );
}

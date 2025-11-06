import { motion } from "framer-motion";

export default function FeatureItem({ label, value, stars, icon, color, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      style={{
        padding: "12px",
        background: "rgba(255, 255, 255, 0.05)",
        borderRadius: "10px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
      }}
    >
      <div
        style={{
          fontSize: "12px",
          color: "rgba(255, 255, 255, 0.5)",
          marginBottom: "6px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div
          style={{
            fontSize: "16px",
            fontWeight: "bold",
            color: color,
          }}
        >
          {value}
        </div>
        {stars && (
          <div style={{ fontSize: "14px" }}>
            {"⭐".repeat(stars)}
            {"☆".repeat(5 - stars)}
          </div>
        )}
        {icon && <div style={{ fontSize: "18px" }}>{icon}</div>}
      </div>
    </motion.div>
  );
}
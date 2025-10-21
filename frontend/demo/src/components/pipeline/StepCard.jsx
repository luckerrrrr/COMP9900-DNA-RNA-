import { motion } from "framer-motion";

export default function StepCard({ step, index, isActive, onClick }) {
  return (
    <motion.div
      onClick={onClick}
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ scale: 1.05 }}
      style={{
        width: isActive ? "130px" : "100px",
        height: isActive ? "130px" : "100px",
        borderRadius: "16px",
        background: isActive
          ? "rgba(0, 212, 255, 0.15)"
          : "rgba(255, 255, 255, 0.05)",
        backdropFilter: "blur(10px)",
        border: isActive
          ? "2px solid #00d4ff"
          : "1px solid rgba(255, 255, 255, 0.1)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        boxShadow: isActive ? "0 0 30px rgba(0, 212, 255, 0.4)" : "none",
        transition: "all 0.3s ease",
      }}
    >
      <div
        style={{
          fontSize: "36px",
          marginBottom: "8px",
          color: isActive ? "#00d4ff" : "rgba(255, 255, 255, 0.6)",
        }}
      >
        {step.icon}
      </div>
      <div
        style={{
          fontSize: "16px",
          fontWeight: isActive ? "bold" : "normal",
          color: isActive ? "#00d4ff" : "#fff",
        }}
      >
        {step.title}
      </div>
      <div
        style={{
          fontSize: "16px",
          opacity: 0.6,
          marginTop: "2px",
        }}
      >
        {step.subtitle}
      </div>
    </motion.div>
  );
}

import { motion } from "framer-motion";

export default function StageCard({ stage, isActive, onClick }) {
  const getStatusColor = () => {
    if (stage.status === "completed") return "#00ff88";
    if (stage.status === "training") return "#00d4ff";
    return "#666";
  };

  const getStatusIcon = () => {
    if (stage.status === "completed") return "✓";
    if (stage.status === "training") return "⏳";
    return "○";
  };

  return (
    <motion.div
      onClick={onClick}
      whileHover={{ scale: 1.05, y: -5 }}
      whileTap={{ scale: 0.95 }}
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: stage.id * 0.2 }}
      style={{
        width: isActive ? "200px" : "180px",
        height: isActive ? "220px" : "200px",
        background: isActive
          ? `rgba(${
              stage.status === "completed"
                ? "0, 255, 136"
                : stage.status === "training"
                ? "0, 212, 255"
                : "100, 100, 100"
            }, 0.15)`
          : "rgba(255, 255, 255, 0.05)",
        border: `2px solid ${getStatusColor()}`,
        borderRadius: "16px",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        position: "relative",
        boxShadow: isActive
          ? `0 0 30px ${getStatusColor()}40`
          : "0 4px 15px rgba(0, 0, 0, 0.2)",
        transition: "all 0.3s ease",
      }}
    >
      {/* Status badge */}
      <div
        style={{
          position: "absolute",
          top: "-12px",
          right: "-12px",
          width: "36px",
          height: "36px",
          borderRadius: "50%",
          background: getStatusColor(),
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "18px",
          color: stage.status === "pending" ? "#fff" : "#000",
          fontWeight: "bold",
          boxShadow: `0 0 15px ${getStatusColor()}60`,
        }}
      >
        {getStatusIcon()}
      </div>

      {/* Icon */}
      <div style={{ fontSize: "48px", marginBottom: "12px" }}>{stage.icon}</div>

      {/* Stage number and name */}
      <div
        style={{
          fontSize: "14px",
          color: "rgba(255, 255, 255, 0.6)",
          marginBottom: "8px",
        }}
      >
        Stage {stage.id}
      </div>
      <div
        style={{
          fontSize: "20px",
          fontWeight: "bold",
          color: getStatusColor(),
          marginBottom: "8px",
        }}
      >
        {stage.name}
      </div>

      {/* Progress indicator */}
      {stage.status === "training" && (
        <motion.div
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: 3 }}
          style={{
            width: "100%",
            height: "4px",
            background: "rgba(255, 255, 255, 0.1)",
            borderRadius: "2px",
            overflow: "hidden",
            marginTop: "12px",
          }}
        >
          <motion.div
            animate={{ x: ["-100%", "200%"] }}
            transition={{ duration: 1.5, repeat: 5, ease: "linear" }}
            style={{
              width: "50%",
              height: "100%",
              background: `linear-gradient(90deg, transparent, ${getStatusColor()}, transparent)`,
            }}
          />
        </motion.div>
      )}

      {stage.status === "completed" && (
        <div
          style={{
            width: "100%",
            height: "4px",
            background: getStatusColor(),
            borderRadius: "2px",
            marginTop: "12px",
          }}
        />
      )}
    </motion.div>
  );
}

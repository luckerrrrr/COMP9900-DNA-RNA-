import { motion } from "framer-motion";

export default function Step2MSAAlignment({ isActive, isCompleted }) {
  return (
    <motion.div
      animate={{
        scale: isCompleted ? 1.05 : 1,
        boxShadow: isCompleted
          ? "0 0 30px rgba(100, 200, 255, 0.5)"
          : "0 0 0px rgba(0,0,0,0)",
      }}
      style={{
        width: "280px",
        height: "300px",
        background: "rgba(255, 255, 255, 0.05)",
        backdropFilter: "blur(10px)",
        border: `2px solid ${
          isCompleted ? "rgba(100, 200, 255, 0.8)" : "rgba(255, 255, 255, 0.2)"
        }`,
        borderRadius: "18px",
        padding: "30px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "20px",
        position: "relative",
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        style={{
          position: "absolute",
          top: "12px",
          right: "12px",
          background: "rgba(255, 100, 100, 0.3)",
          border: "1px solid rgba(255, 100, 100, 0.6)",
          borderRadius: "8px",
          padding: "6px 12px",
          fontSize: "14px",
          fontWeight: "bold",
          color: "#ff6b6b",
        }}
      >
        GPN-MSA
      </motion.div>

      <div
        style={{
          width: "160px",
          height: "120px",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "center",
          gap: "12px",
        }}
      >
        {[0, 1, 2].map((i) => (
          <div key={i} style={{ display: "flex", gap: "4px" }}>
            <motion.div
              initial={{ x: i * 25 }}
              animate={isActive || isCompleted ? { x: 0 } : { x: i * 25 }}
              transition={{ duration: 0.8, delay: i * 0.2 }}
              style={{ display: "flex", gap: "4px" }}
            >
              {["#ef5350", "#5c6bc0", "#ffeb3b", "#66bb6a", "#ef5350"].map(
                (color, j) => (
                  <motion.div
                    key={j}
                    initial={{ opacity: j === 2 && i === 2 ? 0 : 1 }}
                    animate={
                      isActive || isCompleted 
                        ? { opacity: 1 }
                        : { opacity: j === 2 && i === 2 ? 0 : 1 }
                    }
                    transition={{ duration: 0.5, delay: 1 + j * 0.1 }}
                    style={{
                      width: "14px",
                      height: "14px",
                      background: j === 2 && i === 2 ? "#555" : color,
                      borderRadius: "3px",
                    }}
                  />
                )
              )}
            </motion.div>
          </div>
        ))}
      </div>

      <div style={{ textAlign: "center" }}>
        <h3 style={{ fontSize: "26px", fontWeight: "700", margin: 0 }}>
          MSA Alignment
        </h3>
        <p style={{ fontSize: "19px", color: "#aaa", margin: 0 }}>
          Multi-Species
        </p>
      </div>
    </motion.div>
  );
}

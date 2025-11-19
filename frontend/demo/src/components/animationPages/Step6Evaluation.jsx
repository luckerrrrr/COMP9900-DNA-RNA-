import { motion } from "framer-motion";

export default function Step6Evaluation({ isActive, isCompleted }) {
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
      }}
    >
      <div
        style={{
          width: "160px",
          height: "120px",
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "center",
          gap: "16px",
        }}
      >

        {[
          { label: "GPN", height: 70, color: "#64b5f6" },
          { label: "GPN-MSA", height: 90, color: "#66bb6a" },
        ].map((bar, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <motion.div
              animate={
                isActive || isCompleted
                  ? { height: `${bar.height}px`, opacity: 1 }
                  : { height: "0px", opacity: 0 }
              }
              transition={{ duration: 0.8, delay: i * 0.3 }}
              style={{
                width: "40px",
                background: bar.color,
                borderRadius: "6px 6px 0 0",
              }}
            />
            <span
              style={{ fontSize: "14px", color: "#aaa", fontWeight: "600" }}
            >
              {bar.label}
            </span>
          </div>
        ))}
      </div>

      <motion.div
        animate={
          isActive || isCompleted
            ? { opacity: 1, scale: 1 }
            : { opacity: 0, scale: 0 }
        }
        transition={{ delay: 1, duration: 0.5 }}
        style={{
          padding: "8px 16px",
          background: "rgba(102, 187, 106, 0.2)",
          border: "1px solid #66bb6a",
          borderRadius: "8px",
          fontSize: "16px",
          fontWeight: "bold",
          color: "#66bb6a",
        }}
      >
        ✓ Better Performance
      </motion.div>

      <div style={{ textAlign: "center" }}>
        <h3 style={{ fontSize: "26px", fontWeight: "700", margin: 0 }}>
          Evaluation
        </h3>
        <p style={{ fontSize: "19px", color: "#aaa", margin: 0 }}>Analysis</p>
      </div>
    </motion.div>
  );
}

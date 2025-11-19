import { motion } from "framer-motion";

export default function Step5Classification({ isActive, isCompleted }) {
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
      <motion.div
        animate={
          isActive
            ? { opacity: [0, 1, 1, 0], scale: [0.9, 1, 1, 0.9] }
            : isCompleted
            ? { opacity: 0, scale: 0.9 }
            : { opacity: 0, scale: 0.9 }
        }
        transition={{
          duration: 4,
          times: [0, 0.15, 0.85, 1],
        }}
        style={{
          width: "200px",
          height: "140px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          position: "relative",
        }}
      >
        {/* Layer 1: Linear */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={isActive ? { opacity: 1, y: 0 } : { opacity: 0, y: -10 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          style={{
            width: "100%",
            padding: "10px",
            background: "rgba(100, 181, 246, 0.2)",
            border: "1px solid rgba(100, 181, 246, 0.5)",
            borderRadius: "8px",
            textAlign: "center",
            fontSize: "14px",
            fontWeight: "600",
            color: "#64b5f6",
          }}
        >
          Linear
        </motion.div>

        <motion.div
          animate={
            isActive
              ? {
                  y: [0, 18],
                  opacity: [0, 1, 1, 0],
                }
              : { y: 0, opacity: 0 }
          }
          transition={{
            duration: 0.8,
            delay: 1,
            ease: "easeInOut",
          }}
          style={{
            width: "8px",
            height: "8px",
            background: "#64b5f6",
            borderRadius: "50%",
            position: "absolute",
            top: "38px",
          }}
        />

        {/* Layer 2: ReLU/GELU */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={isActive ? { opacity: 1, y: 0 } : { opacity: 0, y: -10 }}
          transition={{ duration: 0.5, delay: 0.7 }}
          style={{
            width: "100%",
            padding: "10px",
            background: "rgba(102, 187, 106, 0.2)",
            border: "1px solid rgba(102, 187, 106, 0.5)",
            borderRadius: "8px",
            textAlign: "center",
            fontSize: "14px",
            fontWeight: "600",
            color: "#66bb6a",
          }}
        >
          ReLU/GELU
        </motion.div>

        <motion.div
          animate={
            isActive
              ? {
                  y: [0, 18],
                  opacity: [0, 1, 1, 0],
                }
              : { y: 0, opacity: 0 }
          }
          transition={{
            duration: 0.8,
            delay: 2,
            ease: "easeInOut",
          }}
          style={{
            width: "8px",
            height: "8px",
            background: "#66bb6a",
            borderRadius: "50%",
            position: "absolute",
            top: "90px",
          }}
        />

        {/* Layer 3: Linear */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={isActive ? { opacity: 1, y: 0 } : { opacity: 0, y: -10 }}
          transition={{ duration: 0.8, delay: 1.1 }}
          style={{
            width: "100%",
            padding: "10px",
            background: "rgba(255, 152, 0, 0.2)",
            border: "1px solid rgba(255, 152, 0, 0.5)",
            borderRadius: "8px",
            textAlign: "center",
            fontSize: "14px",
            fontWeight: "600",
            color: "#ff9800",
          }}
        >
          Linear
        </motion.div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={
          isActive || isCompleted
            ? { opacity: 1, scale: 1 }
            : { opacity: 0, scale: 0.8 }
        }
        transition={{ duration: 0.6, delay: 4 }}
        style={{
          display: "flex",
          gap: "12px",
          position: "absolute",
        }}
      >
        {/* Conserved */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "4px",
          }}
        >
          <div
            style={{
              width: "60px",
              height: "60px",
              background: "linear-gradient(135deg, #66bb6a 0%, #4caf50 100%)",
              borderRadius: "10px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 4px 12px rgba(102, 187, 106, 0.3)",
            }}
          >
            <div style={{ fontSize: "26px", color: "#fff", lineHeight: 1 }}>
              ✓
            </div>
            <div
              style={{
                fontSize: "16px",
                fontWeight: "bold",
                color: "#fff",
                marginTop: "2px",
              }}
            >
              94%
            </div>
          </div>
          <span
            style={{
              fontSize: "12px",
              fontWeight: "600",
              color: "#66bb6a",
            }}
          >
            Conserved
          </span>
        </div>

        {/* Non-conserved */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "4px",
          }}
        >
          <div
            style={{
              width: "60px",
              height: "28px",
              background: "linear-gradient(135deg, #ef5350 0%, #e53935 100%)",
              borderRadius: "10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 2px 8px rgba(239, 83, 80, 0.3)",
            }}
          >
            <div
              style={{
                fontSize: "15px",
                fontWeight: "bold",
                color: "#fff",
              }}
            >
              6%
            </div>
          </div>
          <span
            style={{
              fontSize: "12px",
              fontWeight: "600",
              color: "#ef5350",
            }}
          >
            Other
          </span>
        </div>
      </motion.div>

      {/* Title */}
      <div style={{ textAlign: "center" }}>
        <h3 style={{ fontSize: "26px", fontWeight: "700", margin: 0 }}>
          Classification
        </h3>
        <p style={{ fontSize: "16px", color: "#aaa", margin: 0 }}>
          Conserved or Not
        </p>
      </div>
    </motion.div>
  );
}

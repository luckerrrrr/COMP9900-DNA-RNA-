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
      <div
        style={{
          width: "200px",
          height: "140px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
        }}
      >
        <motion.div
          animate={
            isActive || isCompleted
              ? {
                  scale: [1, 1.1, 1.1, 0.3],
                  opacity: [1, 1, 1, 0],
                }
              : { scale: 1, opacity: 1 }
          }
          transition={{
            duration: 1.2,
            times: [0, 0.3, 0.6, 1],
          }}
          style={{
            position: "absolute",
            padding: "16px 24px",
            background: "rgba(100, 181, 246, 0.2)",
            border: "2px solid #64b5f6",
            borderRadius: "10px",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: "16px",
              fontWeight: "bold",
              color: "#64b5f6",
              marginBottom: "6px",
            }}
          >
            Linear Classifier
          </div>
          <div
            style={{
              fontSize: "13px",
              color: "#81c9f6",
              fontFamily: "monospace",
            }}
          >
            y = W·x + b
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={
            isActive || isCompleted
              ? { opacity: 1, scale: 1 }
              : { opacity: 0, scale: 0.5 }
          }
          transition={{ duration: 0.6, delay: 1 }}
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "8px",
            position: "absolute",
          }}
        >
          <div
            style={{
              fontSize: "42px",
              color: "#66bb6a",
              lineHeight: 1,
            }}
          >
            ✓
          </div>

          <div
            style={{
              fontSize: "36px",
              fontWeight: "bold",
              color: "#66bb6a",
              lineHeight: 1,
            }}
          >
            94%
          </div>

          <div
            style={{
              fontSize: "20px",
              fontWeight: "600",
              color: "#66bb6a",
            }}
          >
            Conserved
          </div>
        </motion.div>
      </div>

      <div style={{ textAlign: "center" }}>
        <h3 style={{ fontSize: "26px", fontWeight: "700", margin: 0 }}>
          Classification
        </h3>
        <p style={{ fontSize: "19px", color: "#aaa", margin: 0 }}>
          Linear Probing
        </p>
      </div>
    </motion.div>
  );
}

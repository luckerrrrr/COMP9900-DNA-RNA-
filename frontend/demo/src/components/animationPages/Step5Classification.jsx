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
          width: "220px",
          height: "140px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
        }}
      >
        {/* Linear Classifier 盒子 - 闪烁然后消失 */}
        <motion.div
          animate={
            isActive
              ? {
                  scale: [1, 1.1, 1.1, 0.3],
                  opacity: [1, 1, 1, 0],
                }
              : isCompleted
              ? { scale: 0.3, opacity: 0 } 
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
        {/* 二分类结果 */}
        <motion.div
          animate={
            isActive || isCompleted
              ? { opacity: 1, scale: 1 }
              : { opacity: 0, scale: 0 }
          }
          transition={{ duration: 0.6, delay: 1 }}
          style={{
            display: "flex",
            gap: "16px",
            position: "absolute",
          }}
        >
          {/* Conserved - 高概率 */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <div
              style={{
                width: "70px",
                height: "70px",
                background: "linear-gradient(135deg, #66bb6a 0%, #4caf50 100%)",
                borderRadius: "10px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 4px 12px rgba(102, 187, 106, 0.3)",
              }}
            >
              <div style={{ fontSize: "28px", color: "#fff", lineHeight: 1 }}>
                ✓
              </div>
              <div
                style={{
                  fontSize: "20px",
                  fontWeight: "bold",
                  color: "#fff",
                  marginTop: "4px",
                }}
              >
                94%
              </div>
            </div>
            <span
              style={{
                fontSize: "13px",
                fontWeight: "600",
                color: "#66bb6a",
              }}
            >
              Conserved
            </span>
          </div>

          {/* Non-conserved - 低概率 */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <div
              style={{
                width: "70px",
                height: "30px",
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
                  fontSize: "16px",
                  fontWeight: "bold",
                  color: "#fff",
                }}
              >
                6%
              </div>
            </div>
            <span
              style={{
                fontSize: "13px",
                fontWeight: "600",
                color: "#ef5350",
              }}
            >
              Other
            </span>
          </div>
        </motion.div>
      </div>

      <div style={{ textAlign: "center" }}>
        <h3 style={{ fontSize: "26px", fontWeight: "700", margin: 0 }}>
          Classification
        </h3>
        <p style={{ fontSize: "19px", color: "#aaa", margin: 0 }}>
          Binary (0 or 1)
        </p>
      </div>
    </motion.div>
  );
}

import { motion } from "framer-motion";

export default function Step4Embedding({ isActive, isCompleted }) {
  const tokens = ["1", "2", "3", "4"];
  const colors = ["#ef5350", "#5c6bc0", "#ffeb3b", "#66bb6a"];

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
          width: "180px",
          height: "120px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "10px",
        }}
      >
        {tokens.map((token, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >

            <motion.div
              style={{
                fontSize: "20px",
                fontWeight: "bold",
                color: colors[i],
                minWidth: "20px",
              }}
            >
              {token}
            </motion.div>


            <motion.div
              animate={
                isActive || isCompleted 
                  ? { opacity: 1, scaleX: 1 }
                  : { opacity: 0, scaleX: 0 }
              }
              transition={{ duration: 0.4, delay: i * 0.1 + 0.3 }}
              style={{
                fontSize: "16px",
                color: "#888",
              }}
            >
              →
            </motion.div>

            <motion.div
              animate={
                isActive || isCompleted  
                    ? { opacity: 1, scaleX: 1 }
                    : { opacity: 0, scaleX: 0 }
                }
              
              transition={{ duration: 0.6, delay: i * 0.1 + 0.4 }}
              style={{
                display: "flex",
                gap: "3px",
                transformOrigin: "left",
              }}
            >
              {[0, 1, 2, 3, 4, 5].map((j) => (
                <div
                  key={j}
                  style={{
                    width: "10px",
                    height: "16px",
                    background: colors[i],
                    borderRadius: "2px",
                    opacity: 0.6 + j * 0.07,
                  }}
                />
              ))}
            </motion.div>
          </div>
        ))}
      </div>

      <div style={{ textAlign: "center" }}>
        <h3 style={{ fontSize: "26px", fontWeight: "700", margin: 0 }}>
          Embedding
        </h3>
        <p style={{ fontSize: "19px", color: "#aaa", margin: 0 }}>
          Representation
        </p>
      </div>
    </motion.div>
  );
}

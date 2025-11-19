import { motion } from "framer-motion";

export default function Step1DataPreprocessing({ isActive, isCompleted }) {
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
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "10px",
        }}
      >
        {[0, 1, 2, 3, 4].map((i) => (
          <motion.div
            key={i}
            animate={
              isActive
                ? {
                    width: "140px",
                    opacity: i === 2 ? 1 : 0,
                    y: i === 2 ? 0 : i < 2 ? -30 : 30,
                  }
                : {
                    width:
                      i === 0
                        ? "80px"
                        : i === 1
                        ? "110px"
                        : i === 2
                        ? "95px"
                        : i === 3
                        ? "70px"
                        : "100px",
                    opacity: 1,
                    y: 0,
                  }
            }
            transition={{ duration: 1, delay: 0.2 }}
            style={{
              height: "12px",
              background: "#64b5f6",
              borderRadius: "4px",
            }}
          />
        ))}

        <motion.div
          animate={
            isActive ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0 }
          }
          transition={{ delay: 1.2, duration: 0.5 }}
          style={{
            marginTop: "12px",
            padding: "8px 16px",
            background: "rgba(100, 181, 246, 0.3)",
            border: "1px solid #64b5f6",
            borderRadius: "8px",
            fontSize: "16px",
            fontWeight: "bold",
            color: "#64b5f6",
          }}
        >
          512bp
        </motion.div>
      </div>

      <div style={{ textAlign: "center" }}>
        <h3 style={{ fontSize: "26px", fontWeight: "700", margin: 0 }}>
          Data Preprocessing
        </h3>
        <p style={{ fontSize: "19px", color: "#aaa", margin: 0 }}>
          Filter & Clean
        </p>
      </div>
    </motion.div>
  );
}

import { motion } from "framer-motion";

export default function Step3Tokenisation({ isActive, isCompleted }) {
  const bases = ["A", "T", "G", "C"];
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
          width: "160px",
          height: "120px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", gap: "10px" }}>
          {bases.map((base, i) => (
            <div
              key={i}
              style={{ position: "relative", width: "20px", height: "50px" }}
            >
              <motion.div
                initial={{ opacity: 1, y: 0 }}
                animate={
                  isActive || isCompleted
                    ? { opacity: 0, y: -15 }
                    : { opacity: 1, y: 0 }
                }
                transition={{
                  duration: 0.6,
                  delay: i * 0.15,
                }}
                style={{
                  position: "absolute",
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: colors[i],
                }}
              >
                {base}
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={
                  isActive || isCompleted 
                    ? { opacity: 1, y: 0 }
                    : { opacity: 0, y: 15 }
                }
                transition={{
                  duration: 0.6,
                  delay: i * 0.15 + 0.3,
                }}
                style={{
                  position: "absolute",
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: colors[i],
                }}
              >
                {tokens[i]}
              </motion.div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ textAlign: "center" }}>
        <h3 style={{ fontSize: "26px", fontWeight: "700", margin: 0 }}>
          Tokenisation
        </h3>
        <p style={{ fontSize: "19px", color: "#aaa", margin: 0 }}>Encoding</p>
      </div>
    </motion.div>
  );
}

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
      }}
    >

      <div
        style={{
          width: "220px",
          height: "130px",
          display: "flex",
          justifyContent: "space-between",
          gap: "16px",
          position: "relative",
        }}
      >

        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "10px",
          }}
        >

          <div
            style={{
              fontSize: "15px",
              fontWeight: "bold",
              color: "#64b5f6",
            }}
          >
            GPN
          </div>


          <motion.div
            animate={isActive ? { opacity: 1 } : { opacity: 1 }}
            transition={{ duration: 0.6 }}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "6px",
              marginTop: "12px",
            }}
          >
 
            <div style={{ display: "flex", gap: "2px" }}>
              {[0, 1, 2, 3, 4].map((j) => (
                <div
                  key={j}
                  style={{
                    width: "10px",
                    height: "10px",
                    background: [
                      "#ef5350",
                      "#5c6bc0",
                      "#ffeb3b",
                      "#66bb6a",
                      "#ef5350",
                    ][j],
                    borderRadius: "2px",
                  }}
                />
              ))}
            </div>
            <div
              style={{
                fontSize: "10px",
                color: "#64b5f6",
                textAlign: "center",
                marginTop: "4px",
              }}
            >
              512 tokens
            </div>
          </motion.div>
        </div>

        <div
          style={{
            width: "2px",
            height: "100%",
            background: "rgba(255, 255, 255, 0.2)",
          }}
        />

        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <div
            style={{
              fontSize: "15px",
              fontWeight: "bold",
              color: "#64b5f6",
            }}
          >
            GPN-MSA
          </div>

          <div
            style={{
              padding: "3px 8px",
              background: "rgba(255, 100, 100, 0.3)",
              border: "1px solid rgba(255, 100, 100, 0.6)",
              borderRadius: "6px",
              fontSize: "9px",
              fontWeight: "bold",
              color: "#ff6b6b",
            }}
          >
            89 species
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "3px",
              marginTop: "4px",
            }}
          >
            {[0, 1, 2, 3].map((i) => (
              <div key={i} style={{ display: "flex", gap: "2px" }}>
                <motion.div
                  initial={{ x: i * 10 }}
                  animate={isActive || isCompleted ? { x: 0 } : { x: i * 10 }}
                  transition={{ duration: 0.8, delay: i * 0.15 }}
                  style={{ display: "flex", gap: "2px" }}
                >
                  {[0, 1, 2, 3, 4].map((j) => (
                    <motion.div
                      key={j}
                      initial={{ opacity: j === 2 && i === 3 ? 0 : 1 }}
                      animate={
                        isActive || isCompleted
                          ? { opacity: 1 }
                          : { opacity: j === 2 && i === 3 ? 0 : 1 }
                      }
                      transition={{ duration: 0.5, delay: 1 + j * 0.1 }}
                      style={{
                        width: "10px",
                        height: "10px",
                        background:
                          j === 2 && i === 3
                            ? "#555"
                            : [
                                "#ef5350",
                                "#5c6bc0",
                                "#ffeb3b",
                                "#66bb6a",
                                "#ef5350",
                              ][j],
                        borderRadius: "2px",
                      }}
                    />
                  ))}
                </motion.div>
              </div>
            ))}
          </div>

          <motion.div
            animate={isActive || isCompleted ? { opacity: 1 } : { opacity: 0 }}
            transition={{ duration: 0.5, delay: 1.5 }}
            style={{
              fontSize: "9px",
              color: "#ff6b6b",
              marginTop: "4px",
              fontWeight: "600",
            }}
          >
            [512×89]
          </motion.div>
        </div>
      </div>

      <div style={{ textAlign: "center" }}>
        <h3 style={{ fontSize: "26px", fontWeight: "700", margin: 0 }}>
          MSA Alignment
        </h3>
        <p style={{ fontSize: "19px", color: "#aaa", margin: 0 }}>
          GPN vs GPN-MSA
        </p>
      </div>
    </motion.div>
  );
}

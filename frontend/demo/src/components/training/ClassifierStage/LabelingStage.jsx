import { motion } from "framer-motion";

export default function LabelingStage() {
  const getBaseColor = (base) => {
    const colors = { A: "#00ff88", T: "#ff5757", C: "#00d4ff", G: "#ffd700" };
    return colors[base] || "#fff";
  };

  const getBaseBackground = (base) => {
    const backgrounds = {
      A: "rgba(0, 255, 136, 0.15)",
      T: "rgba(255, 87, 87, 0.15)",
      C: "rgba(0, 212, 255, 0.15)",
      G: "rgba(255, 215, 0, 0.15)",
    };
    return backgrounds[base] || "rgba(255, 255, 255, 0.05)";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "30px",
      }}
    >
      {/* Title */}
      <div
        style={{
          fontSize: "20px",
          color: "#00ff88",
          fontWeight: "600",
          textAlign: "center",
        }}
      >
        🏷️ Finding & Labeling Conserved Regions
      </div>

      {/* Multi-species alignment */}
      <div
        style={{
          padding: "24px",
          background: "rgba(0, 212, 255, 0.05)",
          borderRadius: "16px",
          border: "1px solid rgba(0, 212, 255, 0.2)",
        }}
      >
        <div
          style={{
            fontSize: "18px",
            color: "rgba(255, 255, 255, 0.6)",
            marginBottom: "16px",
            textAlign: "center",
          }}
        >
          Compare sequences across species
        </div>

        {/* Alignment */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {["Human", "Mouse", "Chimp"].map((species, i) => (
            <motion.div
              key={species}
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.3 }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
              }}
            >
              <div
                style={{
                  width: "80px",
                  fontSize: "20px",
                  color: "rgba(255, 255, 255, 0.6)",
                  fontWeight: "600",
                }}
              >
                {species}:
              </div>
              <div style={{ display: "flex", gap: "4px" }}>
                {["A", "T", "C", "G", "A", "T", "C", "G"].map((base, j) => (
                  <motion.div
                    key={j}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.3 + j * 0.05 }}
                    style={{
                      width: "35px",
                      height: "35px",
                      background: getBaseBackground(base),
                      border: `2px solid ${getBaseColor(base)}`,
                      borderRadius: "6px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "14px",
                      fontWeight: "bold",
                      color: getBaseColor(base),
                    }}
                  >
                    {base}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Conservation indicator */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
          style={{
            marginTop: "20px",
            padding: "16px",
            background: "rgba(0, 255, 136, 0.1)",
            borderRadius: "12px",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: "16px",
              color: "#00ff88",
              fontWeight: "600",
              marginBottom: "8px",
            }}
          >
            ✅ 100% Identical = Highly Conserved!
          </div>
          <div
            style={{
              fontSize: "16px",
              color: "rgba(255, 255, 255, 0.7)",
            }}
          >
            This lncRNA region is conserved → Classify as Conserved
          </div>
        </motion.div>
      </div>

      {/* Label tag */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 1.6, type: "spring" }}
        style={{
          padding: "20px",
          background: "rgba(0, 255, 136, 0.15)",
          border: "2px solid #00ff88",
          borderRadius: "16px",
          textAlign: "center",
          boxShadow: "0 0 30px rgba(0, 255, 136, 0.3)",
        }}
      >
        <div style={{ fontSize: "40px", marginBottom: "12px" }}>🏷️</div>
        <div
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: "#00ff88",
            marginBottom: "8px",
          }}
        >
          Labeled: lncRNA ✓
        </div>
        <div
          style={{
            fontSize: "16px",
            color: "rgba(255, 255, 255, 0.7)",
          }}
        >
          Conserved region marked by biologists
        </div>
      </motion.div>
    </motion.div>
  );
}

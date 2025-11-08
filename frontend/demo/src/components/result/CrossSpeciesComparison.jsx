import React from "react";
import { motion } from "framer-motion";

export default function CrossSpeciesComparison() {
  const sequences = [
    { species: "🧑 Human", seq: "ATC-GACTG--ATC-GACTG", color: "#00d4ff" },
    { species: "🐭 Mouse", seq: "ATC-G--CTGATC-GACTG", color: "#ff6b9d" },
    { species: "🐵 Chimpanzee", seq: "ATC-GACTGATC-GACT-G", color: "#00ff88" }
  ];

  const conservedPositions = [0,1,2,3,4,7,8,9,12,13,14,15,16,17];

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: "30px"
    }}>
      <h3 style={{ fontSize: "28px", color: "#00d4ff", textAlign: "center" }}>
        Cross-species sequence comparison analysis
      </h3>

      <div style={{
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        background: "rgba(255, 255, 255, 0.03)",
        padding: "30px",
        borderRadius: "12px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        minWidth: "600px"
      }}>
        {sequences.map((item, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.2 }}
            style={{ display: "flex", alignItems: "center", gap: "20px" }}
          >
            <div style={{
              minWidth: "100px",
              fontSize: "18px",
              color: item.color,
              fontWeight: "500"
            }}>
              {item.species}
            </div>
            <div style={{
              fontFamily: "monospace",
              fontSize: "20px",
              letterSpacing: "2px",
              position: "relative"
            }}>
              {item.seq.split("").map((base, j) => (
                <span
                  key={j}
                  style={{
                    color: getBaseColor(base),
                    position: "relative",
                    display: "inline-block",
                    padding: "2px 1px"
                  }}
                >
                  {conservedPositions.includes(j) && (
                    <motion.span
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 0.3, scale: 1 }}
                      transition={{ delay: 0.8 + j * 0.05 }}
                      style={{
                        position: "absolute",
                        top: "-2px",
                        left: "-1px",
                        right: "-1px",
                        bottom: "-2px",
                        background: "#ffd700",
                        borderRadius: "3px",
                        zIndex: -1
                      }}
                    />
                  )}
                  {base}
                </span>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Comparison statistics */}
      <div style={{
        display: "flex",
        gap: "30px",
        justifyContent: "center",
        marginTop: "20px"
      }}>
        {[
          { value: conservedPositions.length, label: "Conserved site", color: "#00ff88" },
          { value: "78%", label: "Sequence identity", color: "#00d4ff" },
          { value: "3", label: "Compared species", color: "#ff6b9d" }
        ].map((stat, index) => (
          <motion.div 
            key={index}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1 + index * 0.2 }}
            style={{ textAlign: "center" }}
          >
            <div style={{ fontSize: "24px", color: stat.color, fontWeight: "bold" }}>
              {stat.value}
            </div>
            <div style={{ fontSize: "14px", color: "rgba(255, 255, 255, 0.6)" }}>
              {stat.label}
            </div>
          </motion.div>
        ))}
      </div>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        style={{
          textAlign: "center",
          color: "rgba(255, 255, 255, 0.7)",
          maxWidth: "600px",
          lineHeight: "1.6"
        }}
      >
        Highly conserved regions in lncRNA remain highly consistent across different mammals, suggesting that they may have important regulatory functions
      </motion.p>
    </div>
  );
}

// Helper Functions
function getBaseColor(base) {
  const colors = {
    A: "#00ff88",
    T: "#ff5757", 
    C: "#00d4ff",
    G: "#ffd700",
    "-": "#666"
  };
  return colors[base] || "#fff";
}
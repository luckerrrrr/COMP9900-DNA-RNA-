import React from "react";
import { motion } from "framer-motion";

export default function EmbeddingHeatmap() {
  const embeddingData = generateEmbeddingData(5, 5); 
  
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: "15px", 
      width: "100%",
    }}>
      <h3 style={{ fontSize: "28px", color: "#00d4ff", textAlign: "center" }}>
        Embedding heatmap
      </h3>

      {/* Heatmap container */}
      <div style={{
        display: "grid",
        gridTemplateColumns: `repeat(${embeddingData[0].length}, 1fr)`,
        gap: "2px", 
        width: "100%",
        maxWidth: "300px", 
        margin: "0 auto"
      }}>
        {embeddingData.map((row, i) =>
          row.map((value, j) => (
            <motion.div
              key={`${i}-${j}`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: (i * row.length + j) * 0.02 }}
              style={{
                aspectRatio: "1 / 1",
                minHeight: "35px", 
                background: `rgba(0, 212, 255, ${value})`,
                borderRadius: "3px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "9px", 
                color: value > 0.5 ? "#000" : "#fff",
                fontWeight: "bold",
                cursor: "pointer",
                transition: "transform 0.2s"
              }}
              whileHover={{ scale: 1.1 }}
              title={`维度 ${i}-${j}: ${value.toFixed(2)}`}
            >
              {value.toFixed(1)}
            </motion.div>
          ))
        )}
      </div>

      {/* Color Legend */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "10px", 
        marginTop: "10px",
        maxWidth: "280px",
        width: "100%",
        justifyContent: "center"
      }}>
        <span style={{ fontSize: "10px", color: "rgba(255, 255, 255, 0.6)" }}>Low similarity</span>
        <div style={{
          width: "120px", 
          height: "12px",
          background: "linear-gradient(to right, rgba(0, 212, 255, 0.1), rgba(0, 212, 255, 1))",
          borderRadius: "6px"
        }} />
        <span style={{ fontSize: "10px", color: "rgba(255, 255, 255, 0.6)" }}>Hight similarity</span>
      </div>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5 }}
        style={{
          textAlign: "center",
          color: "rgba(255, 255, 255, 0.7)",
          maxWidth: "600px",
          lineHeight: "1.6"
        }}
      >
        Bright blue regions indicate highly similar sequence features, which often correspond to functionally important conserved modules
      </motion.p>
    </div>
  );
}

// Helper Functions
function generateEmbeddingData(rows, cols) {
  return Array.from({ length: rows }, (_, i) =>
    Array.from({ length: cols }, (_, j) => {
      const diagonal = Math.exp(-Math.abs(i - j) * 0.4);
      const block = Math.sin(i * 1) * Math.cos(j * 1) * 0.2 + 0.4;
      const value = Math.max(0, Math.min(1, diagonal + block));
      return value;
    })
  );
}
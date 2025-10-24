import React from "react";
import { motion } from "framer-motion";

export default function UMAPClustering() {
  const clusters = [
    { species: "Human", color: "#00d4ff", points: generateCluster(60, 60, 15, 25) },
    { species: "Mouse", color: "#ff6b9d", points: generateCluster(120, 90, 18, 25) },
    { species: "Chimpanzee", color: "#00ff88", points: generateCluster(90, 120, 14, 25) }
  ];

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: "20px"
    }}>
      <h3 style={{ fontSize: "28px", color: "#00d4ff", textAlign: "center" }}>
        UMAP dimensionality reduction clustering analysis
      </h3>

      <div style={{
        position: "relative",
        width: "300px",
        height: "250px",
        background: "rgba(255, 255, 255, 0.03)",
        borderRadius: "8px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        overflow: "hidden"
      }}>
        {/* Coordinate axis */}
        <div style={{
          position: "absolute",
          left: "30px",
          bottom: "30px",
          width: "calc(100% - 60px)",
          height: "1px",
          background: "rgba(255, 255, 255, 0.2)"
        }} />
        <div style={{
          position: "absolute",
          left: "30px",
          top: "30px",
          width: "1px",
          height: "calc(100% - 60px)",
          background: "rgba(255, 255, 255, 0.2)"
        }} />

        {/* Data Points */}
        {clusters.map((cluster, clusterIdx) =>
          cluster.points.map((point, pointIdx) => (
            <motion.div
              key={`${clusterIdx}-${pointIdx}`}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 0.8, scale: 1 }}
              transition={{
                delay: clusterIdx * 0.5 + pointIdx * 0.01,
                duration: 0.6
              }}
              whileHover={{ scale: 1.5, opacity: 1 }}
              style={{
                position: "absolute",
                left: `${point.x}px`,
                top: `${point.y}px`,
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: cluster.color,
                boxShadow: `0 0 6px ${cluster.color}60`,
                cursor: "pointer"
              }}
            />
          ))
        )}

        {/* Conserved region markers */}
        <motion.div
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 0.3, scale: 1 }}
          transition={{ delay: 2, duration: 1 }}
          style={{
            position: "absolute",
            left: "70px",
            top: "70px",
            width: "60px",
            height: "60px",
            borderRadius: "50%",
            border: "2px dashed #ffd700",
            background: "rgba(255, 215, 0, 0.1)"
          }}
        />
      </div>

      {/* legend */}
      <div style={{ display: "flex", gap: "15px", justifyContent: "center", flexWrap: "wrap" }}>
        {clusters.map((cluster, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 + i * 0.2 }}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <div style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: cluster.color
            }} />
            <span style={{ color: "#fff", fontSize: "12px" }}>{cluster.species}</span>
          </motion.div>
        ))}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.6 }}
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <div style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            border: "1px dashed #ffd700",
            background: "transparent"
          }} />
          <span style={{ color: "#ffd700", fontSize: "12px" }}>Conserved regions</span>
        </motion.div>
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
        LncRNAs from different species form distinct clusters in the embedding space, and overlapping regions (yellow circles) represent highly conserved sequences that maintain similar expression patterns across species
      </motion.p>
    </div>
  );
}

// Helper Functions
function generateCluster(centerX, centerY, spread, count) {
  return Array.from({ length: count }, () => {
    const angle = Math.random() * Math.PI * 2;
    const radius = Math.random() * spread;
    return {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius
    };
  });
}
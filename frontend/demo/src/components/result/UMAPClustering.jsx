import React from "react";
import { motion } from "framer-motion";

export default function UMAPClustering() {
  const images = [
    { src: "/msa_umap.png", label: "GPN-MSA", top: 60, left: 7 },
    { src: "/gpn.png", label: "GPN", top: 60, left: 257 }
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "20px" }}>
      <h3 style={{ fontSize: "28px", color: "#00d4ff", textAlign: "center" }}>
        UMAP dimensionality reduction clustering analysis
      </h3>

      <div style={{
        position: "relative",
        width: "500px",
        height: "300px",
        background: "rgba(255, 255, 255, 0.03)",
        borderRadius: "8px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        overflow: "hidden"
      }}>
        {images.map((img, idx) => (
          <div key={idx} style={{ position: "absolute", top: img.top, left: img.left }}>
            <img src={img.src} alt={img.label} style={{ width: "235px", borderRadius: "6px" }} />
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + idx * 0.2 }}
              style={{ color: "#00d4ff", fontWeight: "700", fontSize: "14px", textAlign: "center" }}
            >
              {img.label}
            </motion.div>
          </div>
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
        The figure above shows the performance of the GPN-MSA model and the GPN model in gene sequence feature extraction.
      </motion.p>
    </div>
  );
}
import React from "react";
import { motion } from "framer-motion";

export default function Module5Results() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, amount: 0.5 }}
      style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%" }}
    >
      <h2>Results & Visualization</h2>
      <div style={{ width: "400px", height: "200px", backgroundColor: "#eee", display: "flex", alignItems: "center", justifyContent: "center", marginTop: "20px" }}>
        UMAP / Heatmap / Pie Chart
      </div>
    </motion.div>
  );
}

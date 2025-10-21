import React from "react";
import { motion } from "framer-motion";

export default function Module2Pipeline() {
  const steps = ["Data Preprocessing", "MSA Alignment", "Tokenisation", "Embedding", "Prediction", "Evaluation"];
  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, amount: 0.5 }}
      style={{ padding: "50px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", height: "100%" }}
    >
      <h2>Pipeline Overview</h2>
      <div style={{ display: "flex", gap: "20px", marginTop: "30px" }}>
        {steps.map((s, i) => (
          <motion.div key={i} whileHover={{ scale: 1.1 }} style={{ padding: "20px", border: "1px solid gray", borderRadius: "8px" }}>
            {s}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

import React from "react";
import { motion } from "framer-motion";

export default function Module3Model() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, amount: 0.5 }}
      style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%" }}
    >
      <h2>Model Animation (GPN & GPN-MSA)</h2>
      <div style={{ width: "500px", height: "200px", backgroundColor: "#eee", display: "flex", alignItems: "center", justifyContent: "center" }}>
        DNA Sequence + Mask Animation
      </div>
    </motion.div>
  );
}

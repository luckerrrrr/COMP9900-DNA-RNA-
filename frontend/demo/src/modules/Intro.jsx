import React from "react";
import { motion } from "framer-motion";

export default function Module1Intro() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.5 }}
      style={{ padding: "50px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%" }}
    >
      <h1>Finding conserved lncRNA regions across species</h1>
      <p>Only 2% of the human genome codes for proteins, but over 98% is noncoding.</p>
      <div style={{ width: "300px", height: "200px", backgroundColor: "#eee", display: "flex", alignItems: "center", justifyContent: "center" }}>
        DNA Illustration
      </div>
    </motion.div>
  );
}

import React from "react";
import { motion } from "framer-motion";

export default function Module4Training() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, amount: 0.5 }}
      style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%" }}
    >
      <h2>Training & Fine-tuning</h2>
      <motion.div initial={{ width: 0 }} animate={{ width: "70%" }} style={{ height: "20px", backgroundColor: "blue", marginTop: "20px", borderRadius: "10px" }} />
      <p>Pretrain → Retrain → Fine-tune</p>
    </motion.div>
  );
}


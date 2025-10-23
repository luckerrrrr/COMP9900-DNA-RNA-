import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Module3GPN from "./GPN.jsx";
import Module3GPNMSA from "./GPNMSA.jsx";

export default function Module3Model() {
  const [mode, setMode] = useState("GPN"); // 'GPN' or 'MSA'

  const toggleMode = () => setMode((prev) => (prev === "GPN" ? "MSA" : "GPN"));

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100vh",
      padding: "25%",
      color: "#fff",
    }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        style={{ textAlign: "center", marginBottom: "40px" }}
      >
        <h1 style={{ fontSize: "clamp(28px, 4vw, 42px)", fontWeight: "bold", marginBottom: "12px" }}>
          Model Principle (GPN & GPN-MSA)
        </h1>
      </motion.div>

      {/* Animation area */}
      <div style={{
        position: "relative",
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-start",
        width: "100%",
        maxWidth: "1200px",
        padding: "0 20px",
      }}>
        <AnimatePresence mode="wait">
          {mode === "GPN" ? (
            <motion.div
              key="GPN"
              initial={{ opacity: 0, x: -100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 100 }}
              transition={{ duration: 0.6 }}
              style={{ width: "100%", display: "flex", justifyContent: "center" }}
            >
              <Module3GPN />
            </motion.div>
          ) : (
            <motion.div
              key="MSA"
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ duration: 0.6 }}
              style={{ width: "100%", display: "flex", justifyContent: "center" }}
            >
              <Module3GPNMSA />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Comparison label */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.8 }}
        style={{ marginTop: "30px", textAlign: "center" }}
      >
        {mode === "GPN" ? (
          <p style={{ fontSize: "18px", color: "rgba(255, 255, 255, 0.8)" }}>
            🧬 <strong>GPN:</strong> Single-species sequence learning to understand DNA contextual patterns
          </p>
        ) : (
          <p style={{ fontSize: "18px", color: "rgba(255, 255, 255, 0.8)" }}>
            🧬 <strong>GPN-MSA:</strong> Cross-species multi-sequence learning to capture conserved gene features
          </p>
        )}
      </motion.div>

      {/* Toggle button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={toggleMode}
        style={{
          marginTop: "40px",
          padding: "12px 24px",
          borderRadius: "12px",
          background: "rgba(0, 212, 255, 0.2)",
          border: "1px solid #00d4ff",
          color: "#00d4ff",
          fontSize: "18px",
          fontWeight: "500",
          cursor: "pointer",
        }}
      >
        Switch to {mode === "GPN" ? "GPN-MSA" : "GPN"}
      </motion.button>
    </div>
  );
}
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Module3GPN from "../components/model/GPN.jsx";
import Module3GPNMSA from "../components/model/GPNMSA.jsx";

export default function Module3Model() {
  const [mode, setMode] = useState("GPN");
  const toggleMode = () => setMode((prev) => (prev === "GPN" ? "MSA" : "GPN"));

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        minHeight: "100vh",
        padding: "40px 20px",
        color: "#fff",
        overflow: "auto",
        marginTop: "100px",
      }}
    >
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        style={{ textAlign: "center", marginBottom: "20px" }}
      >
        <h1
          style={{
            fontSize: "clamp(24px, 3.5vw, 36px)",
            fontWeight: "bold",
            marginBottom: "8px",
          }}
        >
          Model Principle (GPN & GPN-MSA)
        </h1>
      </motion.div>

      {/* Animation area */}
      <div
        style={{
          position: "relative",
          width: "100%",
          maxWidth: "1000px",
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: "16px",
          padding: "30px",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
          border: "2px solid rgba(0, 212, 255, 0.2)",
        }}
      >
        <AnimatePresence mode="wait">
          {mode === "GPN" ? (
            <motion.div
              key="GPN"
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              transition={{ duration: 0.4 }}
              style={{ width: "100%" }}
            >
              <Module3GPN />
            </motion.div>
          ) : (
            <motion.div
              key="MSA"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.4 }}
              style={{ width: "100%" }}
            >
              <Module3GPNMSA />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Info & Button Container */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.6 }}
        style={{
          marginTop: "30px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "16px",
          maxWidth: "800px",
          textAlign: "center",
        }}
      >
        {/* Description */}
        <p
          style={{
            fontSize: "20px",
            color: "rgba(255, 255, 255, 0.85)",
            margin: 0,
            lineHeight: "1.6",
          }}
        >
          {mode === "GPN" ? (
            <>
              <strong>GPN:</strong> Single-species sequence learning to
              understand DNA contextual patterns
            </>
          ) : (
            <>
              <strong>GPN-MSA:</strong> Cross-species multi-sequence learning to
              capture conserved gene features
            </>
          )}
        </p>

        {/* Toggle button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={toggleMode}
          style={{
            padding: "10px 28px",
            borderRadius: "10px",
            background: "rgba(0, 212, 255, 0.15)",
            border: "1.5px solid #00d4ff",
            color: "#00d4ff",
            fontSize: "16px",
            fontWeight: "600",
            cursor: "pointer",
            transition: "all 0.3s ease",
            minWidth: "160px",
            height: "48px",
          }}
        >
          Switch to {mode === "GPN" ? "GPN-MSA" : "GPN"}
        </motion.button>
      </motion.div>
    </div>
  );
}
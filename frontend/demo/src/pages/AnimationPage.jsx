import React from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { FcLineChart } from "react-icons/fc";

export default function AnimationPage() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "linear-gradient(rgba(0, 10, 24, 0.8), rgba(0, 10, 24, 0.8)), url('/dna.png') center/cover fixed no-repeat",
        color: "#fff",
        padding: "40px",
        position: "relative",
      }}
    >
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => navigate("/")}
        style={{
          position: "fixed",
          top: "20px",
          left: "20px",
          padding: "12px 24px",
          background: "rgba(255, 255, 255, 0.1)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.3)",
          borderRadius: "8px",
          color: "#fff",
          cursor: "pointer",
          fontSize: "16px",
          zIndex: 1000,
          fontWeight: "600",
        }}
      >
        Back
      </motion.button>

      <div style={{ maxWidth: "1200px", margin: "0 auto", paddingTop: "80px" }}>
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{
            fontSize: "clamp(32px, 4vw, 48px)",
            marginBottom: "40px",
            textAlign: "center",
          }}
        >
          <FcLineChart /> Animated Explanation
        </motion.h1>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          style={{
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            borderRadius: "16px",
            padding: "40px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <p style={{ fontSize: "18px", lineHeight: 1.8 }}></p>
        </motion.div>
      </div>
    </div>
  );
}

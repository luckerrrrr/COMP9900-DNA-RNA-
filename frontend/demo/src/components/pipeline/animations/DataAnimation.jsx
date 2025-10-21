import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function DataAnimation() {
  const [stage, setStage] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  // Auto advance stages
  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      setStage((prev) => {
        if (prev === 2) {
          setIsPlaying(false);
          return 2;
        }
        return prev + 1;
      });
    }, 4000);
    return () => clearInterval(timer);
  }, [isPlaying]);

  // Replay function
  const handleReplay = () => {
    setStage(0);
    setIsPlaying(true);
  };

  return (
    <div
      style={{
        width: "100%",
        height: "300px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "30px",
      }}
    >
      {/* Stage indicator with replay button */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          width: "100%",
          maxWidth: "600px",
          marginBottom: "10px",
        }}
      >
        <div style={{ fontSize: "30px", color: "#00d4ff" }}>
          {stage === 0 && "Raw DNA Sequence"}
          {stage === 1 && "Cleaning & Filtering"}
          {stage === 2 && "512bp Windows"}
        </div>

        {/* Replay button - shows when animation is paused */}
        {!isPlaying && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleReplay}
            style={{
              background: "rgba(0, 212, 255, 0.2)",
              border: "1px solid #00d4ff",
              color: "#00d4ff",
              padding: "8px 20px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "30px",
              fontWeight: "500",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span>Replay</span>
          </motion.button>
        )}
      </div>

      {/* Stage 0: Raw sequence */}
      {stage === 0 && <RawSequence />}

      {/* Stage 1: Cleaning */}
      {stage === 1 && <CleaningSequence />}

      {/* Stage 2: Windowing */}
      {stage === 2 && <WindowingSequence />}
    </div>
  );
}

// Raw DNA sequence
function RawSequence() {
  const sequence = "ATCGATCGNNATCGATCG...NNATCG";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      style={{
        fontFamily: "monospace",
        fontSize: "30px",
        letterSpacing: "4px",
        color: "#fff",
        padding: "20px",
        background: "rgba(255, 255, 255, 0.05)",
        borderRadius: "8px",
        border: "1px solid rgba(255, 255, 255, 0.2)",
      }}
    >
      {sequence.split("").map((base, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.05 }}
          style={{
            color: base === "N" ? "#ff5757" : getBaseColor(base),
          }}
        >
          {base}
        </motion.span>
      ))}
    </motion.div>
  );
}

// Cleaning animation
function CleaningSequence() {
  const [cleaned, setCleaned] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setCleaned(true), 1000);
    return () => clearTimeout(timer);
  }, []);

  const dirtySeq = "ATCGATCGNNATCGATCG...NNATCG";
  const cleanSeq = "ATCGATCG--ATCGATCG...--ATCG";

  return (
    <div style={{ textAlign: "center" }}>
      <motion.div
        animate={{ opacity: cleaned ? 0.3 : 1 }}
        style={{
          fontFamily: "monospace",
          fontSize: "30px",
          letterSpacing: "4px",
          color: "#fff",
          padding: "20px",
          background: "rgba(255, 255, 255, 0.05)",
          borderRadius: "8px",
          border: "1px solid rgba(255, 255, 255, 0.2)",
          marginBottom: "20px",
        }}
      >
        {dirtySeq.split("").map((base, i) => (
          <span
            key={i}
            style={{
              color: base === "N" ? "#ff5757" : getBaseColor(base),
              textDecoration: cleaned && base === "N" ? "line-through" : "none",
            }}
          >
            {base}
          </span>
        ))}
      </motion.div>

      {cleaned && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            fontFamily: "monospace",
            fontSize: "30px",
            letterSpacing: "4px",
            color: "#00ff88",
            padding: "20px",
            background: "rgba(0, 255, 136, 0.1)",
            borderRadius: "8px",
            border: "2px solid #00ff88",
          }}
        >
          {cleanSeq.split("").map((base, i) => (
            <span key={i} style={{ color: getBaseColor(base) }}>
              {base}
            </span>
          ))}
        </motion.div>
      )}
    </div>
  );
}

// Windowing animation
function WindowingSequence() {
  const fullSeq = "ATCGATCGATCGATCGATCGATCGATCG...";

  return (
    <div style={{ position: "relative", width: "100%", maxWidth: "600px" }}>
      {/* Full sequence */}
      <div
        style={{
          fontFamily: "monospace",
          fontSize: "30px",
          letterSpacing: "2px",
          color: "rgba(255, 255, 255, 0.3)",
          padding: "15px",
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: "8px",
        }}
      >
        {fullSeq}
      </div>

      {/* Sliding window */}
      <motion.div
        animate={{
          x: [0, 500,0],
        }}
        transition={{
          duration: 3,
          repeat: 2,
          ease: "easeInOut",
        }}
        style={{
          position: "absolute",
          top: "0",
          left: "0",
          width: "150px",
          height: "100%",
          border: "2px solid #00d4ff",
          borderRadius: "8px",
          boxShadow: "0 0 20px rgba(0, 212, 255, 0.5)",
          pointerEvents: "none",
        }}
      />

      {/* Label */}
    </div>
  );
}

// Helper: Get color for DNA base
function getBaseColor(base) {
  const colors = {
    A: "#00ff88", // Green
    T: "#ff5757", // Red
    C: "#00d4ff", // Blue
    G: "#ffd700", // Yellow
    ".": "#888", // Dots
    "-": "#666", // Gap
  };
  return colors[base] || "#fff";
}

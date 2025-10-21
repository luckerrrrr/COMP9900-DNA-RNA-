import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function TokenAnimation() {
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
        height: "400px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "20px",
      }}
    >
      {/* Stage indicator with replay button */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          width: "100%",
          maxWidth: "700px",
          marginBottom: "10px",
        }}
      >
        <div style={{ fontSize: "30px", color: "#00d4ff" }}>
          {stage === 0 && "Original Sequence"}
          {stage === 1 && "Encoding Process"}
          {stage === 2 && "Token Vectors"}
        </div>

        {/* Replay button */}
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
              fontSize: "20px",
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

      {/* Stage description */}
      <div
        style={{
          fontSize: "30px",
          color: "rgba(255, 255, 255, 0.6)",
          textAlign: "center",
          maxWidth: "700px",
          minHeight: "40px",
        }}
      >
        {stage === 0 &&
          "DNA bases (A, T, C, G) need to be converted into numerical format"}
        {stage === 1 &&
          "Each base is assigned a unique token ID (A=0, T=1, C=2, G=3)"}
        {stage === 2 &&
          "Token vectors enable the model to process genetic sequences mathematically"}
      </div>

      {/* Animation content */}
      <div
        style={{
          width: "100%",
          maxWidth: "700px",
          display: "flex",
          justifyContent: "center",
        }}
      >
        {stage === 0 && <OriginalSequence />}
        {stage === 1 && <EncodingProcess />}
        {stage === 2 && <TokenVectors />}
      </div>
    </div>
  );
}

// Stage 0: Original sequence with letters
function OriginalSequence() {
  const bases = ["A", "T", "C", "G", "A", "T", "C", "G"];

  return (
    <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
      {bases.map((base, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, scale: 0.5, rotateY: -90 }}
          animate={{ opacity: 1, scale: 1, rotateY: 0 }}
          transition={{ delay: i * 0.1, duration: 0.5 }}
          style={{
            width: "70px",
            height: "90px",
            borderRadius: "12px",
            background: getBaseBackground(base),
            border: `2px solid ${getBaseColor(base)}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "32px",
            fontWeight: "bold",
            color: getBaseColor(base),
            boxShadow: `0 4px 20px ${getBaseColor(base)}40`,
          }}
        >
          {base}
        </motion.div>
      ))}
    </div>
  );
}

// Stage 1: Flipping cards to show tokens
function EncodingProcess() {
  const bases = ["A", "T", "C", "G", "A", "T", "C", "G"];
  const [flipped, setFlipped] = useState([]);

  useEffect(() => {
    bases.forEach((_, i) => {
      setTimeout(() => {
        setFlipped((prev) => [...prev, i]);
      }, i * 200);
    });
  }, []);

  return (
    <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
      {bases.map((base, i) => (
        <FlipCard
          key={i}
          base={base}
          token={getTokenValue(base)}
          isFlipped={flipped.includes(i)}
        />
      ))}
    </div>
  );
}

// Flip card component with 3D effect
function FlipCard({ base, token, isFlipped }) {
  return (
    <div
      style={{
        width: "70px",
        height: "90px",
        perspective: "1000px",
      }}
    >
      <motion.div
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ duration: 0.6, ease: "easeInOut" }}
        style={{
          width: "100%",
          height: "100%",
          position: "relative",
          transformStyle: "preserve-3d",
        }}
      >
        {/* Front - Letter */}
        <div
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            backfaceVisibility: "hidden",
            borderRadius: "12px",
            background: getBaseBackground(base),
            border: `2px solid ${getBaseColor(base)}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "32px",
            fontWeight: "bold",
            color: getBaseColor(base),
            boxShadow: `0 4px 20px ${getBaseColor(base)}40`,
          }}
        >
          {base}
        </div>

        {/* Back - Number */}
        <div
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            backfaceVisibility: "hidden",
            transform: "rotateY(180deg)",
            borderRadius: "12px",
            background: "rgba(255, 255, 255, 0.1)",
            border: "2px solid rgba(255, 255, 255, 0.3)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 20px rgba(0, 212, 255, 0.3)",
          }}
        >
          <div
            style={{
              fontSize: "30px",
              color: "rgba(255, 255, 255, 0.6)",
              marginBottom: "4px",
            }}
          >
            {base}→{token}
          </div>
          <div
            style={{
              fontSize: "32px",
              fontWeight: "bold",
              color: "#00d4ff",
            }}
          >
            {token}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

// Stage 2: Token vectors with color bars
function TokenVectors() {
  const bases = ["A", "T", "C", "G", "A", "T", "C", "G"];

  return (
    <div style={{ width: "100%" }}>
      {/* Tokens with numbers */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          marginBottom: "20px",
        }}
      >
        {bases.map((base, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            style={{
              width: "70px",
              height: "90px",
              borderRadius: "12px",
              background: "rgba(255, 255, 255, 0.1)",
              border: "2px solid rgba(255, 255, 255, 0.3)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Number */}
            <div
              style={{
                fontSize: "28px",
                fontWeight: "bold",
                color: "#fff",
                marginBottom: "8px",
                zIndex: 2,
              }}
            >
              {getTokenValue(base)}
            </div>

            {/* Color bar */}
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: "40%" }}
              transition={{ delay: 1 + i * 0.1, duration: 0.4 }}
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                background: getBaseColor(base),
                opacity: 0.6,
                zIndex: 1,
              }}
            />

            {/* Base label */}
            <div
              style={{
                fontSize: "20px",
                color: getBaseColor(base),
                fontWeight: "bold",
                zIndex: 2,
              }}
            >
              {base}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Encoding table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 2 }}
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "16px",
          padding: "16px",
          background: "rgba(255, 255, 255, 0.05)",
          borderRadius: "12px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        {["A", "T", "C", "G"].map((base) => (
          <div
            key={base}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "30px",
            }}
          >
            <span style={{ color: getBaseColor(base), fontWeight: "bold" }}>
              {base}
            </span>
            <span style={{ color: "rgba(255, 255, 255, 0.5)" }}>→</span>
            <span style={{ color: "#00d4ff", fontWeight: "bold" }}>
              {getTokenValue(base)}
            </span>
          </div>
        ))}
      </motion.div>
    </div>
  );
}

// Helper functions
function getBaseColor(base) {
  const colors = {
    A: "#00ff88", // Green
    T: "#ff5757", // Red
    C: "#00d4ff", // Blue
    G: "#ffd700", // Yellow
  };
  return colors[base] || "#fff";
}

function getBaseBackground(base) {
  const backgrounds = {
    A: "rgba(0, 255, 136, 0.15)",
    T: "rgba(255, 87, 87, 0.15)",
    C: "rgba(0, 212, 255, 0.15)",
    G: "rgba(255, 215, 0, 0.15)",
  };
  return backgrounds[base] || "rgba(255, 255, 255, 0.1)";
}

function getTokenValue(base) {
  const tokens = {
    A: 0,
    T: 1,
    C: 2,
    G: 3,
  };
  return tokens[base];
}

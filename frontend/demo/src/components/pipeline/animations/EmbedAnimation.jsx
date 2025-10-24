import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function EmbedAnimation() {
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
    }, 4500);
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
        gap: "15px",
      }}
    >
      {/* Stage indicator with replay button */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          width: "100%",
          maxWidth: "800px",
        }}
      >
        <div style={{ fontSize: "30px", color: "#00d4ff" }}>
          {stage === 0 && "Token Sequence (1D)"}
          {stage === 1 && "Vector Expansion (2D)"}
          {stage === 2 && "Embedding Matrix (Heatmap)"}
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
            }}
          >
            <span>Replay</span>
          </motion.button>
        )}
      </div>

      {/* Stage description */}
      <div
        style={{
          fontSize: "20px",
          color: "rgba(255, 255, 255, 0.6)",
          textAlign: "center",
          maxWidth: "700px",
          minHeight: "10px",
        }}
      >
        {stage === 0 &&
          "Token IDs are represented as a one-dimensional sequence"}
        {stage === 1 &&
          "Each token is transformed into a high-dimensional vector (embedding)"}
        {stage === 2 &&
          "The embedding matrix captures semantic relationships between tokens"}
      </div>

      {/* Animation content */}
      <div
        style={{
          width: "100%",
          maxWidth: "800px",
          display: "flex",
          justifyContent: "center",
        }}
      >
        {stage === 0 && <TokenSequence />}
        {stage === 1 && <VectorExpansion />}
        {stage === 2 && <EmbeddingMatrix />}
      </div>
    </div>
  );
}

// Stage 0: Token sequence (1D)
function TokenSequence() {
  const tokens = [0, 1, 2, 3, 0, 1, 2, 3];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
        {tokens.map((token, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            style={{
              width: "60px",
              height: "60px",
              borderRadius: "10px",
              background: "rgba(0, 212, 255, 0.15)",
              border: "2px solid #00d4ff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "24px",
              fontWeight: "bold",
              color: "#00d4ff",
              position: "relative",
            }}
          >
            {token}
            {/* Arrow below */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 + i * 0.1 }}
              style={{
                position: "absolute",
                bottom: "-25px",
                fontSize: "16px",
                color: "#00d4ff",
              }}
            >
              ↓
            </motion.div>
          </motion.div>
        ))}
      </div>

      {/* Label */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2 }}
        style={{
          textAlign: "center",
          fontSize: "30px",
          color: "rgba(255, 255, 255, 0.5)",
          marginTop: "20px",
        }}
      >
        8 tokens, 1 dimension
      </motion.div>
    </div>
  );
}

// Stage 1: Vector expansion showing one token expanding
function VectorExpansion() {
  const tokens = [0, 1, 2, 3, 0, 1, 2, 3];
  const focusIndex = 0; // Focus on first token
  const embeddingDim = 4;
  const vectorValues = [0.2, 0.5, 0.1, 0.8];

  return (
    <div style={{ display: "flex", gap: "40px", alignItems: "flex-start" }}>
      {/* Token list (smaller, faded) */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div
          style={{
            fontSize: "20px",
            color: "rgba(255, 255, 255, 0.5)",
            marginBottom: "8px",
          }}
        >
          Tokens:
        </div>
        {tokens.map((token, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: i === focusIndex ? 1 : 0.3 }}
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "8px",
              background:
                i === focusIndex
                  ? "rgba(0, 212, 255, 0.2)"
                  : "rgba(255, 255, 255, 0.05)",
              border:
                i === focusIndex
                  ? "2px solid #00d4ff"
                  : "1px solid rgba(255, 255, 255, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "30px",
              fontWeight: "bold",
              color: i === focusIndex ? "#00d4ff" : "#666",
            }}
          >
            {token}
          </motion.div>
        ))}
      </div>

      {/* Arrow */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5 }}
        style={{
          fontSize: "32px",
          color: "#00d4ff",
          alignSelf: "center",
        }}
      >
        →
      </motion.div>

      {/* Expanded vector */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div
          style={{
            fontSize: "20px",
            color: "rgba(255, 255, 255, 0.5)",
            marginBottom: "8px",
          }}
        >
          Embedding Vector (dim={embeddingDim}):
        </div>
        {vectorValues.map((value, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -20, scaleX: 0 }}
            animate={{ opacity: 1, x: 0, scaleX: 1 }}
            transition={{ delay: 1 + i * 0.15 }}
            style={{
              height: "40px",
              minWidth: "200px",
              borderRadius: "8px",
              background: `linear-gradient(to right, 
                ${getHeatmapColor(value)} ${value * 100}%, 
                rgba(255, 255, 255, 0.05) ${value * 100}%)`,
              border: "1px solid rgba(255, 255, 255, 0.2)",
              display: "flex",
              alignItems: "center",
              padding: "0 12px",
              fontSize: "20px",
              color: "#fff",
              fontFamily: "monospace",
            }}
          >
            <span style={{ opacity: 0.6 }}>dim[{i}]:</span>
            <span style={{ marginLeft: "8px", fontWeight: "bold" }}>
              {value.toFixed(2)}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// Stage 2: Full embedding matrix heatmap
function EmbeddingMatrix() {
  const tokens = [0, 1, 2, 3, 0, 1, 2, 3];
  const embeddingDim = 6;

  // Generate mock embedding values
  const getEmbeddingValue = (tokenIdx, dimIdx) => {
    // Deterministic but varied values
    return ((tokenIdx * 37 + dimIdx * 23) % 100) / 100;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Header labels */}
      <div style={{ display: "flex", gap: "2px", paddingLeft: "60px" }}>
        {tokens.map((token, i) => (
          <div
            key={i}
            style={{
              width: "60px",
              textAlign: "center",
              fontSize: "20px",
              color: "rgba(255, 255, 255, 0.5)",
            }}
          >
            T{i}
          </div>
        ))}
      </div>

      {/* Heatmap rows */}
      {[...Array(embeddingDim)].map((_, dimIdx) => (
        <motion.div
          key={dimIdx}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: dimIdx * 0.1 }}
          style={{ display: "flex", gap: "2px", alignItems: "center" }}
        >
          {/* Row label */}
          <div
            style={{
              width: "50px",
              fontSize: "20px",
              color: "rgba(255, 255, 255, 0.5)",
              textAlign: "right",
              paddingRight: "10px",
            }}
          >
            D{dimIdx}
          </div>

          {/* Heatmap cells */}
          {tokens.map((token, tokenIdx) => {
            const value = getEmbeddingValue(tokenIdx, dimIdx);
            return (
              <motion.div
                key={tokenIdx}
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5 + tokenIdx * 0.05 + dimIdx * 0.05 }}
                whileHover={{ scale: 1.1, zIndex: 10 }}
                style={{
                  width: "60px",
                  height: "40px",
                  borderRadius: "6px",
                  background: getHeatmapColor(value),
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "20px",
                  color:
                    value > 0.5
                      ? "rgba(0, 0, 0, 0.7)"
                      : "rgba(255, 255, 255, 0.7)",
                  fontFamily: "monospace",
                  cursor: "pointer",
                }}
                title={`Token ${tokenIdx}, Dim ${dimIdx}: ${value.toFixed(2)}`}
              >
                {value.toFixed(1)}
              </motion.div>
            );
          })}
        </motion.div>
      ))}

      {/* Color scale legend */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 2 }}
        style={{
          marginTop: "16px",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          paddingLeft: "60px",
        }}
      >
        <span style={{ fontSize: "20px", color: "rgba(255, 255, 255, 0.5)" }}>
          Value:
        </span>
        <div
          style={{
            width: "200px",
            height: "20px",
            borderRadius: "4px",
            background:
              "linear-gradient(to right, #1e3a5f, #2563eb, #60a5fa, #93c5fd, #dbeafe)",
            border: "1px solid rgba(255, 255, 255, 0.2)",
          }}
        />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            width: "200px",
            fontSize: "20px",
            color: "rgba(255, 255, 255, 0.5)",
          }}
        >
          <span>0.0</span>
          <span>1.0</span>
        </div>
      </motion.div>
    </div>
  );
}

// Helper: Get heatmap color based on value (0-1)
function getHeatmapColor(value) {
  // Blue gradient
  const colors = [
    "#1e3a5f", // 0.0 - dark blue
    "#2563eb", // 0.25
    "#60a5fa", // 0.5
    "#93c5fd", // 0.75
    "#dbeafe", // 1.0 - light blue
  ];

  const index = Math.floor(value * (colors.length - 1));
  const nextIndex = Math.min(index + 1, colors.length - 1);
  const ratio = value * (colors.length - 1) - index;

  // Simple interpolation between two colors
  return colors[index];
}

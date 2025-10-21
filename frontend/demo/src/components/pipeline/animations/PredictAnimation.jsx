import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function PredictAnimation() {
  const [stage, setStage] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  // Auto advance stages
  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      setStage((prev) => {
        if (prev === 3) {
          setIsPlaying(false);
          return 3;
        }
        return prev + 1;
      });
    }, 3500);
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
          maxWidth: "800px",
          marginBottom: "10px",
        }}
      >
        <div style={{ fontSize: "30px", color: "#00d4ff" }}>
          {stage === 0 && "Original Sequence"}
          {stage === 1 && "Masking Bases"}
          {stage === 2 && "Model Predicting..."}
          {stage === 3 && "Prediction Complete"}
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
          fontSize: "20px",
          color: "rgba(255, 255, 255, 0.6)",
          textAlign: "center",
          maxWidth: "700px",
          minHeight: "40px",   
        }}
      >
        {stage === 0 && "The model learns from complete DNA sequences"}
        {stage === 1 && "Random bases are masked to create a prediction task"}
        {stage === 2 && "The model analyzes context to predict masked bases"}
        {stage === 3 &&
          "Predicted bases are compared with the original sequence"}
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
        {stage === 0 && <OriginalSequence />}
        {stage === 1 && <MaskedSequence />}
        {stage === 2 && <PredictingSequence />}
        {stage === 3 && <RecoveredSequence />}
      </div>
    </div>
  );
}

// Original sequence data
const originalBases = [
  "A",
  "T",
  "C",
  "G",
  "A",
  "T",
  "C",
  "G",
  "A",
  "T",
  "C",
  "G",
];
const maskedIndices = [2, 5, 7]; // Positions to mask

// Stage 0: Original complete sequence
function OriginalSequence() {
  return (
    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
      {originalBases.map((base, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: i * 0.1 }}
          style={{
            width: "60px",
            height: "70px",
            borderRadius: "10px",
            background: getBaseBackground(base),
            border: `2px solid ${getBaseColor(base)}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "28px",
            fontWeight: "bold",
            color: getBaseColor(base),
            boxShadow: `0 4px 15px ${getBaseColor(base)}30`,
          }}
        >
          {base}
        </motion.div>
      ))}
    </div>
  );
}

// Stage 1: Masked sequence
function MaskedSequence() {
  return (
    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
      {originalBases.map((base, i) => {
        const isMasked = maskedIndices.includes(i);
        return (
          <motion.div
            key={i}
            initial={{ opacity: 1 }}
            animate={{
              opacity: 1,
              scale: isMasked ? [1, 1.1, 1] : 1,
            }}
            transition={{
              delay: isMasked ? 0.5 + maskedIndices.indexOf(i) * 0.3 : 0,
              duration: 0.5,
            }}
            style={{
              width: "60px",
              height: "70px",
              borderRadius: "10px",
              background: isMasked
                ? "rgba(100, 100, 100, 0.3)"
                : getBaseBackground(base),
              border: isMasked
                ? "2px dashed rgba(255, 255, 255, 0.3)"
                : `2px solid ${getBaseColor(base)}`,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              fontSize: isMasked ? "32px" : "28px",
              fontWeight: "bold",
              color: isMasked ? "#888" : getBaseColor(base),
              position: "relative",
            }}
          >
            {isMasked ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 + maskedIndices.indexOf(i) * 0.3 }}
              >
                ?
                <div
                  style={{
                    fontSize: "10px",
                    color: "#666",
                    marginTop: "4px",
                  }}
                >
                  [MASK]
                </div>
              </motion.div>
            ) : (
              base
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

// Stage 2: Model predicting (with thinking animation)
function PredictingSequence() {
  return (
    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
      {originalBases.map((base, i) => {
        const isMasked = maskedIndices.includes(i);
        return (
          <motion.div
            key={i}
            style={{
              width: "60px",
              height: "70px",
              borderRadius: "10px",
              background: isMasked
                ? "rgba(0, 212, 255, 0.1)"
                : getBaseBackground(base),
              border: isMasked
                ? "2px solid #00d4ff"
                : `2px solid ${getBaseColor(base)}`,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "28px",
              fontWeight: "bold",
              color: isMasked ? "#00d4ff" : getBaseColor(base),
              position: "relative",
              overflow: "hidden",
            }}
          >
            {isMasked ? (
              <>
                {/* Thinking animation */}
                <motion.div
                  animate={{
                    opacity: [0.3, 1, 0.3],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  style={{ fontSize: "32px" }}
                >
                  ?
                </motion.div>

                {/* Scanning line */}
                <motion.div
                  animate={{
                    y: [-35, 35],
                  }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                  style={{
                    position: "absolute",
                    width: "100%",
                    height: "2px",
                    background:
                      "linear-gradient(to right, transparent, #00d4ff, transparent)",
                  }}
                />

                {/* Processing text */}
                <div
                  style={{
                    fontSize: "8px",
                    color: "#00d4ff",
                    marginTop: "4px",
                  }}
                >
                  analyzing...
                </div>
              </>
            ) : (
              base
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

// Stage 3: Recovered sequence with predictions
function RecoveredSequence() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Sequence */}
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        {originalBases.map((base, i) => {
          const isMasked = maskedIndices.includes(i);
          const maskOrder = maskedIndices.indexOf(i);

          return (
            <motion.div
              key={i}
              initial={{ scale: 1 }}
              animate={
                isMasked
                  ? {
                      scale: [1, 1.15, 1],
                    }
                  : {}
              }
              transition={{
                delay: isMasked ? maskOrder * 0.4 : 0,
                duration: 0.5,
              }}
              style={{
                width: "60px",
                height: "70px",
                borderRadius: "10px",
                background: isMasked
                  ? getBaseBackground(base)
                  : getBaseBackground(base),
                border: isMasked
                  ? `3px solid ${getBaseColor(base)}`
                  : `2px solid ${getBaseColor(base)}`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "28px",
                fontWeight: "bold",
                color: getBaseColor(base),
                position: "relative",
                boxShadow: isMasked
                  ? `0 0 20px ${getBaseColor(base)}60`
                  : `0 4px 15px ${getBaseColor(base)}30`,
              }}
            >
              {isMasked ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: maskOrder * 0.4 }}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                  }}
                >
                  {base}
                  {/* Checkmark */}
                  <motion.div
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: maskOrder * 0.4 + 0.3 }}
                    style={{
                      position: "absolute",
                      top: "-8px",
                      right: "-8px",
                      width: "20px",
                      height: "20px",
                      borderRadius: "50%",
                      background: "#00ff88",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "20px",
                      color: "#000",
                    }}
                  >
                    ✓
                  </motion.div>
                </motion.div>
              ) : (
                base
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Prediction accuracy */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5 }}
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "20px",
          padding: "16px",
          background: "rgba(0, 255, 136, 0.1)",
          border: "1px solid rgba(0, 255, 136, 0.3)",
          borderRadius: "12px",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "20px", color: "rgba(255, 255, 255, 0.5)" }}>
            Masked Bases
          </div>
          <div
            style={{ fontSize: "24px", color: "#00d4ff", fontWeight: "bold" }}
          >
            {maskedIndices.length}
          </div>
        </div>
        <div
          style={{
            width: "1px",
            background: "rgba(255, 255, 255, 0.2)",
          }}
        />
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "20px", color: "rgba(255, 255, 255, 0.5)" }}>
            Correctly Predicted
          </div>
          <div
            style={{ fontSize: "24px", color: "#00ff88", fontWeight: "bold" }}
          >
            {maskedIndices.length}/{maskedIndices.length}
          </div>
        </div>
        <div
          style={{
            width: "1px",
            background: "rgba(255, 255, 255, 0.2)",
          }}
        />
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "20px", color: "rgba(255, 255, 255, 0.5)" }}>
            Accuracy
          </div>
          <div
            style={{ fontSize: "24px", color: "#00ff88", fontWeight: "bold" }}
          >
            100%
          </div>
        </div>
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

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { FcPrivacy } from "react-icons/fc";
import {
  IoSnowOutline,
} from "react-icons/io5";
import { TbMathFunction } from "react-icons/tb";

export default function ClassificationAnimation() {
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

  const sequence = ["A", "T", "C", "G", "A", "T", "C", "G"];

  return (
    <div
      style={{
        width: "100%",
        height: "600px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        gap: "20px",
        padding: "20px",
        overflow: "hidden",
      }}
    >
      {/* Stage indicator with replay button */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          width: "100%",
          maxWidth: "900px",
        }}
      >
        <div style={{ fontSize: "20px", color: "#00d4ff", fontWeight: "500" }}>
          {stage === 0 && "Stage 1: Input DNA Sequence"}
          {stage === 1 && "Stage 2: Feature Extraction (Frozen Encoder)"}
          {stage === 2 && "Stage 3: Linear Classification"}
          {stage === 3 && "Stage 4: Probability Output"}
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
              padding: "6px 16px",
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

      {/* Main content - compact vertical layout */}
      <div
        style={{
          width: "100%",
          maxWidth: "900px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          overflowY: "auto",
          padding: "10px",
        }}
      >
        {/* Stage 1: Input Sequence */}
        <motion.div
          animate={{
            scale: stage === 0 ? 1.02 : 1,
            borderColor: stage === 0 ? "#00ff88" : "rgba(0, 255, 136, 0.3)",
            opacity: stage >= 0 ? 1 : 0.5,
          }}
          style={{
            padding: "12px 16px",
            border: "2px solid rgba(0, 255, 136, 0.3)",
            borderRadius: "10px",
            background:
              stage === 0
                ? "rgba(0, 255, 136, 0.08)"
                : "rgba(0, 255, 136, 0.03)",
            transition: "all 0.3s ease",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "10px",
            }}
          >
            <div style={{ fontSize: "24px" }}>🧬</div>
            <div>
              <div
                style={{
                  fontSize: "16px",
                  fontWeight: "bold",
                  color: "#00ff88",
                }}
              >
                Input Sequence
              </div>
              <div
                style={{
                  fontSize: "16px",
                  color: "rgba(255, 255, 255, 0.5)",
                }}
              >
                512bp DNA window
              </div>
            </div>
          </div>

          {/* Sequence display - compact */}
          <div
            style={{
              display: "flex",
              gap: "4px",
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            {sequence.map((base, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0 }}
                animate={{
                  opacity: 1,
                  scale: 1,
                }}
                transition={{ delay: stage === 0 ? i * 0.04 : 0 }}
                style={{
                  width: "28px",
                  height: "28px",
                  background: getBaseBackground(base),
                  border: `2px solid ${getBaseColor(base)}`,
                  borderRadius: "5px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "13px",
                  fontWeight: "bold",
                  color: getBaseColor(base),
                }}
              >
                {base}
              </motion.div>
            ))}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                fontSize: "14px",
                color: "rgba(255, 255, 255, 0.4)",
              }}
            >
              ...
            </div>
          </div>
        </motion.div>

        {/* Arrow */}
        <motion.div
          animate={{
            opacity: stage >= 1 ? 1 : 0.3,
            y: stage >= 1 ? [0, 3, 0] : 0,
          }}
          transition={{ duration: 1, repeat: Infinity }}
          style={{
            textAlign: "center",
            fontSize: "18px",
            color: "#00d4ff",
            margin: "-4px 0",
          }}
        >
          ↓
        </motion.div>

        {/* Stage 2: Encoder */}
        <motion.div
          animate={{
            scale: stage === 1 ? 1.02 : 1,
            borderColor: stage === 1 ? "#00d4ff" : "rgba(0, 212, 255, 0.3)",
            opacity: stage >= 1 ? 1 : 0.5,
          }}
          style={{
            padding: "12px 16px",
            border: "2px solid rgba(0, 212, 255, 0.3)",
            borderRadius: "10px",
            background:
              stage === 1
                ? "rgba(0, 212, 255, 0.08)"
                : "rgba(0, 212, 255, 0.03)",
            position: "relative",
            transition: "all 0.3s ease",
          }}
        >
          {/* Frozen badge */}
          <div
            style={{
              position: "absolute",
              top: "8px",
              right: "8px",
              padding: "3px 10px",
              background: "#00d4ff",
              borderRadius: "10px",
              fontSize: "16px",
              fontWeight: "bold",
              color: "#000",
            }}
          >
            <FcPrivacy /> FROZEN
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "10px",
            }}
          >
            <IoSnowOutline size={24} color="#00d4ff" />
            <div>
              <div
                style={{
                  fontSize: "16px",
                  fontWeight: "bold",
                  color: "#00d4ff",
                }}
              >
                Frozen GPN Encoder
              </div>
              <div
                style={{
                  fontSize: "16px",
                  color: "rgba(255, 255, 255, 0.5)",
                }}
              >
                Extract conservation features
              </div>
            </div>
          </div>

          {/* Feature vector - compact */}
          <div
            style={{
              display: "flex",
              gap: "2px",
              justifyContent: "center",
              alignItems: "flex-end",
              height: "40px",
            }}
          >
            {Array.from({ length: 20 }).map((_, i) => (
              <motion.div
                key={i}
                initial={{ height: 0 }}
                animate={{
                  height: stage >= 1 ? `${Math.random() * 35 + 5}px` : "0px",
                }}
                transition={{
                  delay: stage === 1 ? i * 0.02 : 0,
                  duration: 0.3,
                }}
                style={{
                  width: "14px",
                  background: "#00d4ff",
                  borderRadius: "2px 2px 0 0",
                }}
              />
            ))}
          </div>
          <div
            style={{
              textAlign: "center",
              fontSize: "20px",
              color: "rgba(255, 255, 255, 0.4)",
              marginTop: "6px",
            }}
          >
            768-dim (pooled embedding)
          </div>
          {stage >= 1 && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              style={{
                marginTop: "8px",
                padding: "6px 12px",
                background: "rgba(0, 212, 255, 0.1)",
                borderRadius: "6px",
                fontSize: "20px",
                fontFamily: "monospace",
                color: "#00d4ff",
                textAlign: "center",
              }}
            >
              z = (1/L)Σh<sub>i</sub> or z = h<sub>CLS</sub>
            </motion.div>
          )}
        </motion.div>

        {/* Arrow */}
        <motion.div
          animate={{
            opacity: stage >= 2 ? 1 : 0.3,
            y: stage >= 2 ? [0, 3, 0] : 0,
          }}
          transition={{ duration: 1, repeat: Infinity }}
          style={{
            textAlign: "center",
            fontSize: "18px",
            color: "#00d4ff",
            margin: "-4px 0",
          }}
        >
          ↓
        </motion.div>

        {/* Stage 3: Linear Classifier */}
        <motion.div
          animate={{
            scale: stage === 2 ? 1.02 : 1,
            borderColor: stage === 2 ? "#ffd700" : "rgba(255, 215, 0, 0.3)",
            opacity: stage >= 2 ? 1 : 0.5,
          }}
          style={{
            padding: "12px 16px",
            border: "2px solid rgba(255, 215, 0, 0.3)",
            borderRadius: "10px",
            background:
              stage === 2
                ? "rgba(255, 215, 0, 0.08)"
                : "rgba(255, 215, 0, 0.03)",
            position: "relative",
            transition: "all 0.3s ease",
          }}
        >
          {/* Trainable badge */}
          <div
            style={{
              position: "absolute",
              top: "8px",
              right: "8px",
              padding: "3px 10px",
              background: "#ffd700",
              borderRadius: "10px",
              fontSize: "14px",
              fontWeight: "bold",
              color: "#000",
            }}
          >
            🔥 TRAINABLE
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "10px",
            }}
          >
            <TbMathFunction size={24} color="#ffd700" />

            <div>
              <div
                style={{
                  fontSize: "16px",
                  fontWeight: "bold",
                  color: "#ffd700",
                }}
              >
                Linear Classifier
              </div>
              <div
                style={{
                  fontSize: "16px",
                  color: "rgba(255, 255, 255, 0.5)",
                }}
              >
                768-dim → 2-dim classification
              </div>
            </div>
          </div>

          {/* Formula */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: stage >= 2 ? 1 : 0.3 }}
            style={{
              textAlign: "center",
              padding: "10px",
              background: "rgba(255, 215, 0, 0.1)",
              borderRadius: "6px",
              fontSize: "18px",
              color: "#ffd700",
              fontFamily: "monospace",
            }}
          >
            y = W · x + b
          </motion.div>
        </motion.div>

        {/* Arrow */}
        <motion.div
          animate={{
            opacity: stage >= 3 ? 1 : 0.3,
            y: stage >= 3 ? [0, 3, 0] : 0,
          }}
          transition={{ duration: 1, repeat: Infinity }}
          style={{
            textAlign: "center",
            fontSize: "18px",
            color: "#00d4ff",
            margin: "-4px 0",
          }}
        >
          ↓
        </motion.div>

        {/* Stage 4: Output */}
        <motion.div
          animate={{
            scale: stage === 3 ? 1.02 : 1,
            borderColor: stage === 3 ? "#00ff88" : "rgba(0, 255, 136, 0.3)",
            opacity: stage >= 3 ? 1 : 0.5,
          }}
          style={{
            padding: "12px 16px",
            border: "2px solid rgba(0, 255, 136, 0.3)",
            borderRadius: "10px",
            background:
              stage === 3
                ? "rgba(0, 255, 136, 0.1)"
                : "rgba(0, 255, 136, 0.03)",
            transition: "all 0.3s ease",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "12px",
            }}
          >
            <div style={{ fontSize: "24px" }}>{stage === 3 ? "✅" : "📋"}</div>
            <div>
              <div
                style={{
                  fontSize: "14px",
                  fontWeight: "bold",
                  color: "#00ff88",
                }}
              >
                Classification Result
              </div>
              <div
                style={{
                  fontSize: "16px",
                  color: "rgba(255, 255, 255, 0.5)",
                }}
              >
                Binary classification (0 or 1)
              </div>
            </div>
          </div>

          {/* Probability bars - compact */}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {/* Conserved (Class 1) */}
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: "4px",
                }}
              >
                <span
                  style={{
                    fontSize: "14px",
                    color: "#00ff88",
                    fontWeight: "600",
                  }}
                >
                  ✅ lncRNA Conserved (1)
                </span>
                <motion.span
                  animate={{ opacity: stage >= 3 ? 1 : 0.3 }}
                  style={{
                    fontSize: "14px",
                    fontWeight: "bold",
                    color: "#00ff88",
                  }}
                >
                  {stage >= 3 ? "94.2%" : "0%"}
                </motion.span>
              </div>
              <div
                style={{
                  width: "100%",
                  height: "20px",
                  background: "rgba(255, 255, 255, 0.1)",
                  borderRadius: "10px",
                  overflow: "hidden",
                }}
              >
                <motion.div
                  animate={{ width: stage >= 3 ? "94.2%" : "0%" }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  style={{
                    height: "100%",
                    background: "linear-gradient(90deg, #00ff88, #00cc66)",
                    borderRadius: "10px",
                  }}
                />
              </div>
            </div>

            {/* Non-conserved (Class 0) */}
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: "4px",
                }}
              >
                <span
                  style={{
                    fontSize: "14px",
                    color: "#ff6b9d",
                    fontWeight: "600",
                  }}
                >
                  ❌ lncRNA Non-conserved (0)
                </span>
                <motion.span
                  animate={{ opacity: stage >= 3 ? 1 : 0.3 }}
                  style={{
                    fontSize: "14px",
                    fontWeight: "bold",
                    color: "#ff6b9d",
                  }}
                >
                  {stage >= 3 ? "5.8%" : "0%"}
                </motion.span>
              </div>
              <div
                style={{
                  width: "100%",
                  height: "20px",
                  background: "rgba(255, 255, 255, 0.1)",
                  borderRadius: "10px",
                  overflow: "hidden",
                }}
              >
                <motion.div
                  animate={{ width: stage >= 3 ? "5.8%" : "0%" }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  style={{
                    height: "100%",
                    background: "linear-gradient(90deg, #ff6b9d, #ff4570)",
                    borderRadius: "10px",
                  }}
                />
              </div>
            </div>
          </div>

          {/* Final prediction */}
          {stage === 3 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              style={{
                marginTop: "10px",
                padding: "8px",
                background: "rgba(0, 255, 136, 0.1)",
                borderRadius: "6px",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: "13px",
                  fontWeight: "bold",
                  color: "#00ff88",
                }}
              >
                Prediction: lncRNA Conserved (Class 1) ✓
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Bottom explanation - fixed position */}
      <motion.div
        key={stage}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{
          width: "100%",
          maxWidth: "900px",
          padding: "10px 16px",
          background: "rgba(0, 212, 255, 0.05)",
          borderRadius: "8px",
          fontSize: "20px",
          color: "rgba(255, 255, 255, 0.7)",
          textAlign: "center",
          lineHeight: "1.5",
        }}
      >
        {stage === 0 && "Input: 512bp DNA sequence window from genome"}
        {stage === 1 &&
          "Frozen encoder extracts features without weight updates"}
        {stage === 2 && "Linear classifier maps features to binary output"}
        {stage === 3 &&
          "Softmax output: Conserved (94.2%) vs Non-conserved (5.8%)"}
      </motion.div>
    </div>
  );
}

function getBaseColor(base) {
  const colors = { A: "#00ff88", T: "#ff5757", C: "#00d4ff", G: "#ffd700" };
  return colors[base] || "#fff";
}

function getBaseBackground(base) {
  const backgrounds = {
    A: "rgba(0, 255, 136, 0.15)",
    T: "rgba(255, 87, 87, 0.15)",
    C: "rgba(0, 212, 255, 0.15)",
    G: "rgba(255, 215, 0, 0.15)",
  };
  return backgrounds[base] || "rgba(255, 255, 255, 0.05)";
}

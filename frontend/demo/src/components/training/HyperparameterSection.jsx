import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useSpring, animated } from "@react-spring/web";
import {
  FcIdea,
  FcDataConfiguration,
  FcClock,
  FcParallelTasks,
} from "react-icons/fc";


const PARAMETERS = {
  1: {
    name: "Learning Rate",
    icon: <FcIdea size={20} />,
    before: "Too Large (1e-3)",
    after: "Appropriate (1e-5)",
    description: (
      <>
        <strong>Function:</strong> Controls learning speed.{" "}
        <strong>Impact:</strong> Classification stability.
      </>
    ),
    impact: `Too large causes unstable classification (predictions flip between Class 0 and 1). Appropriate LR yields consistent classification decisions.`,
  },
  2: {
    name: "pos_weight (Positive Sample Weight)",
    icon: <FcDataConfiguration size={20} />,
    before: "Unbalanced (1)",
    after: "Balanced (5)",
    description: (
      <>
        <strong>Function:</strong> Balances conserved (Class 1) and
        non-conserved (Class 0) samples. <strong>Impact:</strong> Class
        prediction balance.
      </>
    ),
    impact:
      "Unbalanced (1): Model predicts most regions as non-conserved (Class 0 bias). Balanced (5): Model correctly identifies both conserved and non-conserved regions.",
  },
  3: {
    name: "Epochs (Training Cycles)",
    icon: <FcClock size={20} />,
    before: "Few (5)",
    after: "Many (10)",
    description: (
      <>
        <strong>Function:</strong> Training cycles. <strong>Impact:</strong>{" "}
        Classification accuracy.
      </>
    ),
    impact:
      "Few (5): Low accuracy, many misclassifications (Accuracy: 75%). Many (10): High accuracy, fewer errors (Accuracy: 94%).",
  },
  4: {
    name: "Batch Size",
    icon: <FcParallelTasks size={20} />,
    before: "Small (16)",
    after: "Large (64)",
    description: (
      <>
        <strong>Function:</strong> Number of samples per batch.{" "}
        <strong>Impact:</strong> Training stability.
      </>
    ),
    impact:
      "Small Batch Size (16): Unstable training, inconsistent classification. Large Batch Size (64): Stable training, more reliable predictions.",
  },
};


// --- Helper Components ---

function AnimatedNumber({ from, to, decimals = 3 }) {
  const props = useSpring({
    from: { value: from },
    to: { value: to },
    config: { mass: 1, tension: 250, friction: 40 },
  });

  return (
    <animated.span>{props.value.to((n) => n.toFixed(decimals))}</animated.span>
  );
}

// --- Main Component ---

export default function HyperparameterSection() {
  const [activeParamId, setActiveParamId] = useState(1);
  const activeParam = PARAMETERS[activeParamId];
  const numParams = Object.keys(PARAMETERS).length;

  return (
    <div style={{ padding: "20px 0" }}>
      {/* Part 1 & 2: Goal and Problem Statement */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ marginBottom: "40px" }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "24px",
            maxWidth: "1200px",
            margin: "0 auto",
          }}
        >
          {/* Left: Goal Statement */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            style={{
              padding: "24px",
              background: "rgba(255, 215, 0, 0.1)",
              border: "2px solid rgba(255, 215, 0, 0.3)",
              borderRadius: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                marginBottom: "16px",
              }}
            >
              <div style={{ fontSize: "20px" }}>🎯</div>
              <h3
                style={{
                  color: "#FFD700",
                  fontSize: "1.3em",
                  margin: 0,
                }}
              >
                Part 1: Goal Statement
              </h3>
            </div>
            <p
              style={{
                fontSize: "1.2em",
                color: "#fff",
                lineHeight: "1.6",
                margin: 0,
              }}
            >
              Accurately predict if an lncRNA region is{" "}
              <strong>conserved (1)</strong> or{" "}
              <strong>not conserved (0)</strong>
            </p>
          </motion.div>

          {/* Right: Problem Statement */}
          <motion.div
            whileHover={{ scale: 1.01 }}
            style={{
              padding: "20px 28px",
              background: "rgba(255, 136, 136, 0.08)",
              border: "2px solid rgba(255, 136, 136, 0.3)",
              borderRadius: "12px",
            }}
          >
            <div
              style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}
            >
              <span style={{ fontSize: "28px" }}>❌</span>
              <div style={{ flex: 1 }}>
                <h3
                  style={{
                    color: "#f88",
                    fontSize: "1.1em",
                    margin: "0 0 8px 0",
                  }}
                >
                  Part 2: Problem (Before Tuning)
                </h3>
                <p
                  style={{
                    color: "#f88",
                    fontSize: "1.05em",
                    margin: "0 0 12px 0",
                    fontWeight: "600",
                  }}
                >
                  Imbalanced Classification Performance:
                </p>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      gap: "8px",
                      alignItems: "flex-start",
                    }}
                  >
                    <span style={{ color: "#ff9900", marginTop: "2px" }}>
                      ▸
                    </span>
                    <span style={{ color: "#ff9900", fontSize: "0.95em" }}>
                      Poor detection of conserved lncRNA regions (low recall for
                      Class 1)
                    </span>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      gap: "8px",
                      alignItems: "flex-start",
                    }}
                  >
                    <span style={{ color: "#ff9900", marginTop: "2px" }}>
                      ▸
                    </span>
                    <span style={{ color: "#ff9900", fontSize: "0.95em" }}>
                      The Model tends to predict non-conserved (Class 0) too
                      frequently
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>

      <hr style={{ borderTop: "1px solid rgba(255, 255, 255, 0.1)" }} />

      {/* Part 3: Parameter Adjustment - Interactive Cards */}
      <h2
        style={{ margin: "40px 0 20px 0", textAlign: "center", color: "#fff" }}
      >
        Part 3: Key Parameter Tuning ({numParams} Key Parameters)
      </h2>

      {/* Parameter Selection Tabs */}
      <motion.div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "15px",
          marginBottom: "30px",
        }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {Object.keys(PARAMETERS).map((id) => (
          <motion.button
            key={id}
            onClick={() => setActiveParamId(parseInt(id))}
            whileHover={{
              scale: 1.05,
              boxShadow: "0 0 15px rgba(0, 212, 255, 0.5)",
            }}
            whileTap={{ scale: 0.95 }}
            style={{
              padding: "12px 20px",
              borderRadius: "8px",
              background:
                activeParamId === parseInt(id)
                  ? "rgba(0, 212, 255, 0.2)"
                  : "rgba(255, 255, 255, 0.08)",
              color:
                activeParamId === parseInt(id)
                  ? "#00d4ff"
                  : "rgba(255, 255, 255, 0.7)",
              border:
                activeParamId === parseInt(id)
                  ? "2px solid #00d4ff"
                  : "1px solid rgba(255, 255, 255, 0.1)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            {PARAMETERS[id].icon}
            <span style={{ fontWeight: "bold", fontSize: "16px" }}>
              {PARAMETERS[id].name.split(" ")[0]}
            </span>
          </motion.button>
        ))}
      </motion.div>

      {/* Parameter Detail View with Transition */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeParamId}
          initial={{ opacity: 0, x: activeParamId % 2 === 0 ? 30 : -30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: activeParamId % 2 === 0 ? -30 : 30 }}
          transition={{ duration: 0.4 }}
          style={{
            border: "1px solid rgba(0, 212, 255, 0.3)",
            padding: "25px",
            borderRadius: "15px",
            background: "rgba(0, 0, 0, 0.2)",
          }}
        >
          <p
            style={{ color: "#00d4ff", marginBottom: "15px", fontSize: "20px" }}
          >
            {activeParam.name}
          </p>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "20px",
              padding: "20px",
              background: "rgba(255, 255, 255, 0.02)",
              borderRadius: "12px",
            }}
          >
            {/* Function & Impact */}
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  marginBottom: "8px",
                }}
              >
                <div
                  style={{
                    width: "4px",
                    height: "20px",
                    background: "#00d4ff",
                    borderRadius: "2px",
                  }}
                />
                <span
                  style={{
                    fontSize: "18px",
                    color: "#00d4ff",
                    fontWeight: "600",
                    textTransform: "uppercase",
                  }}
                >
                  Function & Impact
                </span>
              </div>
              <p
                style={{
                  fontSize: "16px",
                  color: "rgba(255, 255, 255, 0.9)",
                  lineHeight: "1.6",
                  margin: 0,
                  paddingLeft: "12px",
                }}
              >
                {activeParam.description}
              </p>
            </div>

            {/* Divider */}
            <div
              style={{
                height: "1px",
                background:
                  "linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent)",
              }}
            />

            {/* Adjustment */}
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  marginBottom: "8px",
                }}
              >
                <div
                  style={{
                    width: "4px",
                    height: "20px",
                    background: "#00ff99",
                    borderRadius: "2px",
                  }}
                />
                <span
                  style={{
                    fontSize: "18px",
                    color: "#00ff99",
                    fontWeight: "600",
                    textTransform: "uppercase",
                  }}
                >
                  Adjustment
                </span>
              </div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  paddingLeft: "12px",
                }}
              >
                <div
                  style={{
                    padding: "6px 14px",
                    background: "rgba(0, 255, 153, 0.1)",
                    border: "1px solid rgba(0, 255, 153, 0.3)",
                    borderRadius: "8px",
                  }}
                >
                  <span
                    style={{
                      color: "#00ff99",
                      fontFamily: "monospace",
                      fontSize: "16px",
                    }}
                  >
                    {activeParam.before}
                  </span>
                </div>
                <span style={{ color: "#00d4ff", fontSize: "1.3em" }}>→</span>
                <div
                  style={{
                    padding: "6px 14px",
                    background: "rgba(255, 215, 0, 0.1)",
                    border: "1px solid rgba(255, 215, 0, 0.3)",
                    borderRadius: "8px",
                  }}
                >
                  <span
                    style={{
                      color: "#FFD700",
                      fontFamily: "monospace",
                      fontSize: "16px",
                    }}
                  >
                    {activeParam.after}
                  </span>
                </div>
              </div>
            </div>

            {/* Divider */}
            <div
              style={{
                height: "1px",
                background:
                  "linear-gradient(90deg, transparent, rgba(255, 215, 0, 0.3), transparent)",
              }}
            />

            {/* Impact Comparison */}
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  marginBottom: "8px",
                }}
              >
                <div
                  style={{
                    width: "4px",
                    height: "20px",
                    background: "#FFD700",
                    borderRadius: "2px",
                  }}
                />
                <span
                  style={{
                    fontSize: "18px",
                    color: "#FFD700",
                    fontWeight: "600",
                    textTransform: "uppercase",
                  }}
                >
                  Before & After Comparison
                </span>
              </div>
              <p
                style={{
                  fontSize: "16px",
                  color: "rgba(255, 255, 255, 0.85)",
                  lineHeight: "1.7",
                  margin: 0,
                  paddingLeft: "12px",
                }}
              >
                {activeParam.impact}
              </p>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>

      <div style={{ textAlign: "center", marginTop: "30px" }}>
        <p style={{ fontSize: "1.2em", color: "#00ff99", fontWeight: "bold" }}>
          Tuning Successful: Accurate, Uniform Distribution, and Error Balance
          Restored!
        </p>
      </div>
    </div>
  );
}

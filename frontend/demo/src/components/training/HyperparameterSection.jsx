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
    description:
      "Function: Controls learning speed. Impact: Prediction stability.",
    impact: `Too large causes prediction jitter [0.2, 0.9, 0.3]. Appropriate LR yields smooth predictions [0.67, 0.71, 0.69].`,
  },
  2: {
    name: "pos_weight (Positive Sample Weight)",
    icon: <FcDataConfiguration size={20} />,
    before: "Unbalanced (1)",
    after: "Balanced (5)",
    description:
      "Function: Balances positive and negative samples. Impact: Prediction score distribution.",
    impact:
      "Unbalanced (1) results in most predictions < 0.5. Balanced (5) results in a uniform 0-1 distribution.",
  },
  3: {
    name: "Epochs (Training Cycles)",
    icon: <FcClock size={20} />,
    before: "Few (5)",
    after: "Many (10)",
    description: "Function: Training cycles. Impact: Prediction accuracy.",
    impact:
      "Increasing epochs significantly lowers error: Few (5) results in error 0.15. Many (10) results in error 0.02.",
  },
  4: {
    name: "Batch Size",
    icon: <FcParallelTasks size={20} />,
    before: "Small (16)",
    after: "Large (64)",
    description:
      "Function: Number of samples per batch. Impact: Gradient stability.",
    impact:
      "Small Batch Size (16) causes high prediction volatility. Large Batch Size (64) leads to more stable predictions.",
  },
};

// --- 2. Distribution Data (Using provided data) ---

const SCORE_DISTRIBUTION = [
  { range: "0.0-0.2", before: 40, after: 18 },
  { range: "0.2-0.4", before: 35, after: 22 },
  { range: "0.4-0.6", before: 15, after: 21 },
  { range: "0.6-0.8", before: 8, after: 20 },
  { range: "0.8-1.0", before: 2, after: 19 },
];

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

// Distribution Chart Visualization Component
const DistributionVisualization = ({ isAfter }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.8 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ delay: 0.5, duration: 0.6 }}
    style={{ width: "100%" }}
  >
    <h4 style={{ color: isAfter ? "#00d4ff" : "#f88", marginBottom: "15px" }}>
      {isAfter
        ? "✅ After: Uniform Score Distribution"
        : "❌ Before: Skewed Towards Low Scores"}
    </h4>
    {SCORE_DISTRIBUTION.map((d, index) => {
      const percentage = isAfter ? d.after : d.before;
      return (
        <motion.div
          key={d.range}
          initial={{ width: "0%", opacity: 0 }}
          animate={{ width: `${percentage * 2}px`, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.1 * index }}
          style={{
            display: "flex",
            alignItems: "center",
            marginBottom: "4px",
            fontSize: "14px",
            color: "#fff",
          }}
        >
          <span
            style={{ minWidth: "60px", marginRight: "10px", color: "#aaa" }}
          >
            {d.range}:
          </span>
          <div
            style={{
              height: "10px",
              width: `${percentage * 3}px`,
              background: isAfter
                ? "linear-gradient(90deg, #00d4ff, #0077ff)"
                : "linear-gradient(90deg, #ff9900, #ff5500)",
              borderRadius: "2px",
              minWidth: "2px",
            }}
          />
          <span style={{ marginLeft: "10px", fontWeight: "bold" }}>
            {percentage}%
          </span>
        </motion.div>
      );
    })}
  </motion.div>
);

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
        style={{ marginBottom: "40px", textAlign: "center" }}
      >
        <h3 style={{ color: "#FFD700" }}>🎯 Part 1: Goal Statement</h3>
        <p style={{ fontSize: "1.4em", color: "#fff" }}>
          Goal: Accurately Predict [0, 1] Continuous Conservatism Score
        </p>

        <h3 style={{ color: "#f88", marginTop: "30px" }}>
          ❓ Part 2: Problem Display (Before Tuning)
        </h3>
        <p style={{ color: "#f88", fontSize: "1.1em" }}>
          Inaccurate Predictions, Uneven Distribution:
        </p>
        <ul style={{ listStyleType: "none", padding: 0 }}>
          <li style={{ color: "#ff9900", marginBottom: "5px" }}>
            - Most predictions clustered in 0.2-0.4 (75% below 0.4).
          </li>
          <li style={{ color: "#ff9900" }}>
            - High conservatism scores were systematically underestimated
            (0.8-1.0 category only 2%).
          </li>
        </ul>
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
            <span style={{ fontWeight: "bold" }}>
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
          <h4 style={{ color: "#00d4ff", marginBottom: "15px" }}>
            {activeParam.name}
          </h4>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "30px",
            }}
          >
            <div>
              <p style={{ fontSize: "0.95em" }}>
                <strong style={{ color: "#fff" }}>
                  What it is (Function/Impact):
                </strong>{" "}
                {activeParam.description}
              </p>
              <p style={{ fontSize: "0.95em", marginTop: "10px" }}>
                <strong style={{ color: "#fff" }}>Adjustment:</strong>{" "}
                <span style={{ color: "#00ff99" }}>{activeParam.before}</span>{" "}
                &rarr;{" "}
                <span style={{ color: "#FFD700" }}>{activeParam.after}</span>
              </p>
            </div>

            <div style={{ textAlign: "left" }}>
              <p
                style={{
                  fontSize: "0.95em",
                  color: "#fff",
                  fontWeight: "bold",
                }}
              >
                Before & After Comparison:
              </p>
              <p style={{ fontSize: "0.9em", color: "#aaa", marginTop: "5px" }}>
                {activeParam.impact}
              </p>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>

      <hr
        style={{
          margin: "40px 0",
          borderTop: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      />

      {/* Part 4: Final Results Display */}
      <h2
        style={{ margin: "30px 0 40px 0", textAlign: "center", color: "#fff" }}
      >
        Part 4: Final Results (After Tuning)
      </h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "40px",
          alignItems: "start",
        }}
      >
        {/* Result Card 1: Key Metrics (with Animated Number) */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, type: "spring" }}
          style={{
            padding: "20px",
            border: "2px solid #00ff99",
            borderRadius: "15px",
            background: "#0a191f",
          }}
        >
          <h4 style={{ color: "#00ff99", marginBottom: "20px" }}>
            ✅ Key Metrics Comparison
          </h4>

          <div style={{ marginBottom: "15px" }}>
            <p style={{ fontSize: "0.9em", color: "#aaa" }}>
              Mean Absolute Error (MAE):
            </p>
            <p style={{ fontSize: "2.5em", fontWeight: "bold", color: "#fff" }}>
              <AnimatedNumber from={0.4} to={0.02} decimals={3} />
            </p>
            <p style={{ fontSize: "0.9em", color: "#aaa" }}>
              Dropped from 0.4 to 0.02
            </p>
          </div>

          <div style={{ marginTop: "20px" }}>
            <p style={{ fontSize: "0.9em", color: "#aaa" }}>
              Prediction Coverage:
            </p>
            <p style={{ fontSize: "1.5em", fontWeight: "bold", color: "#fff" }}>
              Covers the Full 0-1 Range
            </p>
          </div>
        </motion.div>

        {/* Result Card 2: Prediction Distribution Chart (with Bar Animation) */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          style={{
            padding: "10px 0",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: "15px",
          }}
        >
          <div style={{ padding: "15px" }}>
            <DistributionVisualization isAfter={false} />
            <hr style={{ margin: "20px 0", borderTop: "1px dashed #444" }} />
            <DistributionVisualization isAfter={true} />
          </div>
        </motion.div>
      </div>

      <div style={{ textAlign: "center", marginTop: "30px" }}>
        <p style={{ fontSize: "1.2em", color: "#00ff99", fontWeight: "bold" }}>
          Tuning Successful: Accurate, Uniform Distribution, and Error Balance
          Restored!
        </p>
      </div>
    </div>
  );
}

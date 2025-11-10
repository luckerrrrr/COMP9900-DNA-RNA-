import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function EvalAnimation() {
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
          maxWidth: "800px",
          marginBottom: "10px",
        }}
      >
        <div style={{ fontSize: "30px", color: "#00d4ff" }}>
          {stage === 0 && "Prediction Accuracy"}
          {stage === 1 && "UMAP Clustering"}
          {stage === 2 && "Performance Metrics"}
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
        {stage === 0 &&
          "Model achieves high accuracy in predicting masked bases"}
        {stage === 1 &&
          "UMAP visualization shows clear clustering of conserved regions"}
        {stage === 2 &&
          "Comprehensive metrics evaluate model performance across dimensions"}
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
        {stage === 0 && <AccuracyPieChart />}
        {stage === 1 && <UMAPClustering />}
        {stage === 2 && <MetricsDashboard />}
      </div>
    </div>
  );
}

// Stage 0: Accuracy Pie Chart
function AccuracyPieChart() {
  const accuracy = 95.3;
  const correctPercent = accuracy;
  const wrongPercent = 100 - accuracy;

  const [animatedPercent, setAnimatedPercent] = useState(0);

  useEffect(() => {
    let current = 0;
    const target = correctPercent;
    const increment = target / 50;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      setAnimatedPercent(current);
    }, 20);
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "30px",
      }}
    >
      {/* Pie Chart */}
      <div style={{ position: "relative", width: "250px", height: "250px" }}>
        {/* SVG Pie Chart */}
        <svg width="250" height="250" style={{ transform: "rotate(-90deg)" }}>
          {/* Background circle */}
          <circle
            cx="125"
            cy="125"
            r="100"
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth="30"
          />

          {/* Correct (green) arc */}
          <motion.circle
            cx="125"
            cy="125"
            r="100"
            fill="none"
            stroke="#00ff88"
            strokeWidth="30"
            strokeDasharray={`${2 * Math.PI * 100}`}
            initial={{ strokeDashoffset: 2 * Math.PI * 100 }}
            animate={{
              strokeDashoffset: 2 * Math.PI * 100 * (1 - animatedPercent / 100),
            }}
            transition={{ duration: 2, ease: "easeOut" }}
            strokeLinecap="round"
          />

          {/* Wrong (red) arc */}
          <motion.circle
            cx="125"
            cy="125"
            r="100"
            fill="none"
            stroke="#ff5757"
            strokeWidth="30"
            strokeDasharray={`${2 * Math.PI * 100}`}
            initial={{
              strokeDashoffset: 2 * Math.PI * 100,
              opacity: 0,
            }}
            animate={{
              strokeDashoffset: 2 * Math.PI * 100 * (1 - wrongPercent / 100),
              opacity: 1,
            }}
            transition={{ duration: 1, delay: 2, ease: "easeOut" }}
            strokeLinecap="round"
            style={{
              transform: `rotate(${(correctPercent / 100) * 360}deg)`,
              transformOrigin: "125px 125px",
            }}
          />
        </svg>

        {/* Center text */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            textAlign: "center",
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
            style={{
              fontSize: "42px",
              fontWeight: "bold",
              color: "#00ff88",
            }}
          >
            {animatedPercent.toFixed(1)}%
          </motion.div>
          <div
            style={{
              fontSize: "20px",
              color: "rgba(255, 255, 255, 0.6)",
              marginTop: "4px",
            }}
          >
            Accuracy
          </div>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", gap: "30px" }}>
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1 }}
          style={{ display: "flex", alignItems: "center", gap: "8px" }}
        >
          <div
            style={{
              width: "20px",
              height: "20px",
              borderRadius: "4px",
              background: "#00ff88",
            }}
          />
          <span style={{ fontSize: "20px", color: "#fff" }}>
            Correct ({correctPercent}%)
          </span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 2 }}
          style={{ display: "flex", alignItems: "center", gap: "8px" }}
        >
          <div
            style={{
              width: "20px",
              height: "20px",
              borderRadius: "4px",
              background: "#ff5757",
            }}
          />
          <span style={{ fontSize: "20px", color: "#fff" }}>
            Wrong ({wrongPercent.toFixed(1)}%)
          </span>
        </motion.div>
      </div>
    </div>
  );
}

// Stage 1: UMAP Clustering
function UMAPClustering() {
  // Mock data for 3 species clusters
  const clusters = [
    {
      species: "Human",
      color: "#00d4ff",
      points: generateCluster(50, 100, 30),
    },
    {
      species: "Mouse",
      color: "#ff6b9d",
      points: generateCluster(150, 120, 25),
    },
    {
      species: "Chimp",
      color: "#00ff88",
      points: generateCluster(200, 60, 28),
    },
  ];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "20px",
      }}
    >
      {/* UMAP Plot */}
      <div
        style={{
          position: "relative",
          width: "400px",
          height: "300px",
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: "12px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          overflow: "hidden",
        }}
      >
        {/* Axes */}
        <div
          style={{
            position: "absolute",
            left: "30px",
            bottom: "20px",
            width: "calc(100% - 50px)",
            height: "1px",
            background: "rgba(255, 255, 255, 0.2)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: "30px",
            top: "10px",
            width: "1px",
            height: "calc(100% - 30px)",
            background: "rgba(255, 255, 255, 0.2)",
          }}
        />

        {/* Axis labels */}
        <div
          style={{
            position: "absolute",
            bottom: "5px",
            right: "10px",
            fontSize: "20px",
            color: "rgba(255, 255, 255, 0.4)",
          }}
        >
          UMAP 1
        </div>
        <div
          style={{
            position: "absolute",
            top: "5px",
            left: "5px",
            fontSize: "20px",
            color: "rgba(255, 255, 255, 0.4)",
          }}
        >
          UMAP 2
        </div>

        {/* Data points */}
        {clusters.map((cluster, clusterIdx) =>
          cluster.points.map((point, pointIdx) => (
            <motion.div
              key={`${clusterIdx}-${pointIdx}`}
              initial={{ opacity: 0, scale: 0, x: 200, y: 150 }}
              animate={{
                opacity: 0.7,
                scale: 1,
                x: point.x,
                y: point.y,
              }}
              transition={{
                delay: clusterIdx * 0.3 + pointIdx * 0.02,
                duration: 0.6,
                ease: "easeOut",
              }}
              whileHover={{ scale: 1.5, opacity: 1 }}
              style={{
                position: "absolute",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: cluster.color,
                boxShadow: `0 0 10px ${cluster.color}60`,
                cursor: "pointer",
              }}
            />
          ))
        )}
      </div>

      {/* Legend */}
      <div style={{ display: "flex", gap: "20px" }}>
        {clusters.map((cluster, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.5 + i * 0.2 }}
            style={{ display: "flex", alignItems: "center", gap: "8px" }}
          >
            <div
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                background: cluster.color,
                boxShadow: `0 0 8px ${cluster.color}60`,
              }}
            />
            <span style={{ fontSize: "20px", color: "#fff" }}>
              {cluster.species}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// Stage 2: Metrics Dashboard
function MetricsDashboard() {
  const metrics = [
    { label: "Accuracy", value: 95.3, unit: "%", color: "#00ff88" },
    { label: "F1-Score", value: 0.94, unit: "", color: "#00d4ff" },
    { label: "Precision", value: 96.1, unit: "%", color: "#a78bfa" },
    { label: "Recall", value: 93.7, unit: "%", color: "#ffd700" },
    { label: "Loss", value: 0.12, unit: "", color: "#ff6b9d" },
    { label: "AUC", value: 0.98, unit: "", color: "#00ff88" },
  ];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(3, 1fr)",
        gap: "16px",
        width: "100%",
      }}
    >
      {metrics.map((metric, i) => (
        <MetricCard key={i} metric={metric} delay={i * 0.15} />
      ))}
    </div>
  );
}

// Metric card component with animation
function MetricCard({ metric, delay }) {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      let current = 0;
      const target = metric.value;
      const increment = target / 30;
      const interval = setInterval(() => {
        current += increment;
        if (current >= target) {
          current = target;
          clearInterval(interval);
        }
        setAnimatedValue(current);
      }, 30);
      return () => clearInterval(interval);
    }, delay * 1000);
    return () => clearTimeout(timer);
  }, [metric.value, delay]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      style={{
        padding: "20px",
        background: "rgba(255, 255, 255, 0.05)",
        borderRadius: "12px",
        border: `1px solid ${metric.color}40`,
        textAlign: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "4px",
          background: metric.color,
          opacity: 0.6,
        }}
      />

      {/* Label */}
      <div
        style={{
          fontSize: "20px",
          color: "rgba(255, 255, 255, 0.6)",
          marginBottom: "12px",
          fontWeight: "500",
        }}
      >
        {metric.label}
      </div>

      {/* Value */}
      <div
        style={{
          fontSize: "32px",
          fontWeight: "bold",
          color: metric.color,
        }}
      >
        {metric.unit === "%"
          ? animatedValue.toFixed(1)
          : animatedValue.toFixed(2)}
        {metric.unit}
      </div>
    </motion.div>
  );
}

// Helper: Generate random cluster points
function generateCluster(centerX, centerY, spread) {
  const points = [];
  for (let i = 0; i < 30; i++) {
    const angle = Math.random() * Math.PI * 2;
    const radius = Math.random() * spread;
    points.push({
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
    });
  }
  return points;
}

import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  FaChartPie, 
  FaFire, 
  FaProjectDiagram, 
  FaDna,
  FaLightbulb
} from "react-icons/fa";
import PieChart from "./PieChart.jsx";
import EmbeddingHeatmap from "./EmbeddingHeatmap.jsx";
import UMAPClustering from "./UMAPClustering.jsx";
import CrossSpeciesComparison from "./CrossSpeciesComparison.jsx";

export default function Module5Results() {
  const [activeChart, setActiveChart] = useState(0);

  const charts = [
    { id: 0, title: "lncRNA matching ratio", icon: <FaChartPie />, component: <PieChart /> },
    { id: 1, title: "Embedding heatmap", icon: <FaFire />, component: <EmbeddingHeatmap /> },
    { id: 2, title: "UMAP clustering", icon: <FaProjectDiagram />, component: <UMAPClustering /> },
    { id: 3, title: "Cross-species comparison", icon: <FaDna />, component: <CrossSpeciesComparison /> }
  ];

  return (
    <div style={{
      minHeight: "100vh",
      padding: "0 5%",
      color: "#fff",
    }}>
      {/* Title section */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          textAlign: "center",
          marginBottom: "60px",
        }}
      >
        <h1 style={{
          fontSize: "clamp(32px, 5vw, 48px)",
          fontWeight: "bold",
          marginBottom: "16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "16px"
        }}>
          <FaLightbulb style={{ color: "#ffd700" }} />
          Results presentation and insight analysis
        </h1>
        <p style={{
          fontSize: "18px",
          color: "rgba(255, 255, 255, 0.7)",
          maxWidth: "800px",
          margin: "0 auto",
          lineHeight: "1.6"
        }}>
          Through multi-dimensional visualization analysis, the GPN model demonstrates its excellent performance in detecting conserved regions of lncRNA across species
        </p>
      </motion.div>

      {/* Chart Navigation */}
      <div style={{
        display: "flex",
        justifyContent: "center",
        gap: "16px",
        marginBottom: "40px",
        flexWrap: "wrap"
      }}>
        {charts.map((chart) => (
          <motion.button
            key={chart.id}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setActiveChart(chart.id)}
            style={{
              padding: "12px 24px",
              borderRadius: "12px",
              background: activeChart === chart.id 
                ? "rgba(0, 212, 255, 0.2)" 
                : "rgba(255, 255, 255, 0.05)",
              border: activeChart === chart.id 
                ? "2px solid #00d4ff" 
                : "1px solid rgba(255, 255, 255, 0.1)",
              color: activeChart === chart.id ? "#00d4ff" : "rgba(255, 255, 255, 0.7)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "16px",
              fontWeight: "500",
              transition: "all 0.3s ease"
            }}
          >
            {chart.icon}
            {chart.title}
          </motion.button>
        ))}
      </div>

      {/* Chart content area */}
      <motion.div
        key={activeChart}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: "20px",
          padding: "40px",
          border: "1px solid rgba(0, 212, 255, 0.2)",
          minHeight: "500px"
        }}
      >
        {charts[activeChart].component}
      </motion.div>
    </div>
  );
}

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import ModelToggle from "../components/interactivePages/ModelToggle"
import RegionList from "../components/interactivePages/RegionList";
import PredictionDetail from "../components/interactivePages/PredictionDetail";
import ComparisonList from "../components/interactivePages/ComparisonList";
import { gpnMsa, gpn } from "../constants/predictionData";

export default function InteractivePage() {
  const navigate = useNavigate();
  const [selectedModel, setSelectedModel] = useState("GPN-MSA");
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [showComparison, setShowComparison] = useState(false);

 
  const currentRegions = selectedModel === "GPN-MSA" ? gpnMsa : gpn;


  const handleModelChange = (model) => {
    setSelectedModel(model);
    setSelectedRegion(null);
    setShowComparison(false);
  };

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
      {/* Back button */}
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

      {/* Main content */}
      <div
        style={{
          maxWidth: "1400px",
          margin: "0 auto",
          paddingTop: "80px",
        }}
      >
        {/* Title*/}
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{
            fontSize: "clamp(32px, 4vw, 48px)",
            marginBottom: "20px",
            textAlign: "center",
          }}
        >
          Interactive Conservation Prediction
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          style={{
            fontSize: "18px",
            textAlign: "center",
            color: "#aaa",
            marginBottom: "30px",
          }}
        >
          Explore conserved lncRNA regions predicted by GPN and GPN-MSA models
        </motion.p>

        {/* model toggle */}
        <ModelToggle
          selectedModel={selectedModel}
          onModelChange={handleModelChange}
        />

        {/* Main area */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "400px 1fr",
            gap: "30px",
            marginBottom: "40px",
          }}
        >
          {/* Left：gene list */}
          <RegionList
            regions={currentRegions}
            selectedRegion={selectedRegion}
            onSelectRegion={setSelectedRegion}
            onViewAll={() => setShowComparison(!showComparison)}
            modelName={selectedModel}
          />

          {/* Right: detail */}
          <PredictionDetail region={selectedRegion} modelName={selectedModel} />
        </div>

        {/* Bottom: Comparison list  */}
        <ComparisonList
          gpnRegions={gpn}
          gpnMsaRegions={gpnMsa}
          isVisible={showComparison}
        />
      </div>
    </div>
  );
}

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import StepCards from "../components/pipeline/StepCards";
import DetailSection from "../components/pipeline/DetailSection";
import { PIPELINE_STEPS } from "../constants/pipelineSteps";
import { SiJfrogpipelines } from "react-icons/si";


export default function Module2Pipeline() {
  const [activeStep, setActiveStep] = useState(1);
  const [isPlaying, setIsPlaying] = useState(true); 


  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      setActiveStep((prev) => {
        if (prev >= 6) {
          setIsPlaying(false); 
          return 6;
        }
        return prev + 1;
      });
    }, 15000); 

    return () => clearInterval(timer);
  }, [isPlaying, activeStep]);

  const handleStepClick = (stepId) => {
    setActiveStep(stepId);
    setIsPlaying(false);
  };

  const handleReplay = () => {
    setActiveStep(1);
    setIsPlaying(true);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "5%",
        color: "#fff",
      }}
    >
      {/* Title with play controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "60px",
        }}
      >
        <motion.h2
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            textAlign: "center",
            fontSize: "clamp(32px, 5vw, 48px)",
            flex: 1,
          }}
        >
          <SiJfrogpipelines /> Data Processing Pipeline
        </motion.h2>

        {/* Play/Pause/Replay controls */}
        <div style={{ display: "flex", gap: "12px" }}>
          {!isPlaying && activeStep < 6 && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsPlaying(true)}
              style={{
                background: "rgba(0, 212, 255, 0.2)",
                border: "1px solid #00d4ff",
                color: "#00d4ff",
                padding: "10px 20px",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "20px",
                fontWeight: "500",
              }}
            >
              Play
            </motion.button>
          )}

          {isPlaying && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsPlaying(false)}
              style={{
                background: "rgba(255, 215, 0, 0.2)",
                border: "1px solid #ffd700",
                color: "#ffd700",
                padding: "10px 20px",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "20px",
                fontWeight: "500",
              }}
            >
              Pause
            </motion.button>
          )}

          {!isPlaying && activeStep === 6 && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleReplay}
              style={{
                background: "rgba(0, 255, 136, 0.2)",
                border: "1px solid #00ff88",
                color: "#00ff88",
                padding: "10px 20px",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "20px",
                fontWeight: "500",
              }}
            >
              Replay
            </motion.button>
          )}
        </div>
      </div>

      {/* Step Cards */}
      <StepCards
        steps={PIPELINE_STEPS}
        activeStep={activeStep}
        onStepClick={handleStepClick}
      />

      {/* Detail Section */}
      <DetailSection activeStep={activeStep} steps={PIPELINE_STEPS} />
    </div>
  );
}

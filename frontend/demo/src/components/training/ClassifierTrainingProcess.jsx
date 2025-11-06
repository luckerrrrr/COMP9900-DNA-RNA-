import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import LabelingStage from "./ClassifierStage/LabelingStage";
import LearningFeaturesStage from "./ClassifierStage/LearningFeaturesStage";
import TrainingStage from "./ClassifierStage/TrainingStage";
import ResultsStage from "./ClassifierStage/ResultsStage";

export default function ClassifierTrainingProcess() {
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
    }, 4500);
    return () => clearInterval(timer);
  }, [isPlaying]);

  // Replay function
  const handleReplay = () => {
    setStage(0);
    setIsPlaying(true);
  };

  const stageInfo = [
    { id: 0, title: "🏷️ Step 1: Label Conserved Regions" },
    { id: 1, title: "🧠 Step 2: Learn Conservation Features" },
    { id: 2, title: "🔥 Step 3: Train Classifier" },
    { id: 3, title: "✅ Step 4: Classification Results" },
  ];

  return (
    <div
      style={{
        width: "100%",
        maxWidth: "1000px",
        margin: "0 auto 60px",
      }}
    >


      {/* Stage indicator with replay */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "30px",
        }}
      >
        <div
          style={{
            fontSize: "20px",
            color: "#00d4ff",
            fontWeight: "500",
          }}
        >
          {stageInfo[stage].title}
        </div>

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
            }}
          >
            Replay
          </motion.button>
        )}
      </div>

      {/* Main animation area */}
      <div
        style={{
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: "20px",
          padding: "40px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          minHeight: "500px",
        }}
      >
        {stage === 0 && <LabelingStage />}
        {stage === 1 && <LearningFeaturesStage />}
        {stage === 2 && <TrainingStage />}
        {stage === 3 && <ResultsStage />}
      </div>
    </div>
  );
}

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import LabelingStage from "./ClassifierStage/LabelingStage";
import LearningFeaturesStage from "./ClassifierStage/LearningFeaturesStage";
import TrainingStage from "./ClassifierStage/TrainingStage";
import ResultsStage from "./ClassifierStage/ResultsStage";

export default function ClassifierTrainingProcess() {
  const [stage, setStage] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isAutoPlay, setIsAutoPlay] = useState(true);

  const stageInfo = [
    { id: 0, title: "🏷️ Step 1: Label Conserved Regions" },
    { id: 1, title: "🧠 Step 2: Learn Conservation Features" },
    { id: 2, title: "🔥 Step 3: Train Classifier" },
    { id: 3, title: "✅ Step 4: Classification Results" },
  ];


  useEffect(() => {
    if (!isPlaying || !isAutoPlay) return;

    const timer = setInterval(() => {
      setStage((prev) => {
        if (prev === 3) {
          setIsPlaying(false);
          return 3;
        }
        return prev + 1;
      });
    }, 8000);
    return () => clearInterval(timer);
  }, [isPlaying, isAutoPlay]);


  const handleNext = () => {
    if (stage < 3) {
      setIsAutoPlay(false); 
      setStage(stage + 1);
    }
  };


  const handlePrev = () => {
    if (stage > 0) {
      setIsAutoPlay(false);
      setStage(stage - 1);
    }
  };


  const handleReplay = () => {
    setStage(0);
    setIsPlaying(true);
    setIsAutoPlay(true); 
  };


  const toggleAutoPlay = () => {
    setIsAutoPlay(!isAutoPlay);
    if (!isAutoPlay) {
      setIsPlaying(true); 
    }
  };

  return (
    <div
      style={{
        width: "100%",
        maxWidth: "1000px",
        margin: "0 auto 60px",
      }}
    >
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

        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleAutoPlay}
            style={{
              background: isAutoPlay
                ? "rgba(0, 212, 255, 0.2)"
                : "rgba(255, 215, 0, 0.2)",
              border: `1px solid ${isAutoPlay ? "#00d4ff" : "#ffd700"}`,
              color: isAutoPlay ? "#00d4ff" : "#ffd700",
              padding: "6px 16px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "18px",
              fontWeight: "500",
            }}
          >
            {isAutoPlay ? "Pause Auto" : "Auto Play"}
          </motion.button>

          {stage === 3 && (
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
                fontSize: "18px",
                fontWeight: "500",
              }}
            >
              Replay
            </motion.button>
          )}
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: "8px",
          marginBottom: "20px",
          justifyContent: "center",
        }}
      >
        {stageInfo.map((s, idx) => (
          <div
            key={s.id}
            onClick={() => {
              setStage(idx);
              setIsAutoPlay(false);
            }}
            style={{
              flex: 1,
              height: "4px",
              background:
                idx <= stage
                  ? "linear-gradient(90deg, #00d4ff, #00ff88)"
                  : "rgba(255, 255, 255, 0.2)",
              borderRadius: "2px",
              cursor: "pointer",
              transition: "all 0.3s ease",
            }}
          />
        ))}
      </div>

      <div
        style={{
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: "20px",
          padding: "40px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          minHeight: "500px",
          position: "relative",
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

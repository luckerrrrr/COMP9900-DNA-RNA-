import { motion } from "framer-motion";
import { useState } from "react";
import StageCard from "../components/training/StageCard";
import DetailSection from "../components/training/TrainingDetailSection";

const trainingStages = [
  {
    id: 1,
    name: "Pretrain",
    title: "Original GPN Model",
    description: "Trained on diverse genomes to learn general DNA patterns",
    details: [
      "Foundation model training",
      "Learns universal DNA patterns",
      "Transfer learning base",
    ],
    icon: "🎯",
    status: "completed",
    progress: 100,
  },
  {
    id: 2,
    name: "Retrain",
    title: "Full Human Genome",
    description: "Adapted to human-specific genomic patterns",
    details: [
      "3.2 billion base pairs",
      "512bp sliding windows",
      "Domain adaptation",
    ],
    icon: "🔄",
    status: "training",
    progress: 65,
    epoch: "13/20",
    loss: "0.156",
    accuracy: "89.3%",
    eta: "1h 12m",
  },
  {
    id: 3,
    name: "Fine-tune",
    title: "lncRNA Annotations",
    description: "Optimized for noncoding conservation detection",
    details: [
      "Supervised with lncRNA labels",
      "Focus on conserved regions",
      "Task-specific optimization",
    ],
    icon: "🎯",
    status: "pending",
    progress: 0,
  },
];

export default function Module4Training() {
  const [activeStage, setActiveStage] = useState(1);

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "5%",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      {/* Title */}
      <motion.h2
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          textAlign: "center",
          fontSize: "clamp(32px, 5vw, 48px)",
          marginBottom: "20px",
        }}
      >
        🚀 Training & Fine-tuning Pipeline
      </motion.h2>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        style={{
          fontSize: "16px",
          color: "rgba(255, 255, 255, 0.7)",
          textAlign: "center",
          maxWidth: "700px",
          marginBottom: "60px",
        }}
      >
        Progressive training strategy: Foundation model → Domain adaptation →
        Task-specific optimization
      </motion.p>

      {/* Stage cards */}
      <div
        style={{
          display: "flex",
          gap: "40px",
          marginBottom: "60px",
          alignItems: "center",
          flexWrap: "wrap",
          justifyContent: "center",
        }}
      >
        {trainingStages.map((stage, index) => (
          <div
            key={stage.id}
            style={{ display: "flex", alignItems: "center", gap: "20px" }}
          >
            <StageCard
              stage={stage}
              isActive={activeStage === stage.id}
              onClick={() => setActiveStage(stage.id)}
            />

            {/* Arrow between cards */}
            {index < trainingStages.length - 1 && (
              <motion.div
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 0.6, scale: 1 }}
                transition={{ delay: 0.3 + index * 0.2 }}
                style={{
                  fontSize: "32px",
                  color: "#00d4ff",
                }}
              >
                →
              </motion.div>
            )}
          </div>
        ))}
      </div>

      {/* Detail section */}
      <motion.div
        key={activeStage}
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        style={{
          width: "100%",
          maxWidth: "900px",
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: "20px",
          padding: "40px",
          border: "1px solid rgba(0, 212, 255, 0.2)",
        }}
      >
        <DetailSection stage={trainingStages[activeStage - 1]} />
      </motion.div>

      {/* Bottom explanation */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        style={{
          marginTop: "40px",
          maxWidth: "800px",
          padding: "20px",
          background: "rgba(0, 212, 255, 0.05)",
          border: "1px solid rgba(0, 212, 255, 0.2)",
          borderRadius: "12px",
          textAlign: "center",
        }}
      >
        <p
          style={{
            fontSize: "14px",
            color: "rgba(255, 255, 255, 0.8)",
            lineHeight: "1.7",
            margin: 0,
          }}
        >
          💡 <strong>Training Strategy:</strong> We first retrain GPN on full
          human genome windows to adapt to human-specific patterns, then
          fine-tune it using lncRNA annotations to focus on noncoding
          conservation detection.
        </p>
      </motion.div>
    </div>
  );
}

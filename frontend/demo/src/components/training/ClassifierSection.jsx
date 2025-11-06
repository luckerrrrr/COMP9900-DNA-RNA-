import { motion } from "framer-motion";
import { useState } from "react";
import ClassifierTrainingProcess from "./ClassifierTrainingProcess";
import ClassifierCard from "./ClassifierCard";

const classifierModels = [
  {
    id: 1,
    name: "GPN Classifier",
    title: "GPN + Classification Head",
    description: "Binary classification for lncRNA identification",
    icon: "🧬",
    architecture: "Frozen Encoder + Linear Head",
    trainable: "Classification Head Only",
    lrHead: "1e-4 → 1e-3",
    epochs: "1-5 epochs",
    beforeAP: "89.0%",
    afterAP: "92.3%",
    improvement: "+3.3%",
    color: "#00d4ff",
  },
  {
    id: 2,
    name: "GPN-MSA Classifier",
    title: "GPN-MSA + Classification Head",
    description: "Cross-species lncRNA classification",
    icon: "🔗",
    architecture: "Frozen Encoder + Linear Head",
    trainable: "Classification Head Only",
    lrHead: "1e-4 → 1e-3",
    epochs: "1-5 epochs",
    beforeAP: "91.0%",
    afterAP: "94.1%",
    improvement: "+3.1%",
    color: "#00ff88",
  },
];

export default function ClassifierSection() {
  const [activeModel, setActiveModel] = useState(null);

  return (
    <div>
      {/* Training process animation */}
      <ClassifierTrainingProcess />

      {/* Model cards */}
      <div
        style={{
          maxWidth: "1000px",
          margin: "0 auto",
        }}
      >
        <motion.h3
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            fontSize: "24px",
            color: "#00d4ff",
            marginBottom: "30px",
            textAlign: "center",
          }}
        >
        Trained Classifiers
        </motion.h3>

        <div
          style={{
            display: "flex",
            gap: "30px",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          {classifierModels.map((model) => (
            <ClassifierCard
              key={model.id}
              model={model}
              isActive={activeModel === model.id}
              onClick={() =>
                setActiveModel(activeModel === model.id ? null : model.id)
              }
            />
          ))}
        </div>
      </div>
    </div>
  );
}

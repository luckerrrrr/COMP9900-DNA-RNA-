import { motion } from "framer-motion";
import { useState } from "react";
import ClassifierAnimation from "./ClassifierAnimation";
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
    performance: "AP: 0.89 → 0.92",
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
    performance: "AP: 0.91 → 0.94",
    color: "#00ff88",
  },
];

export default function ClassifierSection() {
  const [activeModel, setActiveModel] = useState(null);

  return (
    <div>
      {/* Title */}
      <motion.h3
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          fontSize: "28px",
          color: "#00d4ff",
          marginBottom: "40px",
          textAlign: "center",
        }}
      >
        📊 Classifier Supervised Learning
      </motion.h3>

      {/* Principle explanation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          maxWidth: "1000px",
          margin: "0 auto 60px",
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: "16px",
          padding: "40px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        <h4
          style={{
            fontSize: "20px",
            color: "#00d4ff",
            marginBottom: "24px",
          }}
        >
          💡 Classification Head Training Principle
        </h4>

        <div
          style={{
            fontSize: "14px",
            color: "rgba(255, 255, 255, 0.8)",
            lineHeight: "1.8",
            marginBottom: "30px",
          }}
        >
          <p style={{ marginBottom: "16px" }}>
            After conservation-supervised training, we add a{" "}
            <strong style={{ color: "#00ff88" }}>
              lightweight classification head
            </strong>{" "}
            on top of the frozen encoder to predict lncRNA vs. protein-coding:
          </p>

          <div
            style={{
              padding: "20px",
              background: "rgba(0, 212, 255, 0.05)",
              borderRadius: "12px",
              border: "1px solid rgba(0, 212, 255, 0.1)",
              marginBottom: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "20px",
                fontSize: "16px",
              }}
            >
              <div
                style={{
                  padding: "12px 20px",
                  background: "rgba(255, 255, 255, 0.05)",
                  borderRadius: "8px",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                }}
              >
                DNA Sequence
              </div>
              <span style={{ color: "#00d4ff" }}>→</span>
              <div
                style={{
                  padding: "12px 20px",
                  background: "rgba(0, 212, 255, 0.1)",
                  borderRadius: "8px",
                  border: "1px solid #00d4ff",
                }}
              >
                Frozen Encoder
              </div>
              <span style={{ color: "#00d4ff" }}>→</span>
              <div
                style={{
                  padding: "12px 20px",
                  background: "rgba(0, 255, 136, 0.1)",
                  borderRadius: "8px",
                  border: "1px solid #00ff88",
                }}
              >
                Linear Head
              </div>
              <span style={{ color: "#00d4ff" }}>→</span>
              <div
                style={{
                  padding: "12px 20px",
                  background: "rgba(255, 215, 0, 0.1)",
                  borderRadius: "8px",
                  border: "1px solid #ffd700",
                }}
              >
                lncRNA / mRNA
              </div>
            </div>
          </div>

          <p style={{ marginBottom: "12px" }}>
            <strong style={{ color: "#00ff88" }}>Key Strategy:</strong>
          </p>
          <ul
            style={{
              paddingLeft: "24px",
              margin: 0,
              listStyle: "none",
            }}
          >
            <li style={{ marginBottom: "8px" }}>
              <span style={{ color: "#00ff88", marginRight: "8px" }}>•</span>
              <strong>Freeze encoder weights</strong>: Keep pre-trained
              knowledge intact
            </li>
            <li style={{ marginBottom: "8px" }}>
              <span style={{ color: "#00ff88", marginRight: "8px" }}>•</span>
              <strong>Train head only</strong>: Fast convergence (1-5 epochs)
            </li>
            <li style={{ marginBottom: "8px" }}>
              <span style={{ color: "#00ff88", marginRight: "8px" }}>•</span>
              <strong>Higher learning rate for head</strong>: LR_HEAD = 1e-4 to
              1e-3
            </li>
            <li style={{ marginBottom: "8px" }}>
              <span style={{ color: "#00ff88", marginRight: "8px" }}>•</span>
              <strong>Monitor validation AP</strong>: Early stop when plateaus
            </li>
          </ul>
        </div>

        {/* Animation */}
        <ClassifierAnimation />
      </motion.div>

      {/* Classifier cards */}
      <div
        style={{
          display: "flex",
          gap: "40px",
          flexWrap: "wrap",
          justifyContent: "center",
          marginBottom: "40px",
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
  );
}

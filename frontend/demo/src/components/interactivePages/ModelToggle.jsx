import { motion } from "framer-motion";

export default function ModelToggle({ selectedModel, onModelChange }) {
  return (
    <div
      style={{
        display: "flex",
        gap: "12px",
        justifyContent: "flex-end",
        marginBottom: "20px",
      }}
    >
      {["GPN", "GPN-MSA"].map((model) => (
        <motion.button
          key={model}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onModelChange(model)}
          style={{
            padding: "10px 24px",
            background:
              selectedModel === model
                ? "rgba(100, 181, 246, 0.3)"
                : "rgba(255, 255, 255, 0.05)",
            border: `2px solid ${
              selectedModel === model ? "#64b5f6" : "rgba(255, 255, 255, 0.2)"
            }`,
            borderRadius: "8px",
            color: selectedModel === model ? "#64b5f6" : "#fff",
            fontSize: "16px",
            fontWeight: "600",
            cursor: "pointer",
          }}
        >
          {model}
        </motion.button>
      ))}
    </div>
  );
}

import { motion } from "framer-motion";

export default function ClassifierCard({ model, isActive, onClick }) {
  return (
    <motion.div
      onClick={onClick}
      whileHover={{ scale: 1.05, y: -10 }}
      whileTap={{ scale: 0.95 }}
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: model.id * 0.2 }}
      style={{
        width: isActive ? "420px" : "380px",
        minHeight: isActive ? "550px" : "500px",
        background: `linear-gradient(135deg, ${model.color}15, rgba(255, 255, 255, 0.05))`,
        border: `2px solid ${model.color}`,
        borderRadius: "20px",
        padding: "30px",
        cursor: "pointer",
        position: "relative",
        boxShadow: isActive
          ? `0 0 40px ${model.color}40`
          : "0 8px 30px rgba(0, 0, 0, 0.3)",
        transition: "all 0.3s ease",
      }}
    >
      {/* Status badge */}
      <div
        style={{
          position: "absolute",
          top: "-12px",
          right: "20px",
          padding: "6px 16px",
          borderRadius: "20px",
          background: model.color,
          fontSize: "12px",
          fontWeight: "bold",
          color: "#000",
        }}
      >
        🔥 Training
      </div>

      {/* Icon */}
      <div
        style={{
          fontSize: "60px",
          textAlign: "center",
          marginBottom: "20px",
        }}
      >
        {model.icon}
      </div>

      {/* Title */}
      <h3
        style={{
          fontSize: "22px",
          color: model.color,
          marginBottom: "12px",
          textAlign: "center",
        }}
      >
        {model.title}
      </h3>

      {/* Description */}
      <p
        style={{
          fontSize: "14px",
          color: "rgba(255, 255, 255, 0.7)",
          textAlign: "center",
          marginBottom: "30px",
        }}
      >
        {model.description}
      </p>

      {/* Architecture info */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        <InfoBox label="Architecture" value={model.architecture} />
        <InfoBox label="Trainable Params" value={model.trainable} />
        <InfoBox label="LR_HEAD Range" value={model.lrHead} />
        <InfoBox label="Training Epochs" value={model.epochs} />
      </div>

      {/* Performance */}
      <div
        style={{
          padding: "16px",
          background: `${model.color}15`,
          borderRadius: "12px",
          border: `1px solid ${model.color}40`,
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            fontSize: "12px",
            color: "rgba(255, 255, 255, 0.6)",
            marginBottom: "8px",
            textAlign: "center",
          }}
        >
          Performance Improvement
        </div>
        <div
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: model.color,
            textAlign: "center",
          }}
        >
          {model.performance}
        </div>
      </div>

      {/* Details */}
      {isActive && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          style={{
            borderTop: "1px solid rgba(255, 255, 255, 0.1)",
            paddingTop: "20px",
          }}
        >
          <p
            style={{
              fontSize: "13px",
              color: "rgba(255, 255, 255, 0.8)",
              lineHeight: "1.6",
              textAlign: "center",
            }}
          >
            Only the classification head is trained while encoder weights remain
            frozen. This enables fast convergence (1-5 epochs) while preserving
            pre-trained conservation knowledge.
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}

function InfoBox({ label, value }) {
  return (
    <div
      style={{
        padding: "12px",
        background: "rgba(255, 255, 255, 0.05)",
        borderRadius: "8px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
      }}
    >
      <div
        style={{
          fontSize: "11px",
          color: "rgba(255, 255, 255, 0.5)",
          marginBottom: "4px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: "14px",
          fontWeight: "600",
          color: "#fff",
        }}
      >
        {value}
      </div>
    </div>
  );
}

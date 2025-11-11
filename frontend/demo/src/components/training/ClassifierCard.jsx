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
        width: isActive ? "450px" : "420px",
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
        ✓ Trained
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

      {/* Performance improvement - prominent display */}
      <div
        style={{
          padding: "20px",
          background: `${model.color}15`,
          borderRadius: "12px",
          border: `2px solid ${model.color}40`,
          marginBottom: "24px",
        }}
      >
        <div
          style={{
            fontSize: "13px",
            color: "rgba(255, 255, 255, 0.6)",
            textAlign: "center",
            marginBottom: "12px",
          }}
        >
          Performance Improvement
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "16px",
          }}
        >
          <div
            style={{
              padding: "12px 20px",
              background: "rgba(255, 87, 87, 0.1)",
              border: "1px solid #ff5757",
              borderRadius: "8px",
              fontSize: "18px",
              fontWeight: "bold",
              color: "#ff5757",
            }}
          >
            {model.beforeAP}
          </div>
          <div style={{ fontSize: "24px", color: model.color }}>→</div>
          <div
            style={{
              padding: "12px 20px",
              background: `${model.color}20`,
              border: `2px solid ${model.color}`,
              borderRadius: "8px",
              fontSize: "18px",
              fontWeight: "bold",
              color: model.color,
            }}
          >
            {model.afterAP}
          </div>
        </div>
        <div
          style={{
            textAlign: "center",
            marginTop: "12px",
            fontSize: "16px",
            fontWeight: "bold",
            color: "#00ff88",
          }}
        >
          {model.improvement}
        </div>
      </div>

      {/* Training info */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        <InfoBox label="Architecture" value={model.architecture} />
        <InfoBox label="Trainable Params" value={model.trainable} />
        <InfoBox label="LR_HEAD Range" value={model.lrHead} />
        <InfoBox label="Training Epochs" value={model.epochs} />
      </div>

      {/* Details (expandable) */}
      {isActive && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          style={{
            borderTop: "1px solid rgba(255, 255, 255, 0.1)",
            paddingTop: "20px",
            marginTop: "20px",
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
            pre-trained conservation knowledge from the base model.
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

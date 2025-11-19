import { motion } from "framer-motion";

export default function PredictionDetail({ region, modelName }) {
  if (!region) {
    return (
      <div
        style={{
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(10px)",
          borderRadius: "16px",
          padding: "40px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          textAlign: "center",
          color: "#aaa",
          fontSize: "30px",
        }}
      >
        Select a region to view prediction details
      </div>
    );
  }

  const predPercent = (region.predProb * 100).toFixed(1);
  const phastPercent = (region.phastcons * 100).toFixed(1);
  const isHighlyConserved = region.predProb > 0.7;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      style={{
        background: "rgba(255, 255, 255, 0.05)",
        backdropFilter: "blur(10px)",
        borderRadius: "16px",
        padding: "30px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
      }}
    >
      {/* Title */}
      <h2
        style={{
          fontSize: "28px",
          fontWeight: "bold",
          color: "#fff",
          marginBottom: "24px",
          margin: "0 0 24px 0",
        }}
      >
        Predict lncRNA Conservation
      </h2>

      {/* Area Info */}
      <div
        style={{
          marginBottom: "30px",
          padding: "16px",
          background: "rgba(100, 181, 246, 0.1)",
          borderRadius: "10px",
          border: "1px solid rgba(100, 181, 246, 0.3)",
        }}
      >
        <div
          style={{
            fontSize: "20px",
            color: "#64b5f6",
            fontWeight: "600",
            marginBottom: "8px",
          }}
        >
          {region.chr}:{region.start.toLocaleString()}-
          {region.end.toLocaleString()}
        </div>
        <div style={{ fontSize: "20px", color: "#aaa" }}>
          Gene: {region.gene}
        </div>
      </div>

      {/* Comparison list */}
      <div style={{ marginBottom: "30px" }}>
        {/* Model Prediction */}
        <div style={{ marginBottom: "24px" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "12px",
            }}
          >
            <span
              style={{ fontSize: "20px", color: "#fff", fontWeight: "600" }}
            >
              {modelName} Prediction
            </span>
            <span
              style={{
                fontSize: "24px",
                fontWeight: "bold",
                color: "#66bb6a",
              }}
            >
              {predPercent}%
            </span>
          </div>
          <div
            style={{
              width: "100%",
              height: "16px",
              background: "rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              overflow: "hidden",
            }}
          >
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${predPercent}%` }}
              transition={{ duration: 1, delay: 0.2 }}
              style={{
                height: "100%",
                background: "linear-gradient(90deg, #66bb6a 0%, #4caf50 100%)",
                borderRadius: "8px",
              }}
            />
          </div>
        </div>

        {/* PhastCons Score */}
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "12px",
            }}
          >
            <span
              style={{ fontSize: "20px", color: "#fff", fontWeight: "600" }}
            >
              PhastCons Score
            </span>
            <span
              style={{
                fontSize: "24px",
                fontWeight: "bold",
                color: "#64b5f6",
              }}
            >
              {phastPercent}%
            </span>
          </div>
          <div
            style={{
              width: "100%",
              height: "16px",
              background: "rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              overflow: "hidden",
            }}
          >
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${phastPercent}%` }}
              transition={{ duration: 1, delay: 0.4 }}
              style={{
                height: "100%",
                background: "linear-gradient(90deg, #64b5f6 0%, #42a5f5 100%)",
                borderRadius: "8px",
              }}
            />
          </div>
        </div>
      </div>

      {/* Conclusion */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.6 }}
        style={{
          padding: "24px",
          background: isHighlyConserved
            ? "rgba(102, 187, 106, 0.1)"
            : "rgba(255, 152, 0, 0.1)",
          border: `2px solid ${isHighlyConserved ? "#66bb6a" : "#ff9800"}`,
          borderRadius: "12px",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: "48px", marginBottom: "12px" }}>
          {isHighlyConserved ? "✓" : "⚠"}
        </div>
        <div
          style={{
            fontSize: "26px",
            fontWeight: "bold",
            color: isHighlyConserved ? "#66bb6a" : "#ff9800",
            marginBottom: "12px",
          }}
        >
          {isHighlyConserved ? "Highly Conserved" : "Moderately Conserved"}
        </div>
        <div style={{ fontSize: "20px", color: "#aaa", lineHeight: 1.6 }}>
          {modelName} detected{" "}
          {region.predProb > region.phastcons
            ? "higher conservation than traditional PhastCons method"
            : "conservation consistent with PhastCons analysis"}
        </div>
      </motion.div>
    </motion.div>
  );
}

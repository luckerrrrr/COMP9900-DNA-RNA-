import { motion } from "framer-motion";

export default function RegionCard({ region, index, isSelected, onClick }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      onClick={onClick}
      style={{
        padding: "20px",
        background: isSelected
          ? "rgba(100, 181, 246, 0.2)"
          : "rgba(255, 255, 255, 0.05)",
        border: `2px solid ${
          isSelected ? "#64b5f6" : "rgba(255, 255, 255, 0.1)"
        }`,
        borderRadius: "12px",
        cursor: "pointer",
        marginBottom: "12px",
      }}
    >
      {/* location Info */}
      <div
        style={{
          fontSize: "14px",
          color: "#aaa",
          marginBottom: "8px",
        }}
      >
        {region.chr}:{region.start.toLocaleString()}-
        {region.end.toLocaleString()}
      </div>

      {/* Gene name */}
      <div
        style={{
          fontSize: "18px",
          fontWeight: "600",
          color: "#fff",
        }}
      >
        {region.gene}
      </div>
    </motion.div>
  );
}

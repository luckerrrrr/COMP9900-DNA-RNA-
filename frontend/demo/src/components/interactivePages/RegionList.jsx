import { motion } from "framer-motion";
import RegionCard from "./RegionCard";

export default function RegionList({
  regions,
  selectedRegion,
  onSelectRegion,
  onViewAll,
  modelName,
}) {
  return (
    <>
      <style>
        {`
          .region-cards-scroll::-webkit-scrollbar {
            width: 8px;
          }
          .region-cards-scroll::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
          }
          .region-cards-scroll::-webkit-scrollbar-thumb {
            background: rgba(100, 181, 246, 0.5);
            border-radius: 4px;
          }
          .region-cards-scroll::-webkit-scrollbar-thumb:hover {
            background: rgba(100, 181, 246, 0.8);
          }
        `}
      </style>

      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        style={{
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(10px)",
          borderRadius: "16px",
          padding: "24px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          display: "flex",
          flexDirection: "column",
          height: "fit-content",
        }}
      >
        {/* title */}
        <h3
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: "#64b5f6",
            marginBottom: "20px",
            margin: "0 0 20px 0",
          }}
        >
          Predictions ({modelName})
        </h3>

        {/* card area  */}
        <div
          className="region-cards-scroll"
          style={{
            maxHeight: "480px", 
            overflowY: "auto",
            marginBottom: "16px",
            paddingRight: "8px", 
          }}
        >
          {regions.map((region, index) => (
            <RegionCard
              key={index}
              region={region}
              index={index}
              isSelected={
                selectedRegion &&
                selectedRegion.start === region.start &&
                selectedRegion.end === region.end
              }
              onClick={() => onSelectRegion(region)}
            />
          ))}
        </div>

        {/* View All button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onViewAll}
          style={{
            width: "100%",
            padding: "12px",
            background: "rgba(100, 181, 246, 0.1)",
            border: "1px solid #64b5f6",
            borderRadius: "8px",
            color: "#64b5f6",
            fontSize: "16px",
            fontWeight: "600",
            cursor: "pointer",
          }}
        >
          View All Predictions
        </motion.button>
      </motion.div>
    </>
  );
}

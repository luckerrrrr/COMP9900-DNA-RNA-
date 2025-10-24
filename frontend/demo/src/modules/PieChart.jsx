import React from "react";
import { motion } from "framer-motion";

export default function PieChart() {
  const data = [
    { label: "Conserved lncRNA", value: 42, color: "#00ff88" },
    { label: "Species-specific lncRNA", value: 35, color: "#00d4ff" },
    { label: "Low conservation", value: 23, color: "#ff6b9d" }
  ];

  let currentAngle = 0;

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: "40px"
    }}>
      <h3 style={{ fontSize: "28px", color: "#00d4ff", textAlign: "center" }}>
      Analysis of lncRNA conservation distribution
      </h3>
      
      <div style={{ display: "flex", alignItems: "center", gap: "60px", flexWrap: "wrap", justifyContent: "center" }}>
        {/* Pie chart */}
        <div style={{ position: "relative", width: "250px", height: "250px" }}>
          <svg width="250" height="250" style={{ transform: "rotate(-90deg)" }}>
            {data.map((item, index) => {
              const percent = (item.value / 100) * 360;
              const startAngle = currentAngle;
              currentAngle += percent;
              
              return (
                <motion.circle
                  key={index}
                  cx="125"
                  cy="125"
                  r="100"
                  fill="none"
                  stroke={item.color}
                  strokeWidth="30"
                  strokeDasharray={`${2 * Math.PI * 100}`}
                  initial={{ strokeDashoffset: 2 * Math.PI * 100 }}
                  animate={{ 
                    strokeDashoffset: 2 * Math.PI * 100 * (1 - item.value / 100)
                  }}
                  transition={{ duration: 1.5, delay: index * 0.3 }}
                  strokeLinecap="round"
                />
              );
            })}
          </svg>
          
          <div style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            textAlign: "center"
          }}>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 1, duration: 0.5 }}
              style={{ fontSize: "32px", fontWeight: "bold", color: "#00ff88" }}
            >
              42%
            </motion.div>
            <div style={{ fontSize: "14px", color: "rgba(255, 255, 255, 0.6)" }}>
            Conserved regions
            </div>
          </div>
        </div>

        {/* legend */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {data.map((item, index) => (
            <motion.div 
              key={index} 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1 + index * 0.2 }}
              style={{ display: "flex", alignItems: "center", gap: "12px" }}
            >
              <div style={{
                width: "20px",
                height: "20px",
                borderRadius: "4px",
                background: item.color
              }} />
              <span style={{ fontSize: "16px", color: "#fff" }}>
                {item.label}: <strong style={{ color: item.color }}>{item.value}%</strong>
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5 }}
        style={{
          textAlign: "center",
          color: "rgba(255, 255, 255, 0.7)",
          maxWidth: "600px",
          lineHeight: "1.6"
        }}
      >
        42% of lncRNAs are highly conserved across species, suggesting that these regions may have important biological functions, while 35% of lncRNAs are species-specific, reflecting functional differentiation during evolution
      </motion.p>
    </div>
  );
}
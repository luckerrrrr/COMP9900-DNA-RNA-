import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ClassifierSection from "../components/training/ClassifierSection";
import HyperparameterSection from "../components/training/HyperparameterSection";
import { FcTreeStructure, FcSettings } from "react-icons/fc";

export default function Module4Training() {
  const [activeSection, setActiveSection] = useState(1);

  const sections = [
    {
      id: 1,
      name: "Classifier",
      icon: <FcTreeStructure />,
      subtitle: "Classification Head",
    },
    {
      id: 2,
      name: "Fine-tuning",
      icon: <FcSettings />,
      subtitle: "Hyperparameters",
    },
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "5%",
        color: "#fff",
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
        Training & Fine-tuning Pipeline
      </motion.h2>


      {/* Section tabs */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "16px",
          marginBottom: "60px",
          flexWrap: "wrap",
        }}
      >
        {sections.map((section) => (
          <SectionTab
            key={section.id}
            section={section}
            isActive={activeSection === section.id}
            onClick={() => setActiveSection(section.id)}
          />
        ))}
      </motion.div>

      {/* Section content with animation */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeSection}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -30 }}
          transition={{ duration: 0.4 }}
        >
          {activeSection === 1 && <ClassifierSection />}
          {activeSection === 2 && <HyperparameterSection />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// Section tab button component
function SectionTab({ section, isActive, onClick }) {
  return (
    <motion.button
      whileHover={{ scale: 1.05, y: -3 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      style={{
        padding: "16px 28px",
        borderRadius: "12px",
        background: isActive
          ? "linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(0, 150, 200, 0.2))"
          : "rgba(255, 255, 255, 0.05)",
        border: isActive
          ? "2px solid #00d4ff"
          : "1px solid rgba(255, 255, 255, 0.1)",
        color: isActive ? "#00d4ff" : "rgba(255, 255, 255, 0.6)",
        fontSize: "16px",
        fontWeight: "600",
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "6px",
        minWidth: "140px",
        boxShadow: isActive ? "0 0 30px rgba(0, 212, 255, 0.3)" : "none",
        transition: "all 0.3s ease",
      }}
    >
      <div style={{ fontSize: "24px" }}>{section.icon}</div>
      <div>{section.name}</div>
      <div
        style={{
          fontSize: "11px",
          opacity: 0.7,
          fontWeight: "400",
        }}
      >
        {section.subtitle}
      </div>
    </motion.button>
  );
}

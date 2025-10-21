import { motion } from "framer-motion";
import { STEP_DESCRIPTIONS } from "../../constants/pipelineSteps";
import DataAnimation from "./animations/DataAnimation"; // ← 导入

export default function DetailSection({ activeStep, steps }) {
  const currentStep = steps[activeStep - 1];

  return (
    <motion.div
      key={activeStep}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{
        background: "rgba(255, 255, 255, 0.03)",
        borderRadius: "20px",
        padding: "40px",
        border: "1px solid rgba(0, 212, 255, 0.2)",
        minHeight: "400px",
      }}
    >
      <h3
        style={{
          color: "#00d4ff",
          fontSize: "35px",
          marginBottom: "20px",
        }}
      >
        Step {activeStep}: {currentStep.title} {currentStep.subtitle}
      </h3>

      {/* Animation Area */}
      <div
        style={{
          background: "rgba(255, 255, 255, 0.05)",
          borderRadius: "12px",
          height: "300px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "24px",
          border: "1px solid rgba(0, 212, 255, 0.2)",
        }}
      >
        {activeStep === 1 && <DataAnimation />} 
        {activeStep !== 1 && (
          <div style={{ textAlign: "center", opacity: 0.5 }}>
            <div style={{ fontSize: "48px", marginBottom: "12px" }}>
              {currentStep.icon}
            </div>
            <div>Animation for {currentStep.title} goes here</div>
          </div>
        )}
      </div>

      <div style={{ color: "rgba(255, 255, 255, 0.7)", lineHeight: 1.8 }}>
        {STEP_DESCRIPTIONS[activeStep]}
      </div>
    </motion.div>
  );
}

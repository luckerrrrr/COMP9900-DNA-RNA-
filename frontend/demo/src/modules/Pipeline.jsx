import { motion } from "framer-motion";
import { useState } from "react";
import StepCards from "../components/pipeline/StepCards";
import DetailSection from "../components/pipeline/DetailSection";
import { PIPELINE_STEPS } from "../constants/pipelineSteps";
import { SiJfrogpipelines } from "react-icons/si";


export default function Module2Pipeline() {
  const [activeStep, setActiveStep] = useState(null);

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
        <SiJfrogpipelines /> Data Processing Pipeline
      </motion.h2>

      {/* Step Cards */}
      <StepCards
        steps={PIPELINE_STEPS}
        activeStep={activeStep}
        onStepClick={setActiveStep}
      />

      {/* Detail Section */}
      <DetailSection activeStep={activeStep} steps={PIPELINE_STEPS} />
    </div>
  );
}

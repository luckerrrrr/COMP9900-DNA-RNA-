import { motion } from "framer-motion";
import { STEP_DESCRIPTIONS } from "../../constants/pipelineSteps";
import DataAnimation from "./animations/DataAnimation";
import MSAAnimation from "./animations/MSAAnimation";
import TokenAnimation from "./animations/TokenAnimation";
import EmbedAnimation from "./animations/EmbedAnimation";
import ClassificationAnimation from "./animations/ClassificationAnimation";
import EvalAnimation from "./animations/EvalAnimation";
import { FaArrowUp } from "react-icons/fa";
import ClassifierExplanation from "./animations/ClassifierExplanation"

export default function PipelineDetailSection({ activeStep, steps }) {
  if (!activeStep) {
    return (
      <div
        style={{
          height: "500px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "24px",
        }}
      >
        <div style={{ textAlign: "center", opacity: 0.5 }}>
          <div
            style={{ fontSize: "48px", marginBottom: "16px", color: "#00d4ff" }}
          >
            <FaArrowUp />
          </div>
          <div style={{ fontSize: "40px", color: "rgba(255, 255, 255, 0.7)" }}>
            Click a step above to view details
          </div>
        </div>
      </div>
    );
  }

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
        border: "2px solid rgba(0, 212, 255, 0.2)",
        minHeight: "400px",
        width: "80%",
        margin: "40px auto 0 auto",
      }}
    >
      {/* <h3
        style={{
          color: "#00d4ff",
          fontSize: "35px",
          marginBottom: "20px",
        }}
      >
        Step {activeStep}: {currentStep.title} {currentStep.subtitle}
      </h3> */}

      {/* Animation Area */}
      <div
        style={{
          height: "500px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "24px",
        }}
      >
        {activeStep === 1 && <DataAnimation />}
        {activeStep === 2 && <MSAAnimation />}
        {activeStep === 3 && <TokenAnimation />}
        {activeStep === 4 && <EmbedAnimation />}
        {activeStep === 5 && <ClassificationAnimation />}
        {activeStep === 6 && <EvalAnimation />}
      </div>

      {/* <div style={{ color: "rgba(255, 255, 255, 0.7)", lineHeight: 1.8, fontSize: "20px" }}>
        {STEP_DESCRIPTIONS[activeStep]}
      </div> */}
    </motion.div>
  );
}

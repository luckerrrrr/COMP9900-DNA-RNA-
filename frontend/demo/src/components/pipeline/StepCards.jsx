import StepCard from "./StepCard";

export default function StepCards({ steps, activeStep, onStepClick }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        gap: "20px",
        marginBottom: "50px",
        flexWrap: "wrap",
      }}
    >
      {steps.map((step, index) => (
        <div key={step.id} style={{ display: "flex", alignItems: "center" }}>
          {/* Step Card */}
          <StepCard
            step={step}
            index={index}
            isActive={activeStep === step.id}
            onClick={() => onStepClick(step.id)}
          />

          {/* Arrow between cards */}
          {index < steps.length - 1 && (
            <div
              style={{
                fontSize: "24px",
                color: "#00d4ff",
                opacity: 0.5,
                margin: "0 10px",
              }}
            >
              →
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

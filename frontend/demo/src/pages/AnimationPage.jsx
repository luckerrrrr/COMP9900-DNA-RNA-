import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Step1DataPreprocessing from "../components/animationPages/Step1DataPreprocessing";
import Step2MSAAlignment from "../components/animationPages/Step2MSAAlignment";
import Step3Tokenisation from "../components/animationPages/Step3Tokenisation";
import Step4Embedding from "../components/animationPages/Step4Embedding";
import Step5Classification from "../components/animationPages/Step5Classification";
import Step6Evaluation from "../components/animationPages/Step6Evaluation";

export default function AnimationPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState([]);


  const steps = [
    { component: Step1DataPreprocessing },  
    { component: Step2MSAAlignment },       
    { component: Step3Tokenisation },      
    { component: Step4Embedding },         
    { component: Step5Classification },    
    { component: Step6Evaluation },        
  ];


  const displayOrder = [0, 1, 2, 5, 4, 3];


  useEffect(() => {
    if (currentStep < steps.length) {
      const timer = setTimeout(() => {
        setCurrentStep(currentStep + 1);
        setCompletedSteps((prev) => [...prev, currentStep]);
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [currentStep, steps.length]);

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "linear-gradient(rgba(0, 10, 24, 0.8), rgba(0, 10, 24, 0.8)), url('/dna.png') center/cover fixed no-repeat",
        color: "#fff",
        padding: "40px",
        position: "relative",
      }}
    >
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => navigate("/")}
        style={{
          position: "fixed",
          top: "20px",
          left: "20px",
          padding: "12px 24px",
          background: "rgba(255, 255, 255, 0.1)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.3)",
          borderRadius: "8px",
          color: "#fff",
          cursor: "pointer",
          fontSize: "16px",
          zIndex: 1000,
          fontWeight: "600",
        }}
      >
        Back
      </motion.button>

      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          paddingTop: "80px",
        }}
      >
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{
            fontSize: "clamp(32px, 4vw, 48px)",
            marginBottom: "60px",
            textAlign: "center",
          }}
        >
          Animated Explanation
        </motion.h1>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "50px 40px",
            maxWidth: "1100px",
            margin: "0 auto",
            position: "relative",
          }}
        >
          {displayOrder.map((stepIndex, displayIndex) => {
            const step = steps[stepIndex];
            const StepComponent = step.component;
            const row = Math.floor(displayIndex / 3);
            const col = displayIndex % 3;

            return (
              <div
                key={displayIndex}
                style={{
                  position: "relative",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <StepComponent
                  isActive={currentStep === stepIndex}
                  isCompleted={completedSteps.includes(stepIndex)}
                />

                {row === 0 && col < 2 && (
                  <motion.div
                    initial={{ opacity: 0.3 }}
                    animate={{
                      opacity: completedSteps.includes(stepIndex) ? 1 : 0.3,
                    }}
                    style={{
                      position: "absolute",
                      right: "-35px",
                      fontSize: "32px",
                      color: "#64b5f6",
                      zIndex: 10,
                    }}
                  >
                    →
                  </motion.div>
                )}

                {displayIndex === 2 && (
                  <motion.div
                    initial={{ opacity: 0.3 }}
                    animate={{
                      opacity: completedSteps.includes(2) ? 1 : 0.3,
                    }}
                    style={{
                      position: "absolute",
                      bottom: "-45px",
                      fontSize: "32px",
                      color: "#64b5f6",
                      zIndex: 10,
                      transform: "rotate(90deg)",
                    }}
                  >
                    →
                  </motion.div>
                )}

                {row === 1 && col > 0 && (
                  <motion.div
                    initial={{ opacity: 0.3 }}
                    animate={{
                      opacity: completedSteps.includes(
                        displayOrder[displayIndex - 1]
                      )
                        ? 1
                        : 0.3,
                    }}
                    style={{
                      position: "absolute",
                      left: "-35px",
                      fontSize: "32px",
                      color: "#64b5f6",
                      zIndex: 10,
                    }}
                  >
                    ←
                  </motion.div>
                )}
              </div>
            );
          })}
        </div>

        {currentStep >= steps.length && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              textAlign: "center",
              marginTop: "60px",
            }}
          >
            <button
              onClick={() => {
                setCurrentStep(0);
                setCompletedSteps([]);
              }}
              style={{
                padding: "12px 32px",
                background: "rgba(100, 200, 255, 0.2)",
                border: "1px solid rgba(100, 200, 255, 0.5)",
                borderRadius: "8px",
                color: "#fff",
                cursor: "pointer",
                fontSize: "16px",
                fontWeight: "600",
              }}
            >
              Replay Animation
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
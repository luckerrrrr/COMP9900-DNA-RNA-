import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import DNA3D from "../components/intro/DNA3D";


export default function Module1Intro() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        minHeight: "100vh",
        position: "relative",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "8%",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "90vw",
          height: "90vh",
          opacity: 0.3,
          zIndex: 1,
        }}
      >
        <DNA3D width="100%" height="100%" />
      </div>

      <motion.h1
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        style={{
          fontSize: "clamp(32px, 5vw, 64px)",
          fontWeight: "bold",
          maxWidth: "900px",
          lineHeight: "1.2",
          margin: 0,
          zIndex: 10,
          alignSelf: "flex-start",
          textAlign: "left",
        }}
      >
        Finding conserved lncRNA regions across species
      </motion.h1>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "30px",
          alignSelf: "flex-end",
          alignItems: "center",
          zIndex: 10,
          maxWidth: "700px",
        }}
      >
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          style={{
            fontSize: "clamp(16px, 2vw, 22px)",
            lineHeight: 1.8,
            margin: 0,
          }}
        >
          Only 2% of the human genome codes for proteins, but over 98% is
          noncoding. Our project uses GPN and GPN-MSA models to detect conserved
          noncoding RNAs (ncRNAs) across species.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          style={{
            display: "flex",
            gap: "16px",
            flexWrap: "wrap",
            justifyContent: "flex-end",
          }}
        >
          <motion.button
            whileHover={{
              scale: 1.05,
              boxShadow: "0 8px 20px rgba(255, 255, 255, 0.2)",
            }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate("/animation")}
            style={{
              padding: "14px 28px",
              fontSize: "clamp(14px, 1.5vw, 16px)",
              fontWeight: "600",
              background: "rgba(255, 255, 255, 0.15)",
              backdropFilter: "blur(10px)",
              border: "1px solid rgba(255, 255, 255, 0.3)",
              borderRadius: "10px",
              color: "#fff",
              cursor: "pointer",
              minWidth: "160px",
            }}
          >
             Animated Explanation
          </motion.button>

          <motion.button
            whileHover={{
              scale: 1.05,
              boxShadow: "0 8px 20px rgba(255, 255, 255, 0.2)",
            }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate("/interactive")}
            style={{
              padding: "14px 28px",
              fontSize: "clamp(14px, 1.5vw, 16px)",
              fontWeight: "600",
              background: "rgba(255, 255, 255, 0.15)",
              backdropFilter: "blur(10px)",
              border: "1px solid rgba(255, 255, 255, 0.3)",
              borderRadius: "10px",
              color: "#fff",
              cursor: "pointer",
              minWidth: "160px",
            }}
          >
            Interactive Exploration
          </motion.button>
        </motion.div>
      </div>
    </div>
  );
}

import { motion } from "framer-motion";
import DNA3D from "../components/intro/DNA3D";

export default function Module1Intro() {
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

      <motion.p
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.3 }}
        style={{
          fontSize: "clamp(16px, 2vw, 22px)",
          lineHeight: 1.8,
          maxWidth: "700px",
          margin: 0,
          zIndex: 10,
          alignSelf: "flex-end", 
        }}
      >
        Only 2% of the human genome codes for proteins, but over 98% is
        noncoding. Our project uses GPN and GPN-MSA models to detect conserved
        noncoding RNAs (ncRNAs) across species.
      </motion.p>
    </div>
  );
}

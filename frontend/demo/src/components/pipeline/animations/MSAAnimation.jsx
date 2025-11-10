import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function MSAAnimation() {
  const [stage, setStage] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  // Auto advance stages
  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      setStage((prev) => {
        if (prev === 2) {
          setIsPlaying(false);
          return 2;
        }
        return prev + 1;
      });
    }, 4000);
    return () => clearInterval(timer);
  }, [isPlaying]);

  // Replay function
  const handleReplay = () => {
    setStage(0);
    setIsPlaying(true);
  };

  return (
    <div
      style={{
        width: "100%",
        height: "400px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "20px",
      }}
    >
      {/* Stage indicator with replay button */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          width: "100%",
          maxWidth: "800px",
          marginBottom: "10px",
        }}
      >
        <div style={{ fontSize: "30px", color: "#00d4ff" }}>
          {stage === 0 && "Unaligned Sequences"}
          {stage === 1 && "Alignment Process"}
          {stage === 2 && "Conserved Regions"}
        </div>

        {/* Replay button */}
        {!isPlaying && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleReplay}
            style={{
              background: "rgba(0, 212, 255, 0.2)",
              border: "1px solid #00d4ff",
              color: "#00d4ff",
              padding: "8px 20px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "20px",
              fontWeight: "500",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span>Replay</span>
          </motion.button>
        )}
      </div>

      {/* Stage description */}
      <div
        style={{
          fontSize: "25px",
          color: "rgba(255, 255, 255, 0.6)",
          textAlign: "center",
          maxWidth: "700px",
          minHeight: "10px",
        }}
      >
        {stage === 0 &&
          "DNA sequences from different species are initially misaligned"}
        {stage === 1 &&
          "Alignment algorithm inserts gaps (-) to match homologous regions"}
        {stage === 2 &&
          "Conserved regions (highlighted) indicate functional importance across species"}
      </div>

      {/* Animation content */}
      <div style={{ width: "100%", maxWidth: "800px" }}>
        {stage === 0 && <UnalignedSequences />}
        {stage === 1 && <AlignmentProcess />}
        {stage === 2 && <ConservedRegions />}
      </div>
    </div>
  );
}

// Stage 0: Unaligned sequences
function UnalignedSequences() {
  const sequences = [
    { species: "🧑 Human", seq: "ATCGATCG--TCGATCG", offset: 0, color: "#00d4ff" },
    { species: "🐭 Mouse", seq: "--ATCGATCGTCGA--", offset: 0, color: "#ff6b9d" },
    { species: "🐵 Chimp", seq: "ATCG--ATCGTCGATCG", offset: 0, color: "#00ff88" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {sequences.map((item, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.2 }}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "20px",
            justifyContent: "center",
            width: "100%",
          }}
        >
          <div
            style={{
              minWidth: "120px",
              fontSize: "30px",
              color: item.color,
              fontWeight: "500",
            }}
          >
            {item.species}
          </div>
          <div
            style={{
              fontFamily: "monospace",
              fontSize: "30px",
              letterSpacing: "3px",
              transform: `translateX(${item.offset}px)`,
              transition: "transform 0.3s",
            }}
          >
            {item.seq.split("").map((base, j) => (
              <span key={j} style={{ color: getBaseColor(base) }}>
                {base}
              </span>
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// Stage 1: Alignment process
function AlignmentProcess() {
  const sequences = [
    { species: "🧑 Human", seq: "ATCGATCG--TCGATCG", offset: 0, color: "#00d4ff" },
    { species: "🐭 Mouse", seq: "--ATCGATCGTCGA--", offset: 0, color: "#ff6b9d" },
    { species: "🐵 Chimp", seq: "ATCG--ATCGTCGATCG", offset: 0, color: "#00ff88" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {sequences.map((item, i) => (
        <motion.div
          key={i}
          initial={{ x: i === 1 ? 80 : i === 2 ? -60 : 0 }}
          animate={{ x: 0 }}
          transition={{ duration: 1.5, delay: 0.3, ease: "easeInOut" }}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            gap: "20px",
          }}
        >
          <div
            style={{
              minWidth: "120px",
              fontSize: "30px",
              color: item.color,
              fontWeight: "500",
            }}
          >
            {item.species}
          </div>
          <div
            style={{
              fontFamily: "monospace",
              fontSize: "30px",
              letterSpacing: "3px",
            }}
          >
            {item.seq.split("").map((base, j) => (
              <motion.span
                key={j}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 + j * 0.05 }}
                style={{ color: getBaseColor(base) }}
              >
                {base}
              </motion.span>
            ))}
          </div>
        </motion.div>
      ))}

      {/* Alignment guide lines */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.3 }}
        transition={{ delay: 1.5 }}
        style={{
          position: "absolute",
          top: "50%",
          left: "120px",
          width: "calc(100% - 140px)",
          height: "100%",
          pointerEvents: "none",
        }}
      >
        {[...Array(17)].map((_, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${i * 24}px`,
              top: 0,
              bottom: 0,
              width: "1px",
              background: "rgba(0, 212, 255, 0.2)",
            }}
          />
        ))}
      </motion.div>
    </div>
  );
}

// Stage 2: Conserved regions highlighted
function ConservedRegions() {
  const sequences = [
    { species: "🧑 Human", seq: "ATCGATCG--TCGATCG", color: "#00d4ff" },
    { species: "🐭 Mouse", seq: "--ATCGATCGTCGA--", color: "#ff6b9d" },
    { species: "🐵 Chimp", seq: "ATCG--ATCGTCGATCG", color: "#00ff88" },
  ];

  // Conserved positions (where bases match across species)
  const conservedPositions = [2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14];

  return (
    <div style={{ position: "relative" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {sequences.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "20px",
              justifyContent: "center",
              width: "100%",
            }}
          >
            <div
              style={{
                minWidth: "120px",
                fontSize: "30px",
                color: item.color,
                fontWeight: "500",
              }}
            >
              {item.species}
            </div>
            <div
              style={{
                fontFamily: "monospace",
                fontSize: "30px",
                letterSpacing: "3px",
                position: "relative",
              }}
            >
              {item.seq.split("").map((base, j) => {
                const isConserved = conservedPositions.includes(j);
                return (
                  <span
                    key={j}
                    style={{
                      color: getBaseColor(base),
                      position: "relative",
                      display: "inline-block",
                    }}
                  >
                    {/* Conserved region highlight */}
                    {isConserved && (
                      <motion.span
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 0.3, scale: 1 }}
                        transition={{ delay: j * 0.05 }}
                        style={{
                          position: "absolute",
                          top: "-4px",
                          left: "-2px",
                          right: "-2px",
                          bottom: "-4px",
                          background: "#00ff88",
                          borderRadius: "4px",
                          zIndex: -1,
                        }}
                      />
                    )}
                    {base}
                  </span>
                );
              })}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Conservation indicator */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        style={{
          marginTop: "24px",
          padding: "12px",
          background: "rgba(0, 255, 136, 0.1)",
          border: "1px solid rgba(0, 255, 136, 0.3)",
          borderRadius: "8px",
          fontSize: "30px",
          color: "#00ff88",
          textAlign: "center",
        }}
      >
        ✓ {conservedPositions.length} conserved positions identified
      </motion.div>
    </div>
  );
}

// Helper: Get color for DNA base
function getBaseColor(base) {
  const colors = {
    A: "#00ff88", // Green
    T: "#ff5757", // Red
    C: "#00d4ff", // Blue
    G: "#ffd700", // Yellow
    "-": "#666", // Gap (gray)
  };
  return colors[base] || "#fff";
}
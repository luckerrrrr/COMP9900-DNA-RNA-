import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { motion } from "framer-motion";

export default function Module3GPN() {
  const svgRef = useRef();
  const [step, setStep] = useState(0);

  // NOTE: Keeping user's original baseColors
  const baseColors = {
    A: "#ff4d4d", // Red
    T: "#4d4dff", // Blue
    C: "#4dff4d", // Green
    G: "#ffff4d", // Yellow
    mask: "#888888",
    gap: "#cccccc",
  };
  const bases = ["A", "T", "C", "G"];
  const seqLength = 60;
  // Use useCallback or React.memo if performance is an issue, but useState is fine here
  const [sequence] = useState(() =>
    Array.from(
      { length: seqLength },
      () => bases[Math.floor(Math.random() * 4)]
    )
  );
  const [mouseSequence] = useState(() =>
    Array.from(
      { length: seqLength },
      () => bases[Math.floor(Math.random() * 4)]
    )
  );

  const maskedIndices = useRef([]);

  // --- D3 Sequence Visualization Helper for Step 0 ---
  // g: The D3 group element already translated for centering
  const drawSequenceComparison = (g, data, startY, label, isPlant = true) => {
    if (!g.node()) return; // Safety check for the group element

    const rectSize = 25;
    const padding = 3;
    const labelX = 0;

    const labelColor = isPlant ? "#2ecc71" : "#e74c3c";
    const gapColor = baseColors.gap;

    // 绘制标签 (Label)
    g.append("text")
      .attr("x", labelX)
      .attr("y", startY + rectSize / 2 + 5)
      .attr("text-anchor", "end")
      .attr("font-size", "14px")
      .attr("font-weight", "700")
      .attr("fill", labelColor)
      .text(label);

    // 绘制矩形 (Rectangles)
    g.selectAll(`.rect-${label}-${startY}`)
      .data(data)
      .enter()
      .append("rect")
      .attr("class", `rect-${label}-${startY}`)
      .attr("x", (d, i) => i * (rectSize + padding) + 10) // 10px offset from label end
      .attr("y", startY)
      .attr("width", rectSize)
      .attr("height", rectSize)
      .attr("rx", 3)
      .attr("fill", (d) => (d === "-" ? gapColor : baseColors[d]));

    // 绘制碱基文本 (Base Text)
    g.selectAll(`text.${label}-${startY}`)
      .data(data)
      .enter()
      .append("text")
      .attr("class", `text-${label}-${startY}`)
      .attr("x", (d, i) => i * (rectSize + padding) + rectSize / 2 + 10)
      .attr("y", startY + rectSize / 2 + 5)
      .attr("text-anchor", "middle")
      .attr("font-size", "14px")
      .attr("font-weight", "700")
      .attr("fill", "#333")
      .text((d) => (d === "-" ? "" : d));
  };
  // --------------------------------------------------

  const actions = [
    // Step 0: Plant vs Mammal (D3 Drawn, Centered)
    () => {
      const svg = d3.select(svgRef.current);
      if (!svgRef.current) return;
      svg.selectAll("*").remove();

      const svgWidth = 800;
      const rectSize = 25;
      const padding = 3;
      const maxBlocks = 14;
      const labelSpace = 60;
      const contentWidth = maxBlocks * (rectSize + padding) + labelSpace;
      const startX = (svgWidth - contentWidth) / 2; // X translation for centering

      d3.select(svgRef.current).attr("height", 350);

      const g = svg.append("g").attr("transform", `translate(${startX}, 0)`);

      // Data based on the image
      const plantSequence1 = [
        "T",
        "T",
        "G",
        "A",
        "C",
        "T",
        "T",
        "C",
        "T",
        "C",
        "A",
        "G",
        "G", 
        "A",
      ];
      const plantSequence2 = [
        "G",
        "T",
        "A",
        "A",
        "C",
        "T",
        "T",
        "C",
        "A",
        "G",
        "A",
        "T",
        "G",
        "A",
      ];
      const riceSequence = [
        "G",
        "T",
        "C",
        "A",
        "C",
        "-",
        "-",
        "G",
        "A",
        "C",
        "A",
        "G",
        "G",
        "C",
      ];

      const cowSequence = [
        "G",
        "T",
        "C",
        "A",
        "C",
        "T",
        "T",
        "G",
        "A",
        "G",
        "A",
        "G",
        "G",
        "C",
      ];
      const pigSequence = [
        "G",
        "T",
        "C",
        "A",
        "C",
        "T",
        "T",
        "G",
        "A",
        "G",
        "A",
        "C",
        "G",
        "C",
      ];

      // --- Plants Section ---
      drawSequenceComparison(g, plantSequence1, 20, "Maize", true);
      drawSequenceComparison(g, plantSequence2, 50, "Maize", true);
      drawSequenceComparison(g, riceSequence, 80, "Rice", true);

      // --- Explanation Text (Relative to SVG) ---
      svg
        .append("text")
        .attr("x", svgWidth / 2)
        .attr("y", 170)
        .attr("text-anchor", "middle")
        .attr("font-size", "22px")
        .attr("font-weight", "500")
        .attr("fill", "#ddd")
        .text("Sequence diversity is higher in plants,");

      svg
        .append("text")
        .attr("x", svgWidth / 2)
        .attr("y", 200)
        .attr("text-anchor", "middle")
        .attr("font-size", "20px")
        .attr("font-weight", "400")
        .attr("fill", "#aaa")
        .text("likely due to lower effective population size in mammals.");

      // 绘制分隔线
      svg
        .append("line")
        .attr("x1", startX + labelSpace)
        .attr("y1", 240)
        .attr("x2", startX + contentWidth)
        .attr("y2", 240)
        .attr("stroke", "#555")
        .attr("stroke-dasharray", "4 4");

      // --- Mammals Section ---
      drawSequenceComparison(g, cowSequence, 260, "Cow", false);
      drawSequenceComparison(g, pigSequence, 290, "Pig", false);
    },

    // Step 1: Show sequence (Reset height and center content)
    () => {
      const svg = d3.select(svgRef.current);
      if (!svgRef.current) return;
      svg.selectAll("*").remove();

      const rectSize = 28;
      const padding = 4;
      const seqWidth = seqLength * (rectSize + padding);
      const svgWidth = 800;
      const startX = (svgWidth - seqWidth) / 2;

      svg.attr("height", 200);

      const g = svg.append("g").attr("transform", `translate(${startX}, 0)`);

      const humanY = 50;
      const mouseY = 110;

      // Human tag
      g.append("text")
        .attr("class", "species-label human-label")
        .attr("x", 0)
        .attr("y", humanY + rectSize / 2 - 20)
        .attr("text-anchor", "start")
        .attr("font-size", "18px")
        .attr("font-weight", "700")
        .attr("fill", "rgb(0, 212, 255)")
        .text("🧑 Human");

      // Mapping human sequences
      g.selectAll("rect.human")
        .data(sequence)
        .enter()
        .append("rect")
        .attr("class", "human")
        .attr("x", (d, i) => i * (rectSize + padding))
        .attr("y", humanY)
        .attr("width", rectSize)
        .attr("height", rectSize)
        .attr("rx", 5)
        .attr("fill", (d) => baseColors[d]);

      g.selectAll("text.human")
        .data(sequence)
        .enter()
        .append("text")
        .attr("class", "human")
        .attr("x", (d, i) => i * (rectSize + padding) + rectSize / 2)
        .attr("y", humanY + rectSize / 2 + 6)
        .attr("text-anchor", "middle")
        .attr("font-size", "18px")
        .attr("font-weight", "700")
        .text((d) => d);

      // Mouse tag
      g.append("text")
        .attr("class", "species-label mouse-label")
        .attr("x", 0)
        .attr("y", mouseY + rectSize / 2 - 20)
        .attr("text-anchor", "start")
        .attr("font-size", "18px")
        .attr("font-weight", "700")
        .attr("fill", "rgb(255, 107, 157")
        .text("🐭 Mouse");

      // Mapping mouse sequences
      g.selectAll("rect.mouse")
        .data(mouseSequence)
        .enter()
        .append("rect")
        .attr("class", "mouse")
        .attr("x", (d, i) => i * (rectSize + padding))
        .attr("y", mouseY)
        .attr("width", rectSize)
        .attr("height", rectSize)
        .attr("rx", 5)
        .attr("fill", (d) => baseColors[d]);

      g.selectAll("text.mouse")
        .data(mouseSequence)
        .enter()
        .append("text")
        .attr("class", "mouse")
        .attr("x", (d, i) => i * (rectSize + padding) + rectSize / 2)
        .attr("y", mouseY + rectSize / 2 + 6)
        .attr("text-anchor", "middle")
        .attr("font-size", "18px")
        .attr("font-weight", "700")
        .text((d) => d);
    },
    // Step 2: Mask 15% of bases
    () => {
      const svg = d3.select(svgRef.current);
      if (!svgRef.current) return;

      svg.selectAll(".mouse").remove();
      svg.selectAll(".species-label").remove();

      maskedIndices.current = sequence
        .map((b, i) => (Math.random() < 0.15 ? i : null))
        .filter((d) => d !== null);

      svg
        .selectAll("rect.human")
        .transition()
        .duration(500)
        .attr("fill", (d, i) =>
          maskedIndices.current.includes(i) ? baseColors.mask : baseColors[d]
        );
    },
    // Step 3: Show attention (context learning)
    () => {
      const svg = d3.select(svgRef.current);
      if (!svgRef.current) return;

      const rectSize = 28;
      const padding = 4;
      const humanY = 50;

      // Select the centered group to append attention lines
      const g = svg.select("g");
      const lines = g.append("g").attr("class", "attention-lines");

      maskedIndices.current.forEach((maskIdx, i) => {
        let left = maskIdx - 1;
        while (left >= 0 && maskedIndices.current.includes(left)) left--;
        let right = maskIdx + 1;
        while (right < sequence.length && maskedIndices.current.includes(right))
          right++;

        if (left >= 0 && right < sequence.length) {
          const x1 = left * (rectSize + padding) + rectSize / 2;
          const x2 = right * (rectSize + padding) + rectSize / 2;
          const y = humanY + rectSize / 2;

          lines
            .append("path")
            .attr(
              "d",
              `M${x1},${y} Q${maskIdx * (rectSize + padding) + rectSize / 2},${
                y - 80
              } ${x2},${y}`
            )
            .attr("stroke", "#ff00ff")
            .attr("stroke-width", 3)
            .attr("fill", "none")
            .attr("opacity", 0)
            .transition()
            .delay(i * 100)
            .duration(800)
            .attr("opacity", 0.8);
        }
      });
    },
    // Step 4: Predict masked bases
    () => {
      const svg = d3.select(svgRef.current);
      if (!svgRef.current) return;

      svg.selectAll(".attention-lines").remove();
      maskedIndices.current.forEach((idx, i) => {
        const base = sequence[idx];
        svg
          .selectAll("rect.human")
          .filter((d, j) => j === idx)
          .transition()
          .delay(i * 200)
          .duration(400)
          .attr("fill", baseColors[base]);
      });
    },
    // Step 5: Final flash
    () => {
      const svg = d3.select(svgRef.current);
      if (!svgRef.current) return;

      svg
        .transition()
        .duration(600)
        .ease(d3.easeSin)
        .style("filter", "drop-shadow(0px 0px 10px #00ffff)")
        .transition()
        .duration(600)
        .style("filter", "none");
    },
  ];

  // Custom useEffect to handle actions
  useEffect(() => {
    actions[step]();
  }, [step]);

  // Initial run of Step 0 on mount
  useEffect(() => {
    // Only run on mount, unless step is managed by the main useEffect
    actions[0]();
  }, []);

  const stepTexts = [
    "Step 0: Plant vs Mammal Gene-Genome Comparison",
    "Step 1: Input DNA Sequence and Retrain (Human and Mouse)",
    "Step 2: Model Hides 15% of Bases to Predict Them Back",
    "Step 3: GPN Learns Context Relationships Between Bases (Attention)",
    "Step 4: GPN Predicts Masked Bases",
    "Step 5: GPN Understands DNA Grammar",
  ];

  const handleNext = () => {
    if (step < actions.length - 1) {
      setStep((s) => s + 1);
    } else {
      setStep(0); // Loop back to Step 0
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        color: "#fff",
        textAlign: "center",
        padding: "20px", // Add padding for better look
      }}
    >
      <h2 style={{ fontSize: "32px", marginBottom: "20px" }}>
        GPN Model Animation
      </h2>
      {/* SVG width is fixed, height adjusts based on step */}
      <svg ref={svgRef} width={800} height={350}></svg>
      <motion.p
        key={step}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        style={{ fontSize: "28px", margin: "20px 0", minHeight: "34px" }}
      >
        {stepTexts[step]}
      </motion.p>
      <button
        onClick={handleNext}
        style={{
          marginTop: "10px",
          padding: "8px 16px",
          cursor: "pointer",
          background:
            step < actions.length - 1
              ? "rgba(0, 212, 255, 0.2)"
              : "rgba(255, 87, 51, 0.2)",
          border: `1px solid ${
            step < actions.length - 1 ? "#00d4ff" : "#ff5733"
          }`,
          color: step < actions.length - 1 ? "#00d4ff" : "#ff5733",
          borderRadius: "8px",
          fontSize: "20px",
          minWidth: "180px",
        }}
      >
        {step < actions.length - 1 ? "Next Step" : "Restart Animation"}
      </button>
    </motion.div>
  );
}

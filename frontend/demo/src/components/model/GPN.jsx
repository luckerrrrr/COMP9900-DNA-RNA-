import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { motion } from "framer-motion";

export default function Module3GPN() {
  const svgRef = useRef();
  const [step, setStep] = useState(0);

  const baseColors = { A: "#ff4d4d", T: "#4d4dff", C: "#4dff4d", G: "#ffff4d", mask: "#888888" };
  const bases = ["A", "T", "C", "G"];
  const seqLength = 60;
  const [sequence] = useState(() => Array.from({ length: seqLength }, () => bases[Math.floor(Math.random() * 4)]));
  const maskedIndices = useRef([]);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const rectSize = 28;
    const padding = 4;

    svg
      .selectAll("rect")
      .data(sequence)
      .enter()
      .append("rect")
      .attr("x", (d, i) => i * (rectSize + padding))
      .attr("y", 80)
      .attr("width", rectSize)
      .attr("height", rectSize)
      .attr("rx", 5)
      .attr("fill", (d) => baseColors[d]);

    svg
      .selectAll("text.base")
      .data(sequence)
      .enter()
      .append("text")
      .attr("x", (d, i) => i * (rectSize + padding) + rectSize / 2)
      .attr("y", 80 + rectSize / 2 + 6)
      .attr("text-anchor", "middle")
      .attr("font-size", "18px")
      .attr("font-weight", "700")
      
      .text((d) => d);
  }, [sequence]);

  const actions = [
    // Step 0: Show sequence
    () => {},
    // Step 1: Mask 15% of bases
    () => {
      const svg = d3.select(svgRef.current);
      maskedIndices.current = sequence
        .map((b, i) => (Math.random() < 0.15 ? i : null))
        .filter((d) => d !== null);

      svg
        .selectAll("rect")
        .transition()
        .duration(500)
        .attr("fill", (d, i) => (maskedIndices.current.includes(i) ? baseColors.mask : baseColors[d]));
    },
    // Step 2: Show attention (context learning)
    () => {
      const svg = d3.select(svgRef.current);
      const width = 800;
      const rectSize = 28;
      const padding = 4;

      const lines = svg.append("g").attr("class", "attention-lines");
      for (let i = 0; i < 10; i++) {
        const x1 = Math.random() * (seqLength * (rectSize + padding));
        const x2 = Math.random() * (seqLength * (rectSize + padding));
        lines
          .append("path")
          .attr("d", `M${x1},80 Q${(x1 + x2) / 2},40 ${x2},80`)
          .attr("stroke", "#ff00ff")
          .attr("stroke-width", 1)
          .attr("fill", "none")
          .attr("opacity", 0)
          .transition()
          .delay(i * 100)
          .duration(800)
          .attr("opacity", 0.4);
      }
    },
    // Step 3: Predict masked bases
    () => {
      const svg = d3.select(svgRef.current);
      maskedIndices.current.forEach((idx, i) => {
        const base = sequence[idx];
        svg
          .selectAll("rect")
          .filter((d, j) => j === idx)
          .transition()
          .delay(i * 200)
          .duration(400)
          .attr("fill", baseColors[base]);
      });
    },
    // Step 4: Final flash
    () => {
      const svg = d3.select(svgRef.current);
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

  useEffect(() => {
    if (step > 0) actions[step]?.();
  }, [step]);

  const stepTexts = [
    "Step 1: Input DNA sequence",
    "Step 2: Model hides 15% of bases to predict them back",
    "Step 3: GPN learns context relationships between bases",
    "Step 4: GPN predicts masked bases",
    "Step 5: GPN understands DNA grammar",
  ];

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
      }}
    >
      <h2 style={{ fontSize: "32px", marginBottom: "20px" }}>
        GPN Model Animation
      </h2>
      <svg ref={svgRef} width={800} height={200}></svg>
      <motion.p
        key={step}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        style={{ fontSize: "28px", margin: "20px 0" }}
      >
        {stepTexts[step]}
      </motion.p>
      <button
        onClick={() => setStep((s) => Math.min(s + 1, stepTexts.length - 1))}
        style={{
          marginTop: "10px",
          padding: "8px 16px",
          cursor: "pointer",
          background: "rgba(0, 212, 255, 0.2)",
          border: "1px solid #00d4ff",
          color: "#00d4ff",
          borderRadius: "8px",
          fontSize: "20px",
          minWidth: "140px",
        }}
      >
        Next
      </button>
    </motion.div>
  );
}
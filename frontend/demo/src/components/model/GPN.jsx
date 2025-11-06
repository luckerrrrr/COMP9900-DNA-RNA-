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
  const [mouseSequence] = useState(() => Array.from({ length: seqLength }, () => bases[Math.floor(Math.random() * 4)]));

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
    // Step 0: plant vs mammal
    () => {
      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove();
      // Load image
      svg.append("image")
         .attr("href", "/plant_vs_mammal.png") 
         .attr("x", 100)
         .attr("y", -10)
         .attr("width", 600)
         .attr("height", 200);
    },
    // Step 1: Show sequence
    () => {
      const svg = d3.select(svgRef.current);

      svg.selectAll("*").remove();
    
      const rectSize = 28;
      const padding = 4;

      // Mapping human sequences
      svg.selectAll("rect.human")
        .data(sequence)
        .enter()
        .append("rect")
        .attr("class", "human")
        .attr("x", (d, i) => i * (rectSize + padding))
        .attr("y", 80)
        .attr("width", rectSize)
        .attr("height", rectSize)
        .attr("rx", 5)
        .attr("fill", d => baseColors[d]);

      svg.selectAll("text.human")
        .data(sequence)
        .enter()
        .append("text")
        .attr("class", "human")
        .attr("x", (d, i) => i * (rectSize + padding) + rectSize / 2)
        .attr("y", 80 + rectSize / 2 + 6)
        .attr("text-anchor", "middle")
        .attr("font-size", "18px")
        .attr("font-weight", "700")
        .text(d => d);

      // Human tag
      svg.append("text")
      .attr("class", "species-label human-label")
      .attr("x", 0)
      .attr("y", 80 + rectSize / 2 - 20)
      .attr("text-anchor", "start")
      .attr("font-size", "18px")
      .attr("font-weight", "700")
      .attr("fill", "rgb(0, 212, 255)") 
      .text("🧑 Human");

      // Mapping mouse sequences
      svg.selectAll("rect.mouse")
        .data(mouseSequence)
        .enter()
        .append("rect")
        .attr("class", "mouse")
        .attr("x", (d, i) => i * (rectSize + padding))
        .attr("y", 140)
        .attr("width", rectSize)
        .attr("height", rectSize)
        .attr("rx", 5)
        .attr("fill", d => baseColors[d]);

      svg.selectAll("text.mouse")
        .data(mouseSequence)
        .enter()
        .append("text")
        .attr("class", "mouse")
        .attr("x", (d, i) => i * (rectSize + padding) + rectSize / 2)
        .attr("y", 140 + rectSize / 2 + 6)
        .attr("text-anchor", "middle")
        .attr("font-size", "18px")
        .attr("font-weight", "700")
        .text(d => d);

      // Mouse tag
      svg.append("text")
      .attr("class", "species-label mouse-label")
      .attr("x", 0)
      .attr("y", 140 + rectSize / 2 - 20)
      .attr("text-anchor", "start")
      .attr("font-size", "18px")
      .attr("font-weight", "700")
      .attr("fill", "rgb(255, 107, 157") 
      .text("🐭 Mouse");
    },
    // Step 2: Mask 15% of bases
    () => {
      const svg = d3.select(svgRef.current);
      svg.selectAll(".mouse").remove();
      svg.selectAll(".species-label").remove();

      maskedIndices.current = sequence
        .map((b, i) => (Math.random() < 0.15 ? i : null))
        .filter((d) => d !== null);

      svg
        .selectAll("rect")
        .transition()
        .duration(500)
        .attr("fill", (d, i) => (maskedIndices.current.includes(i) ? baseColors.mask : baseColors[d]));
    },
    // Step 3: Show attention (context learning)
    () => {
      const svg = d3.select(svgRef.current);
      const rectSize = 28;
      const padding = 4;

      const lines = svg.append("g").attr("class", "attention-lines");

      maskedIndices.current.forEach((maskIdx, i) => {
        // Left
        let left = maskIdx - 1;
        while (left >= 0 && maskedIndices.current.includes(left)) left--;
        // Right
        let right = maskIdx + 1;
        while (right < sequence.length && maskedIndices.current.includes(right)) right++;

        if (left >= 0 && right < sequence.length) {
          const x1 = left * (rectSize + padding) + rectSize / 2;
          const x2 = right * (rectSize + padding) + rectSize / 2;
          const y = 80 + rectSize / 2; 

          lines
            .append("path")
            .attr("d", `M${x1},${y} Q${maskIdx * (rectSize + padding) + rectSize / 2},${y - 80} ${x2},${y}`)
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
      svg.selectAll(".attention-lines").remove();
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
    // Step 5: Final flash
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
    actions[0](); 
  }, []);
  useEffect(() => {
    if (step > 0) actions[step]?.();
  }, [step]);

  const stepTexts = [
    "Step 0: Plant vs Mammal gene-genome comparison",
    "Step 1: Input DNA sequence and Retrain (human and mouse)",
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
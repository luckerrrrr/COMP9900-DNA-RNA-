import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { motion } from "framer-motion";

export default function Module3GPNMSA() {
  const svgRef = useRef();
  const [step, setStep] = useState(0); // 当前动画步骤
  const [sequenceMatrix, setSequenceMatrix] = useState([]);
  const [maskedIndices, setMaskedIndices] = useState([]);
  const maskRatio = 0.15; // 遮蔽比例
  const msaCount = 3; // 多序列行数

  const baseColors = { A: "#ff4d4d", T: "#4d4dff", C: "#4dff4d", G: "#ffff4d", mask: "#888888" };

  // 生成多序列对齐矩阵
  useEffect(() => {
    const bases = ["A", "T", "C", "G"];
    const seqLength = 50; // 示例长度
    const matrix = [];
    for (let i = 0; i < msaCount; i++) {
      const row = Array.from({ length: seqLength }, () => bases[Math.floor(Math.random() * 4)]);
      matrix.push(row);
    }
    setSequenceMatrix(matrix);

    // 随机 Mask 目标序列（第0行）
    const masked = matrix[0]
      .map((b, i) => (Math.random() < maskRatio ? i : null))
      .filter((d) => d !== null);
    setMaskedIndices(masked);
  }, []);
  // 绘制动画
  useEffect(() => {
    if (!sequenceMatrix.length) return;
  
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
  
    const rectSize = 12;
    const padding = 2;
    const textAbove = 5;       
    const rowGap = 30;          
  
    sequenceMatrix.forEach((seq, rowIdx) => {
      const yRect = 50 + rowIdx * rowGap;
      const yText = yRect - textAbove;
  
      // --- 文本行 ---
      svg
        .selectAll(`text.seq-text-${rowIdx}`)
        .data(seq)
        .enter()
        .append("text")
        .attr("class", `seq-text-${rowIdx}`)
        .attr("x", (d, i) => i * (rectSize + padding) + rectSize / 2)
        .attr("y", yText)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "alphabetic")
        .attr("font-size", 12)
        .attr("fill", "#000")
        .text((d, i) => {
          if (rowIdx === 0 && maskedIndices.includes(i) && step >= 1) return "";
          return d;
        });
  
      // --- 矩形 ---
      svg
        .selectAll(`.row-${rowIdx}`)
        .data(seq)
        .enter()
        .append("rect")
        .attr("class", `row-${rowIdx}`)
        .attr("x", (d, i) => i * (rectSize + padding))
        .attr("y", yRect)
        .attr("width", rectSize)
        .attr("height", rectSize)
        .attr("rx", 2)
        .attr("fill", (d, i) => {
          if (rowIdx === 0 && maskedIndices.includes(i) && step >= 1) return baseColors.mask;
          return baseColors[d];
        })
        .attr("opacity", rowIdx === 0 ? 1 : 0.35);
    });
  
    // Step 2: 模型观察其他物种
    if (step >= 2) {
      maskedIndices.forEach((idx) => {
        sequenceMatrix.slice(1).forEach((_, rowIdx) => {
          const y0 = 50 + 0 * rowGap + rectSize / 2;
          const y1 = 50 + (rowIdx + 1) * rowGap + rectSize / 2;
          svg
            .append("line")
            .attr("x1", idx * (rectSize + padding) + rectSize / 2)
            .attr("y1", y0)
            .attr("x2", idx * (rectSize + padding) + rectSize / 2)
            .attr("y2", y1)
            .attr("stroke", "orange")
            .attr("stroke-width", 2)
            .attr("opacity", 0)
            .transition()
            .duration(400)
            .attr("opacity", 1);
        });
      });
    }
  
    // Step 3: 逐步预测恢复
    if (step === 3) {
      const targetSeq = sequenceMatrix[0];
      maskedIndices.forEach((idx, i) => {
        setTimeout(() => {
          // 更新矩形颜色
          svg
            .selectAll(`.row-0`)
            .filter((d, j) => j === idx)
            .transition()
            .duration(300)
            .attr("fill", targetSeq[idx]);
  
          // 更新文本显示
          svg
            .selectAll("text.seq-text-0")
            .filter((d, j) => j === idx)
            .transition()
            .duration(300)
            .text(targetSeq[idx]);
        }, i * 200);
      });
    }
  }, [step, sequenceMatrix, maskedIndices]);

  const nextStep = () => {
    if (step < 3) setStep(step + 1);
  };
  const prevStep = () => {
    if (step > 0) setStep(step - 1);
  };

  return (
    <div style={{ 
      display: "flex", 
      flexDirection: "column", 
      alignItems: "center", 
      justifyContent: "center",
      color: "#fff"
    }}>
      <h2 style={{ fontSize: "32px", marginBottom: "20px" }}>GPN-MSA Model Animation</h2>
      <svg ref={svgRef} width={900} height={200} style={{ border: "1px solid #ccc" }} />
      <div style={{ 
        display: "flex", 
        gap: "16px", 
        marginTop: "16px" 
      }}>
        <button
          onClick={prevStep}
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            background: "rgba(255, 255, 255, 0.1)",
            border: "1px solid rgba(255, 255, 255, 0.3)",
            color: "#fff",
            cursor: "pointer",
            fontSize: "14px",
          }}
        >
          Previous step
        </button>
        <button
          onClick={nextStep}
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            background: "rgba(0, 212, 255, 0.2)",
            border: "1px solid #00d4ff",
            color: "#00d4ff",
            cursor: "pointer",
            fontSize: "14px",
          }}
        >
          Next step
        </button>
      </div>
      <div style={{ 
        marginTop: "8px", 
        textAlign: "center",
        color: "rgba(255, 255, 255, 0.8)",
        fontSize: "14px"
      }}>
        {step === 0 && "Step 0: Original input sequence"}
        {step === 1 && "Step 1: Mask target sequence"}
        {step === 2 && "Step 2: Model observes gene sequences of other species"}
        {step === 3 && "Step 3: redicted recovery of masked bases"}
      </div>
    </div>
  );
}
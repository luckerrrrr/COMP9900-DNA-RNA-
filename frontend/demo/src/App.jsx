import React, { useState, useEffect } from "react";
import Module1Intro from "./modules/Intro.jsx";
import Module2Pipeline from "./modules/Pipeline.jsx";
import Module3Model from "./modules/Model.jsx";
import Module4Training from "./modules/Training.jsx";
import Module5Results from "./modules/Results.jsx";

const modules = [
  { id: "module1", component: Module1Intro },
  { id: "module2", component: Module2Pipeline },
  { id: "module3", component: Module3Model },
  { id: "module4", component: Module4Training },
  { id: "module5", component: Module5Results },
];

export default function App() {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const index = Math.round(window.scrollY / window.innerHeight);
      setCurrent(index);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div>
      <div style={{
        position: "fixed",
        top: "50%",
        right: "20px",
        transform: "translateY(-50%)",
        display: "flex",
        flexDirection: "column",
        gap: "10px"
      }}>
        {modules.map((_, i) => (
          <div key={i} style={{
            width: "12px",
            height: "12px",
            borderRadius: "50%",
            backgroundColor: i === current ? "blue" : "gray",
            cursor: "pointer"
          }} onClick={() => window.scrollTo({ top: i * window.innerHeight, behavior: 'smooth' })}/>
        ))}
      </div>

      {modules.map((mod, i) => {
        const Component = mod.component;
        return (
          <div key={i} style={{ height: "100vh" }}>
            <Component />
          </div>
        );
      })}
    </div>
  );
}
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainPage from "./MainPage";
import AnimationPage from "./pages/AnimationPage";
import InteractivePage from "./pages/InteractivePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/animation" element={<AnimationPage />} />
        <Route path="/interactive" element={<InteractivePage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default function LearnedFeature({ icon, text, detail }) {
  return (
    <div
      style={{
        padding: "16px",
        background: "rgba(255, 255, 255, 0.03)",
        borderRadius: "12px",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "28px", marginBottom: "8px" }}>{icon}</div>
      <div
        style={{
          fontSize: "14px",
          fontWeight: "600",
          color: "#fff",
          marginBottom: "4px",
        }}
      >
        {text}
      </div>
      <div style={{ fontSize: "12px", color: "rgba(255, 255, 255, 0.6)" }}>
        {detail}
      </div>
    </div>
  );
}

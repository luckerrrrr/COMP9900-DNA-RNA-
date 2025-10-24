export default function MetricCard({ label, value, trend }) {
  return (
    <div
      style={{
        padding: "16px",
        background: "rgba(255, 255, 255, 0.05)",
        borderRadius: "12px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
      }}
    >
      <div
        style={{
          fontSize: "12px",
          color: "rgba(255, 255, 255, 0.6)",
          marginBottom: "8px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <span
          style={{
            fontSize: "20px",
            fontWeight: "bold",
            color: "#fff",
          }}
        >
          {value}
        </span>
        {trend && (
          <span
            style={{
              fontSize: "16px",
              color: trend === "up" ? "#00ff88" : "#ff6b9d",
            }}
          >
            {trend === "up" ? "↑" : "↓"}
          </span>
        )}
      </div>
    </div>
  );
}

import React from "react";

export function Header({ onClear, hasMessages }) {
  return (
    <header style={{
      padding: "14px 20px",
      borderBottom: "1px solid var(--border)",
      background: "var(--bg-secondary)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: "8px",
          background: "linear-gradient(135deg, #6366f1, #7c3aed)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "16px",
          boxShadow: "0 2px 12px rgba(99,102,241,0.4)",
        }}>
          🧠
        </div>
        <div>
          <div style={{
            fontFamily: "var(--font-display)",
            fontSize: "16px",
            fontWeight: 800,
            color: "var(--text-primary)",
            letterSpacing: "0.02em",
            lineHeight: 1.2,
          }}>
            NeuralChat
          </div>
          <div style={{
            fontSize: "10px",
            color: "var(--text-muted)",
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.05em",
          }}>
            5-Agent AI Pipeline
          </div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        {/* Agent count */}
        <div style={{
          display: "flex",
          gap: "4px",
          alignItems: "center",
          padding: "4px 10px",
          background: "rgba(99,102,241,0.1)",
          border: "1px solid rgba(99,102,241,0.2)",
          borderRadius: "20px",
        }}>
          {["🎯","🔬","💻","📖","✨"].map((icon, i) => (
            <span key={i} style={{ fontSize: "11px" }}>{icon}</span>
          ))}
          <span style={{
            fontSize: "10px",
            color: "#6366f1",
            fontFamily: "var(--font-mono)",
            marginLeft: "4px",
            fontWeight: 600,
          }}>
            5 agents
          </span>
        </div>

        {/* Clear button */}
        {hasMessages && (
          <button
            onClick={onClear}
            style={{
              fontSize: "11px",
              color: "var(--text-muted)",
              background: "transparent",
              border: "1px solid var(--border)",
              padding: "5px 12px",
              borderRadius: "8px",
              cursor: "pointer",
              fontFamily: "var(--font-mono)",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.target.style.borderColor = "#f87171";
              e.target.style.color = "#f87171";
            }}
            onMouseLeave={(e) => {
              e.target.style.borderColor = "var(--border)";
              e.target.style.color = "var(--text-muted)";
            }}
          >
            clear chat
          </button>
        )}
      </div>
    </header>
  );
}

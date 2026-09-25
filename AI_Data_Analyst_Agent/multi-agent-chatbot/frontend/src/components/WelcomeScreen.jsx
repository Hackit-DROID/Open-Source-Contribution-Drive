import React from "react";

const FEATURES = [
  { icon: "🎯", label: "Intent Detection", desc: "Classifies your question type" },
  { icon: "🔬", label: "Research", desc: "Gathers relevant knowledge" },
  { icon: "💻", label: "Coding", desc: "Generates clean code" },
  { icon: "📖", label: "Explanation", desc: "Beginner-friendly breakdown" },
  { icon: "✨", label: "Formatter", desc: "Polished final output" },
];

export function WelcomeScreen({ onSend }) {
  const samples = [
    "How do I implement a binary search tree in Python?",
    "What is the difference between TCP and UDP?",
    "Explain closures in JavaScript with examples",
    "How does React's reconciliation algorithm work?",
  ];

  return (
    <div style={{
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "40px 20px",
      overflowY: "auto",
    }}>
      {/* Hero */}
      <div className="fade-in" style={{ textAlign: "center", marginBottom: "40px" }}>
        <div style={{
          width: 64,
          height: 64,
          borderRadius: "16px",
          background: "linear-gradient(135deg, #6366f1, #7c3aed)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "30px",
          margin: "0 auto 20px",
          boxShadow: "0 4px 30px rgba(99,102,241,0.4)",
          animation: "glow 3s ease-in-out infinite",
        }}>
          🧠
        </div>

        <h1 style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(24px, 4vw, 36px)",
          fontWeight: 800,
          color: "var(--text-primary)",
          marginBottom: "10px",
          letterSpacing: "-0.02em",
        }}>
          NeuralChat
        </h1>

        <p style={{
          color: "var(--text-secondary)",
          fontSize: "15px",
          maxWidth: "480px",
          lineHeight: "1.6",
        }}>
          A 5-agent AI pipeline that detects intent, researches, codes,
          explains, and formats answers — all in real time.
        </p>
      </div>

      {/* Pipeline visualization */}
      <div className="fade-in" style={{
        display: "flex",
        alignItems: "center",
        gap: "0",
        marginBottom: "40px",
        flexWrap: "wrap",
        justifyContent: "center",
        maxWidth: "600px",
      }}>
        {FEATURES.map((f, i) => (
          <React.Fragment key={i}>
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              padding: "12px",
              borderRadius: "12px",
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              width: "90px",
              animationDelay: `${i * 0.08}s`,
            }}>
              <span style={{ fontSize: "20px", marginBottom: "6px" }}>{f.icon}</span>
              <div style={{
                fontSize: "9px",
                fontFamily: "var(--font-display)",
                fontWeight: 700,
                color: "var(--text-primary)",
                textAlign: "center",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "3px",
              }}>{f.label}</div>
              <div style={{
                fontSize: "9px",
                color: "var(--text-muted)",
                textAlign: "center",
                lineHeight: 1.3,
              }}>{f.desc}</div>
            </div>
            {i < FEATURES.length - 1 && (
              <div style={{
                width: "16px",
                height: "1px",
                background: "linear-gradient(90deg, #6366f1, #a78bfa)",
                flexShrink: 0,
                margin: "0 -1px",
              }} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Sample questions */}
      <div className="fade-in" style={{ width: "100%", maxWidth: "560px" }}>
        <p style={{
          fontSize: "11px",
          fontFamily: "var(--font-mono)",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          marginBottom: "12px",
          textAlign: "center",
        }}>
          Try asking
        </p>
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "8px",
        }}>
          {samples.map((q, i) => (
            <button
              key={i}
              onClick={() => onSend(q)}
              style={{
                padding: "12px 14px",
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "10px",
                color: "var(--text-secondary)",
                fontSize: "12px",
                fontFamily: "var(--font-body)",
                cursor: "pointer",
                textAlign: "left",
                lineHeight: "1.4",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "#6366f1";
                e.currentTarget.style.color = "var(--text-primary)";
                e.currentTarget.style.background = "rgba(99,102,241,0.06)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.color = "var(--text-secondary)";
                e.currentTarget.style.background = "var(--bg-card)";
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

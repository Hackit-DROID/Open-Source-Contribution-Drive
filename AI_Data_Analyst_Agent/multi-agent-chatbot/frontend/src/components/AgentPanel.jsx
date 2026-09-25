import React from "react";

const statusConfig = {
  waiting:   { color: "#55556a", bg: "transparent",          dot: "#55556a",  label: "Waiting"   },
  running:   { color: "#6366f1", bg: "rgba(99,102,241,0.1)", dot: "#6366f1",  label: "Running"   },
  completed: { color: "#34d399", bg: "rgba(52,211,153,0.1)", dot: "#34d399",  label: "Done"      },
  skipped:   { color: "#fbbf24", bg: "rgba(251,191,36,0.1)", dot: "#fbbf24",  label: "Skipped"   },
  skipping:  { color: "#fb923c", bg: "rgba(251,146,60,0.1)", dot: "#fb923c",  label: "Skipping"  },
  error:     { color: "#f87171", bg: "rgba(248,113,113,0.1)",dot: "#f87171",  label: "Error"     },
};

function AgentRow({ agent, index }) {
  const config = statusConfig[agent.status] || statusConfig.waiting;
  const isRunning = agent.status === "running";

  return (
    <div
      className="slide-in"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "10px 14px",
        borderRadius: "10px",
        background: config.bg,
        border: `1px solid ${isRunning ? config.dot : "transparent"}`,
        transition: "all 0.3s ease",
        animationDelay: `${index * 0.05}s`,
        opacity: agent.status === "waiting" ? 0.45 : 1,
      }}
    >
      {/* Status dot */}
      <div style={{ position: "relative", flexShrink: 0 }}>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: config.dot,
            animation: isRunning ? "pulse 1s ease-in-out infinite" : "none",
          }}
        />
        {isRunning && (
          <div
            style={{
              position: "absolute",
              inset: -3,
              borderRadius: "50%",
              border: `1.5px solid ${config.dot}`,
              animation: "spin 2s linear infinite",
              opacity: 0.5,
            }}
          />
        )}
      </div>

      {/* Icon */}
      <span style={{ fontSize: "16px", lineHeight: 1 }}>{agent.icon}</span>

      {/* Info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontFamily: "var(--font-display)",
          fontSize: "12px",
          fontWeight: 600,
          color: config.color,
          letterSpacing: "0.02em",
        }}>
          {agent.name}
        </div>
        <div style={{
          fontSize: "11px",
          color: "var(--text-muted)",
          marginTop: "1px",
        }}>
          {agent.skipReason ? agent.skipReason : agent.description}
        </div>
      </div>

      {/* Status badge */}
      <div style={{
        fontSize: "10px",
        fontFamily: "var(--font-mono)",
        color: config.color,
        background: config.bg,
        padding: "2px 8px",
        borderRadius: "20px",
        border: `1px solid ${config.dot}30`,
        flexShrink: 0,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}>
        {config.label}
      </div>
    </div>
  );
}

export function AgentPanel({ agentStates, isLoading }) {
  const completedCount = agentStates.filter((a) => a.status === "completed").length;
  const totalActive = agentStates.some((a) => a.status !== "waiting");
  const progress = agentStates.length ? (completedCount / agentStates.length) * 100 : 0;

  return (
    <aside style={{
      width: "280px",
      flexShrink: 0,
      background: "var(--bg-secondary)",
      borderLeft: "1px solid var(--border)",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        padding: "20px 16px 16px",
        borderBottom: "1px solid var(--border)",
      }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "12px",
        }}>
          <div style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: isLoading ? "#6366f1" : "#34d399",
            animation: isLoading ? "pulse 1s ease-in-out infinite" : "none",
          }} />
          <span style={{
            fontFamily: "var(--font-display)",
            fontSize: "11px",
            fontWeight: 700,
            color: "var(--text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.1em",
          }}>
            Agent Pipeline
          </span>
        </div>

        {/* Progress bar */}
        {totalActive && (
          <div style={{ marginTop: "8px" }}>
            <div style={{
              height: "3px",
              background: "rgba(255,255,255,0.06)",
              borderRadius: "2px",
              overflow: "hidden",
            }}>
              <div style={{
                height: "100%",
                width: `${progress}%`,
                background: "linear-gradient(90deg, #6366f1, #a78bfa)",
                borderRadius: "2px",
                transition: "width 0.5s ease",
              }} />
            </div>
            <div style={{
              fontSize: "10px",
              color: "var(--text-muted)",
              marginTop: "4px",
              fontFamily: "var(--font-mono)",
            }}>
              {completedCount}/{agentStates.length} agents complete
            </div>
          </div>
        )}
      </div>

      {/* Agent list */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "12px",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
      }}>
        {agentStates.length === 0 ? (
          <div style={{
            textAlign: "center",
            padding: "40px 16px",
            color: "var(--text-muted)",
          }}>
            <div style={{ fontSize: "28px", marginBottom: "12px" }}>🤖</div>
            <div style={{ fontSize: "12px", fontFamily: "var(--font-mono)", lineHeight: 1.5 }}>
              Send a message to<br />activate the pipeline
            </div>
          </div>
        ) : (
          agentStates.map((agent, i) => (
            <AgentRow key={agent.id} agent={agent} index={i} />
          ))
        )}
      </div>

      {/* Footer info */}
      <div style={{
        padding: "12px 16px",
        borderTop: "1px solid var(--border)",
        fontSize: "10px",
        color: "var(--text-muted)",
        fontFamily: "var(--font-mono)",
        lineHeight: 1.6,
      }}>
        Powered by Claude Sonnet
        <br />
        5 agents · SSE streaming
      </div>
    </aside>
  );
}

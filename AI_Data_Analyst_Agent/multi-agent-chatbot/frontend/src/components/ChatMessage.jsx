import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

function IntentBadge({ intentData }) {
  if (!intentData) return null;
  const colors = {
    coding: "#6366f1",
    research: "#34d399",
    explanation: "#a78bfa",
    general: "#60a5fa",
    math: "#fbbf24",
    creative: "#f472b6",
  };
  const color = colors[intentData.intent] || "#60a5fa";

  return (
    <div style={{
      display: "flex",
      flexWrap: "wrap",
      gap: "6px",
      marginBottom: "12px",
    }}>
      <span style={{
        fontSize: "10px",
        fontFamily: "var(--font-mono)",
        color,
        background: `${color}18`,
        border: `1px solid ${color}40`,
        padding: "2px 8px",
        borderRadius: "20px",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}>
        {intentData.intent}
      </span>
      {intentData.language && (
        <span style={{
          fontSize: "10px",
          fontFamily: "var(--font-mono)",
          color: "#8888aa",
          background: "rgba(255,255,255,0.05)",
          border: "1px solid rgba(255,255,255,0.08)",
          padding: "2px 8px",
          borderRadius: "20px",
        }}>
          {intentData.language}
        </span>
      )}
      <span style={{
        fontSize: "10px",
        fontFamily: "var(--font-mono)",
        color: "#8888aa",
        background: "rgba(255,255,255,0.05)",
        border: "1px solid rgba(255,255,255,0.08)",
        padding: "2px 8px",
        borderRadius: "20px",
      }}>
        {intentData.complexity}
      </span>
    </div>
  );
}

function LoadingDots() {
  return (
    <div style={{ display: "flex", gap: "5px", padding: "4px 0", alignItems: "center" }}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "#6366f1",
            animation: `pulse 1.4s ease-in-out infinite`,
            animationDelay: `${i * 0.16}s`,
          }}
        />
      ))}
      <span style={{
        fontSize: "11px",
        color: "var(--text-muted)",
        fontFamily: "var(--font-mono)",
        marginLeft: "6px",
      }}>
        Processing pipeline...
      </span>
    </div>
  );
}

const MarkdownComponents = {
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || "");
    const language = match ? match[1] : "";

    if (!inline && language) {
      return (
        <div style={{ position: "relative", margin: "12px 0" }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "6px 14px",
            background: "#1a1a2e",
            borderRadius: "8px 8px 0 0",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
          }}>
            <span style={{
              fontSize: "11px",
              fontFamily: "var(--font-mono)",
              color: "#6366f1",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}>
              {language}
            </span>
            <button
              onClick={() => navigator.clipboard?.writeText(String(children))}
              style={{
                fontSize: "10px",
                fontFamily: "var(--font-mono)",
                color: "var(--text-muted)",
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "2px 6px",
                borderRadius: "4px",
              }}
              onMouseEnter={(e) => (e.target.style.color = "#fff")}
              onMouseLeave={(e) => (e.target.style.color = "var(--text-muted)")}
            >
              copy
            </button>
          </div>
          <SyntaxHighlighter
            language={language}
            style={oneDark}
            customStyle={{
              margin: 0,
              borderRadius: "0 0 8px 8px",
              fontSize: "13px",
              lineHeight: "1.6",
              padding: "16px",
            }}
            {...props}
          >
            {String(children).replace(/\n$/, "")}
          </SyntaxHighlighter>
        </div>
      );
    }

    return (
      <code style={{
        fontFamily: "var(--font-mono)",
        fontSize: "12px",
        color: "#a78bfa",
        background: "rgba(167,139,250,0.12)",
        padding: "1px 5px",
        borderRadius: "4px",
        border: "1px solid rgba(167,139,250,0.2)",
      }} {...props}>
        {children}
      </code>
    );
  },

  h2({ children }) {
    return (
      <h2 style={{
        fontFamily: "var(--font-display)",
        fontSize: "16px",
        fontWeight: 700,
        color: "#f0f0ff",
        margin: "20px 0 8px",
        paddingBottom: "6px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        letterSpacing: "0.01em",
      }}>
        {children}
      </h2>
    );
  },

  h3({ children }) {
    return (
      <h3 style={{
        fontFamily: "var(--font-display)",
        fontSize: "14px",
        fontWeight: 600,
        color: "#d0d0f0",
        margin: "14px 0 6px",
      }}>
        {children}
      </h3>
    );
  },

  p({ children }) {
    return (
      <p style={{ marginBottom: "10px", lineHeight: "1.7", color: "#c8c8e0", fontSize: "14px" }}>
        {children}
      </p>
    );
  },

  ul({ children }) {
    return <ul style={{ paddingLeft: "20px", marginBottom: "10px" }}>{children}</ul>;
  },

  ol({ children }) {
    return <ol style={{ paddingLeft: "20px", marginBottom: "10px" }}>{children}</ol>;
  },

  li({ children }) {
    return (
      <li style={{ marginBottom: "5px", color: "#c8c8e0", fontSize: "14px", lineHeight: "1.6" }}>
        {children}
      </li>
    );
  },

  blockquote({ children }) {
    return (
      <blockquote style={{
        borderLeft: "3px solid #6366f1",
        paddingLeft: "12px",
        margin: "12px 0",
        color: "#a8a8c0",
        fontStyle: "italic",
        background: "rgba(99,102,241,0.06)",
        padding: "10px 12px",
        borderRadius: "0 8px 8px 0",
      }}>
        {children}
      </blockquote>
    );
  },

  strong({ children }) {
    return <strong style={{ color: "#e0e0ff", fontWeight: 600 }}>{children}</strong>;
  },
};

export function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div
      className="fade-in"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        marginBottom: "20px",
      }}
    >
      {/* Label */}
      <div style={{
        fontSize: "10px",
        fontFamily: "var(--font-mono)",
        color: "var(--text-muted)",
        marginBottom: "5px",
        paddingLeft: isUser ? "0" : "4px",
        paddingRight: isUser ? "4px" : "0",
        textTransform: "uppercase",
        letterSpacing: "0.08em",
      }}>
        {isUser ? "You" : "NeuralChat"}
      </div>

      {/* Bubble */}
      <div style={{
        maxWidth: "85%",
        padding: isUser ? "10px 16px" : "14px 18px",
        borderRadius: isUser ? "18px 18px 4px 18px" : "4px 18px 18px 18px",
        background: isUser
          ? "linear-gradient(135deg, #6366f1, #7c3aed)"
          : "var(--bg-card)",
        border: isUser ? "none" : "1px solid var(--border)",
        boxShadow: isUser
          ? "0 4px 20px rgba(99,102,241,0.3)"
          : "0 2px 12px rgba(0,0,0,0.3)",
        wordBreak: "break-word",
      }}>
        {isUser ? (
          <p style={{ color: "#fff", fontSize: "14px", lineHeight: "1.6", margin: 0 }}>
            {message.content}
          </p>
        ) : message.loading ? (
          <LoadingDots />
        ) : (
          <>
            {message.intentData && <IntentBadge intentData={message.intentData} />}
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={MarkdownComponents}
            >
              {message.content}
            </ReactMarkdown>
          </>
        )}
      </div>

      {/* Timestamp */}
      <div style={{
        fontSize: "10px",
        color: "var(--text-muted)",
        marginTop: "4px",
        fontFamily: "var(--font-mono)",
      }}>
        {message.timestamp?.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
      </div>
    </div>
  );
}

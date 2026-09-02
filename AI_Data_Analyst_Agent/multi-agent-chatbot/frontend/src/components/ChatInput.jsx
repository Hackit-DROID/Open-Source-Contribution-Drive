import React, { useState, useRef, useEffect } from "react";

const EXAMPLE_QUESTIONS = [
  "How do I reverse a linked list in Python?",
  "Explain how async/await works in JavaScript",
  "What is the difference between TCP and UDP?",
  "Write a binary search function in TypeScript",
  "How does React's virtual DOM work?",
];

export function ChatInput({ onSend, isLoading }) {
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + "px";
    }
  }, [value]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const useExample = (q) => {
    if (!isLoading) {
      setValue(q);
      textareaRef.current?.focus();
    }
  };

  return (
    <div style={{
      padding: "16px 20px 20px",
      borderTop: "1px solid var(--border)",
      background: "var(--bg-secondary)",
    }}>
      {/* Example questions */}
      <div style={{
        display: "flex",
        gap: "6px",
        flexWrap: "wrap",
        marginBottom: "12px",
      }}>
        {EXAMPLE_QUESTIONS.slice(0, 3).map((q, i) => (
          <button
            key={i}
            onClick={() => useExample(q)}
            disabled={isLoading}
            style={{
              fontSize: "11px",
              color: "var(--text-muted)",
              background: "var(--bg-input)",
              border: "1px solid var(--border)",
              padding: "4px 10px",
              borderRadius: "20px",
              cursor: isLoading ? "not-allowed" : "pointer",
              fontFamily: "var(--font-body)",
              transition: "all 0.2s",
              whiteSpace: "nowrap",
              maxWidth: "200px",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                e.target.style.borderColor = "#6366f1";
                e.target.style.color = "#a78bfa";
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.borderColor = "var(--border)";
              e.target.style.color = "var(--text-muted)";
            }}
            title={q}
          >
            {q.length > 28 ? q.slice(0, 28) + "…" : q}
          </button>
        ))}
      </div>

      {/* Input row */}
      <div style={{
        display: "flex",
        gap: "10px",
        alignItems: "flex-end",
        background: "var(--bg-input)",
        border: "1px solid var(--border)",
        borderRadius: "14px",
        padding: "10px 14px",
        transition: "border-color 0.2s",
      }}
        onFocusCapture={(e) => (e.currentTarget.style.borderColor = "#6366f1")}
        onBlurCapture={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything... (Shift+Enter for new line)"
          disabled={isLoading}
          rows={1}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "var(--text-primary)",
            fontFamily: "var(--font-body)",
            fontSize: "14px",
            lineHeight: "1.6",
            resize: "none",
            maxHeight: "150px",
            overflowY: "auto",
            caretColor: "#6366f1",
          }}
        />

        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading}
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "8px",
            background: value.trim() && !isLoading
              ? "linear-gradient(135deg, #6366f1, #7c3aed)"
              : "rgba(255,255,255,0.05)",
            border: "none",
            cursor: value.trim() && !isLoading ? "pointer" : "not-allowed",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            transition: "all 0.2s",
            boxShadow: value.trim() && !isLoading
              ? "0 2px 12px rgba(99,102,241,0.4)"
              : "none",
          }}
          onMouseEnter={(e) => {
            if (value.trim() && !isLoading)
              e.currentTarget.style.transform = "scale(1.05)";
          }}
          onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
        >
          {isLoading ? (
            <div style={{
              width: 16,
              height: 16,
              border: "2px solid rgba(255,255,255,0.3)",
              borderTopColor: "#fff",
              borderRadius: "50%",
              animation: "spin 0.8s linear infinite",
            }} />
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </button>
      </div>

      <div style={{
        textAlign: "center",
        fontSize: "10px",
        color: "var(--text-muted)",
        marginTop: "8px",
        fontFamily: "var(--font-mono)",
      }}>
        5-agent pipeline · Intent → Research → Code → Explain → Format
      </div>
    </div>
  );
}

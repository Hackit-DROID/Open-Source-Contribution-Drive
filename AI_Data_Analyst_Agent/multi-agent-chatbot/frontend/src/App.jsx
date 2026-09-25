import React, { useRef, useEffect } from "react";
import { useChat } from "./hooks/useChat";
import { Header } from "./components/Header";
import { AgentPanel } from "./components/AgentPanel";
import { ChatMessage } from "./components/ChatMessage";
import { ChatInput } from "./components/ChatInput";
import { WelcomeScreen } from "./components/WelcomeScreen";

export default function App() {
  const { messages, agentStates, isLoading, error, sendMessage, clearHistory, AGENTS } = useChat();
  const messagesEndRef = useRef(null);
  const hasMessages = messages.length > 0;

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div style={{
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      background: "var(--bg-primary)",
      overflow: "hidden",
    }}>
      <Header onClear={clearHistory} hasMessages={hasMessages} />

      {/* Main layout */}
      <div style={{
        flex: 1,
        display: "flex",
        overflow: "hidden",
      }}>
        {/* Chat area */}
        <div style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}>
          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: "auto",
            padding: hasMessages ? "20px 24px" : "0",
          }}>
            {!hasMessages ? (
              <WelcomeScreen onSend={sendMessage} />
            ) : (
              <>
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}

                {/* Error banner */}
                {error && (
                  <div className="fade-in" style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "12px 16px",
                    background: "rgba(248,113,113,0.1)",
                    border: "1px solid rgba(248,113,113,0.2)",
                    borderRadius: "10px",
                    marginBottom: "16px",
                  }}>
                    <span style={{ fontSize: "16px" }}>⚠️</span>
                    <div>
                      <div style={{
                        fontSize: "13px",
                        fontWeight: 500,
                        color: "#f87171",
                        marginBottom: "2px",
                      }}>
                        Error
                      </div>
                      <div style={{ fontSize: "12px", color: "#ff9999" }}>{error}</div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          <ChatInput onSend={sendMessage} isLoading={isLoading} />
        </div>

        {/* Agent Panel */}
        <AgentPanel agentStates={agentStates} isLoading={isLoading} />
      </div>
    </div>
  );
}

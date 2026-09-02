import { useState, useCallback, useRef } from "react";

const API_URL = import.meta.env.VITE_API_URL || "";

/**
 * useChat — manages chat history and agent pipeline streaming
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [agentStates, setAgentStates] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  const AGENTS = [
    { id: 1, name: "Intent Detection", icon: "🎯", description: "Analyzing your question" },
    { id: 2, name: "Research", icon: "🔬", description: "Gathering knowledge" },
    { id: 3, name: "Coding", icon: "💻", description: "Generating code" },
    { id: 4, name: "Explanation", icon: "📖", description: "Simplifying concepts" },
    { id: 5, name: "Formatter", icon: "✨", description: "Polishing the response" },
  ];

  const resetAgentStates = () =>
    setAgentStates(AGENTS.map((a) => ({ ...a, status: "waiting" })));

  const updateAgentState = (agentId, updates) => {
    setAgentStates((prev) =>
      prev.map((a) => (a.id === agentId ? { ...a, ...updates } : a))
    );
  };

  const sendMessage = useCallback(async (userText) => {
    if (!userText.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);
    resetAgentStates();

    // Add user message
    const userMessage = { id: Date.now(), role: "user", content: userText, timestamp: new Date() };
    setMessages((prev) => [...prev, userMessage]);

    // Placeholder for assistant response
    const assistantId = Date.now() + 1;
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", loading: true, timestamp: new Date() },
    ]);

    try {
      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `Server error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete line in buffer

        let currentEvent = null;
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const rawData = line.slice(6).trim();
            if (!rawData || rawData === "{}") continue;
            try {
              const data = JSON.parse(rawData);
              handleSSEEvent(currentEvent, data, assistantId);
            } catch (e) {
              // ignore parse errors for partial data
            }
          }
        }
      }
    } catch (err) {
      console.error("Chat error:", err);
      setError(err.message || "Failed to connect to the server.");
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
      setAgentStates((prev) => prev.map((a) => ({ ...a, status: "waiting" })));
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const handleSSEEvent = (eventType, data, assistantId) => {
    switch (eventType) {
      case "pipeline_start":
        break;

      case "agent_update":
        updateAgentState(data.agentId, { status: data.status, skipReason: data.skipReason });
        break;

      case "pipeline_complete":
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: data.finalAnswer, loading: false, metadata: data.metadata, intentData: data.intentData }
              : m
          )
        );
        setAgentStates((prev) =>
          prev.map((a) => ({ ...a, status: a.status === "running" ? "completed" : a.status }))
        );
        break;

      case "error":
        setError(data.error || "An error occurred.");
        setMessages((prev) => prev.filter((m) => m.id !== assistantId));
        setAgentStates((prev) => prev.map((a) => ({ ...a, status: "waiting" })));
        break;

      default:
        break;
    }
  };

  const clearHistory = () => {
    setMessages([]);
    setAgentStates([]);
    setError(null);
  };

  return {
    messages,
    agentStates,
    isLoading,
    error,
    sendMessage,
    clearHistory,
    AGENTS,
  };
}

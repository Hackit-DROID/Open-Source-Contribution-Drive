const express = require("express");
const router = express.Router();
const { runAgentPipeline } = require("../agents/pipeline");

/**
 * POST /api/chat/stream
 * Streams agent updates via Server-Sent Events (SSE)
 * The client connects and receives real-time agent status + final answer.
 */
router.post("/stream", async (req, res) => {
  const { message } = req.body;

  if (!message || typeof message !== "string" || message.trim().length === 0) {
    return res.status(400).json({ error: "Message is required." });
  }

  if (message.length > 2000) {
    return res.status(400).json({ error: "Message too long. Max 2000 characters." });
  }

  // Set up SSE headers
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no"); // Disable Nginx buffering
  res.flushHeaders();

  // Helper to send SSE events
  const sendEvent = (eventType, data) => {
    res.write(`event: ${eventType}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
    // Flush if available (some environments need explicit flush)
    if (res.flush) res.flush();
  };

  try {
    sendEvent("pipeline_start", { message: "Pipeline started", totalAgents: 5 });

    // Callback for real-time agent updates
    const onAgentUpdate = (agentUpdate) => {
      sendEvent("agent_update", agentUpdate);
    };

    const result = await runAgentPipeline(message.trim(), onAgentUpdate);

    sendEvent("pipeline_complete", {
      finalAnswer: result.finalAnswer,
      metadata: result.metadata,
      intentData: result.intentData,
    });

    res.write("event: done\ndata: {}\n\n");
    res.end();
  } catch (error) {
    console.error("Pipeline error:", error);

    const errorMessage =
      error.status === 401
        ? "Invalid API key. Please check your ANTHROPIC_API_KEY."
        : error.status === 429
        ? "Rate limit reached. Please try again in a moment."
        : error.status === 529
        ? "Claude API is overloaded. Please try again shortly."
        : "An error occurred while processing your request.";

    sendEvent("error", { error: errorMessage });
    res.write("event: done\ndata: {}\n\n");
    res.end();
  }
});

/**
 * GET /api/chat/health
 * Health check endpoint
 */
router.get("/health", (req, res) => {
  res.json({
    status: "ok",
    message: "Multi-Agent Chatbot API is running",
    agents: [
      "Intent Detection Agent",
      "Research Agent",
      "Coding Agent",
      "Explanation Agent",
      "Formatter Agent",
    ],
  });
});

module.exports = router;

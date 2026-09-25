const Anthropic = require("@anthropic-ai/sdk");

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

/**
 * Agent 1: Intent Detection Agent
 * Analyzes the user's question and classifies intent, extracts key topics,
 * and determines what kind of response is needed.
 */
async function intentDetectionAgent(userMessage) {
  const systemPrompt = `You are an Intent Detection Agent. Your job is to analyze user questions and classify them.

You must respond with a JSON object containing:
{
  "intent": "one of: coding | explanation | research | general | math | creative",
  "topics": ["array", "of", "key", "topics"],
  "requires_code": true/false,
  "complexity": "beginner | intermediate | advanced",
  "language": "programming language if coding related, else null",
  "summary": "one sentence summarizing what the user wants"
}

ONLY respond with valid JSON. No extra text.`;

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 500,
    system: systemPrompt,
    messages: [{ role: "user", content: userMessage }],
  });

  const raw = response.content[0].text.trim();
  // Strip markdown code fences if present
  const clean = raw.replace(/```json\n?|\n?```/g, "").trim();
  const parsed = JSON.parse(clean);

  return {
    agentName: "Intent Detection Agent",
    agentId: 1,
    input: userMessage,
    output: parsed,
    status: "completed",
  };
}

module.exports = { intentDetectionAgent };

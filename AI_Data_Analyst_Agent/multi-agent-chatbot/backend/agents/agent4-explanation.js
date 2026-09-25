const Anthropic = require("@anthropic-ai/sdk");

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

/**
 * Agent 4: Explanation Agent
 * Converts complex research and code into beginner-friendly explanations.
 * Uses analogies, plain language, and step-by-step breakdowns.
 */
async function explanationAgent(
  userMessage,
  intentData,
  researchData,
  codeData
) {
  const complexity = intentData.complexity || "intermediate";

  const codeSection = codeData
    ? `\n\nGenerated Code:\n${codeData}`
    : "\n\n(No code was generated for this question)";

  const systemPrompt = `You are an Explanation Agent. Your job is to create clear, beginner-friendly explanations.

You are writing for a ${complexity} level audience.

You have access to:
1. Research notes: ${researchData}
${codeSection}

Your explanation must:
- Use simple, plain language (avoid jargon unless explained)
- Use real-world analogies where helpful
- Break complex ideas into small, digestible steps
- Explain the "why" behind concepts, not just the "what"
- If there's code, explain what each important part does in plain English
- Use encouraging, friendly tone

Write a clear explanation that would help someone understand this topic well.
Do NOT include the code itself — just explain the concepts and logic.
Do NOT add any headers or markdown formatting — that's the next agent's job.
Write in flowing prose with clear paragraphs.`;

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1200,
    system: systemPrompt,
    messages: [{ role: "user", content: userMessage }],
  });

  return {
    agentName: "Explanation Agent",
    agentId: 4,
    input: { userMessage, intentData, researchData, codeData },
    output: response.content[0].text,
    status: "completed",
  };
}

module.exports = { explanationAgent };

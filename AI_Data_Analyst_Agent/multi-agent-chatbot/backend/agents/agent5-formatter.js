const Anthropic = require("@anthropic-ai/sdk");

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

/**
 * Agent 5: Formatter Agent
 * Takes all the assembled content and formats it into a clean,
 * structured, readable final response with proper markdown.
 */
async function formatterAgent(
  userMessage,
  intentData,
  explanationData,
  codeData
) {
  const codeSection = codeData
    ? `\n\nCode to include:\n${codeData}`
    : "";

  const systemPrompt = `You are a Formatter Agent. Your job is to assemble and format the final response beautifully.

You have:
- User's original question: "${userMessage}"
- Intent: ${JSON.stringify(intentData)}
- Explanation content: ${explanationData}
${codeSection}

Create a well-structured final response using proper Markdown:

Rules:
1. Start with a brief, direct answer (1-2 sentences) — no heading needed
2. Use ## for main section headings
3. Use ### for sub-sections
4. Use bullet points (- ) for lists of items
5. Use numbered lists (1. 2. 3.) for sequential steps
6. Wrap all code in proper markdown code blocks with the language specified: \`\`\`javascript ... \`\`\`
7. Use **bold** for important terms or key points
8. Use > blockquotes for tips, warnings, or important notes
9. End with a "## Summary" section with 2-3 key takeaways
10. Keep it clean, scannable, and professional

Do NOT add a title at the very top. Start directly with the answer.
Make the response feel complete, helpful, and polished.`;

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 2000,
    system: systemPrompt,
    messages: [{ role: "user", content: userMessage }],
  });

  return {
    agentName: "Formatter Agent",
    agentId: 5,
    input: { userMessage, intentData, explanationData, codeData },
    output: response.content[0].text,
    status: "completed",
  };
}

module.exports = { formatterAgent };

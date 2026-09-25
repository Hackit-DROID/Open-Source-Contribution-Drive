const Anthropic = require("@anthropic-ai/sdk");

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

/**
 * Agent 2: Research Agent
 * Gathers relevant knowledge, context, facts, and background information
 * about the topic based on the detected intent.
 */
async function researchAgent(userMessage, intentData) {
  const systemPrompt = `You are a Research Agent. Your job is to gather comprehensive knowledge and context about a topic.

Given a user question and its classified intent, provide:
1. Key concepts and definitions relevant to the topic
2. Background context and foundational knowledge
3. Important facts, best practices, or common patterns
4. Any relevant warnings, pitfalls, or considerations
5. Related subtopics that may be helpful

The intent classification is: ${JSON.stringify(intentData)}

Format your response as structured research notes. Be thorough but focused.
If it's a coding question, include relevant technical concepts, algorithms, or patterns.
If it's a general question, include factual information and context.`;

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1000,
    system: systemPrompt,
    messages: [{ role: "user", content: userMessage }],
  });

  return {
    agentName: "Research Agent",
    agentId: 2,
    input: { userMessage, intentData },
    output: response.content[0].text,
    status: "completed",
  };
}

module.exports = { researchAgent };

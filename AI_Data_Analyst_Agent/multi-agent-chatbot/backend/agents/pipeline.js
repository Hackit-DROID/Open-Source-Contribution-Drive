const { intentDetectionAgent } = require("./agent1-intent");
const { researchAgent } = require("./agent2-research");
const { codingAgent } = require("./agent3-coding");
const { explanationAgent } = require("./agent4-explanation");
const { formatterAgent } = require("./agent5-formatter");

/**
 * Pipeline Orchestrator
 * Runs all 5 agents in sequence, passing output of each to the next.
 * Sends real-time Server-Sent Events (SSE) to the client for live updates.
 *
 * @param {string} userMessage - The user's question
 * @param {Function} onAgentUpdate - Callback called after each agent completes
 * @returns {Object} - Full pipeline results and final answer
 */
async function runAgentPipeline(userMessage, onAgentUpdate) {
  const pipelineLog = [];

  // ─── Agent 1: Intent Detection ────────────────────────────────────────────
  onAgentUpdate({ agentId: 1, agentName: "Intent Detection Agent", status: "running" });

  const agent1Result = await intentDetectionAgent(userMessage);
  pipelineLog.push(agent1Result);
  onAgentUpdate({ agentId: 1, agentName: "Intent Detection Agent", status: "completed", output: agent1Result.output });

  const intentData = agent1Result.output;

  // ─── Agent 2: Research ────────────────────────────────────────────────────
  onAgentUpdate({ agentId: 2, agentName: "Research Agent", status: "running" });

  const agent2Result = await researchAgent(userMessage, intentData);
  pipelineLog.push(agent2Result);
  onAgentUpdate({ agentId: 2, agentName: "Research Agent", status: "completed" });

  const researchData = agent2Result.output;

  // ─── Agent 3: Coding ──────────────────────────────────────────────────────
  onAgentUpdate({
    agentId: 3,
    agentName: "Coding Agent",
    status: intentData.requires_code ? "running" : "skipping",
  });

  const agent3Result = await codingAgent(userMessage, intentData, researchData);
  pipelineLog.push(agent3Result);
  onAgentUpdate({
    agentId: 3,
    agentName: "Coding Agent",
    status: agent3Result.skipped ? "skipped" : "completed",
    skipReason: agent3Result.skipReason,
  });

  const codeData = agent3Result.skipped ? null : agent3Result.output;

  // ─── Agent 4: Explanation ─────────────────────────────────────────────────
  onAgentUpdate({ agentId: 4, agentName: "Explanation Agent", status: "running" });

  const agent4Result = await explanationAgent(userMessage, intentData, researchData, codeData);
  pipelineLog.push(agent4Result);
  onAgentUpdate({ agentId: 4, agentName: "Explanation Agent", status: "completed" });

  const explanationData = agent4Result.output;

  // ─── Agent 5: Formatter ───────────────────────────────────────────────────
  onAgentUpdate({ agentId: 5, agentName: "Formatter Agent", status: "running" });

  const agent5Result = await formatterAgent(userMessage, intentData, explanationData, codeData);
  pipelineLog.push(agent5Result);
  onAgentUpdate({ agentId: 5, agentName: "Formatter Agent", status: "completed" });

  const finalAnswer = agent5Result.output;

  return {
    pipelineLog,
    finalAnswer,
    intentData,
    metadata: {
      totalAgents: 5,
      completedAgents: pipelineLog.filter((r) => r.status === "completed").length,
      skippedAgents: pipelineLog.filter((r) => r.status === "skipped").length,
    },
  };
}

module.exports = { runAgentPipeline };

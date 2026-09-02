# NeuralChat — Multi-AI-Agent Chatbot

A full-stack chatbot powered by a **5-agent AI pipeline** built with Node.js + Express (backend) and React.js (frontend), using the Claude API for all AI agents.

---

## System Architecture

```
User Message
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ChatInput → SSE stream listener → AgentPanel + Chat    │
└─────────────────────────┬───────────────────────────────┘
                          │ POST /api/chat/stream (SSE)
                          ▼
┌─────────────────────────────────────────────────────────┐
│                Express.js Backend                        │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Agent 1  │→ │ Agent 2  │→ │ Agent 3  │→ ...         │
│  │ Intent   │  │ Research │  │ Coding   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│       ↓             ↓             ↓                     │
│  ┌──────────┐  ┌──────────┐                            │
│  │ Agent 4  │→ │ Agent 5  │→ Final Answer              │
│  │ Explain  │  │ Formatter│                            │
│  └──────────┘  └──────────┘                            │
│                                                          │
│  Each agent sends SSE event → Frontend updates in RT    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                    Claude API
               (claude-sonnet-4-20250514)
```

### How the Pipeline Works

| # | Agent | Input | Output |
|---|-------|-------|--------|
| 1 | Intent Detection | Raw user message | JSON: intent, topics, requires_code, complexity |
| 2 | Research | User message + intent | Detailed knowledge/context notes |
| 3 | Coding | User message + intent + research | Code solution (skipped if not coding) |
| 4 | Explanation | Everything above | Beginner-friendly plain-English explanation |
| 5 | Formatter | Explanation + code | Final polished Markdown response |

---

## Folder Structure

```
multi-agent-chatbot/
├── backend/
│   ├── agents/
│   │   ├── agent1-intent.js       # Intent Detection Agent
│   │   ├── agent2-research.js     # Research Agent
│   │   ├── agent3-coding.js       # Coding Agent
│   │   ├── agent4-explanation.js  # Explanation Agent
│   │   ├── agent5-formatter.js    # Formatter Agent
│   │   └── pipeline.js            # Pipeline orchestrator
│   ├── routes/
│   │   └── chat.js               # SSE streaming endpoint
│   ├── .env.example
│   ├── package.json
│   └── server.js                 # Express server entry point
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentPanel.jsx    # Real-time agent status panel
│   │   │   ├── ChatInput.jsx     # Message input + examples
│   │   │   ├── ChatMessage.jsx   # Message bubble + markdown
│   │   │   ├── Header.jsx        # Top navigation bar
│   │   │   └── WelcomeScreen.jsx # Initial landing screen
│   │   ├── hooks/
│   │   │   └── useChat.js        # SSE client + chat state
│   │   ├── App.jsx               # Root component
│   │   ├── index.css             # Global design system
│   │   └── main.jsx              # React entry point
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## Setup: Environment Variables

### Backend (`backend/.env`)
```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
PORT=3001
FRONTEND_URL=http://localhost:5173
```

Get your API key at: https://console.anthropic.com/

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:3001
```

---

## Running Locally

### Prerequisites
- Node.js v18+
- An Anthropic API key

### Step 1 — Clone & Install

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
npm install

# Frontend
cd ../frontend
cp .env.example .env
npm install
```

### Step 2 — Start Backend

```bash
cd backend
npm run dev
# Server starts on http://localhost:3001
```

### Step 3 — Start Frontend

```bash
cd frontend
npm run dev
# App opens at http://localhost:5173
```

### Step 4 — Test

Open http://localhost:5173 and ask any question!
The agent panel on the right shows real-time status.

---

## Deployment

### Backend → Render.com

1. Push your code to GitHub
2. Go to https://render.com → New Web Service
3. Connect your GitHub repo
4. Set:
   - **Root Directory**: `backend`
   - **Build Command**: `npm install`
   - **Start Command**: `node server.js`
5. Add environment variables:
   - `ANTHROPIC_API_KEY` = your key
   - `FRONTEND_URL` = your Vercel URL (after deploying frontend)
6. Deploy

### Frontend → Vercel

1. Go to https://vercel.com → New Project
2. Import your GitHub repo
3. Set:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
4. Add environment variable:
   - `VITE_API_URL` = your Render backend URL
5. Deploy

### After Both Are Deployed

- Update `FRONTEND_URL` in Render to your Vercel URL
- Update `VITE_API_URL` in Vercel to your Render URL
- Redeploy both services

---

## API Reference

### POST `/api/chat/stream`

Streams agent updates via SSE.

**Request body:**
```json
{ "message": "How do I reverse a string in Python?" }
```

**SSE Events emitted:**
```
event: pipeline_start
event: agent_update    (for each agent, twice: running + completed/skipped)
event: pipeline_complete
event: error           (only on failure)
event: done
```

### GET `/api/chat/health`

Returns service status.

---

## Key Design Decisions

- **SSE (Server-Sent Events)** instead of WebSockets — simpler, one-way, works over HTTP
- **Agent 3 is conditional** — the Coding Agent is skipped if intent detection says `requires_code: false`
- **Rate limiting** — 20 requests per 15 minutes per IP to protect your API quota
- **Vite proxy** — in local dev, `/api` requests are proxied to avoid CORS issues
- **Error handling** — API errors (401, 429, 529) show user-friendly messages

---

## Customization

### Adding a new agent
1. Create `backend/agents/agent6-newagent.js`
2. Import and call it in `pipeline.js` after agent 5
3. Send an `onAgentUpdate` call with `agentId: 6`
4. Add the agent to the `AGENTS` array in `frontend/src/hooks/useChat.js`

### Changing the AI model
In each agent file, change:
```js
model: "claude-sonnet-4-20250514"
```
to any available Claude model.

### Switching to OpenAI
Replace the Anthropic SDK calls with the OpenAI SDK.
The pipeline orchestration logic stays the same.

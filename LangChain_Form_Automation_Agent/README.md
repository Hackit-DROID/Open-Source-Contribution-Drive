# LangChain Form Automation Agent

A resilient multi-node workflow agent built on top of **LangGraph** and custom state-machine graph execution. It automates processing questionnaire inputs (such as Google Sheets), generating answers via LLMs (OpenRouter / OpenAI), routing notifications via Gmail SMTP, storing records into Supabase, and dispatching webhook callbacks to Google Apps Script.

## Features

- **Resilient Multi-Node State Machine:** Powered by [`resilient_graph.py`](resilient_graph.py) with schema validation, bounded exponential backoff, retry routing, and fallback containment.
- **Google Sheets & Forms Ingestion:** Dynamically reads user questions and inputs from published Google Sheet CSV exports.
- **LLM Question Answering:** Integrates with OpenAI / OpenRouter models.
- **Automated Email Dispatch:** Sends formatted responses to recipient emails via Gmail SMTP with status tracking.
- **Supabase Persistence:** Records responses and metadata to Supabase (`qa_log` table).
- **Google Apps Script Webhooks:** Posts generated responses back to Google Sheets or webhooks.
- **100% Mocked Offline Unit Testing:** Fully testable without real API keys or external network connectivity.

---

## Directory Structure

```
LangChain_Form_Automation_Agent/
├── .env.example                # Sample environment variables template
├── resilient_graph.py          # Resilient StateGraph engine with retry/recovery logic
├── langchain task/             # Workflow scripts and agents
│   ├── email_langchain.py      # Resilient email QA agent with retry & recovery
│   ├── supabase_form_agent.py  # End-to-end form agent with Supabase storage
│   ├── sheet_webhook_agent.py  # Agent with Google Apps Script webhook integration
│   ├── langgraph_form.py       # Basic LangGraph Q&A agent
│   ├── form_langchain.py       # Direct LLM invocation script
│   └── main.py                 # Minimal graph demonstration
└── tests/
    └── test_resilient_graph.py # Complete unit test suite (19 test cases)
```

---

## Setup & Installation

### 1. Clone & Enter the Directory

```bash
cd LangChain_Form_Automation_Agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

*(Or install core dependencies manually: `pip install pandas langchain-openai langgraph python-dotenv requests supabase`)*

### 3. Configure Environment Variables

Copy the example `.env` file and configure your credentials:

```bash
cp .env.example .env
```

Available environment variables:

| Variable | Description |
| :--- | :--- |
| `OPENROUTER_API_KEY` | OpenRouter or OpenAI API key |
| `SENDER_EMAIL` | Gmail address for sending notifications |
| `GMAIL_APP_PASSWORD` | Google App Password for SMTP authentication |
| `SUPABASE_URL` | Supabase Project URL |
| `SUPABASE_KEY` | Supabase Service / Anon API Key |
| `GOOGLE_SHEET_CSV_URL` | *(Optional)* Published Google Sheet CSV endpoint |
| `GOOGLE_SHEET_WEBHOOK_URL` | *(Optional)* Google Apps Script Webhook endpoint |

---

## Running the Agents

### Resilient Email Agent
```bash
python "langchain task/email_langchain.py"
```

### Supabase Form Automation Agent
```bash
python "langchain task/supabase_form_agent.py"
```

### Google Sheet Webhook Agent
```bash
python "langchain task/sheet_webhook_agent.py"
```

---

## Running Unit Tests

Run the test suite with `pytest`:

```bash
python -m pytest tests
```

All 19 test cases run completely offline with mocked HTTP, SMTP, LLM, and pandas operations.

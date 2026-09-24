# 🤖 LangGraph AI Assistant & Interactive Streamlit Dashboard

An interactive AI chat dashboard powered by **LangGraph**, **Groq LLM**, and **Streamlit** with memory persistence and multi-conversation management.

---

## 🌟 Features

- **Dynamic Conversation Threads**: Easily switch between multiple chats with automatic chat titling based on initial query.
- **Conversation Lifecycle**: Create new chats, clear message history in an active thread, or delete conversations.
- **LangGraph Memory Saver**: Stateful multi-turn reasoning graph with checkpointed conversation memory.
- **Streaming Responses**: Real-time token streaming with custom-styled user and assistant chat bubbles.
- **Resilient Database Layer**: Optional MongoDB integration for persistent chat archiving with non-blocking error fallbacks.
- **Secure Credentials Handling**: Strict adherence to `.env` variable configuration with zero hardcoded credentials.

---

## 🏗️ Architecture

```
Streamlit_Interactive_Dashboard/
└── Chatbot/
    ├── streamlit_frontend.py  # Streamlit UI with multi-chat sidebar and message bubbles
    ├── langgraph_backend.py   # StateGraph, ChatGroq model runner, and MongoDB logger
    ├── requirements.txt       # Project dependencies
    ├── .gitignore             # Secrets & cache ignore rules
    └── README.md              # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- A free [Groq Cloud](https://console.groq.com/) API Key

### 2. Environment Setup

Create a virtual environment and install the required dependencies:

```bash
# Navigate to the Chatbot directory
cd Streamlit_Interactive_Dashboard/Chatbot

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration (.env)

Create a `.env` file in the `Chatbot/` folder (or workspace root):

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
GROQ_MAX_TOKENS=1024

# Optional: MongoDB connection string for persistent chat archiving
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
```

> **Note:** If `MONGO_URI` is omitted, the chatbot runs completely in-memory without errors.

---

## 💻 Running the Application

Launch the Streamlit web dashboard:

```bash
streamlit run streamlit_frontend.py
```

Access the UI at `http://localhost:8501`.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit, Custom CSS
- **Orchestration:** LangGraph, LangChain Core
- **Inference Engine:** Groq API (`ChatGroq`)
- **Database (Optional):** MongoDB (`pymongo`)
- **Config:** `python-dotenv`

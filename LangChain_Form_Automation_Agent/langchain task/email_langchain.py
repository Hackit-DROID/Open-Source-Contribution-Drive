import os
from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# ---------------------------
# LLM setup
# ---------------------------
llm = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    model="openai/gpt-3.5-turbo"
)

# ---------------------------
# Gmail config
# ---------------------------
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# ---------------------------
# Google Sheet (CSV read)
# ---------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/12uWwn4JHwYrqiSH4_yVr-LqnuNW8jrC-eV9Rp2x534Q/gviz/tq?tqx=out:csv"

# ---------------------------
# LangGraph State
# ---------------------------
class GraphState(TypedDict):
    email: str
    question: str
    answer: str

# ---------------------------
# Node 1: Read latest entry
# ---------------------------
def get_latest_input(state):
    df = pd.read_csv(SHEET_URL)

    print("COLUMNS:", df.columns.tolist())  # 👈 DEBUG LINE

    last_row = df.iloc[-1]
    return {
        "email": last_row["Email"],
        "question": last_row["Ask your question here !"]
    }

# ---------------------------
# Node 2: LLM Answer
# ---------------------------
def llm_answer(state: GraphState):
    response = llm.invoke(state["question"])
    return {"answer": response.content}

# ---------------------------
# Node 3: Send Email
# ---------------------------
def send_email(state: GraphState):
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = state["email"]
    msg["Subject"] = "Your AI Generated Answer"

    body = f"""
Hello 👋

You asked:
{state['question']}

AI Answer:
{state['answer']}

Regards,
AI Assistant
"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

    print("📩 Email sent to:", state["email"])
    return state

# ---------------------------
# Build LangGraph
# ---------------------------
graph = StateGraph(GraphState)

graph.add_node("get_input", get_latest_input)
graph.add_node("llm_answer", llm_answer)
graph.add_node("send_email", send_email)

graph.set_entry_point("get_input")
graph.add_edge("get_input", "llm_answer")
graph.add_edge("llm_answer", "send_email")
graph.add_edge("send_email", END)

app = graph.compile()

# ---------------------------
# Run
# ---------------------------
result = app.invoke({})
print("✅ Workflow completed")


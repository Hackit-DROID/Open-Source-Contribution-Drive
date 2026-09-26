import os
from typing import TypedDict, Optional
from dotenv import load_dotenv

load_dotenv()

import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import sys
from pathlib import Path

# Ensure parent directory is in sys.path for local resilient_graph fallback
_parent_dir = str(Path(__file__).resolve().parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from langchain_openai import ChatOpenAI
from resilient_graph import StateGraph, END

try:
    from supabase import create_client
except ImportError:
    create_client = None

# ---------------------------
# Configuration
# ---------------------------
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/12uWwn4JHwYrqiSH4_yVr-LqnuNW8jrC-eV9Rp2x534Q/gviz/tq?tqx=out:csv"
SHEET_URL = os.getenv("GOOGLE_SHEET_CSV_URL", DEFAULT_SHEET_URL)

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:
        print(f"⚠️ Supabase client initialization error: {exc}")


def get_llm():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-3.5-turbo"
    )


# ---------------------------
# LangGraph State
# ---------------------------
class GraphState(TypedDict, total=False):
    email: str
    question: str
    answer: str
    name: Optional[str]
    phone: Optional[str]
    email_status: Optional[str]
    db_status: Optional[str]
    error: Optional[str]


# ---------------------------
# Node 1: Read latest entry
# ---------------------------
def get_latest_input(state: GraphState) -> GraphState:
    df = pd.read_csv(SHEET_URL)
    if hasattr(df.columns, "str"):
        df.columns = df.columns.str.strip()
    else:
        df.columns = [str(c).strip() for c in df.columns]
    last_row = df.iloc[-1]

    # Flexible column resolution
    email_col = next((c for c in df.columns if "email" in str(c).lower()), "Email")
    question_col = next((c for c in df.columns if "question" in str(c).lower()), df.columns[1] if len(df.columns) > 1 else df.columns[0])
    name_col = next((c for c in df.columns if "name" in str(c).lower()), None)
    phone_col = next((c for c in df.columns if "phone" in str(c).lower()), None)

    return {
        "email": str(last_row[email_col]),
        "question": str(last_row[question_col]),
        "name": str(last_row[name_col]) if name_col and name_col in last_row else "",
        "phone": str(last_row[phone_col]) if phone_col and phone_col in last_row else ""
    }


# ---------------------------
# Node 2: LLM Answer
# ---------------------------
def llm_answer(state: GraphState) -> GraphState:
    llm = get_llm()
    if llm is None:
        return {"answer": f"Simulated answer for: {state.get('question')}"}

    response = llm.invoke(state["question"])
    content = response.content if hasattr(response, "content") else str(response)
    return {"answer": str(content)}


# ---------------------------
# Node 3: Send Email
# ---------------------------
def send_email(state: GraphState) -> GraphState:
    recipient = state.get("email")
    if not recipient or not SENDER_EMAIL or not APP_PASSWORD:
        print("⚠️ Email skipped: missing recipient or SMTP credentials.")
        return {"email_status": "skipped"}

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient
    msg["Subject"] = "Your AI Generated Answer"

    user_name = f" {state.get('name')}" if state.get("name") else ""
    body = f"""Hello{user_name} 👋

You asked:
{state.get('question')}

AI Answer:
{state.get('answer')}

Regards,
AI Assistant
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print("📩 Email sent to:", recipient)
        return {"email_status": "sent"}
    except Exception as exc:
        print(f"⚠️ Failed to send email: {exc}")
        return {"email_status": f"failed: {exc}"}


# ---------------------------
# Node 4: Save to Supabase
# ---------------------------
def save_to_supabase(state: GraphState) -> GraphState:
    if not supabase:
        print("⚠️ Supabase skipped: client not configured.")
        return {"db_status": "skipped"}

    try:
        supabase.table("qa_log").insert({
            "email": state.get("email", ""),
            "question": state.get("question", ""),
            "answer": state.get("answer", ""),
            "name": state.get("name", ""),
            "phone_no": state.get("phone", "")
        }).execute()
        print("✅ Saved to Supabase!")
        return {"db_status": "saved"}
    except Exception as exc:
        print(f"⚠️ Supabase write failed: {exc}")
        return {"db_status": f"failed: {exc}"}


# ---------------------------
# Build Graph
# ---------------------------
def build_supabase_form_agent():
    graph = StateGraph(GraphState)
    graph.add_node("get_input", get_latest_input)
    graph.add_node("llm_answer", llm_answer)
    graph.add_node("send_email", send_email)
    graph.add_node("save_to_supabase", save_to_supabase)

    graph.set_entry_point("get_input")
    graph.add_edge("get_input", "llm_answer")
    graph.add_edge("llm_answer", "send_email")
    graph.add_edge("send_email", "save_to_supabase")
    graph.add_edge("save_to_supabase", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_supabase_form_agent()
    result = app.invoke({})
    print("✅ Workflow completed:", result)

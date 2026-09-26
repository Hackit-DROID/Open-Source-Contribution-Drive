import os
import sys
from pathlib import Path
from typing import TypedDict, Optional, List, Callable, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure parent directory is in sys.path for local resilient_graph fallback
_parent_dir = str(Path(__file__).resolve().parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    import pandas as pd
except ImportError:
    pd = None

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

from resilient_graph import (
    StateGraph,
    END,
    classify_error,
    calculate_backoff_delay,
    execute_backoff,
    execute_backoff_async,
    StateValidationError,
)

# ---------------------------
# LLM setup
# ---------------------------
llm = None
if ChatOpenAI and os.getenv("OPENROUTER_API_KEY"):
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
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/12uWwn4JHwYrqiSH4_yVr-LqnuNW8jrC-eV9Rp2x534Q/gviz/tq?tqx=out:csv"
SHEET_URL = os.getenv("GOOGLE_SHEET_CSV_URL", DEFAULT_SHEET_URL)

# ---------------------------
# LangGraph State
# ---------------------------
class GraphState(TypedDict, total=False):
    email: str
    question: str
    answer: str
    error: Optional[str]
    error_type: Optional[str]
    retry_count: int
    status: str
    email_status: str
    recovery_status: str
    trace: List[str]

# ---------------------------
# Node 1: Read latest entry
# ---------------------------
def get_latest_input(state: GraphState) -> GraphState:
    if state.get("email") and state.get("question"):
        return {
            "email": state["email"],
            "question": state["question"],
            "error": None,
            "error_type": None
        }

    if pd is None:
        return {
            "error": "pandas is required to read Google Sheet input",
            "error_type": "fatal",
            "status": "fatal"
        }

    try:
        df = pd.read_csv(SHEET_URL)
        if df.empty:
            return {
                "error": "Google Sheet is empty",
                "error_type": "fatal",
                "status": "fatal"
            }

        last_row = df.iloc[-1]
        return {
            "email": last_row["Email"],
            "question": last_row["Ask your question here !"],
            "error": None,
            "error_type": None
        }
    except Exception as exc:
        err_type = classify_error(exc)
        current_retries = state.get("retry_count", 0) + (1 if err_type == "transient" else 0)
        return {
            "error": str(exc),
            "error_type": err_type,
            "retry_count": current_retries,
            "status": "retrying" if err_type == "transient" else "fatal"
        }

# ---------------------------
# Node 2: LLM Answer
# ---------------------------
def llm_answer(state: GraphState) -> GraphState:
    question = state.get("question")
    if not question:
        return {
            "error": "Cannot generate LLM answer without question",
            "error_type": "fatal",
            "status": "fatal"
        }

    if llm is None:
        return {
            "answer": f"Simulated response for: {question}",
            "error": None,
            "error_type": None,
            "retry_count": 0,
            "status": "success"
        }

    try:
        response = llm.invoke(question)
        if hasattr(response, "content") and isinstance(response.content, str):
            content = response.content
        elif hasattr(response, "content"):
            content = str(response.content)
        else:
            content = str(response)

        return {
            "answer": content,
            "error": None,
            "error_type": None,
            "retry_count": 0,
            "status": "success"
        }
    except Exception as exc:
        err_type = classify_error(exc)
        current_retries = state.get("retry_count", 0) + (1 if err_type == "transient" else 0)
        return {
            "error": str(exc),
            "error_type": err_type,
            "retry_count": current_retries,
            "status": "retrying" if err_type == "transient" else "fatal"
        }

# ---------------------------
# Node 3: Send Email
# ---------------------------
def send_email(state: GraphState) -> GraphState:
    recipient = state.get("email")
    if not recipient or "@" not in recipient:
        return {
            "error": f"Invalid recipient email address: '{recipient}'",
            "error_type": "fatal",
            "status": "fatal"
        }

    answer = state.get("answer")
    if not answer:
        return {
            "error": "Cannot send email without an answer",
            "error_type": "fatal",
            "status": "fatal"
        }

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL or "noreply@example.com"
    msg["To"] = recipient
    msg["Subject"] = "Your AI Generated Answer"

    body = f"""
Hello 👋

You asked:
{state.get('question', '')}

AI Answer:
{answer}

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
        return {
            "email_status": "sent",
            "error": None,
            "error_type": None,
            "retry_count": 0,
            "status": "success"
        }
    except Exception as exc:
        err_type = classify_error(exc)
        current_retries = state.get("retry_count", 0) + (1 if err_type == "transient" else 0)
        return {
            "error": str(exc),
            "error_type": err_type,
            "retry_count": current_retries,
            "status": "retrying" if err_type == "transient" else "fatal"
        }

# ---------------------------
# Recovery Node
# ---------------------------
def recovery_node(state: GraphState) -> GraphState:
    print("🛡️ Recovery node executed")
    q = state.get("question", "")
    fallback_answer = state.get("answer") or (
        f"Thank you for contacting us. We received your question: '{q}'. "
        "Our automated assistant is temporarily operating in fallback mode, and an update will follow."
    )
    email_status = state.get("email_status") or "queued_offline"
    return {
        "answer": fallback_answer,
        "email_status": email_status,
        "recovery_status": "recovered",
        "status": "recovered"
    }

# ---------------------------
# Conditional Routing Helper
# ---------------------------
def make_route_fn(
    max_retries: int = 2,
    base_delay: float = 0.1,
    factor: float = 2.0,
    max_delay: float = 30.0,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> Callable[[GraphState], str]:
    """Generates a synchronous conditional routing function."""
    def route_fn(state: GraphState) -> str:
        err_type = state.get("error_type")
        retries = state.get("retry_count", 0)

        if err_type == "transient":
            if retries <= max_retries:
                execute_backoff(retries, base_delay, factor, max_delay, sleep_fn)
                return "retry"
            return "fallback"
        elif err_type == "fatal":
            return "fallback"
        return "next"

    return route_fn


def make_async_route_fn(
    max_retries: int = 2,
    base_delay: float = 0.1,
    factor: float = 2.0,
    max_delay: float = 30.0,
    async_sleep_fn: Optional[Callable[[float], Any]] = None,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> Callable[[GraphState], Any]:
    """Generates an asynchronous conditional routing function."""
    async def route_fn(state: GraphState) -> str:
        err_type = state.get("error_type")
        retries = state.get("retry_count", 0)

        if err_type == "transient":
            if retries <= max_retries:
                await execute_backoff_async(retries, base_delay, factor, max_delay, async_sleep_fn, sleep_fn)
                return "retry"
            return "fallback"
        elif err_type == "fatal":
            return "fallback"
        return "next"

    return route_fn

# ---------------------------
# Build LangGraph
# ---------------------------
def create_email_agent_graph(
    llm_client=None,
    max_retries: int = 2,
    base_delay: float = 0.1,
    factor: float = 2.0,
    max_delay: float = 30.0,
    sleep_fn: Optional[Callable[[float], None]] = None,
    is_async: bool = False,
    async_sleep_fn: Optional[Callable[[float], Any]] = None,
) -> StateGraph:
    """Build the resilient multi-node state graph with conditional retry edges."""
    global llm
    if llm_client is not None:
        llm = llm_client

    graph = StateGraph(GraphState)

    graph.add_node("get_input", get_latest_input)
    graph.add_node("llm_answer", llm_answer)
    graph.add_node("send_email", send_email)
    graph.add_node("recovery", recovery_node)

    graph.set_entry_point("get_input")

    route_fn = (
        make_async_route_fn(max_retries, base_delay, factor, max_delay, async_sleep_fn, sleep_fn)
        if is_async
        else make_route_fn(max_retries, base_delay, factor, max_delay, sleep_fn)
    )

    graph.add_conditional_edges(
        "get_input",
        route_fn,
        {"next": "llm_answer", "retry": "get_input", "fallback": "recovery"}
    )
    graph.add_conditional_edges(
        "llm_answer",
        route_fn,
        {"next": "send_email", "retry": "llm_answer", "fallback": "recovery"}
    )
    graph.add_conditional_edges(
        "send_email",
        route_fn,
        {"next": END, "retry": "send_email", "fallback": "recovery"}
    )
    graph.add_edge("recovery", END)

    return graph


graph = create_email_agent_graph()
app = graph.compile()

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    result = app.invoke({})
    print("✅ Workflow completed")

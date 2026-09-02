import os
from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict
import pandas as pd

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
import requests


WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx9emYc3_SUeWIACIzOmvJAlmllZ9hvpJ3ZuZQXAl7YcMisP6HBN72XaMId2vhsOV19tA/exec"

def save_answer_to_sheet(answer):
    requests.post(WEB_APP_URL, json={"answer": answer})

# ---------------------------
# LLM setup
# ---------------------------
llm = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    model="openai/gpt-3.5-turbo"
)

# ---------------------------
# Google Sheet
# ---------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/12uWwn4JHwYrqiSH4_yVr-LqnuNW8jrC-eV9Rp2x534Q/gviz/tq?tqx=out:csv"

# ---------------------------
# State definition (LangGraph ka brain)
# ---------------------------
class GraphState(TypedDict):
    question: str
    answer: str

# ---------------------------
# Node 1: Read question
# ---------------------------
def get_latest_question(state: GraphState):
    df = pd.read_csv(SHEET_URL)
    question = df.iloc[-1][df.columns[1]]
    return {"question": question}

# ---------------------------
# Node 2: LLM answer
# ---------------------------
def llm_answer(state: GraphState):
    response = llm.invoke(state["question"])
    return {"answer": response.content}

# ---------------------------
# Build LangGraph
# ---------------------------
graph = StateGraph(GraphState)

graph.add_node("get_question", get_latest_question)
graph.add_node("llm_answer", llm_answer)

graph.set_entry_point("get_question")
graph.add_edge("get_question", "llm_answer")
graph.add_edge("llm_answer", END)

app = graph.compile()

# ---------------------------
# Run graph
# ---------------------------
result = app.invoke({})

print("User Question:", result["question"])
print("LangGraph Answer:", result["answer"])

# ✅ SAVE TO GOOGLE SHEET
save_answer_to_sheet(result["answer"])

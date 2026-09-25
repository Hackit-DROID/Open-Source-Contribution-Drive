# -----------------------------
# 1️⃣ Imports
# -----------------------------
import os
from dotenv import load_dotenv

load_dotenv()

import pandas as pd
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# -----------------------------
# 2️⃣ LLM Setup (OpenRouter)
# -----------------------------
llm = ChatOpenAI(
    model="openai/gpt-4.1-mini",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# -----------------------------
# 3️⃣ Graph State
# -----------------------------
class GraphState(TypedDict):
    question: str
    answer: str

# -----------------------------
# 4️⃣ LLM Node
# -----------------------------
def llm_node(state: GraphState):
    response = llm.invoke(state["question"])
    return {"answer": response.content}

# -----------------------------
# 5️⃣ Build LangGraph
# -----------------------------
graph = StateGraph(GraphState)

graph.add_node("llm", llm_node)
graph.set_entry_point("llm")
graph.add_edge("llm", END)

app = graph.compile()

# -----------------------------
# 6️⃣ Read Google Sheet
# -----------------------------
# -----------------------------
# 6️⃣ Read Google Sheet (FIXED)
# -----------------------------
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/12uWwn4JHwYrqiSH4_yVr-LqnuNW8jrC-eV9Rp2x534Q/export?format=csv"

df = pd.read_csv(
    SHEET_CSV_URL,
    engine="python",
    on_bad_lines="skip"
)

# Remove hidden spaces in column names
df.columns = df.columns.str.strip()

# Check columns
print(df.columns)

# Get last question
user_question = df["Ask Your Questions here !"].iloc[-1]
print("User Question:", user_question)


user_question = df["Ask Your Questions here !"].iloc[-1]
print("User Question:", user_question)

# -----------------------------
# 7️⃣ Invoke Graph
# -----------------------------
result = app.invoke({
    "question": user_question
})

print("LangChain Answer:", result["answer"])

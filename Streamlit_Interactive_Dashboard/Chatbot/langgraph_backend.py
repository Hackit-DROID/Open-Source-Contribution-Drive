from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# -------- NEW IMPORTS --------
from pymongo import MongoClient
from datetime import datetime
import os

# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- DATABASE ----------------
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client["langgraph_chatbot"]
chat_collection = db["conversations"]

# ---------------- STATE ----------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ---------------- LLM ----------------
llm = ChatGroq(
    model="llama-3.1-8b-instant"
)

# ---------------- NODE ----------------
def chat_node(state: ChatState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# ---------------- MEMORY ----------------
checkpointer = MemorySaver()

# ---------------- GRAPH ----------------
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# ---------------- NORMAL RESPONSE ----------------
def get_ai_response(user_text: str, thread_id: str = "default"):
    result = chatbot.invoke(
        {"messages": [HumanMessage(content=user_text)]},
        config={"configurable": {"thread_id": thread_id}},
    )

    ai_reply = result["messages"][-1].content

    # -------- SAVE TO MONGODB --------
    chat_collection.insert_one({
        "thread_id": thread_id,
        "user_message": user_text,
        "assistant_message": ai_reply,
        "timestamp": datetime.utcnow()
    })

    return ai_reply

# ---------------- STREAMING RESPONSE ----------------
def stream_ai_response(user_text: str, thread_id: str):
    """
    Streaming WITH memory using LangGraph + MongoDB persistence
    """
    full_response = ""

    events = chatbot.stream(
        {"messages": [HumanMessage(content=user_text)]},
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="messages",
    )

    for event in events:
        if event[0].content:
            token = event[0].content
            full_response += token
            yield token

    # -------- SAVE COMPLETE CHAT TO MONGODB --------
    chat_collection.insert_one({
        "thread_id": thread_id,
        "user_message": user_text,
        "assistant_message": full_response,
        "timestamp": datetime.utcnow()
    })
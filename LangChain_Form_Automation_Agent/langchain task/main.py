"""
Resilient agent execution graph example (CR-1491).
Features multi-node execution with retry policy, exponential backoff,
and fallback recovery.
"""
import sys
from pathlib import Path

# Add project path to enable resilient_graph import
current_dir = Path(__file__).resolve().parent
if str(current_dir.parent) not in sys.path:
    sys.path.insert(0, str(current_dir.parent))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from resilient_graph import ResilientStateGraph as StateGraph, END, RetryPolicy, AgentState
except ImportError:
    from langgraph.graph import StateGraph, END  # Fallback for standard LangGraph environments
    RetryPolicy = None
    AgentState = dict

# -----------------------
# NODE 1: Input Node
# -----------------------
def input_node(state):
    print("👉 Input Node")
    return {
        "question": state["question"]
    }

# -----------------------
# NODE 2: Processing Node
# -----------------------
def process_node(state):
    print("👉 Process Node")
    q = state["question"]
    return {
        "question": q,
        "processed": q.upper()
    }

# -----------------------
# FALLBACK: Fallback Recovery for Process Node
# -----------------------
def process_fallback(state, error):
    print(f"⚠️ Process Node fallback triggered on error: {error}")
    q = state.get("question", "")
    return {
        "question": q,
        "processed": f"{q} (fallback)"
    }

# -----------------------
# NODE 3: Output Node
# -----------------------
def output_node(state):
    print("👉 Output Node")
    return {
        "answer": f"Processed Question: {state['processed']}"
    }

# -----------------------
# GRAPH CREATION
# -----------------------
graph = StateGraph(dict)

if RetryPolicy:
    retry_policy = RetryPolicy(max_retries=2, base_delay=0.1, factor=2.0)
    graph.add_node("input", input_node)
    graph.add_node("process", process_node, retry_policy=retry_policy, fallback_handler=process_fallback)
    graph.add_node("output", output_node)
else:
    graph.add_node("input", input_node)
    graph.add_node("process", process_node)
    graph.add_node("output", output_node)

graph.add_edge("input", "process")
graph.add_edge("process", "output")
graph.add_edge("output", END)

graph.set_entry_point("input")

app = graph.compile()

# -----------------------
# RUN GRAPH
# -----------------------
if __name__ == '__main__':
    result = app.invoke({
        "question": "hello langchain"
    })

    print("\n✅ FINAL RESULT:")
    print(result["answer"])

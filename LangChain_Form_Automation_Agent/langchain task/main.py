from langgraph.graph import StateGraph, END

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
result = app.invoke({
    "question": "hello langchain"
})

print("\n✅ FINAL RESULT:")
print(result["answer"])

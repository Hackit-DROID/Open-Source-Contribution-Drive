import streamlit as st
import time
import uuid
from langgraph_backend import stream_ai_response

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="LangGraph AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS =================
st.markdown("""
<style>
/* Background */
.stApp {
    background-color: #0f172a;
    color: white;
}

/* Title Styling */
.main-title {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(90deg, #38bdf8, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 20px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #111827;
}

/* Chat Bubbles */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 8px;
}

/* User message */
[data-testid="stChatMessage"][data-testid*="user"] {
    background-color: #1e293b;
}

/* Assistant message */
[data-testid="stChatMessage"][data-testid*="assistant"] {
    background-color: #0ea5e9;
    color: white;
}

/* Buttons */
.stButton>button {
    border-radius: 8px;
    background-color: #1f2937;
    color: white;
    border: 1px solid #374151;
}

.stButton>button:hover {
    background-color: #374151;
}
</style>
""", unsafe_allow_html=True)

# ================= TITLE =================
st.markdown('<div class="main-title">🤖 LangGraph AI Assistant</div>', unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 💬 Conversations")

    if "chats" not in st.session_state:
        st.session_state.chats = {}

    if "current_chat" not in st.session_state:
        new_id = str(uuid.uuid4())
        st.session_state.current_chat = new_id
        st.session_state.chats[new_id] = []

    # -------- NEW CHAT BUTTON --------
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.current_chat = new_id
        st.session_state.chats[new_id] = []
        st.rerun()

    st.divider()

    # -------- CHAT LIST --------
    for chat_id in st.session_state.chats.keys():
        label = f"💬 {chat_id[:8]}"
        if st.button(label, key=chat_id, use_container_width=True):
            st.session_state.current_chat = chat_id
            st.rerun()

# ================= CURRENT CHAT =================
current_chat_id = st.session_state.current_chat
messages = st.session_state.chats[current_chat_id]

# -------- DISPLAY OLD MESSAGES --------
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ================= INPUT =================
user_input = st.chat_input("Type your message...")

if user_input:
    messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # -------- STREAMING RESPONSE --------
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        for token in stream_ai_response(user_input, current_chat_id):
            full_response += token
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.01)

        message_placeholder.markdown(full_response)

    messages.append({"role": "assistant", "content": full_response})
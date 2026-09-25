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

    if "chat_titles" not in st.session_state:
        st.session_state.chat_titles = {}

    if "current_chat" not in st.session_state:
        new_id = str(uuid.uuid4())
        st.session_state.current_chat = new_id
        st.session_state.chats[new_id] = []
        st.session_state.chat_titles[new_id] = "New Chat"

    # -------- NEW CHAT BUTTON --------
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        st.session_state.current_chat = new_id
        st.session_state.chats[new_id] = []
        st.session_state.chat_titles[new_id] = "New Chat"
        st.rerun()

    st.divider()

    # -------- CHAT LIST WITH DELETE --------
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in chat_ids:
        title = st.session_state.chat_titles.get(chat_id, f"Chat {chat_id[:6]}")
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            is_active = (chat_id == st.session_state.current_chat)
            label = f"👉 {title}" if is_active else f"💬 {title}"
            if st.button(label, key=f"select_{chat_id}", use_container_width=True):
                st.session_state.current_chat = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}", help="Delete chat", use_container_width=True):
                del st.session_state.chats[chat_id]
                if chat_id in st.session_state.chat_titles:
                    del st.session_state.chat_titles[chat_id]
                # If deleted current chat, pick another or make a new one
                remaining = list(st.session_state.chats.keys())
                if remaining:
                    st.session_state.current_chat = remaining[0]
                else:
                    new_id = str(uuid.uuid4())
                    st.session_state.current_chat = new_id
                    st.session_state.chats[new_id] = []
                    st.session_state.chat_titles[new_id] = "New Chat"
                st.rerun()

# ================= CURRENT CHAT CONTROLS =================
current_chat_id = st.session_state.current_chat
messages = st.session_state.chats[current_chat_id]

top_col1, top_col2 = st.columns([0.8, 0.2])
with top_col1:
    chat_title = st.session_state.chat_titles.get(current_chat_id, "New Chat")
    st.caption(f"Active Conversation: **{chat_title}** (`{current_chat_id[:8]}`)")
with top_col2:
    if st.button("🧹 Clear Chat", use_container_width=True, help="Clear messages in this conversation"):
        st.session_state.chats[current_chat_id] = []
        st.session_state.chat_titles[current_chat_id] = "New Chat"
        st.rerun()

# -------- DISPLAY OLD MESSAGES --------
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ================= INPUT =================
user_input = st.chat_input("Type your message...")

if user_input:
    # Auto-generate title from first message
    if not messages:
        auto_title = user_input.strip()[:24] + ("..." if len(user_input.strip()) > 24 else "")
        st.session_state.chat_titles[current_chat_id] = auto_title

    messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # -------- STREAMING RESPONSE --------
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            for token in stream_ai_response(user_input, current_chat_id):
                full_response += token
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.01)

            message_placeholder.markdown(full_response)
            messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            error_msg = f"⚠️ **Error generating response:** {e}"
            message_placeholder.error(error_msg)
            messages.append({"role": "assistant", "content": error_msg})
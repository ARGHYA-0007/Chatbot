import streamlit as st
import requests
import time
import random

# --- Config ---
API_URL = "http://127.0.0.1:8000/chatbot"

st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="centered")

# --- Custom CSS for animations & polish ---
st.markdown("""
<style>
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0% { opacity: 0.4; }
    50% { opacity: 1; }
    100% { opacity: 0.4; }
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.stChatMessage {
    animation: fadeIn 0.35s ease-out;
}
.typing-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    margin: 0 2px;
    border-radius: 50%;
    background: #8a8a8a;
    animation: pulse 1.2s infinite ease-in-out;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

.gradient-title {
    background: linear-gradient(270deg, #7F5FFF, #22C1C3, #7F5FFF);
    background-size: 600% 600%;
    animation: gradientShift 6s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.2rem;
    margin-bottom: 0;
}
.subtitle {
    color: #9a9a9a;
    font-size: 0.9rem;
    margin-top: -6px;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<p class="gradient-title">🤖 AI Chatbot</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">FastAPI + LangGraph + Ollama (qwen2.5:1.5b)</p>', unsafe_allow_html=True)
st.divider()

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Render chat history ---
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


def typing_indicator(placeholder):
    """Animated 'thinking' dots while waiting on the backend."""
    placeholder.markdown(
        '<span class="typing-dot"></span><span class="typing-dot"></span>'
        '<span class="typing-dot"></span>',
        unsafe_allow_html=True,
    )


def stream_text(placeholder, full_text: str, speed: float = 0.015):
    """Client-side typewriter effect — reveals text word by word."""
    words = full_text.split(" ")
    shown = ""
    for i, word in enumerate(words):
        shown += word + (" " if i < len(words) - 1 else "")
        placeholder.markdown(shown + "▌")
        # slight randomness so it doesn't feel robotic
        time.sleep(speed + random.uniform(0, 0.01))
    placeholder.markdown(shown)


def call_backend(query: str) -> str:
    response = requests.post(API_URL, params={"query": query}, timeout=300)
    response.raise_for_status()
    return response.json().get("AI", "No response received.")


# --- Chat input ---
user_query = st.chat_input("Ask something...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_query)

    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()
        typing_indicator(placeholder)

        try:
            answer = call_backend(user_query)
            stream_text(placeholder, answer)
        except requests.exceptions.ConnectionError:
            answer = "⚠️ Could not connect to the backend. Is FastAPI running on port 8000?"
            placeholder.markdown(answer)
        except requests.exceptions.Timeout:
            answer = "⚠️ The model took too long to respond. Try again or check Ollama."
            placeholder.markdown(answer)
        except requests.exceptions.RequestException as e:
            answer = f"⚠️ Error calling backend: {e}"
            placeholder.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.text_input("API URL", value=API_URL, key="api_url_display", disabled=True)
    speed = st.slider("Typing speed", 0.0, 0.08, 0.015, 0.005,
                       help="Lower = faster typewriter animation")
    st.caption(f"Messages in this session: {len(st.session_state.messages)}")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
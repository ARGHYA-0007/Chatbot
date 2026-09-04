import streamlit as st
import requests
import time
import random
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
API_BASE = "http://127.0.0.1:8000"
CHAT_URL = f"{API_BASE}/chatbot"

st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="wide")

# ============================================================
# STYLES
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

* { font-family: 'Inter', sans-serif; }

@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(10px) scale(0.98); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes pulse {
    0%, 100% { opacity: 0.35; transform: scale(0.85); }
    50%      { opacity: 1;    transform: scale(1); }
}
@keyframes bgShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 6px 1px rgba(80,220,120,0.6); }
    50%      { box-shadow: 0 0 12px 4px rgba(80,220,120,0.9); }
}
@keyframes blink { 50% { opacity: 0; } }

.stApp {
    background: linear-gradient(120deg, #0f0c29, #302b63, #24243e, #1a1a3d);
    background-size: 400% 400%;
    animation: bgShift 18s ease infinite;
}

.gradient-title {
    background: linear-gradient(270deg, #7F5FFF, #22C1C3, #FF6FD8, #7F5FFF);
    background-size: 600% 600%;
    animation: bgShift 8s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.4rem;
    margin-bottom: 0;
}
.subtitle { color: #b8b8d1; font-size: 0.92rem; margin-top: -6px; }

.status-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px;
    background: rgba(255,255,255,0.06); font-size: 0.8rem; color: #ddd;
    border: 1px solid rgba(255,255,255,0.1);
}
.status-dot {
    width: 8px; height: 8px; border-radius: 50%;
}
.dot-online  { background: #4ade80; animation: glowPulse 1.8s infinite; }
.dot-offline { background: #f87171; }

.bubble-wrap { animation: fadeSlideIn 0.35s ease-out; margin-bottom: 14px; display: flex; }
.bubble-user { justify-content: flex-end; }
.bubble-assistant { justify-content: flex-start; }

.bubble {
    max-width: 72%; padding: 12px 16px; border-radius: 18px;
    font-size: 0.96rem; line-height: 1.5; position: relative;
    backdrop-filter: blur(10px);
}
.bubble-user .bubble {
    background: linear-gradient(135deg, #7F5FFF, #22C1C3);
    color: white; border-bottom-right-radius: 4px;
}
.bubble-assistant .bubble {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    color: #f0f0f5; border-bottom-left-radius: 4px;
}
.msg-time { font-size: 0.68rem; opacity: 0.55; margin-top: 4px; }

.avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; flex-shrink: 0;
}
.avatar-user { background: linear-gradient(135deg, #22C1C3, #7F5FFF); margin-left: 10px; }
.avatar-assistant { background: rgba(255,255,255,0.1); margin-right: 10px; }

.typing-dot {
    display: inline-block; width: 7px; height: 7px; margin: 0 2px;
    border-radius: 50%; background: #b8b8d1; animation: pulse 1.2s infinite ease-in-out;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

.cursor { animation: blink 0.9s step-end infinite; }

.chip {
    display: inline-block; padding: 6px 14px; margin: 4px 6px 4px 0;
    border-radius: 16px; background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15); font-size: 0.82rem;
    color: #ddd; cursor: pointer;
}

section[data-testid="stSidebar"] {
    background: rgba(20, 18, 45, 0.9); backdrop-filter: blur(12px);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []   # {role, content, time, response_time?, reaction?}
if "typing_speed" not in st.session_state:
    st.session_state.typing_speed = 0.015
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# ============================================================
# BACKEND HEALTH CHECK (cached briefly so it isn't hit every rerun)
# ============================================================
@st.cache_data(ttl=5)
def check_backend():
    try:
        r = requests.get(f"{API_BASE}/", timeout=2)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False

is_online = check_backend()

# ============================================================
# HEADER
# ============================================================
col_title, col_status = st.columns([4, 1])
with col_title:
    st.markdown('<p class="gradient-title">🤖 AI Chatbot</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">FastAPI + LangGraph + Ollama (qwen2.5:1.5b)</p>', unsafe_allow_html=True)
with col_status:
    dot_class = "dot-online" if is_online else "dot-offline"
    label = "Online" if is_online else "Offline"
    st.markdown(f"""
    <div style="display:flex; justify-content:flex-end; margin-top:18px;">
        <span class="status-badge"><span class="status-dot {dot_class}"></span>{label}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# QUICK PROMPT CHIPS (only shown before any conversation starts)
# ============================================================
if not st.session_state.messages:
    st.markdown("**Try one of these:**")
    suggestions = ["Explain LangGraph in simple terms", "Write a haiku about AI",
                   "What's the capital of Japan?", "Give me a Python one-liner for Fibonacci"]
    cols = st.columns(len(suggestions))
    for i, s in enumerate(suggestions):
        if cols[i].button(s, key=f"chip_{i}", use_container_width=True):
            st.session_state.pending_query = s
            st.rerun()

# ============================================================
# RENDER CHAT HISTORY
# ============================================================
def render_bubble(role, content, msg_time, idx=None):
    if role == "user":
        st.markdown(f"""
        <div class="bubble-wrap bubble-user">
            <div class="bubble">{content}<div class="msg-time">{msg_time}</div></div>
            <div class="avatar avatar-user">🧑</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="bubble-wrap bubble-assistant">
            <div class="avatar avatar-assistant">🤖</div>
            <div class="bubble">{content}<div class="msg-time">{msg_time}</div></div>
        </div>""", unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    render_bubble(msg["role"], msg["content"], msg["time"])
    if msg["role"] == "assistant":
        c1, c2, c3, c4 = st.columns([0.06, 0.06, 0.06, 0.82])
        if c1.button("👍", key=f"up_{i}"):
            st.session_state.messages[i]["reaction"] = "up"
            st.toast("Thanks for the feedback!", icon="👍")
        if c2.button("👎", key=f"down_{i}"):
            st.session_state.messages[i]["reaction"] = "down"
            st.toast("Noted — I'll aim better.", icon="👎")
        if c3.button("📋", key=f"copy_{i}", help="Show raw text to copy"):
            st.session_state[f"show_raw_{i}"] = not st.session_state.get(f"show_raw_{i}", False)
        if st.session_state.get(f"show_raw_{i}"):
            st.code(msg["content"], language=None)
        if "response_time" in msg:
            c4.caption(f"⏱ {msg['response_time']:.1f}s")

# ============================================================
# CORE FUNCTIONS
# ============================================================
def call_backend(query: str):
    t0 = time.time()
    response = requests.post(CHAT_URL, params={"query": query}, timeout=300)
    response.raise_for_status()
    answer = response.json().get("AI", "No response received.")
    return answer, time.time() - t0


def stream_placeholder(placeholder, full_text: str, speed: float):
    words = full_text.split(" ")
    shown = ""
    for i, word in enumerate(words):
        shown += word + (" " if i < len(words) - 1 else "")
        placeholder.markdown(f"""
        <div class="bubble-wrap bubble-assistant">
            <div class="avatar avatar-assistant">🤖</div>
            <div class="bubble">{shown}<span class="cursor">▌</span></div>
        </div>""", unsafe_allow_html=True)
        time.sleep(speed + random.uniform(0, 0.01))
    placeholder.markdown(f"""
    <div class="bubble-wrap bubble-assistant">
        <div class="avatar avatar-assistant">🤖</div>
        <div class="bubble">{shown}</div>
    </div>""", unsafe_allow_html=True)


def process_query(query: str):
    now = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "user", "content": query, "time": now})
    render_bubble("user", query, now)

    placeholder = st.empty()
    placeholder.markdown("""
    <div class="bubble-wrap bubble-assistant">
        <div class="avatar avatar-assistant">🤖</div>
        <div class="bubble"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>
    </div>""", unsafe_allow_html=True)

    try:
        answer, elapsed = call_backend(query)
        stream_placeholder(placeholder, answer, st.session_state.typing_speed)
    except requests.exceptions.ConnectionError:
        answer, elapsed = "⚠️ Could not connect to the backend. Is FastAPI running on port 8000?", 0
        placeholder.markdown(answer)
    except requests.exceptions.Timeout:
        answer, elapsed = "⚠️ The model took too long to respond. Try again or check Ollama.", 0
        placeholder.markdown(answer)
    except requests.exceptions.RequestException as e:
        answer, elapsed = f"⚠️ Error calling backend: {e}", 0
        placeholder.markdown(answer)

    st.session_state.messages.append({
        "role": "assistant", "content": answer,
        "time": datetime.now().strftime("%H:%M"), "response_time": elapsed
    })

# ============================================================
# INPUT HANDLING (chat box OR a clicked quick-prompt chip)
# ============================================================
typed_query = st.chat_input("Ask something...")
final_query = typed_query or st.session_state.pending_query
st.session_state.pending_query = None

if final_query:
    process_query(final_query)
    st.rerun()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.typing_speed = st.slider(
        "Typing speed", 0.0, 0.08, st.session_state.typing_speed, 0.005,
        help="Lower = faster typewriter animation"
    )

    st.divider()
    st.subheader("📊 Session Stats")
    total = len(st.session_state.messages)
    assistant_msgs = [m for m in st.session_state.messages if m["role"] == "assistant" and m.get("response_time")]
    avg_time = sum(m["response_time"] for m in assistant_msgs) / len(assistant_msgs) if assistant_msgs else 0
    c1, c2 = st.columns(2)
    c1.metric("Messages", total)
    c2.metric("Avg response", f"{avg_time:.1f}s")

    st.divider()
    if st.session_state.messages:
        transcript = "\n\n".join(
            f"**{m['role'].capitalize()}** ({m['time']}): {m['content']}"
            for m in st.session_state.messages
        )
        st.download_button("⬇️ Export chat (.md)", transcript,
                            file_name="chat_history.md", use_container_width=True)

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption(f"Backend: `{API_BASE}`")
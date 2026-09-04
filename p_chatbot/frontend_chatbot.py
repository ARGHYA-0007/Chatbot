import streamlit as st
import requests
import time
import random
import json
import uuid
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
API_BASE = "http://127.0.0.1:8000"
CHAT_URL = f"{API_BASE}/chatbot"

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide")

# ============================================================
# STATE INITIALIZATION
# ============================================================
def new_chat(title="New Chat"):
    cid = str(uuid.uuid4())[:8]
    st.session_state.chats[cid] = {"title": title, "messages": []}
    st.session_state.current_chat = cid
    return cid

if "chats" not in st.session_state:
    st.session_state.chats = {}
    new_chat("AI Assistant")

if "typing_speed" not in st.session_state:
    st.session_state.typing_speed = 0.015
if "skip_animation" not in st.session_state:
    st.session_state.skip_animation = False
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "search_term" not in st.session_state:
    st.session_state.search_term = ""

cid = st.session_state.current_chat
messages = st.session_state.chats[cid]["messages"]

# ============================================================
# WHATSAPP DARK MODE PALETTE (matches the real app's dark theme)
# ============================================================
WA_BG            = "#0B141A"   # main chat background
WA_HEADER        = "#202C33"   # header bar / sidebar panel
WA_HEADER_HOVER  = "#2A3942"
WA_BUBBLE_OUT    = "#005C4B"   # outgoing (your) message bubble
WA_BUBBLE_IN     = "#202C33"   # incoming (assistant) message bubble
WA_TEXT          = "#E9EDEF"
WA_TIME          = "#8696A0"
WA_TICK_BLUE     = "#53BDEB"
WA_ACCENT_GREEN  = "#00A884"
WA_DATE_CHIP_BG  = "#182229"
WA_INPUT_BG      = "#2A3942"

st.markdown(f"""
<style>
html, body, [class*="css"] {{
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
}}

@keyframes bubbleIn {{
    from {{ opacity: 0; transform: translateY(6px) scale(0.96); }}
    to   {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 0.3; transform: scale(0.8); }}
    50%      {{ opacity: 1;   transform: scale(1); }}
}}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
@keyframes tickPop {{
    0% {{ transform: scale(0); }}
    60% {{ transform: scale(1.3); }}
    100% {{ transform: scale(1); }}
}}

/* Dark WhatsApp wallpaper */
.stApp {{
    background-color: {WA_BG};
    background-image:
        radial-gradient(circle at 20% 20%, rgba(255,255,255,0.015) 2px, transparent 2px),
        radial-gradient(circle at 60% 70%, rgba(255,255,255,0.015) 2px, transparent 2px),
        radial-gradient(circle at 85% 30%, rgba(255,255,255,0.015) 2px, transparent 2px);
    background-size: 60px 60px, 80px 80px, 100px 100px;
    color: {WA_TEXT};
}}

/* Header bar */
.wa-header {{
    background: {WA_HEADER};
    color: {WA_TEXT}; padding: 14px 20px; border-radius: 10px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4); margin-bottom: 4px;
}}
.wa-header-left {{ display: flex; align-items: center; gap: 12px; }}
.wa-avatar-header {{
    width: 42px; height: 42px; border-radius: 50%;
    background: {WA_ACCENT_GREEN}; display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
}}
.wa-title {{ font-weight: 600; font-size: 1.05rem; margin: 0; color: {WA_TEXT}; }}
.wa-subtitle {{ font-size: 0.75rem; opacity: 0.7; margin: 0; color: {WA_TIME}; }}
.wa-status-online {{ display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: {WA_TIME}; }}
.wa-status-dot {{ width: 8px; height: 8px; border-radius: 50%; }}
.dot-online  {{ background: #4ade80; }}
.dot-offline {{ background: #f87171; }}

/* Bubbles */
.bubble-wrap {{ animation: bubbleIn 0.25s ease-out; margin-bottom: 3px; display: flex; }}
.bubble-user {{ justify-content: flex-end; }}
.bubble-assistant {{ justify-content: flex-start; }}

.bubble {{
    max-width: 68%; padding: 7px 9px 6px 10px; border-radius: 8px;
    font-size: 0.92rem; line-height: 1.4; color: {WA_TEXT};
    box-shadow: 0 1px 0.5px rgba(0,0,0,0.3);
    position: relative;
}}
.bubble-user .bubble {{
    background: {WA_BUBBLE_OUT}; border-top-right-radius: 0;
}}
.bubble-assistant .bubble {{
    background: {WA_BUBBLE_IN}; border-top-left-radius: 0;
}}
.bubble.dimmed {{ opacity: 0.25; }}

.msg-meta {{
    display: flex; justify-content: flex-end; align-items: center; gap: 3px;
    font-size: 0.68rem; color: {WA_TIME}; margin-top: 2px; float: right; margin-left: 8px;
}}
.tick {{ animation: tickPop 0.3s ease-out; color: {WA_TICK_BLUE}; }}
.pin-flag {{ font-size: 0.72rem; }}

/* Typing indicator bubble */
.typing-dot {{
    display: inline-block; width: 6px; height: 6px; margin: 0 2px;
    border-radius: 50%; background: {WA_TIME}; animation: pulse 1.2s infinite ease-in-out;
}}
.typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
.typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
.cursor {{ animation: blink 0.9s step-end infinite; color: {WA_TEXT}; }}

/* Date divider chip */
.date-chip {{
    text-align: center; margin: 10px auto; width: fit-content;
    background: {WA_DATE_CHIP_BG}; color: {WA_TIME}; font-size: 0.72rem;
    padding: 4px 12px; border-radius: 8px; box-shadow: 0 1px 0.5px rgba(0,0,0,0.3);
}}

/* Sidebar = WhatsApp chat list, dark panel */
section[data-testid="stSidebar"] {{
    background: {WA_HEADER};
}}
section[data-testid="stSidebar"] * {{
    color: {WA_TEXT};
}}
.chat-list-header {{
    background: {WA_BG}; color: {WA_TEXT}; padding: 12px 14px;
    border-radius: 8px; font-weight: 600; margin-bottom: 10px;
}}

/* Chat input row */
div[data-testid="stChatInput"] {{
    background: {WA_INPUT_BG}; border-radius: 24px;
}}
div[data-testid="stChatInput"] textarea {{
    color: {WA_TEXT} !important;
}}

/* Text inputs / text areas / search box */
.stTextInput input, .stTextArea textarea {{
    background: {WA_INPUT_BG} !important;
    color: {WA_TEXT} !important;
    border: 1px solid #344048 !important;
}}

/* Buttons */
.stButton button {{
    border-radius: 18px !important;
    background: {WA_HEADER_HOVER} !important;
    color: {WA_TEXT} !important;
    border: 1px solid #344048 !important;
}}
.stButton button:hover {{
    background: {WA_ACCENT_GREEN} !important;
    border-color: {WA_ACCENT_GREEN} !important;
}}

/* Captions / metrics text */
[data-testid="stCaptionContainer"], .stMetric label, .stMetric div {{
    color: {WA_TIME} !important;
}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# BACKEND HEALTH CHECK
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
# HEADER (WhatsApp chat header bar)
# ============================================================
dot_class = "dot-online" if is_online else "dot-offline"
status_label = "online" if is_online else "offline"
st.markdown(f"""
<div class="wa-header">
    <div class="wa-header-left">
        <div class="wa-avatar-header">🤖</div>
        <div>
            <p class="wa-title">{st.session_state.chats[cid]['title']}</p>
            <p class="wa-subtitle">qwen2.5:1.5b via Ollama</p>
        </div>
    </div>
    <div class="wa-status-online">
        <span class="wa-status-dot {dot_class}"></span>{status_label}
    </div>
</div>
""", unsafe_allow_html=True)

search = st.text_input("🔍 Search this chat", value=st.session_state.search_term,
                        placeholder="Search messages...", label_visibility="collapsed")
st.session_state.search_term = search

# ============================================================
# QUICK PROMPT CHIPS
# ============================================================
if not messages:
    st.caption("Say hi to start the conversation 👋")
    suggestions = ["Explain LangGraph in simple terms", "Write a haiku about AI",
                   "What's the capital of Japan?", "Give me a Python one-liner for Fibonacci"]
    cols = st.columns(len(suggestions))
    for i, s in enumerate(suggestions):
        if cols[i].button(s, key=f"chip_{cid}_{i}", use_container_width=True):
            st.session_state.pending_query = s
            st.rerun()

# ============================================================
# CORE BACKEND CALLS
# ============================================================
def call_backend(query: str):
    t0 = time.time()
    response = requests.post(CHAT_URL, params={"query": query}, timeout=300)
    response.raise_for_status()
    answer = response.json().get("AI", "No response received.")
    return answer, time.time() - t0


def stream_placeholder(placeholder, full_text: str):
    if st.session_state.skip_animation:
        placeholder.markdown(f"""
        <div class="bubble-wrap bubble-assistant">
            <div class="bubble">{full_text}</div>
        </div>""", unsafe_allow_html=True)
        return
    words = full_text.split(" ")
    shown = ""
    for i, word in enumerate(words):
        shown += word + (" " if i < len(words) - 1 else "")
        placeholder.markdown(f"""
        <div class="bubble-wrap bubble-assistant">
            <div class="bubble">{shown}<span class="cursor">▌</span></div>
        </div>""", unsafe_allow_html=True)
        time.sleep(st.session_state.typing_speed + random.uniform(0, 0.01))
    placeholder.markdown(f"""
    <div class="bubble-wrap bubble-assistant">
        <div class="bubble">{shown}</div>
    </div>""", unsafe_allow_html=True)


def generate_assistant_reply(query: str):
    placeholder = st.empty()
    placeholder.markdown("""
    <div class="bubble-wrap bubble-assistant">
        <div class="bubble"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>
    </div>""", unsafe_allow_html=True)

    try:
        answer, elapsed = call_backend(query)
        stream_placeholder(placeholder, answer)
    except requests.exceptions.ConnectionError:
        answer, elapsed = "⚠️ Could not connect to the backend. Is FastAPI running on port 8000?", 0
        placeholder.markdown(answer)
    except requests.exceptions.Timeout:
        answer, elapsed = "⚠️ The model took too long to respond. Try again or check Ollama.", 0
        placeholder.markdown(answer)
    except requests.exceptions.RequestException as e:
        answer, elapsed = f"⚠️ Error calling backend: {e}", 0
        placeholder.markdown(answer)

    messages.append({
        "role": "assistant", "content": answer,
        "time": datetime.now().strftime("%H:%M"), "response_time": elapsed,
        "pinned": False, "seen": True
    })
    if any(k in query.lower() for k in ["thank you", "thanks", "awesome", "great job"]):
        st.balloons()


def process_new_query(query: str):
    now = datetime.now().strftime("%H:%M")
    messages.append({"role": "user", "content": query, "time": now, "pinned": False})
    if st.session_state.chats[cid]["title"] in ("New Chat", "AI Assistant") and len(messages) == 1:
        st.session_state.chats[cid]["title"] = (query[:28] + "…") if len(query) > 28 else query
    generate_assistant_reply(query)


def regenerate(assistant_idx: int):
    user_query = messages[assistant_idx - 1]["content"]
    del st.session_state.chats[cid]["messages"][assistant_idx:]
    generate_assistant_reply(user_query)


def edit_and_resend(user_idx: int, new_text: str):
    messages[user_idx]["content"] = new_text
    del st.session_state.chats[cid]["messages"][user_idx + 1:]
    generate_assistant_reply(new_text)

# ============================================================
# RENDER CHAT HISTORY
# ============================================================
def matches_search(text):
    return st.session_state.search_term.lower() in text.lower() if st.session_state.search_term else True

if messages:
    st.markdown(f'<div class="date-chip">{datetime.now().strftime("%A, %B %d")}</div>', unsafe_allow_html=True)

for i, msg in enumerate(messages):
    dim_class = "" if matches_search(msg["content"]) else " dimmed"
    pin_flag = "📌 " if msg.get("pinned") else ""

    edit_key = f"editing_{cid}_{i}"
    if msg["role"] == "user" and st.session_state.get(edit_key):
        new_val = st.text_area("Edit message", value=msg["content"], key=f"edit_area_{cid}_{i}")
        ce1, ce2 = st.columns([0.18, 0.82])
        if ce1.button("✅ Save & resend", key=f"save_{cid}_{i}"):
            st.session_state[edit_key] = False
            edit_and_resend(i, new_val)
            st.rerun()
        if ce2.button("✖️ Cancel", key=f"cancel_{cid}_{i}"):
            st.session_state[edit_key] = False
            st.rerun()
        continue

    if msg["role"] == "user":
        ticks = '<span class="tick">✓✓</span>' if msg.get("time") else ""
        st.markdown(f"""
        <div class="bubble-wrap bubble-user">
            <div class="bubble{dim_class}">{pin_flag}{msg['content']}
                <span class="msg-meta">{msg['time']} {ticks}</span>
                <div style="clear:both;"></div>
            </div>
        </div>""", unsafe_allow_html=True)
        b1, b2, b3 = st.columns([0.06, 0.06, 0.88])
        if b1.button("✏️", key=f"edit_btn_{cid}_{i}", help="Edit & resend"):
            st.session_state[edit_key] = True
            st.rerun()
        if b2.button("📌", key=f"pin_u_{cid}_{i}", help="Pin message"):
            messages[i]["pinned"] = not messages[i].get("pinned", False)
            st.rerun()
    else:
        st.markdown(f"""
        <div class="bubble-wrap bubble-assistant">
            <div class="bubble{dim_class}">{pin_flag}{msg['content']}
                <span class="msg-meta">{msg['time']}</span>
                <div style="clear:both;"></div>
            </div>
        </div>""", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns([0.05, 0.05, 0.05, 0.05, 0.8])
        if c1.button("👍", key=f"up_{cid}_{i}"):
            messages[i]["reaction"] = "up"
            st.toast("Thanks for the feedback!", icon="👍")
        if c2.button("👎", key=f"down_{cid}_{i}"):
            messages[i]["reaction"] = "down"
            st.toast("Noted — I'll aim better.", icon="👎")
        if c3.button("🔄", key=f"regen_{cid}_{i}", help="Regenerate"):
            regenerate(i)
            st.rerun()
        if c4.button("📌", key=f"pin_a_{cid}_{i}", help="Pin message"):
            messages[i]["pinned"] = not messages[i].get("pinned", False)
            st.rerun()
        if "response_time" in msg:
            c5.caption(f"⏱ {msg['response_time']:.1f}s")

# ============================================================
# INPUT HANDLING
# ============================================================
typed_query = st.chat_input("Type a message")
final_query = typed_query or st.session_state.pending_query
st.session_state.pending_query = None

if final_query:
    process_new_query(final_query)
    st.rerun()

if messages:
    total_words = sum(len(m["content"].split()) for m in messages)
    st.caption(f"💬 {len(messages)} messages · ~{total_words} words")

# ============================================================
# SIDEBAR — WhatsApp-style dark chat list
# ============================================================
with st.sidebar:
    st.markdown('<div class="chat-list-header">💬 Chats</div>', unsafe_allow_html=True)

    if st.button("➕ New Chat", use_container_width=True):
        new_chat()
        st.rerun()

    for chat_id, chat in list(st.session_state.chats.items()):
        last_msg = chat["messages"][-1]["content"][:34] + "…" if chat["messages"] else "No messages yet"
        c1, c2 = st.columns([0.82, 0.18])
        label = f"🟢 **{chat['title']}**\n\n{last_msg}" if chat_id == cid else f"🤖 **{chat['title']}**\n\n{last_msg}"
        if c1.button(label, key=f"switch_{chat_id}", use_container_width=True):
            st.session_state.current_chat = chat_id
            st.rerun()
        if len(st.session_state.chats) > 1 and c2.button("🗑️", key=f"del_{chat_id}"):
            del st.session_state.chats[chat_id]
            if st.session_state.current_chat == chat_id:
                st.session_state.current_chat = next(iter(st.session_state.chats))
            st.rerun()

    st.divider()
    st.subheader("⚙️ Chat settings")
    st.session_state.skip_animation = st.checkbox("⚡ Instant replies (skip typing animation)",
                                                   value=st.session_state.skip_animation)
    if not st.session_state.skip_animation:
        st.session_state.typing_speed = st.slider("Typing speed", 0.0, 0.08, st.session_state.typing_speed, 0.005)

    st.divider()
    st.subheader("📌 Pinned messages")
    pinned = [m for m in messages if m.get("pinned")]
    if pinned:
        for p in pinned:
            st.caption(f"**{p['role']}:** {p['content'][:60]}{'…' if len(p['content'])>60 else ''}")
    else:
        st.caption("No pinned messages yet.")

    st.divider()
    st.subheader("📊 Stats")
    all_msgs = [m for c in st.session_state.chats.values() for m in c["messages"]]
    assistant_msgs = [m for m in all_msgs if m["role"] == "assistant" and m.get("response_time")]
    avg_time = sum(m["response_time"] for m in assistant_msgs) / len(assistant_msgs) if assistant_msgs else 0
    s1, s2 = st.columns(2)
    s1.metric("Chats", len(st.session_state.chats))
    s2.metric("Avg response", f"{avg_time:.1f}s")

    st.divider()
    if messages:
        md_transcript = "\n\n".join(f"**{m['role'].capitalize()}** ({m['time']}): {m['content']}" for m in messages)
        st.download_button("⬇️ Export (.md)", md_transcript, file_name=f"{st.session_state.chats[cid]['title']}.md", use_container_width=True)
        st.download_button("⬇️ Export (.json)", json.dumps(messages, indent=2), file_name=f"{st.session_state.chats[cid]['title']}.json", use_container_width=True)

    uploaded = st.file_uploader("⬆️ Import chat (.json)", type="json")
    if uploaded is not None:
        try:
            imported = json.load(uploaded)
            new_id = new_chat(title="Imported Chat")
            st.session_state.chats[new_id]["messages"] = imported
            st.rerun()
        except Exception:
            st.error("Couldn't parse that file — expected a JSON export from this app.")

    if st.button("🗑️ Clear this chat", use_container_width=True):
        st.session_state.chats[cid]["messages"] = []
        st.rerun()

    st.divider()
    st.caption(f"Backend: `{API_BASE}`")
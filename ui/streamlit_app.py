# ==================================================
# MyGenius AI  |  Financial Intelligence Copilot
# Built by Abhinav Nautiyal
# ==================================================

import streamlit as st
import requests
import uuid
import time

st.set_page_config(
    page_title="MyGenius AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session State ─────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quick_query" not in st.session_state:
    st.session_state.quick_query = None

# ── Animated canvas background injected via components trick ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background: #F0F4FF !important;
    font-family: 'Inter', sans-serif;
    color: #1E293B;
    position: relative;
}

/* ── Kill Streamlit's black top toolbar ── */
header[data-testid="stHeader"] {
    background: rgba(240,244,255,0.85) !important;
    backdrop-filter: blur(16px) !important;
    border-bottom: 1px solid rgba(99,102,241,0.10) !important;
}
header[data-testid="stHeader"] * { color: #1E293B !important; }

/* Hamburger / deploy button icons */
[data-testid="stToolbar"] { background: transparent !important; }
button[kind="header"] { color: #6366F1 !important; }

/* ── Kill black bottom chat bar ── */
[data-testid="stBottom"] {
    background: rgba(240,244,255,0.88) !important;
    backdrop-filter: blur(20px) !important;
    border-top: 1px solid rgba(99,102,241,0.10) !important;
}
[data-testid="stBottom"] > div {
    background: transparent !important;
}

/* ── Animated aurora canvas behind everything ── */
#aurora-canvas {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    z-index: 0;
    pointer-events: none;
}

/* Push Streamlit content above canvas */
.stApp > * { position: relative; z-index: 1; }
section[data-testid="stSidebar"] { z-index: 10 !important; }
header[data-testid="stHeader"]   { z-index: 11 !important; }
[data-testid="stBottom"]         { z-index: 11 !important; }

.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1300px; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #EEF2FF; }
::-webkit-scrollbar-thumb { background: #C7D2FE; border-radius: 99px; }

/* ═══════════════════════════════
   SIDEBAR
═══════════════════════════════ */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.75) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(99,102,241,0.12) !important;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1.8rem 1.2rem !important;
}

.sb-brand {
    display: flex; align-items: center; gap: 11px;
    padding: 14px 16px;
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(168,85,247,0.06));
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 14px; margin-bottom: 28px;
}
.sb-brand .b-icon { font-size: 24px; }
.sb-brand .b-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 15px; font-weight: 800;
    background: linear-gradient(90deg, #6366F1, #A855F7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.sb-brand .b-sub { font-size: 10px; color: #94A3B8; letter-spacing: 0.06em; margin-top: 2px; }

.sb-label {
    font-size: 10px; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; color: #CBD5E1;
    margin: 22px 0 10px 2px;
}

.agent-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 13px;
    background: rgba(255,255,255,0.6);
    border: 1px solid rgba(99,102,241,0.1);
    border-radius: 11px; margin-bottom: 7px;
    font-size: 13px; color: #475569;
    transition: border-color 0.2s, background 0.2s;
}
.agent-row:hover {
    background: rgba(99,102,241,0.05);
    border-color: rgba(99,102,241,0.25);
}
.agent-row .a-left { display: flex; align-items: center; gap: 9px; }
.agent-row .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #22C55E; box-shadow: 0 0 6px #22C55E99;
    animation: blink 2.4s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

.sess-badge {
    padding: 9px 13px;
    background: rgba(255,255,255,0.5);
    border: 1px solid rgba(99,102,241,0.1);
    border-radius: 10px; font-size: 11px;
    color: #94A3B8; font-family: monospace; margin-top: 6px;
}

/* ── Text inputs in sidebar ── */
.stTextInput input {
    background: rgba(255,255,255,0.7) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 10px !important;
    color: #1E293B !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}
.stTextInput input:focus {
    border-color: rgba(99,102,241,0.45) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.08) !important;
}
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.5) !important;
    border: 1px dashed rgba(99,102,241,0.2) !important;
    border-radius: 12px !important;
}

/* ═══════════════════════════════
   HERO
═══════════════════════════════ */
.hero {
    position: relative; overflow: hidden;
    padding: 60px 48px;
    border-radius: 24px;
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(99,102,241,0.15);
    text-align: center;
    margin-bottom: 24px;
    box-shadow: 0 8px 40px rgba(99,102,241,0.08);
}
.hero-glow-l {
    position: absolute; top: -40px; left: -60px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(99,102,241,0.18), transparent 70%);
    pointer-events: none;
}
.hero-glow-r {
    position: absolute; bottom: -40px; right: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(168,85,247,0.14), transparent 70%);
    pointer-events: none;
}
.hero-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 15px; border-radius: 99px;
    border: 1px solid rgba(99,102,241,0.25);
    background: rgba(99,102,241,0.07);
    font-size: 11px; font-weight: 600; letter-spacing: 0.07em;
    color: #6366F1; margin-bottom: 20px;
}
.hero-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: clamp(46px, 5.5vw, 74px);
    font-weight: 800; line-height: 1.05;
    background: linear-gradient(135deg, #6366F1 0%, #A855F7 50%, #6366F1 100%);
    background-size: 200% auto;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: shine 5s linear infinite;
    margin-bottom: 12px;
}
@keyframes shine { to { background-position: 200% center; } }
.hero-sub {
    font-size: 17px; font-weight: 400;
    color: #64748B; margin-bottom: 28px;
}
.hero-chips { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
.hero-chip {
    padding: 6px 14px; border-radius: 8px;
    background: rgba(99,102,241,0.06);
    border: 1px solid rgba(99,102,241,0.15);
    font-size: 12px; color: #6366F1; font-weight: 500;
}

/* ═══════════════════════════════
   KPI CARDS
═══════════════════════════════ */
.kpi {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(99,102,241,0.12);
    border-radius: 18px; padding: 22px 20px;
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    position: relative; overflow: hidden;
}
.kpi:hover {
    transform: translateY(-4px);
    border-color: rgba(99,102,241,0.3);
    box-shadow: 0 12px 32px rgba(99,102,241,0.12);
}
.kpi::after {
    content:''; position: absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, #6366F1, #A855F7);
    opacity: 0; transition: opacity 0.2s;
}
.kpi:hover::after { opacity: 1; }
.kpi-ico { font-size: 26px; margin-bottom: 10px; }
.kpi-lbl {
    font-size: 10px; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #94A3B8; margin-bottom: 5px;
}
.kpi-val {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 28px; font-weight: 800; color: #1E293B; line-height: 1;
}
.kpi-note { font-size: 11px; color: #22C55E; margin-top: 6px; font-weight: 500; }

/* ═══════════════════════════════
   SECTION HEADING
═══════════════════════════════ */
.sh {
    display: flex; align-items: center; gap: 10px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 15px; font-weight: 700; color: #1E293B;
    margin: 28px 0 16px;
}
.sh .sh-line {
    flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(99,102,241,0.2), transparent);
}

/* ═══════════════════════════════
   ARCHITECTURE NODES
═══════════════════════════════ */
.an {
    text-align: center; padding: 14px 10px;
    border-radius: 12px; font-size: 13px; font-weight: 600;
    line-height: 1.4; transition: transform 0.2s, box-shadow 0.2s;
}
.an:hover { transform: translateY(-2px); }
.an-user {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.25);
    color: #6366F1;
    box-shadow: 0 2px 12px rgba(99,102,241,0.08);
}
.an-router {
    background: rgba(168,85,247,0.08);
    border: 1px solid rgba(168,85,247,0.28);
    color: #A855F7;
    box-shadow: 0 2px 12px rgba(168,85,247,0.08);
}
.an-agent {
    background: rgba(255,255,255,0.7);
    border: 1px solid rgba(99,102,241,0.15);
    color: #475569;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}
.an-llm {
    background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(168,85,247,0.08));
    border: 1px solid rgba(99,102,241,0.25);
    color: #1E293B; font-weight: 700;
    box-shadow: 0 4px 20px rgba(99,102,241,0.1);
}
.an-arrow {
    display: flex; justify-content: center; align-items: center;
    font-size: 18px; color: #C7D2FE; padding: 5px 0;
}
.an-label {
    font-size: 10px; letter-spacing: 0.09em; text-transform: uppercase;
    color: #94A3B8; text-align: center; margin-top: 5px;
}

/* ═══════════════════════════════
   QUICK ACTIONS
═══════════════════════════════ */
.stButton > button {
    width: 100% !important;
    background: rgba(255,255,255,0.65) !important;
    backdrop-filter: blur(12px) !important;
    color: #475569 !important;
    border: 1px solid rgba(99,102,241,0.15) !important;
    border-radius: 12px !important;
    padding: 13px 15px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important; font-weight: 500 !important;
    height: auto !important; text-align: left !important;
    transition: all 0.18s !important;
}
.stButton > button:hover {
    background: rgba(99,102,241,0.07) !important;
    border-color: rgba(99,102,241,0.35) !important;
    color: #6366F1 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.12) !important;
}

/* ═══════════════════════════════
   CHAT
═══════════════════════════════ */
.stChatMessage { background: transparent !important; }
[data-testid="stChatMessageContent"] {
    background: rgba(255,255,255,0.7) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(99,102,241,0.12) !important;
    border-radius: 14px !important;
    padding: 14px 17px !important;
    font-size: 14px !important; line-height: 1.75 !important;
    color: #1E293B !important;
    box-shadow: 0 2px 10px rgba(99,102,241,0.05) !important;
}
[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.7) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(12px) !important;
}
[data-testid="stChatInput"] textarea {
    color: #1E293B !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}

/* ═══════════════════════════════
   ALERTS
═══════════════════════════════ */
.stAlert {
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}

/* ═══════════════════════════════
   FOOTER
═══════════════════════════════ */
.stack { display: flex; flex-wrap: wrap; gap: 7px; justify-content: center; margin-top: 12px; }
.stack-b {
    padding: 4px 11px; border-radius: 6px;
    background: rgba(99,102,241,0.06);
    border: 1px solid rgba(99,102,241,0.15);
    font-size: 11px; font-weight: 500; color: #6366F1;
}
.ft {
    text-align: center; padding: 36px 20px 16px;
    border-top: 1px solid rgba(99,102,241,0.1);
    margin-top: 3rem;
}
.ft-brand {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 18px; font-weight: 800;
    background: linear-gradient(90deg, #6366F1, #A855F7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.ft-sub { font-size: 12px; color: #94A3B8; }
.ft-credit { font-size: 11px; color: #CBD5E1; margin-top: 14px; }

hr { border: none !important; border-top: 1px solid rgba(99,102,241,0.1) !important; }
</style>

<!-- ── Floating orbs aurora animation ── -->
<canvas id="aurora-canvas"></canvas>
<script>
(function(){
  const canvas = document.getElementById('aurora-canvas');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize(){
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  // Orbs
  const orbs = [
    { x:0.15, y:0.20, r:340, hue:245, speed:0.00018, phase:0.0  },
    { x:0.75, y:0.15, r:280, hue:270, speed:0.00022, phase:1.8  },
    { x:0.50, y:0.65, r:300, hue:220, speed:0.00015, phase:3.3  },
    { x:0.85, y:0.70, r:240, hue:255, speed:0.00025, phase:5.1  },
    { x:0.10, y:0.80, r:200, hue:280, speed:0.00020, phase:2.5  },
  ];

  // Floating particles
  const particles = Array.from({length: 55}, () => ({
    x: Math.random(),
    y: Math.random(),
    size: Math.random() * 2.5 + 0.5,
    speed: Math.random() * 0.00008 + 0.00003,
    phase: Math.random() * Math.PI * 2,
    opacity: Math.random() * 0.35 + 0.08,
    hue: 230 + Math.random() * 60,
  }));

  let t = 0;
  function draw(){
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background base
    ctx.fillStyle = '#F0F4FF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Orbs
    orbs.forEach(o => {
      const cx = (o.x + 0.06 * Math.sin(t * o.speed * 1000 + o.phase)) * canvas.width;
      const cy = (o.y + 0.05 * Math.cos(t * o.speed * 800  + o.phase)) * canvas.height;
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, o.r);
      grad.addColorStop(0,   `hsla(${o.hue},85%,70%,0.22)`);
      grad.addColorStop(0.4, `hsla(${o.hue},75%,65%,0.10)`);
      grad.addColorStop(1,   `hsla(${o.hue},70%,60%,0.00)`);
      ctx.beginPath();
      ctx.arc(cx, cy, o.r, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();
      o.phase += o.speed;
    });

    // Floating sparkles
    particles.forEach(p => {
      const px = (p.x + 0.04 * Math.sin(t * p.speed * 1200 + p.phase)) * canvas.width;
      const py = (p.y + 0.03 * Math.cos(t * p.speed * 900  + p.phase)) * canvas.height;
      const pulse = p.opacity * (0.6 + 0.4 * Math.sin(t * p.speed * 2000 + p.phase));
      ctx.beginPath();
      ctx.arc(px, py, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${p.hue},80%,60%,${pulse})`;
      ctx.fill();
    });

    t += 16;
    requestAnimationFrame(draw);
  }
  draw();
})();
</script>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="b-icon">🚀</div>
        <div>
            <div class="b-title">MyGenius AI</div>
            <div class="b-sub">FINANCIAL COPILOT v2.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-label">API Configuration</div>', unsafe_allow_html=True)
    api_key = st.text_input(
        "Gemini API Key", type="password",
        placeholder="Enter Gemini API key…",
        label_visibility="collapsed"
    )
    st.caption("🔒 Stored in session only")

    st.markdown('<div class="sb-label">Document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
    if uploaded_file:
        st.success(f"📄 {uploaded_file.name} — ready for RAG")

    st.markdown('<div class="sb-label">Agent Status</div>', unsafe_allow_html=True)
    agents = [
        ("🤖", "Chatbot Agent"),
        ("📈", "Finance Agent"),
        ("🗄️", "SQL Agent"),
        ("📚", "RAG Agent"),
        ("📝", "Summarizer"),
    ]
    for icon, name in agents:
        st.markdown(f"""
        <div class="agent-row">
            <div class="a-left"><span>{icon}</span><span>{name}</span></div>
            <span class="dot"></span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sb-label">Session</div>', unsafe_allow_html=True)
    sid = st.session_state.session_id[:8]
    st.markdown(f'<div class="sess-badge">ID: {sid}…</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-glow-l"></div>
  <div class="hero-glow-r"></div>
  <div class="hero-pill">✦ &nbsp;Powered by Gemini 2.5 Flash</div>
  <div class="hero-title">MyGenius AI</div>
  <div class="hero-sub">Your Financial Intelligence Copilot</div>
  <div class="hero-chips">
    <span class="hero-chip">💬 Chat</span>
    <span class="hero-chip">📈 Finance</span>
    <span class="hero-chip">🗄️ SQL</span>
    <span class="hero-chip">📚 RAG</span>
    <span class="hero-chip">⚡ Multi-Agent</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# KPI CARDS
# ═══════════════════════════════════════════════════
k1, k2, k3, k4 = st.columns(4)
kpi_data = [
    (k1, "🤖", "Active Agents", "5",      "● All online"),
    (k2, "⚡", "AI Model",      "Gemini",  "↑ 2.5 Flash"),
    (k3, "🧭", "Router",        "AI",      "↑ Intent-aware"),
    (k4, "📂", "Documents",     "Ready",   "● FAISS indexed"),
]
for col, ico, lbl, val, note in kpi_data:
    with col:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-ico">{ico}</div>
          <div class="kpi-lbl">{lbl}</div>
          <div class="kpi-val">{val}</div>
          <div class="kpi-note">{note}</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# ARCHITECTURE
# ═══════════════════════════════════════════════════
st.markdown('<div class="sh">🧠 Multi-Agent Architecture <div class="sh-line"></div></div>', unsafe_allow_html=True)

_, mid, _ = st.columns([2, 3, 2])
with mid:
    st.markdown('<div class="an an-user">👤 &nbsp; User Query</div>', unsafe_allow_html=True)

_, mid, _ = st.columns([2, 3, 2])
with mid:
    st.markdown('<div class="an-arrow">↓</div>', unsafe_allow_html=True)

_, mid, _ = st.columns([2, 3, 2])
with mid:
    st.markdown('<div class="an an-router">🧭 &nbsp; Router Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="an-label">selects the right specialist</div>', unsafe_allow_html=True)

_, mid, _ = st.columns([2, 3, 2])
with mid:
    st.markdown('<div class="an-arrow">↓</div>', unsafe_allow_html=True)

a1, a2, a3, a4 = st.columns(4)
for col, ico, lbl in [(a1,"📈","Finance Agent"),(a2,"🗄️","SQL Agent"),(a3,"📚","RAG Agent"),(a4,"📝","Summarizer")]:
    with col:
        st.markdown(f'<div class="an an-agent">{ico}<br>{lbl}</div>', unsafe_allow_html=True)

_, mid, _ = st.columns([2, 3, 2])
with mid:
    st.markdown('<div class="an-arrow">↓</div>', unsafe_allow_html=True)

_, mid, _ = st.columns([2, 3, 2])
with mid:
    st.markdown('<div class="an an-llm">⚡ &nbsp; Gemini 2.5 Flash</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# QUICK ACTIONS
# ═══════════════════════════════════════════════════
st.markdown('<div class="sh">⚡ Quick Actions <div class="sh-line"></div></div>', unsafe_allow_html=True)

quick_actions = [
    ("📈  Explain EMI",           "Explain EMI"),
    ("📊  SIP vs FD",             "Compare SIP vs FD"),
    ("📄  Summarize Report",      "Summarize annual report"),
    ("🗄️  Show All Customers",    "Show all customers"),
    ("💰  Balance Sheet",         "Analyze balance sheet"),
    ("📉  Risk Analysis",         "Perform risk analysis"),
]

r1 = st.columns(3)
r2 = st.columns(3)
rows = [r1, r1, r1, r2, r2, r2]
for i, (label, payload) in enumerate(quick_actions):
    with rows[i][i % 3]:
        if st.button(label, key=f"qa_{i}"):
            st.session_state.quick_query = payload

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# CHAT WORKSPACE
# ═══════════════════════════════════════════════════
st.markdown('<div class="sh">💬 Chat Workspace <div class="sh-line"></div></div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

active_query = st.session_state.pop("quick_query", None)
user_input   = st.chat_input("Ask MyGenius AI anything…")
query        = user_input or active_query

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        status = st.empty()
        for icon, txt in [("🔍","Analyzing intent…"),("🧭","Routing to agent…"),("⚡","Generating response…")]:
            status.info(f"{icon} {txt}")
            time.sleep(0.6)
        try:
            resp   = requests.post(
                "http://127.0.0.1:8000/ask",
                data={"query": query, "session_id": st.session_state.session_id},
                timeout=300
            )
            answer = resp.json().get("response", "No response returned.")
        except Exception as e:
            answer = f"❌ Backend Error: {e}"
        status.empty()
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": str(answer)})

# ═══════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════
st.markdown("""
<div class="ft">
  <div class="ft-brand">🚀 MyGenius AI</div>
  <div class="ft-sub">Financial Intelligence Copilot</div>
  <div class="stack">
    <span class="stack-b">Gemini 2.5 Flash</span>
    <span class="stack-b">LangChain</span>
    <span class="stack-b">LangGraph</span>
    <span class="stack-b">FAISS</span>
    <span class="stack-b">FastAPI</span>
    <span class="stack-b">Streamlit</span>
  </div>
  <div class="ft-credit">Built by Abhinav Nautiyal</div>
</div>
""", unsafe_allow_html=True)
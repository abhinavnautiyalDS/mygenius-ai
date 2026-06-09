# ==================================================
# MyGenius AI  |  Financial Intelligence Copilot
# ==================================================
import os

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
)

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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&family=Sora:wght@700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body { background: #EEF0FF !important; }

.stApp {
    background: #EEF0FF !important;
    font-family: 'DM Sans', sans-serif;
    color: #18181B;
}

/* Aurora Canvas */
#aurora-canvas {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 0;
    pointer-events: none;
    width: 100vw; height: 100vh;
}

.stApp > * { position: relative; z-index: 1; }
section[data-testid="stSidebar"]  { z-index: 15 !important; }
header[data-testid="stHeader"]    { z-index: 14 !important; }
[data-testid="stBottom"]          { z-index: 14 !important; }

.block-container { padding: 1.5rem 2.5rem 3rem !important; max-width: 1400px; }

/* ══════════════════════════════════════
   SIDEBAR — strong contrast
══════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: #1E1B4B !important;
    backdrop-filter: none !important;
    border-right: 2px solid #3730A3 !important;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1.25rem 0.875rem !important;
}

/* sidebar logo */
.sb-logo {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 14px;
    background: #312E81;
    border: 1.5px solid #4F46E5;
    border-radius: 12px;
    margin-bottom: 20px;
}
.sb-logo .text {
    font-family: 'Sora', sans-serif;
    font-size: 14px; font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.3px;
}
.sb-logo .sub {
    font-size: 9px; color: #A5B4FC;
    letter-spacing: 0.08em; margin-top: 2px;
    font-family: 'DM Mono', monospace;
}

/* sidebar section label */
.sb-section {
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #A5B4FC;
    margin: 20px 0 8px 2px;
    display: flex; align-items: center; gap: 6px;
}
.sb-section::after {
    content: '';
    flex: 1; height: 1px;
    background: #3730A3;
}

/* sidebar inputs */
.stTextInput input {
    background: #312E81 !important;
    border: 1.5px solid #4F46E5 !important;
    border-radius: 9px !important;
    color: #E0E7FF !important;
    font-size: 13px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input::placeholder { color: #818CF8 !important; }
.stTextInput input:focus {
    border-color: #818CF8 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.25) !important;
}

/* sidebar caption */
section[data-testid="stSidebar"] .stCaption {
    color: #818CF8 !important;
    font-size: 11px !important;
}

/* file uploader */
[data-testid="stFileUploader"] {
    background: #312E81 !important;
    border: 2px dashed #4F46E5 !important;
    border-radius: 10px !important;
    padding: 10px !important;
}
[data-testid="stFileUploader"] section { background: transparent !important; }
[data-testid="stFileUploader"] * { color: #C7D2FE !important; }

/* agent pills */
.agent-pill {
    display: flex; align-items: center; justify-content: space-between;
    padding: 9px 12px;
    background: #312E81;
    border: 1.5px solid #4338CA;
    border-radius: 9px; margin-bottom: 6px;
    font-size: 13px; font-weight: 500;
    color: #E0E7FF;
    transition: all 0.18s;
}
.agent-pill:hover {
    background: #3730A3;
    border-color: #818CF8;
}
.agent-pill .lft { display: flex; align-items: center; gap: 8px; }
.agent-pill .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #34D399;
    box-shadow: 0 0 6px #34D39999;
    animation: blink 2.4s ease-in-out infinite;
    flex-shrink: 0;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.35} }

.sess-id {
    padding: 8px 12px;
    background: #312E81;
    border: 1.5px solid #4338CA;
    border-radius: 9px;
    font-size: 11px; color: #A5B4FC;
    font-family: 'DM Mono', monospace;
    margin-top: 4px;
}

/* ══════════════════════════════════════
   HEADER / BOTTOM BAR
══════════════════════════════════════ */
header[data-testid="stHeader"] {
    background: rgba(238,240,255,0.92) !important;
    backdrop-filter: blur(16px) !important;
    border-bottom: 1.5px solid #C7D2FE !important;
}
[data-testid="stToolbar"] { background: transparent !important; }

[data-testid="stBottom"] {
    background: rgba(238,240,255,0.96) !important;
    backdrop-filter: blur(20px) !important;
    border-top: 1.5px solid #C7D2FE !important;
}

/* ══════════════════════════════════════
   HERO
══════════════════════════════════════ */
.hero {
    position: relative; overflow: hidden;
    padding: 52px 44px;
    border-radius: 20px;
    background: linear-gradient(145deg, #FFFFFF 0%, #EEF2FF 100%);
    border: 2px solid #C7D2FE;
    text-align: center;
    margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(79,70,229,0.10), inset 0 1px 0 rgba(255,255,255,0.8);
}
.hero-glow1 {
    position: absolute; top: -60px; left: -80px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(99,102,241,0.18), transparent 70%);
    pointer-events: none;
}
.hero-glow2 {
    position: absolute; bottom: -60px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(168,85,247,0.14), transparent 70%);
    pointer-events: none;
}
.hero-tag {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 14px; border-radius: 99px;
    border: 1.5px solid #818CF8;
    background: #EEF2FF;
    font-size: 11px; font-weight: 700;
    color: #4338CA;
    margin-bottom: 16px;
    letter-spacing: 0.02em;
}
.hero-title {
    font-family: 'Sora', sans-serif;
    font-size: 68px; font-weight: 800; line-height: 1.05;
    background: linear-gradient(135deg, #4338CA 0%, #7C3AED 55%, #4338CA 100%);
    background-size: 200% auto;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: shimmer 5s linear infinite;
    margin-bottom: 10px;
}
@keyframes shimmer { to { background-position: 200% center; } }
.hero-sub {
    font-size: 17px; font-weight: 500;
    color: #3730A3;
    margin-bottom: 24px;
}
.hero-chips { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
.hero-chip {
    padding: 7px 15px; border-radius: 8px;
    background: #EEF2FF;
    border: 1.5px solid #818CF8;
    font-size: 12px; font-weight: 600;
    color: #3730A3;
}

/* ══════════════════════════════════════
   KPI CARDS — strong borders, high contrast
══════════════════════════════════════ */
.kpi {
    background: #FFFFFF;
    border: 2px solid #C7D2FE;
    border-radius: 16px; padding: 20px;
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    position: relative; overflow: hidden;
    box-shadow: 0 2px 10px rgba(79,70,229,0.08);
}
.kpi:hover {
    transform: translateY(-3px);
    border-color: #6366F1;
    box-shadow: 0 8px 24px rgba(79,70,229,0.15);
}
.kpi::before {
    content:''; position: absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg, #4F46E5, #7C3AED);
    border-radius: 2px 2px 0 0;
}
.kpi-icon { font-size: 22px; margin-bottom: 10px; }
/* FIX: label is now dark and clearly visible */
.kpi-label {
    font-size: 11px; font-weight: 700; letter-spacing: 0.10em;
    text-transform: uppercase;
    color: #4338CA;
    margin-bottom: 6px;
}
/* FIX: value is bold and high contrast */
.kpi-value {
    font-family: 'Sora', sans-serif;
    font-size: 26px; font-weight: 800;
    color: #1E1B4B;
}
.kpi-detail { font-size: 12px; color: #059669; margin-top: 6px; font-weight: 600; }

/* ══════════════════════════════════════
   SECTION HEADERS — visible & strong
══════════════════════════════════════ */
.section-head {
    display: flex; align-items: center; gap: 10px;
    font-family: 'Sora', sans-serif;
    font-size: 15px; font-weight: 700;
    color: #1E1B4B;
    margin: 32px 0 16px;
}
.section-head .section-line {
    flex: 1; height: 2px;
    background: linear-gradient(90deg, #818CF8, transparent);
    border-radius: 2px;
}

/* ══════════════════════════════════════
   ARCHITECTURE — visible nodes
══════════════════════════════════════ */
.arch-wrapper {
    display: flex; flex-direction: column;
    align-items: center; gap: 0;
}
.arch-node {
    text-align: center; padding: 12px 10px;
    border-radius: 11px; font-size: 13px; font-weight: 600;
    transition: transform 0.2s; width: 100%;
}
.arch-node:hover { transform: translateY(-2px); }
.arch-user {
    background: #EEF2FF;
    border: 2px solid #6366F1;
    color: #3730A3;
}
.arch-router {
    background: #F5F3FF;
    border: 2px solid #7C3AED;
    color: #5B21B6;
}
.arch-agent {
    background: #FFFFFF;
    border: 2px solid #C7D2FE;
    color: #1E1B4B;
    font-weight: 600;
}
.arch-llm {
    background: linear-gradient(135deg, #EEF2FF, #F5F3FF);
    border: 2px solid #6366F1;
    color: #1E1B4B; font-weight: 700;
    width: 100%;
}
.arch-arrow { text-align: center; color: #6366F1; padding: 4px 0; font-size: 20px; font-weight: 700; width: 100%; }
.arch-label { font-size: 11px; text-transform: uppercase; font-weight: 600; color: #6366F1; text-align: center; width: 100%; margin-bottom: 2px; letter-spacing: 0.06em; }

/* ══════════════════════════════════════
   QUICK ACTION BUTTONS
══════════════════════════════════════ */
.stButton > button {
    width: 100% !important;
    background: #FFFFFF !important;
    color: #1E1B4B !important;
    border: 2px solid #C7D2FE !important;
    border-radius: 11px !important;
    padding: 12px 14px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    height: auto !important;
    text-align: left !important;
    transition: all 0.18s !important;
    box-shadow: 0 1px 4px rgba(79,70,229,0.07) !important;
}
.stButton > button:hover {
    background: #EEF2FF !important;
    border-color: #6366F1 !important;
    color: #3730A3 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(79,70,229,0.13) !important;
}

/* ══════════════════════════════════════
   CHAT
══════════════════════════════════════ */
.stChatMessage { background: transparent !important; }
[data-testid="stChatMessageContent"] {
    background: #FFFFFF !important;
    border: 2px solid #C7D2FE !important;
    border-radius: 13px !important;
    padding: 14px 16px !important;
    font-size: 14px !important; line-height: 1.75 !important;
    color: #18181B !important;
    box-shadow: 0 1px 6px rgba(79,70,229,0.07) !important;
}
/* FIX: chat input matches light theme */
[data-testid="stChatInput"] {
    background: #FFFFFF !important;
    border: 2px solid #818CF8 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 12px rgba(79,70,229,0.10) !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div,
[data-testid="stChatInput"] p {
    color: #18181B !important;
    -webkit-text-fill-color: #18181B !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    background: #FFFFFF !important;
    caret-color: #4F46E5 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #818CF8 !important;
    -webkit-text-fill-color: #818CF8 !important;
    font-weight: 500 !important;
    opacity: 1 !important;
}

/* ══════════════════════════════════════
   ALERTS
══════════════════════════════════════ */
.stAlert {
    border-radius: 11px !important;
    border: 1.5px solid #C7D2FE !important;
    background: #FFFFFF !important;
    font-size: 13px !important;
    color: #1E1B4B !important;
}

/* ══════════════════════════════════════
   FOOTER
══════════════════════════════════════ */
.stack { display: flex; flex-wrap: wrap; gap: 7px; justify-content: center; margin-top: 14px; }
.stack-badge {
    display: inline-block;
    padding: 5px 13px; border-radius: 7px;
    background: #EEF2FF;
    border: 1.5px solid #818CF8;
    font-size: 11px; font-weight: 700;
    color: #3730A3;
    letter-spacing: 0.02em;
}
.footer {
    text-align: center; padding: 32px 20px 14px;
    border-top: 2px solid #C7D2FE;
    margin-top: 2.5rem;
}
.footer-title {
    font-family: 'Sora', sans-serif;
    font-size: 18px; font-weight: 800;
    background: linear-gradient(90deg, #4338CA, #7C3AED);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.footer-sub { font-size: 13px; color: #4338CA; font-weight: 500; }
.footer-credit { font-size: 11px; color: #818CF8; margin-top: 10px; font-weight: 500; }

hr { border: none !important; border-top: 2px solid #C7D2FE !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #818CF8; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #4F46E5; }
</style>

<canvas id="aurora-canvas"></canvas>
<script>
(function(){
  const canvas = document.getElementById('aurora-canvas');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  function resize(){ canvas.width=window.innerWidth; canvas.height=window.innerHeight; }
  resize(); window.addEventListener('resize', resize);
  const orbs=[
    {x:0.15,y:0.20,r:340,hue:245,speed:0.00018,phase:0.0},
    {x:0.75,y:0.15,r:280,hue:260,speed:0.00022,phase:1.8},
    {x:0.50,y:0.65,r:300,hue:230,speed:0.00015,phase:3.3},
    {x:0.85,y:0.70,r:240,hue:250,speed:0.00025,phase:5.1},
    {x:0.10,y:0.80,r:200,hue:270,speed:0.00020,phase:2.5},
  ];
  const particles=Array.from({length:40},()=>({
    x:Math.random(),y:Math.random(),
    size:Math.random()*2+0.5,
    speed:Math.random()*0.00007+0.00003,
    phase:Math.random()*Math.PI*2,
    opacity:Math.random()*0.25+0.06,
    hue:230+Math.random()*50,
  }));
  let t=0;
  function draw(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle='#EEF0FF'; ctx.fillRect(0,0,canvas.width,canvas.height);
    orbs.forEach(o=>{
      const cx=(o.x+0.06*Math.sin(t*o.speed*1000+o.phase))*canvas.width;
      const cy=(o.y+0.05*Math.cos(t*o.speed*800+o.phase))*canvas.height;
      const g=ctx.createRadialGradient(cx,cy,0,cx,cy,o.r);
      g.addColorStop(0,`hsla(${o.hue},80%,72%,0.18)`);
      g.addColorStop(0.4,`hsla(${o.hue},70%,68%,0.08)`);
      g.addColorStop(1,`hsla(${o.hue},65%,65%,0.00)`);
      ctx.beginPath(); ctx.arc(cx,cy,o.r,0,Math.PI*2);
      ctx.fillStyle=g; ctx.fill();
    });
    particles.forEach(p=>{
      const px=(p.x+0.04*Math.sin(t*p.speed*1200+p.phase))*canvas.width;
      const py=(p.y+0.03*Math.cos(t*p.speed*900+p.phase))*canvas.height;
      const pulse=p.opacity*(0.6+0.4*Math.sin(t*p.speed*2000+p.phase));
      ctx.beginPath(); ctx.arc(px,py,p.size,0,Math.PI*2);
      ctx.fillStyle=`hsla(${p.hue},75%,55%,${pulse})`; ctx.fill();
    });
    t+=16; requestAnimationFrame(draw);
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
    <div class="sb-logo">
        <div style="font-size:22px">🚀</div>
        <div>
            <div class="text">MyGenius AI</div>
            <div class="sub">FINANCIAL COPILOT v2.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section">⚙️ API Config</div>', unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Enter your API key…", label_visibility="collapsed")
    st.caption("🔒 Session-only storage")

    st.markdown('<div class="sb-section">📄 Documents</div>', unsafe_allow_html=True)

    #uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
    #if uploaded_file:
        #st.success(f"✓ {uploaded_file.name} loaded")

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )
    if uploaded_file:

        if "uploaded_doc" not in st.session_state:

            try:

                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "application/pdf"
                    )
                }

                data = {
                    "session_id":
                    st.session_state.session_id
                }

                response = requests.post(
                    f"{API_URL}/upload-rag",
                    files=files,
                    data=data,
                    timeout=300
                )

                result = response.json()

                if result.get("success"):

                    st.session_state.uploaded_doc = True

                    st.success(
                        f"✓ {uploaded_file.name} indexed successfully"
                    )

                else:

                    st.error(
                        result.get(
                            "error",
                            "Upload failed"
                        )
                    )

            except Exception as e:

                st.error(
                    f"Upload Error: {e}"
                )

    

    st.markdown('<div class="sb-section">🟢 Agent Status</div>', unsafe_allow_html=True)
    agents = [("🤖", "Chatbot Agent"), ("📈", "Finance Agent"), ("🗄️", "SQL Agent"), ("📚", "RAG Agent"), ("📝", "Summarizer")]
    for icon, name in agents:
        st.markdown(f'<div class="agent-pill"><div class="lft"><span>{icon}</span><span>{name}</span></div><span class="dot"></span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">🔑 Session</div>', unsafe_allow_html=True)
    sid = st.session_state.session_id[:8]
    st.markdown(f'<div class="sess-id">{sid}…</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-glow1"></div>
  <div class="hero-glow2"></div>
  <div class="hero-tag">✦ Powered by Gemini 2.5 Flash</div>
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
k1, k2, k3, k4 = st.columns(4, gap="small")
kpis = [
    (k1, "🤖", "Active Agents", "5",      "● All online"),
    (k2, "⚡", "AI Model",      "Gemini",  "↑ 2.5 Flash"),
    (k3, "🧭", "Router",        "AI",      "↑ Intent-aware"),
    (k4, "📂", "Documents",     "Ready",   "● FAISS indexed"),
]
for col, ico, lbl, val, detail in kpis:
    with col:
        st.markdown(f'<div class="kpi"><div class="kpi-icon">{ico}</div><div class="kpi-label">{lbl}</div><div class="kpi-value">{val}</div><div class="kpi-detail">{detail}</div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# ARCHITECTURE
# ═══════════════════════════════════════════════════
st.markdown('<div class="section-head">🧠 Multi-Agent Architecture<div class="section-line"></div></div>', unsafe_allow_html=True)

_, arch_mid, _ = st.columns([1.5, 2, 1.5])
with arch_mid:
    st.markdown("""
    <div class="arch-wrapper">
        <div class="arch-node arch-user">👤 &nbsp; User Query</div>
        <div class="arch-arrow">↓</div>
        <div class="arch-node arch-router">🧭 &nbsp; Router Agent</div>
        <div class="arch-label" style="margin-top:4px">Route to specialist</div>
        <div class="arch-arrow">↓</div>
    </div>
    """, unsafe_allow_html=True)

a1, a2, a3, a4 = st.columns(4, gap="small")
for col, ico, lbl in [(a1,"📈","Finance"),(a2,"🗄️","SQL"),(a3,"📚","RAG"),(a4,"📝","Summarize")]:
    with col:
        st.markdown(f'<div class="arch-node arch-agent">{ico}<br><span style="font-size:11px;color:#4338CA;font-weight:700">{lbl}</span></div>', unsafe_allow_html=True)

_, arch_mid2, _ = st.columns([1.5, 2, 1.5])
with arch_mid2:
    st.markdown("""
    <div class="arch-wrapper">
        <div class="arch-arrow">↓</div>
        <div class="arch-node arch-llm">⚡ &nbsp; Gemini 2.5 Flash</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# QUICK ACTIONS
# ═══════════════════════════════════════════════════
st.markdown('<div class="section-head">⚡ Quick Actions<div class="section-line"></div></div>', unsafe_allow_html=True)

qa_buttons = [
    ("📈 Explain EMI",       "Explain EMI"),
    ("📊 SIP vs FD",         "Compare SIP vs FD"),
    ("📄 Summarize Report",  "Summarize annual report"),
    ("🗄️ Show Customers",   "Show all customers"),
    ("💰 Balance Sheet",     "Analyze balance sheet"),
    ("📉 Risk Analysis",     "Perform risk analysis"),
]

r1 = st.columns(3, gap="small")
r2 = st.columns(3, gap="small")
for i, (label, payload) in enumerate(qa_buttons):
    row = r1 if i < 3 else r2
    with row[i % 3]:
        if st.button(label, key=f"qa_{i}"):
            st.session_state.quick_query = payload

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# CHAT
# ═══════════════════════════════════════════════════
st.markdown('<div class="section-head">💬 Chat Workspace<div class="section-line"></div></div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

active_query = st.session_state.get("quick_query", None)
if active_query:
    del st.session_state["quick_query"]

user_input = st.chat_input("Ask MyGenius AI anything…")
query = user_input or active_query

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        status = st.empty()
        for icon, txt in [("🔍", "Analyzing intent…"), ("🧭", "Routing to agent…"), ("⚡", "Generating…")]:
            status.info(f"{icon} {txt}")
            time.sleep(0.5)
        try:
            
            resp = requests.post(
            f"{API_URL}/ask",
            data={
                "query": query,
                "session_id": st.session_state.session_id
            },
            timeout=300
        )

            st.write("Status:", resp.status_code)
            st.write("Raw Response:", resp.text)

            result = resp.json()

            answer = result.get(
                "response",
                "No response returned."
            )

            answer = resp.json().get("response", "No response.")
        except Exception as e:
            answer = f"❌ Error: {e}"
        finally:
            status.empty()
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": str(answer)})

# ═══════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════
st.markdown("""
<div class="footer">
  <div class="footer-title">🚀 MyGenius AI</div>
  <div class="footer-sub">Financial Intelligence Copilot</div>
  <div class="stack">
    <span class="stack-badge">Gemini 2.5 Flash</span>
    <span class="stack-badge">LangChain</span>
    <span class="stack-badge">LangGraph</span>
    <span class="stack-badge">FAISS</span>
    <span class="stack-badge">FastAPI</span>
    <span class="stack-badge">Streamlit</span>
  </div>
  <div class="footer-credit">Built by Abhinav Nautiyal</div>
</div>
""", unsafe_allow_html=True)

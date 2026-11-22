import { useState } from "react";
import { Activity, ArrowUp, BookOpen, Bot, CircleHelp, Command, FileText, Globe2, Layers3, Menu, Plus, Settings2, ShieldCheck, Sparkles, Wrench } from "lucide-react";

type Message = { role: "user" | "assistant"; text: string };
const starters = [
  [Layers3, "Analyze a codebase", "Understand architecture, risks and next steps"],
  [FileText, "Research documents", "Find answers across your knowledge sources"],
  [Globe2, "Research a topic", "Collect and synthesize information from the web"],
  [Wrench, "Build a workflow", "Coordinate tools and multi-step tasks"],
] as const;

export default function App() {
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [web, setWeb] = useState(false);
  const [busy, setBusy] = useState(false);
  const [sidebar, setSidebar] = useState(true);

  async function send(value = draft) {
    const text = value.trim();
    if (!text || busy) return;
    setMessages(old => [...old, { role: "user", text }]);
    setDraft(""); setBusy(true);
    try {
      const api = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
      const res = await fetch(api + "/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: text, web_search: web }) });
      if (!res.ok) throw new Error("API error");
      const data = await res.json();
      setMessages(old => [...old, { role: "assistant", text: data.answer }]);
    } catch {
      setMessages(old => [...old, { role: "assistant", text: "I couldn't reach the AgenticDesk API. Start the FastAPI backend and verify the API URL." }]);
    } finally { setBusy(false); }
  }

  return <div className="shell">
    <aside className={sidebar ? "sidebar" : "sidebar hidden"}>
      <div className="brand"><span className="brand-icon"><Command size={19}/></span>Agentic<span>Desk</span></div>
      <button className="new-chat" onClick={() => setMessages([])}><Plus size={16}/> New workspace</button>
      <div className="section-label">WORKSPACE</div>
      <button className="nav active"><Bot size={17}/> Assistant</button>
      <button className="nav"><BookOpen size={17}/> Knowledge bases</button>
      <button className="nav"><Wrench size={17}/> MCP integrations <small>SOON</small></button>
      <div className="section-label recent">RECENT</div><p className="empty-recent">Your conversations will appear here.</p>
      <div className="bottom"><div className="privacy"><ShieldCheck size={18}/><div><b>Private by design</b><small>Tools run with permission</small></div></div><button className="nav"><Settings2 size={17}/> Settings</button><div className="account"><i>A</i><div><b>Workspace</b><small>Personal account</small></div></div></div>
    </aside>
    <main className="main">
      <header><button className="menu" onClick={() => setSidebar(!sidebar)}><Menu size={18}/></button><div className="breadcrumb">Workspace <span>/</span> <b>Assistant</b></div><div className="ready"><i/> Workspace ready <CircleHelp size={17}/></div></header>
      <section className="content">
        {!messages.length ? <div className="welcome"><div className="spark"><Sparkles size={24}/></div><label>YOUR AI WORKSPACE</label><h1>Good work starts<br/><em>with a clear question.</em></h1><p>Bring your knowledge, tools and ideas together.<br/>Turn complex tasks into clear outcomes.</p><div className="starter-grid">{starters.map(([Icon,title,desc]) => <button className="starter" key={title} onClick={() => send(title + ": ")}><i><Icon size={18}/></i><span><b>{title}</b><small>{desc}</small></span></button>)}</div></div> :
        <div className="messages">{messages.map((m,i) => <article className="message" key={i}><div className="message-icon">{m.role === "assistant" ? <Sparkles size={16}/> : "A"}</div><div><b>{m.role === "assistant" ? "AgenticDesk" : "You"}</b><p>{m.text}</p></div></article>)}{busy && <div className="loading"><Activity size={15}/> AgenticDesk is thinking…</div>}</div>}
      </section>
      <div className="composer-wrap"><div className="composer"><textarea rows={2} value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}}} placeholder="Ask anything, or describe a task to get started…"/><div className="composer-bottom"><div className="tools"><button className={web?"chosen":""} onClick={()=>setWeb(!web)}><Globe2 size={14}/> Web search</button><button><BookOpen size={14}/> Knowledge</button><button><Wrench size={14}/> Tools</button></div><button className="send" disabled={!draft.trim()||busy} onClick={()=>send()}><ArrowUp size={18}/></button></div></div><div className="footnote"><ShieldCheck size={12}/> Review actions before execution. AgenticDesk can make mistakes.</div></div>
    </main>
  </div>;
}
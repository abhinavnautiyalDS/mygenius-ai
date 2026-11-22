import { useCallback, useEffect, useState } from "react";
import { Activity, ArrowUp, BookOpen, Bot, Check, ChevronDown, CircleHelp, Command, FileText, Globe2, Layers3, Menu, Plus, RefreshCw, Search, Settings2, ShieldCheck, Sparkles, Upload, Workflow, Wrench, X, PanelLeftClose } from "lucide-react";

const API = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
type View = "assistant" | "knowledge" | "mcp" | "approvals" | "workflows" | "settings";
type Message = { role: "user" | "assistant"; content: string };
type Conversation = { id: string; title: string; updated_at: string };
type DocumentItem = { id: string; filename: string; characters: number; chunks: number; created_at: string };
type ServerItem = { id: string; name: string; url: string; enabled: number };
type Approval = { id: string; server_name: string; tool_name: string; arguments: string; status: string; created_at: string };
type WorkflowItem = { id: string; task: string; status: string; result: string; created_at: string };

const nav: { id: View; label: string; icon: typeof Bot }[] = [
  { id: "assistant", label: "Assistant", icon: Bot },
  { id: "knowledge", label: "Knowledge base", icon: BookOpen },
  { id: "mcp", label: "MCP integrations", icon: Wrench },
  { id: "approvals", label: "Approvals", icon: ShieldCheck },
  { id: "workflows", label: "Workflows", icon: Workflow },
  { id: "settings", label: "Settings", icon: Settings2 },
];

async function api(path: string, init: RequestInit = {}) {
  const response = await fetch(API + path, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || body.message || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}
const json = (value: unknown) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) });

export default function App() {
  const [view, setView] = useState<View>("assistant");
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [servers, setServers] = useState<ServerItem[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [capabilities, setCapabilities] = useState<Record<string, any>>({});
  const [serverName, setServerName] = useState("");
  const [serverUrl, setServerUrl] = useState("");
  const [web, setWeb] = useState(false);
  const [useKnowledge, setUseKnowledge] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebar, setSidebar] = useState(true);
  const [search, setSearch] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [c, d, s, a, w, caps] = await Promise.all([
        api("/conversations"), api("/knowledge/documents"), api("/mcp/servers"),
        api("/approvals"), api("/workflows"), api("/capabilities")
      ]);
      setConversations(c.items || []); setDocuments(d.items || []); setServers(s.items || []);
      setApprovals(a.items || []); setWorkflows(w.items || []); setCapabilities(caps);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not load workspace"); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  async function openConversation(id: string) {
    try {
      const data = await api("/conversations/" + id);
      setConversationId(id);
      setMessages(data.messages.map((m: any) => ({ role: m.role, content: m.content })));
      setView("assistant");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not open conversation"); }
  }
  function newChat() { setConversationId(null); setMessages([]); setDraft(""); setView("assistant"); setError(""); }

  async function send(value = draft) {
    const content = value.trim();
    if (!content || busy) return;
    setMessages(old => [...old, { role: "user", content }]); setDraft(""); setBusy(true); setError("");
    try {
      const data = await api("/chat", { ...json({ message: content, conversation_id: conversationId, web_search: web, use_knowledge: useKnowledge }) });
      setConversationId(data.conversation_id);
      setMessages(old => [...old, { role: "assistant", content: data.answer }]);
      await refresh();
    } catch (e) {
      setMessages(old => [...old, { role: "assistant", content: "I couldn't complete the request. Check the model connection and workspace settings." }]);
      setError(e instanceof Error ? e.message : "Chat request failed");
    } finally { setBusy(false); }
  }

  async function uploadFile(file?: File) {
    if (!file) return;
    const body = new FormData(); body.append("file", file); setBusy(true); setError("");
    try { await api("/knowledge/documents", { method: "POST", body }); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Upload failed"); }
    finally { setBusy(false); }
  }
  async function addServer() {
    if (!serverName.trim() || !serverUrl.trim()) return;
    try { await api("/mcp/servers", json({ name: serverName, url: serverUrl })); setServerName(""); setServerUrl(""); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not add MCP server"); }
  }
  async function approvalAction(id: string, action: "approve" | "reject") {
    try { await api(`/approvals/${id}/${action}`, json({})); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Approval action failed"); }
  }
  async function runWorkflow() {
    const task = draft.trim(); if (!task || busy) return;
    setBusy(true); setError("");
    try { await api("/workflows", json({ message: task })); setDraft(""); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Workflow failed"); }
    finally { setBusy(false); }
  }

  const title = nav.find(n => n.id === view)?.label || "Assistant";
  const filteredConversations = conversations.filter(c => c.title.toLowerCase().includes(search.toLowerCase()));

  return <div className="shell">
    <aside className={sidebar ? "sidebar" : "sidebar hidden"}>
      <div className="brand"><span className="brand-icon"><Command size={19}/></span>Agentic<span>Desk</span></div>
      <button className="new-chat" onClick={newChat}><Plus size={16}/> New chat</button>
      <div className="section-label">WORKSPACE</div>
      {nav.map(item => { const Icon = item.icon; return <button key={item.id} className={view === item.id ? "nav active" : "nav"} onClick={() => { setView(item.id); setError(""); }}><Icon size={17}/>{item.label}{item.id === "approvals" && approvals.filter(a => a.status === "pending").length > 0 && <small>{approvals.filter(a => a.status === "pending").length}</small>}</button>; })}
      <div className="section-label recent">CONVERSATIONS</div>
      <div className="conversation-search"><Search size={13}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search history"/></div>
      <div className="recent-list">{filteredConversations.slice(0, 30).map(c => <button key={c.id} className={conversationId === c.id ? "recent-item selected" : "recent-item"} onClick={() => void openConversation(c.id)}>{c.title || "New conversation"}</button>)}{!filteredConversations.length && <p className="empty-recent">No conversations yet.</p>}</div>
      <div className="bottom"><div className="privacy"><ShieldCheck size={18}/><div><b>Approval-first tools</b><small>External actions need permission</small></div></div><div className="account"><i>A</i><div><b>AgenticDesk</b><small>Self-hosted workspace</small></div></div></div>
    </aside>
    <main className="main">
      <header><button className="menu" onClick={() => setSidebar(!sidebar)}><Menu size={18}/></button><div className="breadcrumb">Workspace <span>/</span> <b>{title}</b></div><div className="ready"><i/> API connected <button className="icon-button" onClick={() => void refresh()} title="Refresh"><RefreshCw size={15}/></button></div></header>
      {error && <div className="error-banner"><span>{error}</span><button onClick={() => setError("")}><X size={15}/></button></div>}
      {view === "assistant" && <><section className="content chat-content">
        {!messages.length ? <div className="welcome"><div className="spark"><Sparkles size={24}/></div><label>YOUR AI WORKSPACE</label><h1>Think clearly.<br/><em>Build with agents.</em></h1><p>Bring your knowledge, tools and ideas together.<br/>Turn complex tasks into clear outcomes.</p><div className="starter-grid">
          {[[Layers3,"Analyze a codebase","Understand architecture and next steps"],[FileText,"Research documents","Find answers from your knowledge base"],[Globe2,"Research the web","Synthesize information with sources"],[Workflow,"Plan a workflow","Turn a goal into an executable task"]] .map(([Icon, name, desc]: any) => <button className="starter" key={name} onClick={() => send(name + ": ")}><i><Icon size={18}/></i><span><b>{name}</b><small>{desc}</small></span></button>)}
        </div></div> : <div className="messages">{messages.map((m,i) => <article className="message" key={i}><div className="message-icon">{m.role === "assistant" ? <Sparkles size={16}/> : "A"}</div><div><b>{m.role === "assistant" ? "AgenticDesk" : "You"}</b><p>{m.content}</p></div></article>)}{busy && <div className="loading"><Activity size={15}/> AgenticDesk is thinking…</div>}</div>}
      </section><div className="composer-wrap"><div className="composer"><textarea rows={2} value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();void send();}}} placeholder="Ask anything, or describe a task…"/><div className="composer-bottom"><div className="tools"><button className={web?"chosen":""} onClick={()=>setWeb(!web)}><Globe2 size={14}/> Web research</button><button className={useKnowledge?"chosen":""} onClick={()=>setUseKnowledge(!useKnowledge)}><BookOpen size={14}/> Knowledge</button></div><button className="send" disabled={!draft.trim()||busy} onClick={()=>void send()}><ArrowUp size={18}/></button></div></div><div className="footnote"><ShieldCheck size={12}/> Review tool actions before execution. AI can make mistakes.</div></div></>}

      {view === "knowledge" && <section className="page-panel"><div className="page-heading"><div><span>YOUR DATA</span><h1>Knowledge base</h1><p>Upload documents to index them with your self-hosted Granite embedding service.</p></div><label className="primary-action"><Upload size={16}/> Add documents<input type="file" accept=".pdf,.docx,.txt,.md" multiple={false} onChange={e=>void uploadFile(e.target.files?.[0])}/></label></div><div className="stat-row"><div><b>{documents.length}</b><small>Indexed documents</small></div><div><b>{documents.reduce((n,d)=>n+(d.chunks||0),0)}</b><small>Text chunks</small></div><div><b>384</b><small>Embedding dimensions</small></div></div><div className="data-card"><div className="card-title"><h3>Indexed sources</h3><button className="icon-button" onClick={()=>void refresh()}><RefreshCw size={15}/></button></div>{documents.map(d=><div className="data-row" key={d.id}><FileText size={19}/><div className="grow"><b>{d.filename}</b><small>{d.chunks} chunks · {d.characters.toLocaleString()} characters</small></div><button className="danger-link" onClick={async()=>{try{await api("/knowledge/documents/"+d.id,{method:"DELETE"});await refresh();}catch(e){setError(String(e));}}}>Remove</button></div>)}{!documents.length&&<div className="empty-state"><BookOpen size={25}/><b>No documents yet</b><p>Upload PDF, DOCX, TXT or Markdown files to start retrieval.</p></div>}</div></section>}

      {view === "mcp" && <section className="page-panel"><div className="page-heading"><div><span>TOOL CONNECTIVITY</span><h1>MCP integrations</h1><p>Connect Model Context Protocol servers over HTTP. Tool calls always enter the approval queue.</p></div></div><div className="data-card form-card"><h3>Connect an MCP server</h3><div className="form-grid"><label>Server name<input value={serverName} onChange={e=>setServerName(e.target.value)} placeholder="e.g. Internal tools"/></label><label>Streamable HTTP endpoint<input value={serverUrl} onChange={e=>setServerUrl(e.target.value)} placeholder="https://your-server.example/mcp"/></label></div><button className="primary-action" onClick={()=>void addServer()} disabled={!serverName.trim()||!serverUrl.trim()}><Plus size={15}/> Add server</button></div><div className="data-card"><div className="card-title"><h3>Connected servers</h3><span>{servers.length} configured</span></div>{servers.map(s=><div className="data-row" key={s.id}><span className="server-icon"><Wrench size={17}/></span><div className="grow"><b>{s.name}</b><small>{s.url}</small></div><button className="secondary-action" onClick={async()=>{try{const r=await api(`/mcp/servers/${s.id}/tools`);alert((r.tools||[]).map((t:any)=>t.name+" — "+(t.description||"")).join("\n")||"No tools found");}catch(e){setError(e instanceof Error?e.message:"Tool discovery failed");}}}>Discover tools</button></div>)}{!servers.length&&<div className="empty-state"><Wrench size={25}/><b>No MCP servers connected</b><p>Add a Streamable HTTP MCP endpoint to discover its tools.</p></div>}</div></section>}

      {view === "approvals" && <section className="page-panel"><div className="page-heading"><div><span>HUMAN IN THE LOOP</span><h1>Tool approvals</h1><p>Review each proposed external tool call before it executes.</p></div></div><div className="data-card">{approvals.map(a=><div className="approval-row" key={a.id}><div className="grow"><div className="approval-meta"><b>{a.tool_name}</b><span className={"status "+a.status}>{a.status}</span></div><small>{a.server_name} · {new Date(a.created_at).toLocaleString()}</small><pre>{a.arguments}</pre></div>{a.status==="pending"&&<div className="approval-actions"><button className="approve" onClick={()=>void approvalAction(a.id,"approve")}><Check size={14}/> Approve & run</button><button className="reject" onClick={()=>void approvalAction(a.id,"reject")}><X size={14}/> Reject</button></div>}</div>)}{!approvals.length&&<div className="empty-state"><ShieldCheck size={25}/><b>No approval requests</b><p>Requested MCP tool calls will appear here for review.</p></div>}</div></section>}

      {view === "workflows" && <section className="page-panel"><div className="page-heading"><div><span>ORCHESTRATION</span><h1>Workflows</h1><p>Run a task through the configured reasoning model and review execution history.</p></div></div><div className="data-card form-card"><h3>Start a workflow</h3><textarea className="workflow-input" rows={3} value={draft} onChange={e=>setDraft(e.target.value)} placeholder="Describe the outcome you want to achieve…"/><button className="primary-action" onClick={()=>void runWorkflow()} disabled={!draft.trim()||busy}><Workflow size={15}/> {busy?"Running…":"Run workflow"}</button></div><div className="data-card"><div className="card-title"><h3>Execution history</h3><span>{workflows.length} runs</span></div>{workflows.map(w=><div className="data-row" key={w.id}><Workflow size={18}/><div className="grow"><b>{w.task}</b><small>{w.status} · {new Date(w.created_at).toLocaleString()}</small></div><details><summary>Result</summary><pre>{w.result}</pre></details></div>)}{!workflows.length&&<div className="empty-state"><Workflow size={25}/><b>No workflow runs yet</b><p>Your task executions will be listed here.</p></div>}</div></section>}

      {view === "settings" && <section className="page-panel"><div className="page-heading"><div><span>WORKSPACE CONFIGURATION</span><h1>Settings & capabilities</h1><p>Service configuration status reported by the backend.</p></div></div><div className="data-card">{Object.entries(capabilities).map(([key,value])=><div className="capability-row" key={key}><div className="grow"><b>{key.replace("_"," ")}</b><small>{value.provider || value.embedding_model || value.status}</small></div><span className={"status "+(value.status==="configured"||value.status==="available"||value.status==="http-json-rpc"?"approved":"pending")}>{value.status}</span></div>)}</div><div className="notice"><ShieldCheck size={18}/><p>Secrets belong in the backend environment, never in frontend code or Git. MCP servers should be trusted endpoints; review tool arguments before approval.</p></div></section>}
    </main>
  </div>;
}

# AgenticDesk
**Multilingual Agentic AI Workspace**

A clean, isolated next-generation workspace alongside the original MyGenius AI application. The original root-level code and `main` branch are preserved.

## Architecture
- React + TypeScript + Vite single-chat workspace.
- FastAPI backend with explicit health and capability endpoints.
- Existing self-hosted Qwen-compatible reasoning endpoint.
- Existing IBM Granite Embedding 97M Multilingual R2 service (384 dimensions).
- MCP integration boundary with approval-first tool execution.
- Retrieval/vector-store and LangGraph orchestration will be connected behind service interfaces.

## Existing model services
Configure `QWEN_BASE_URL` and `GRANITE_EMBEDDING_URL` to point to the existing private services. Do not deploy duplicate model servers. Keep endpoints private or behind an authenticated gateway; never expose model ports publicly or commit credentials.

## Run locally
Backend:
```bash
cd agenticdesk/backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Frontend:
```bash
cd agenticdesk/frontend
npm install
npm run dev
```

## Current status
This is the foundation commit: polished workspace shell, API health/capability endpoints and a safe placeholder chat response. Live model inference, persistent conversations, RAG ingestion, MCP lifecycle and approval-gated execution are not yet wired or claimed as working.

## Safety
- Never execute arbitrary model-generated code or shell commands.
- Allowlist MCP servers and tools; scope permissions.
- Require approval before consequential external actions.
- Treat retrieved content and tool output as untrusted.
- Log tool identity, execution state and concise result summaries.

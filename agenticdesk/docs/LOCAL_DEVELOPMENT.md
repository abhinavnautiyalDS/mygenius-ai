# AgenticDesk local development

## Prerequisites
- Python 3.11 or 3.12
- Node.js 20+
- Access to the Qwen-compatible chat endpoint
- Access to the Granite-compatible embeddings endpoint for Knowledge Base features
- Optional Tavily API key for web research

## Backend
From `agenticdesk/backend`:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Set the values in backend/.env. Do not commit the file. If the gateway token is set, send `x-agenticdesk-token` on protected API calls.

## Frontend
From `agenticdesk/frontend`:

```bash
npm ci
cp .env.example .env.local
npm run dev
```

Set `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1` in frontend/.env.local for local development.

## Validation
Backend:

```bash
cd agenticdesk/backend
python -m py_compile app/main.py
pytest -q
```

Frontend:

```bash
cd agenticdesk/frontend
npm ci
npm run build
```

Smoke test:
- GET /api/v1/health
- GET /api/v1/capabilities
- POST /api/v1/chat with `{"message":"Reply with a short greeting","use_knowledge":false}`
- GET /api/v1/conversations and open the returned conversation ID

Knowledge upload requires the Granite endpoint. MCP registration requires a public HTTPS MCP endpoint; loopback/private/reserved IPs and HTTP endpoints are rejected. MCP tool execution is only reachable after an approval is explicitly approved.

## Operational notes
- SQLite data is created under backend/data by default; keep it on persistent storage.
- Uploaded document contents and chunk embeddings are stored in SQLite in this initial implementation. Back up the database.
- The initial vector retrieval implementation stores 384-dimensional Granite vectors alongside chunk text and performs cosine ranking in Python. For larger corpora, move to a dedicated vector index without changing the API contract.
- The chat stream endpoint currently streams completed answer text in SSE chunks after the model response completes; it is not token streaming from Qwen.
- Workflows currently execute one bounded Qwen request. They are not a multi-agent graph.
- MCP supports a constrained HTTP JSON-RPC request shape. Some MCP servers require session initialization/negotiation; verify transport compatibility before using them.

# AgenticDesk
**Multilingual Agentic AI Workspace**

AgenticDesk is a self-hosted agent workspace built alongside MyGenius AI. It combines a React/TypeScript UI, FastAPI orchestration API, a private OpenAI-compatible Qwen endpoint, and IBM Granite multilingual embeddings.

## Workspace features
- Assistant: persistent SQLite conversations, conversation history, multilingual Qwen responses, optional knowledge retrieval and web research.
- Knowledge base: PDF, DOCX, TXT and Markdown ingestion, chunking, Granite embeddings (384 dimensions), similarity retrieval and source metadata.
- MCP integrations: register HTTP JSON-RPC MCP endpoints, discover tools, queue tool calls for approval, and execute only after approval.
- Approvals: inspect proposed tool arguments and explicitly approve or reject each pending call.
- Workflows: submit a task to the reasoning model and retain an execution record.
- Capabilities: backend-reported status for model, retrieval, MCP and web search configuration.

## Implementation status

The integration branch now includes the FastAPI workspace routes, SQLite conversation memory migration, Qwen chat client, Granite document embeddings and cosine retrieval, optional Tavily research, HTTP JSON-RPC MCP discovery, approval-gated tool execution, workflow run history, Cloudflare Worker source, tests, and EC2 deployment templates. Read [the A-to-Z plan](docs/AGENTICDESK_A_TO_Z_MASTER_PLAN.md), [implementation checklist](docs/IMPLEMENTATION_CHECKLIST.md), [local development guide](docs/LOCAL_DEVELOPMENT.md), and [EC2 connect-only runbook](deploy/EC2_CONNECT.md).

**Important limitations:** the MCP adapter is a narrow HTTP JSON-RPC implementation and may need session negotiation for some servers; SSRF protection should be reinforced with network egress controls and DNS pinning; SQLite cosine search is for a small demo corpus; workflow runs are single Qwen tasks; the stream route chunks the completed response rather than streaming model tokens; shared gateway auth is not per-user authentication. Run the test suite and complete the release checklist before production deployment.

## Architecture
- Frontend: React 18, TypeScript, Vite, lucide-react.
- API: FastAPI, Pydantic Settings, HTTPX.
- Reasoning: existing private Qwen-compatible endpoint (/v1/chat/completions).
- Embeddings: existing IBM Granite Embedding 97M Multilingual R2 endpoint (/v1/embeddings, 384 dimensions).
- Storage: SQLite for conversations, messages, documents, MCP server registrations, approvals and workflow runs.
- Web search: Tavily API (optional).
- MCP: HTTP JSON-RPC transport adapter with approval-gated tool execution.

## Environment
Copy .env.example to .env and configure:

| Variable | Purpose |
|---|---|
| QWEN_BASE_URL | Private OpenAI-compatible model base URL |
| QWEN_MODEL | Model identifier served by Qwen endpoint |
| QWEN_API_KEY | Private model API key |
| GRANITE_EMBEDDING_URL | Private Granite embedding service |
| GRANITE_API_KEY | Embedding API key, if enabled |
| AGENTICDESK_GATEWAY_TOKEN | Shared secret injected by the Cloudflare Worker |
| TAVILY_API_KEY | Optional key to enable web research |
| DATABASE_PATH | Persistent SQLite database path |
| UPLOAD_DIR | Upload storage directory |
| CORS_ORIGINS | Comma-separated trusted browser origins |

Never commit .env, API keys, model credentials, or uploaded private documents. Keep model ports private. The Cloudflare Worker should inject x-agenticdesk-token; never expose that token in frontend code.

## Run locally
Backend:

    cd agenticdesk/backend
    python -m venv .venv
    # Windows: .venv\\Scripts\\activate
    # Linux/macOS: source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    uvicorn app.main:app --reload --port 8000

Frontend:

    cd agenticdesk/frontend
    npm install
    # Set VITE_API_BASE_URL=http://localhost:8000/api/v1 in frontend/.env.local
    npm run dev

## API surface
- GET /api/v1/health and /api/v1/capabilities
- GET /api/v1/conversations and /api/v1/conversations/{id}
- POST /api/v1/chat and /api/v1/chat/stream
- GET/POST/DELETE /api/v1/knowledge/documents
- GET/POST /api/v1/mcp/servers and GET /api/v1/mcp/servers/{id}/tools
- POST /api/v1/mcp/servers/{id}/tools/{tool}/request
- GET /api/v1/approvals and POST /api/v1/approvals/{id}/approve or reject
- POST/GET /api/v1/workflows

## Important integration notes
1. The backend expects an OpenAI-compatible Qwen chat-completions API and an OpenAI-compatible Granite embeddings API.
2. Web research is disabled until TAVILY_API_KEY is configured.
3. Document ingestion requires the Granite endpoint to accept POST /v1/embeddings with an OpenAI-style request body.
4. MCP server registration currently targets HTTP JSON-RPC endpoints. The server must expose tools/list and tools/call at the configured URL. Verify compatibility with the server transport/session requirements before production use.
5. The workflow endpoint currently executes a single reasoning request and records its result; it is not yet a multi-agent graph or autonomous planner.
6. The stream endpoint currently emits the completed answer in SSE chunks; model tokens are not yet streamed live from the inference server.
7. Production deployment must persist the SQLite data directory and uploads across releases, enforce HTTPS, restrict MCP endpoints to trusted hosts, and add user-level authentication/authorization before exposing the workspace to multiple users.

## Safety
- Never execute arbitrary model-generated shell commands or code.
- Never expose model or embedding service ports publicly.
- Allowlist trusted MCP endpoints and tools; validate arguments.
- Require explicit approval before MCP tool execution.
- Treat retrieved documents and tool output as untrusted data.
- Keep secrets in server-side environment variables only.

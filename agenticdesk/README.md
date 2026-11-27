# AgenticDesk
**Multilingual Agentic AI Workspace**

AgenticDesk is a self-hosted agent workspace built alongside MyGenius AI. It combines a React/TypeScript UI, FastAPI orchestration API, a private OpenAI-compatible Qwen endpoint, and IBM Granite multilingual embeddings.

## Workspace features
- Assistant: persistent SQLite conversations, conversation history, multilingual Qwen responses, optional knowledge retrieval and web research.
- Knowledge base: PDF, DOCX, TXT and Markdown ingestion, chunking, Granite embeddings (384 dimensions), similarity retrieval and source metadata.
- MCP integrations: register HTTP JSON-RPC MCP endpoints, discover tools, queue tool calls for approval, and execute only after approval.
- Approvals: inspect proposed tool arguments and explicitly approve or reject each pending call.
- Workflows / CareerPilot: LangGraph-powered job-search workflow with parallel research/profile branches, dependent job matching, parallel resume/outreach/interview preparation, and per-agent status output.
- Capabilities: backend-reported status for model, retrieval, MCP and web search configuration.

## Implementation status

The integration branch now includes the FastAPI workspace routes, SQLite conversation memory migration, Qwen chat client, Granite document embeddings and cosine retrieval, optional Tavily research, HTTP JSON-RPC MCP discovery, approval-gated tool execution, workflow run history, Cloudflare Worker source, tests, and EC2 deployment templates. Read [the A-to-Z plan](docs/AGENTICDESK_A_TO_Z_MASTER_PLAN.md), [implementation checklist](docs/IMPLEMENTATION_CHECKLIST.md), [local development guide](docs/LOCAL_DEVELOPMENT.md), and [EC2 connect-only runbook](deploy/EC2_CONNECT.md).

**Important limitations:** CareerPilot is an initial execution foundation. Job discovery uses optional Tavily web search and returns unverified leads, not confirmed vacancies. Greenhouse/Lever/Ashby adapters, resume-file-to-profile extraction, Granite semantic job reranking, dedicated company research, and application submission are not connected yet. Resume/outreach/interview outputs are drafts only. The MCP adapter is a narrow HTTP JSON-RPC implementation and may need session negotiation for some servers; SSRF protection should be reinforced with network egress controls and DNS pinning; SQLite cosine search is for a small demo corpus; the stream route chunks the completed response rather than streaming model tokens; shared gateway auth is not per-user authentication. Run the test suite and complete the release checklist before production deployment.

## Architecture
- Frontend: React 18, TypeScript, Vite, lucide-react.
- API: FastAPI, Pydantic Settings, HTTPX.
- Reasoning: existing private Qwen-compatible endpoint (/v1/chat/completions).
- Embeddings: existing IBM Granite Embedding 97M Multilingual R2 endpoint (/v1/embeddings, 384 dimensions).
- Storage: SQLite for conversations, messages, documents, MCP server registrations, approvals, workflow runs and the candidate profile.
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


## CareerPilot multi-agent workflow

The Workflows view is the initial job-search product surface. Save a candidate profile (skills, target roles, locations and salary range), describe a goal, and optionally enable Web Search.

Current graph:
- Orchestrator parses the goal and merges saved candidate preferences.
- Parallel: job discovery, candidate profile loading and company research.
- Sequential dependency: resume/profile analysis -> skill-gap analysis; job discovery + skill-gap analysis + company research -> matching.
- Parallel after matching: resume optimization, recruiter outreach drafting and interview preparation.
- Finalize merges agent outputs and returns each agent's status.

The graph uses reducers for concurrent list, dictionary and artifact updates. The existing Dhir-compatible chat-completions wrapper is reused for reasoning; the existing Tavily integration is reused for opt-in web discovery. Granite remains available to the existing Knowledge Base and is not yet used for semantic job reranking.

Candidate profile API:
- GET /api/v1/career/profile
- PUT /api/v1/career/profile

Workflow API:
- POST /api/v1/workflows with JSON body `{"message":"...","web_search":true}`
- GET /api/v1/workflows

All generated resume and outreach content is draft-only. No application is submitted and no recruiter message is sent by CareerPilot. Job links from general web search are leads and require manual verification. Do not treat them as verified vacancies.

## API surface
- GET /api/v1/health and /api/v1/capabilities
- GET /api/v1/conversations and /api/v1/conversations/{id}
- POST /api/v1/chat and /api/v1/chat/stream
- GET/POST/DELETE /api/v1/knowledge/documents
- GET/POST /api/v1/mcp/servers and GET /api/v1/mcp/servers/{id}/tools
- POST /api/v1/mcp/servers/{id}/tools/{tool}/request
- GET /api/v1/approvals and POST /api/v1/approvals/{id}/approve or reject
- GET/PUT /api/v1/career/profile
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

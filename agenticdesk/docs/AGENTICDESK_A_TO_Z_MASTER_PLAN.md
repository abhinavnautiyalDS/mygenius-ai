# AgenticDesk — A-to-Z Engineering Blueprint

**Purpose:** Turn AgenticDesk into a reliable, demonstrable, portfolio-ready multilingual agent workspace, using the existing private Qwen reasoning endpoint and IBM Granite embedding endpoint. This document is the source of truth for implementation order, architecture, acceptance criteria, and deployment safety.

**Status:** Blueprint created from the GitHub `feature/agenticdesk-foundation` branch and the known EC2 deployment notes. This is a plan, not a claim that every listed capability is already implemented or production-ready.

## 1. Product definition

AgenticDesk is a self-hosted AI workspace where a user can:
1. Chat with a persistent multilingual assistant.
2. Upload documents and retrieve grounded answers from them.
3. Connect trusted MCP servers and discover tools.
4. Review and approve/reject proposed external tool calls before execution.
5. Run saved workflow tasks and inspect execution history.
6. Use optional web research with citations.
7. Keep conversation history and compact summaries for long-running chats.
8. Inspect service/model capability and health status.

### Product principles
- Local/private inference first; do not introduce paid model dependencies unless explicitly chosen.
- Qwen is the reasoning/chat model. Granite is the embedding model. They have separate responsibilities.
- No shell/code execution from model output.
- External side effects require explicit human approval.
- Retrieved documents, web pages, and tool output are untrusted input.
- Secrets remain server-side. Never place gateway/model keys in frontend code or Git.
- Build in small verified slices; retain working behavior at each phase.

## 2. Verified starting point and known gaps

### Repository facts observed on `feature/agenticdesk-foundation`
- Workspace is under `agenticdesk/`.
- Frontend: React 18, TypeScript, Vite, lucide-react.
- Backend dependencies include FastAPI, Uvicorn, Pydantic Settings, HTTPX, python-multipart, pypdf, python-docx and pytest.
- Backend settings already describe Qwen, Granite, gateway auth, optional Tavily, SQLite path and upload directory.
- SQLite schema initializer declares conversations, messages, documents, MCP servers, approvals and workflow runs.
- Qwen helper calls an OpenAI-compatible `/chat/completions` endpoint.
- Frontend UI includes Assistant, Knowledge Base, MCP Integrations, Approvals, Workflows and Settings.
- Worker documentation describes a Cloudflare gateway that injects `x-agenticdesk-token`.
- README describes the intended API surface and operational safety rules.

### Important mismatch to resolve first
The fetched `agenticdesk/backend/app/main.py` on the reviewed branch ends after the `qwen_chat()` helper. The README and frontend expect multiple API routes, but those route handlers were not present in that fetched file, and a repository code search did not locate separate routers. Treat this as a **blocking verification gap**, not proof that the features work. Before merging/deploying, inspect the complete branch tree and implement or restore the backend route handlers so every frontend API call has a tested endpoint.

### Known live EC2 state from the deployment handoff
- AgenticDesk API service: `agenticdesk.service`, Uvicorn on `127.0.0.1:8002`.
- Qwen service: `aura-qwen.service`, private endpoint `127.0.0.1:8001`.
- Granite service: `aura-ai.service`, private endpoint `127.0.0.1:8000`.
- Cloudflare Worker fronts the API; Cloudflare Pages hosts the frontend.
- The live EC2 working tree had local uncommitted changes and a local-only commit, while the remote feature branch had additional commits. **Do not pull, reset, merge, force-push, clean, or switch branches in that dirty live checkout until it has been backed up and reconciled.**
- Never restart the Qwen or Granite services as part of an AgenticDesk deployment.

## 3. Target architecture

```text
Browser (Cloudflare Pages / local Vite)
        |
        | HTTPS, allowlisted origin
        v
Cloudflare Worker API Gateway
        | injects x-agenticdesk-token (Worker secret)
        v
AgenticDesk FastAPI (127.0.0.1:8002)
        |
        +---- SQLite: conversations, messages, summaries,
        |             documents, MCP servers, approvals, workflows
        |
        +---- Qwen OpenAI-compatible API (127.0.0.1:8001)
        |       reasoning, chat, summaries, workflow planning
        |
        +---- Granite embeddings API (127.0.0.1:8000)
        |       document and query embeddings (384 dimensions)
        |
        +---- Optional Tavily API
        |       web search, only when configured and requested
        |
        +---- Trusted MCP HTTP endpoints
                discovery + approval-gated tool execution
```

### Module boundaries (target)
- `app/main.py`: application creation, middleware, lifespan and router registration only.
- `app/core/config.py`: validated settings and environment configuration.
- `app/core/security.py`: gateway authentication and trusted-origin/host checks.
- `app/db/`: SQLite connection, schema migrations and repositories.
- `app/routers/health.py`: health and capability endpoints.
- `app/routers/conversations.py`: conversation CRUD, message history and summaries.
- `app/routers/chat.py`: orchestration of context, retrieval, web search and Qwen.
- `app/routers/knowledge.py`: upload, extraction, chunking, embedding, search and delete.
- `app/routers/mcp.py`: server registration, endpoint validation and tool discovery.
- `app/routers/approvals.py`: approval queue and safe execution.
- `app/routers/workflows.py`: workflow run lifecycle and results.
- `app/services/qwen.py`: private Qwen-compatible client.
- `app/services/embeddings.py`: Granite-compatible embedding client.
- `app/services/retrieval.py`: chunking, vector search and source assembly.
- `app/services/web_search.py`: optional Tavily client.
- `app/services/mcp_client.py`: constrained MCP HTTP JSON-RPC adapter.
- `app/services/summarization.py`: summary generation and context compaction.
- `app/schemas/`: request/response Pydantic models.
- `tests/`: unit, integration, security and contract tests.

Do not perform a large rewrite merely to achieve this folder structure. Refactor incrementally after the current route/API behavior is tested.

## 4. Data model and migration policy

Use one configured SQLite database. Preserve existing data and migrate additively.

### Target tables
- `conversations`: id, title, summary, created_at, updated_at.
- `messages`: id, conversation_id, role, content, created_at; index by conversation and creation time.
- `documents`: id, filename, content or storage reference, chunks metadata, created_at, checksum, status.
- `document_chunks`: id, document_id, chunk_index, text, embedding reference/vector metadata, source metadata.
- `mcp_servers`: id, name, url, enabled, created_at, last_checked_at.
- `approvals`: id, server_id, tool_name, arguments JSON, status, result, created_at, reviewed_at.
- `workflow_runs`: id, task, status, result, created_at, updated_at.
- Optional future `audit_events`: actor, action, resource, outcome, timestamp, safe metadata.

### Migration rules
1. Back up the database before every schema migration.
2. Use additive migrations and `PRAGMA table_info` checks; do not drop/recreate tables.
3. Add `conversations.summary` safely if absent.
4. Add foreign keys and indexes only after checking existing rows and compatibility.
5. Store large uploads outside the database; store metadata and references in SQLite.
6. Keep document/chunk IDs stable so re-indexing can be retried safely.
7. Make migrations idempotent and test against both an empty DB and a copy of the existing live DB.
8. Never put the live database, uploads, or user data into Git.

## 5. API contract

The frontend and backend must agree on exact paths, methods, payloads and response shapes. Publish OpenAPI from FastAPI and add contract tests.

| Area | Required endpoints | Minimum behavior |
|---|---|---|
| Health | `GET /api/v1/health`, `GET /api/v1/capabilities` | Liveness plus configured/available state for Qwen, Granite, Tavily and MCP |
| Conversations | `GET/POST /api/v1/conversations`, `GET/DELETE /api/v1/conversations/{id}` | Create, list, load messages, delete; preserve summaries |
| Chat | `POST /api/v1/chat`, `POST /api/v1/chat/stream` | Validate input, persist user/assistant turns, Qwen response, optional RAG/web context |
| Knowledge | `GET/POST /api/v1/knowledge/documents`, `DELETE /api/v1/knowledge/documents/{id}` | Upload, extract, chunk, embed, index, list, delete |
| MCP | `GET/POST /api/v1/mcp/servers`, `GET /api/v1/mcp/servers/{id}/tools`, tool request endpoint | Register trusted server, discover tools, queue proposed calls |
| Approvals | `GET /api/v1/approvals`, `POST /api/v1/approvals/{id}/approve`, `POST /api/v1/approvals/{id}/reject` | Pending queue, idempotent review, execution only after approval |
| Workflows | `GET/POST /api/v1/workflows` | Execute one bounded task, persist status/result, expose history |

The Cloudflare Worker allowlist must match this API contract, including every parameterized route. Add tests that compare the Worker allowlist to the FastAPI route inventory. The Worker currently documents an allowlist; update it whenever endpoints change.

## 6. Feature specifications

### A. Persistent assistant and conversation memory
- Create a conversation on first message or explicit New Chat.
- Persist each user and assistant message with deterministic ordering.
- Load history when a conversation is reopened.
- Update title from the first user message; keep title generation deterministic and bounded.
- Keep a rolling summary separate from raw messages.
- Send system instructions + summary + a bounded recent-message window to Qwen.
- Trigger summary compaction by token/character budget, not a brittle fixed message count alone.
- Summary generation failure must not fail the user's chat request.
- Avoid duplicate messages on client retries; consider request IDs/idempotency keys.

### B. Qwen reasoning client
- Reuse the already-running private OpenAI-compatible endpoint.
- Configure base URL, model alias, API key and timeout via environment.
- Never expose Qwen credentials to the browser.
- Handle timeout, connection errors, non-2xx responses and malformed model payloads.
- Keep one shared HTTP client with lifecycle management when practical.
- Test request shape with a mock HTTP server.
- Verify the configured model identifier against the running service's model list before changing it.

### C. Knowledge base / RAG
1. Accept only PDF, DOCX, TXT and Markdown initially.
2. Enforce file-size, content-type and extension limits; sanitize filenames.
3. Extract text with pypdf/python-docx and safe text decoding.
4. Chunk with overlap and preserve page/source metadata.
5. Generate 384-dimensional embeddings through Granite.
6. Validate vector dimensions and finite values.
7. Persist chunk metadata and vectors/index files safely; define rebuild behavior.
8. Embed the user query with the same model/version.
9. Retrieve top-k chunks with a configurable similarity threshold.
10. Include source references in the assistant answer; do not imply unsupported claims.
11. Handle empty, scanned, malformed and oversized documents with clear errors.
12. Delete document metadata, chunks and associated vector entries consistently.

### D. MCP integrations
- Start with HTTP JSON-RPC transport only; document transport/session compatibility limits.
- Validate URLs and block loopback, link-local, private, metadata and other unsafe destinations unless explicitly allowlisted by operator configuration. Prevent DNS rebinding and redirect-based SSRF.
- Restrict server registration to authenticated administrators in any multi-user deployment.
- Set connection/read timeouts and response-size limits.
- Discover tools and validate names/schema before use.
- Treat tool descriptions, arguments and results as untrusted.
- Never execute a tool call directly from model output.
- Create a pending approval record containing exact server, tool and arguments.
- Execute only after explicit approval; reject stale, duplicate or already-reviewed approvals.
- Record outcome safely and redact secrets from logs.
- Add an allowlist of trusted MCP hosts and optionally per-tool policy.

### E. Approval workflow
- States: pending, approved, rejected, executing, succeeded, failed, expired.
- Approve/reject operations must be atomic and idempotent.
- A rejected or expired request must never execute.
- Revalidate server enabled state and tool schema immediately before execution.
- Show the exact arguments and destination to the user before approval.
- Store result/error safely with truncation and redaction.
- Add audit events for every state transition.

### F. Web research
- Optional Tavily key; feature must show disabled/unconfigured state when absent.
- Only call web search when the user explicitly enables it or a workflow policy requests it.
- Return URLs, titles and short source snippets to the model.
- Cite sources in the answer and label external content as untrusted.
- Apply timeout, result-count and response-size limits.
- Never silently fall back to web search if the user disabled it.

### G. Workflows
- First version is a bounded single reasoning request, not a claim of autonomous multi-agent orchestration.
- Persist task, status, timestamps and result.
- Enforce request timeout and output-size limits.
- Make run status observable; handle failed and interrupted runs.
- Future version may introduce LangGraph/state machine, explicit tools, retries, checkpoints and human approval nodes.
- Do not call a simple prompt-to-Qwen endpoint a multi-agent workflow.

### H. Frontend workspace
- Preserve the complete existing six-section workspace UI.
- Assistant: conversation list/search, new chat, history, summary indicator, web/RAG toggles, clear loading/error states.
- Knowledge: upload progress, file validation feedback, document list, chunk counts, delete confirmation.
- MCP: server registration, enable/disable, discovery, tool schemas and safe errors.
- Approvals: pending count, full arguments, destination, approve/reject and final status.
- Workflows: submit task, status, result and history.
- Settings: model/service status, environment capability flags and deployment diagnostics (never secrets).
- Add responsive layout, keyboard accessibility, focus states, empty states and error boundaries.
- Never render untrusted Markdown/HTML without sanitization.
- Use API types generated from or validated against OpenAPI where practical.

## 7. Security and reliability requirements

### Gateway and API
- In production, fail startup if gateway authentication is expected but token is missing.
- Protect all non-public API routes; health/capabilities should reveal no secrets or internal sensitive details.
- Constant-time token comparison where appropriate.
- Restrict CORS to exact production/local origins.
- Enforce request body, upload and response limits.
- Add rate limiting at the edge or API layer.
- Use HTTPS externally; keep backend/model ports bound to loopback or private network.
- Add user authentication/authorization before multi-user exposure. The current shared gateway token is a service-to-service control, not per-user identity.

### MCP / SSRF
- Do not allow arbitrary internet/private-network MCP URLs by default.
- Deny cloud metadata endpoints, loopback, link-local and private IP ranges unless explicitly permitted for a controlled deployment.
- Revalidate resolved IPs and redirects.
- Apply outbound network policy at the host/firewall layer too.

### Data and observability
- Keep secrets, databases, uploads, logs, caches and build outputs out of Git.
- Use structured logs with request IDs; redact authorization headers, tokens, uploaded content and tool secrets.
- Add backups with retention and a tested restore procedure.
- Use health checks that distinguish API liveness from dependency readiness.
- Set explicit timeouts and graceful shutdown.
- Avoid logging full conversation/document contents by default.

## 8. Test strategy and release gates

### Automated tests
- Unit: settings, DB repositories, migrations, chunking, summary compaction, response parsing.
- API: all route status codes, schemas, auth, invalid IDs, empty data and error cases.
- Qwen: mock success, timeout, connection failure, 401/5xx and malformed payload.
- Granite: mock embeddings, dimension mismatch, timeout and empty document.
- RAG: relevant retrieval, no-match threshold, source metadata and delete consistency.
- MCP: SSRF blocks, malformed JSON-RPC, tool discovery, pending approval, reject never executes, approve executes once.
- Workflow: success, timeout, failure and history persistence.
- Frontend: build, API contract smoke tests, key workspace flows.
- Worker: CORS, method/path allowlist, auth injection, backend outage and no-store behavior.
- Migration: empty DB and copied live DB.

### Release gates (all required)
- Backend tests pass.
- Frontend TypeScript + production build pass.
- OpenAPI route inventory matches frontend calls and Worker allowlist.
- Health and capabilities work through Worker.
- Chat round-trip works and persists after service restart.
- Conversation summary survives reload and does not lose raw history.
- RAG answer includes retrieved source metadata.
- MCP call remains pending until approval; rejection proves no execution.
- Workflow result persists.
- No secrets or data files in Git diff.
- Database backup and rollback steps verified.
- Qwen/Granite services remain healthy and untouched.

## 9. Delivery phases and order

### Phase 0 — Repository and live-state safety (first)
- Confirm Git root, branch, remotes and current dirty files.
- Preserve the existing working tree and local-only Qwen/conversation implementation.
- Make a timestamped source/database backup before any checkout or migration.
- Compare remote feature branch against the live local state.
- Use a new integration branch; never force-push or reset the live branch.

### Phase 1 — Restore a coherent backend API
- Inspect the full repository tree and route inventory.
- Implement/restore all routes expected by the frontend.
- Add a unified SQLite repository and additive migration for conversation summaries.
- Preserve the known-good Qwen request behavior and error mapping.
- Add tests for auth, chat and conversation persistence.

### Phase 2 — Stabilize assistant memory
- Integrate persistent messages and summary compaction in the unified DB.
- Add conversation list/detail/delete and title updates.
- Test multi-turn recall, restart persistence and summary failure handling.

### Phase 3 — Complete RAG
- Implement extraction, chunking, Granite embedding client and vector persistence.
- Add query retrieval, citations/source display and deletion/re-indexing.
- Verify embedding dimension and model consistency.

### Phase 4 — Secure MCP and approvals
- Implement endpoint validation, tool discovery and JSON-RPC client.
- Add approval state machine and idempotent execution.
- Add SSRF/security tests before connecting real external servers.

### Phase 5 — Workflows and web research
- Implement bounded workflow execution/history.
- Add optional Tavily research with citations and explicit opt-in.
- Keep workflow capabilities honest in UI and README.

### Phase 6 — Frontend integration
- Preserve the full workspace UI.
- Connect all views to the finalized API contract.
- Add summaries, loading/errors, upload feedback, approval detail and capability states.
- Run production build and browser smoke test.

### Phase 7 — Deployment and operations
- Back up DB/uploads and environment configuration securely.
- Deploy backend without touching Qwen/Granite services.
- Confirm local API on 127.0.0.1:8002.
- Update Cloudflare Worker BACKEND_ORIGIN only when the Quick Tunnel URL changes.
- Verify Worker auth injection and Pages frontend.
- Keep previous app version and DB backup for rollback.

### Phase 8 — Portfolio readiness
- README with architecture diagram, screenshots, features, setup and limitations.
- Demo dataset with non-sensitive sample documents.
- Short demo video showing chat memory, RAG sources, MCP approval/rejection and workflow history.
- Architecture decisions, API docs and threat model.
- Honest limitations and roadmap; no unsupported claims such as autonomous multi-agent execution if not implemented.

## 10. Definition of done

AgenticDesk is ready for portfolio demonstration when:
- A fresh clone can be configured using documented environment variables.
- Backend and frontend start using documented commands.
- Health/capabilities show Qwen and Granite connectivity.
- User can create/reopen/delete conversations and retain context across restarts.
- User can upload a supported document and receive a source-grounded answer.
- MCP tools can be discovered and cannot execute without explicit approval.
- Workflow runs are persisted and inspectable.
- Optional web research returns cited sources.
- Worker protects the API and frontend contains no secrets.
- Tests and production build pass.
- Deployment and rollback are documented and repeatable.

## 11. Non-goals for the first stable release
- Arbitrary shell/code execution.
- Unrestricted MCP endpoint access.
- Multi-user enterprise auth/RBAC unless explicitly scoped.
- Claiming a full autonomous multi-agent graph before implementing it.
- Replacing Qwen or Granite without measured evidence.
- Introducing paid API dependencies as a default path.
- Rewriting the entire frontend or backend in one risky change.

## 12. Immediate next action

Start with **Phase 0 and Phase 1**. Do not ask the operator to run exploratory commands repeatedly. Provide one consolidated, read-only state capture when required, then make a concrete integration branch and implement/test the backend contract before deploying.

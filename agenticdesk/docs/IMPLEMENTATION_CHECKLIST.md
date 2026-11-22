# AgenticDesk Implementation Checklist

Use this as the single execution tracker. Check an item only after code and evidence exist.

## Phase 0 — Safety and repository reconciliation
- [ ] Confirm repository root, current branch, remote URLs and exact commit SHAs.
- [ ] Capture `git status --short`, `git diff --stat`, staged diff and untracked inventory.
- [ ] Preserve local-only Qwen and conversation-memory changes.
- [ ] Back up the AgenticDesk source tree and SQLite database/uploads.
- [ ] Compare the live EC2 branch with `origin/feature/agenticdesk-foundation`.
- [ ] Create an integration branch from the intended remote base.
- [ ] Do not reset, clean, force-push, blind-pull or switch a dirty live checkout.

## Phase 1 — Backend API foundation
- [ ] Inventory all frontend API calls.
- [ ] Inventory all FastAPI routes and compare against README/Worker allowlist.
- [ ] Implement health and capabilities.
- [ ] Implement gateway authentication and production fail-closed behavior.
- [ ] Implement unified SQLite connection/repository layer.
- [ ] Add additive schema migration for `conversations.summary`.
- [ ] Add indexes, constraints and migration tests.
- [ ] Implement conversation create/list/detail/delete.
- [ ] Implement Qwen client with timeouts and typed error handling.
- [ ] Implement chat route with persistent messages.
- [ ] Add API tests for all implemented routes.
- [ ] Confirm OpenAPI contains the documented API surface.

## Phase 2 — Conversation memory
- [ ] Generate/update conversation title.
- [ ] Generate rolling summary using Qwen.
- [ ] Keep raw messages even after summary compaction.
- [ ] Use summary + bounded recent messages as model context.
- [ ] Make summary failure non-fatal to chat.
- [ ] Add retry/idempotency handling for chat requests.
- [ ] Verify context recall after API restart.
- [ ] Show summary/context status in frontend.

## Phase 3 — Knowledge and RAG
- [ ] Validate upload type, size and filename.
- [ ] Extract PDF/DOCX/TXT/Markdown.
- [ ] Chunk text with overlap and source metadata.
- [ ] Generate embeddings through private Granite endpoint.
- [ ] Validate 384 dimensions and finite values.
- [ ] Persist chunks/index and document metadata.
- [ ] Implement query embedding and top-k retrieval.
- [ ] Add similarity threshold and no-match behavior.
- [ ] Ground responses with source references.
- [ ] Implement document deletion and index consistency.
- [ ] Test empty, malformed, scanned and oversized files.

## Phase 4 — MCP integrations
- [ ] Define trusted-host policy.
- [ ] Block unsafe IP ranges, metadata endpoints, redirects and DNS rebinding.
- [ ] Add MCP HTTP JSON-RPC client with timeouts/size limits.
- [ ] Register, enable and disable servers.
- [ ] Discover and validate tool schemas.
- [ ] Queue tool calls as pending approvals.
- [ ] Never execute model-proposed tools directly.
- [ ] Add approve/reject state transitions.
- [ ] Make approvals atomic and idempotent.
- [ ] Revalidate server/tool immediately before execution.
- [ ] Redact secrets from results/logs.
- [ ] Prove rejection never executes a tool.
- [ ] Prove approval executes at most once.

## Phase 5 — Workflows and web research
- [ ] Implement bounded single-task workflow.
- [ ] Persist status, timestamps and result.
- [ ] Handle timeout, failure and interrupted execution.
- [ ] Add optional Tavily client.
- [ ] Require explicit web-research opt-in.
- [ ] Return source URLs/titles and cite sources.
- [ ] Clearly label current workflow as single reasoning task, not multi-agent orchestration.

## Phase 6 — Frontend
- [ ] Preserve Assistant, Knowledge, MCP, Approvals, Workflows and Settings views.
- [ ] Connect each view to the finalized API contract.
- [ ] Add conversation search/history and summary state.
- [ ] Add upload progress and validation feedback.
- [ ] Add MCP tool discovery and server status.
- [ ] Show approval arguments and destination before approval.
- [ ] Show workflow state and result.
- [ ] Show service capabilities without leaking secrets.
- [ ] Add responsive layout, accessibility and error boundaries.
- [ ] Sanitize untrusted content.
- [ ] Run TypeScript check and production build.

## Phase 7 — Gateway and deployment
- [ ] Match Cloudflare Worker allowlist to FastAPI routes.
- [ ] Verify exact allowed frontend origin and CORS headers.
- [ ] Verify Worker injects gateway token and never exposes it.
- [ ] Verify backend binds only to loopback/private interface.
- [ ] Verify Qwen and Granite remain on private ports.
- [ ] Back up DB/uploads before release.
- [ ] Deploy AgenticDesk API only; do not restart Qwen/Granite.
- [ ] Verify health, capabilities and chat through Worker.
- [ ] Verify Pages frontend uses the Worker API base URL.
- [ ] Verify persistent DB/uploads survive service restart.
- [ ] Record rollback procedure and last known-good commit.

## Phase 8 — Portfolio
- [ ] Architecture diagram and module overview.
- [ ] Feature screenshots and demo video.
- [ ] Safe sample documents and MCP demo server.
- [ ] Setup guide and environment variable reference.
- [ ] API docs/OpenAPI link.
- [ ] Threat model and approval-first explanation.
- [ ] Honest limitations and roadmap.
- [ ] Final clean clone test.

## Release gate
Do not deploy if any of these are true:
- [ ] Frontend calls an endpoint that is absent from FastAPI.
- [ ] Worker rejects a required route or method.
- [ ] Gateway auth can be bypassed on a protected route.
- [ ] MCP tool execution can occur without an approved record.
- [ ] DB migration can drop or overwrite existing data.
- [ ] Qwen/Granite service health is not verified.
- [ ] Secrets, DB files, uploads or local build artifacts appear in Git changes.

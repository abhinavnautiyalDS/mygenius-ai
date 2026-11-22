# EC2 connect-only deployment

This deployment assumes the EC2 host already runs the private model services:
- Qwen OpenAI-compatible API: `http://127.0.0.1:8001/v1`
- Granite embeddings API: `http://127.0.0.1:8000`

AgenticDesk binds to `127.0.0.1:8002`. It does not install, restart, or modify Qwen or Granite services.

## 1. Clone or fetch the integration branch

For a new clean checkout:

```bash
git clone --branch feature/agenticdesk-implementation https://github.com/abhinavnautiyalDS/mygenius-ai.git
cd mygenius-ai/agenticdesk
```

If using an existing checkout, do not pull over uncommitted work. Back it up and use a separate clean worktree first.

## 2. Configure backend environment

```bash
cd backend
cp .env.example .env
chmod 600 .env
nano .env
```

Set at minimum:
- `APP_ENV=production`
- `CORS_ORIGINS=https://3db7b20b.agenticdesk.pages.dev`
- `QWEN_BASE_URL=http://127.0.0.1:8001/v1`
- `QWEN_MODEL` to the model alias actually served by the Qwen endpoint
- `QWEN_API_KEY` if the Qwen endpoint requires it
- `GRANITE_EMBEDDING_URL=http://127.0.0.1:8000`
- `GRANITE_API_KEY` if the Granite endpoint requires it
- `AGENTICDESK_GATEWAY_TOKEN` matching the Cloudflare Worker secret
- `DATABASE_PATH=./data/agenticdesk.db`
- `UPLOAD_DIR=./data/uploads`
- Optional `TAVILY_API_KEY`

Never commit or paste the real .env. Do not use the sample values as production credentials.

## 3. Install and validate

```bash
cd /home/ubuntu/agenticdesk/agenticdesk
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ../backend
python -m py_compile app/main.py
pytest -q
```

## 4. Install the AgenticDesk service

Review `deploy/agenticdesk.service.example` and adjust paths/user only if your checkout differs. Then:

```bash
sudo cp ../deploy/agenticdesk.service.example /etc/systemd/system/agenticdesk.service
sudo systemctl daemon-reload
sudo systemctl enable agenticdesk.service
sudo systemctl restart agenticdesk.service
sudo systemctl status agenticdesk.service --no-pager
curl -fsS http://127.0.0.1:8002/api/v1/health
```

This restarts only AgenticDesk. Do not restart `aura-ai.service` or `aura-qwen.service`.

## 5. Connect the Cloudflare Worker

The Worker must have:
- `BACKEND_ORIGIN`: HTTPS origin forwarding to 127.0.0.1:8002 through the existing approved tunnel.
- `AGENTICDESK_GATEWAY_TOKEN`: secret matching backend .env.

The Worker allowlist must include the FastAPI API paths:
- `/api/v1/health`, `/api/v1/capabilities`
- `/api/v1/chat`, `/api/v1/chat/stream`
- `/api/v1/conversations` and UUID detail/delete
- `/api/v1/knowledge/documents` and UUID delete
- `/api/v1/mcp/servers`, UUID tools discovery, and tool request
- `/api/v1/approvals` and UUID approve/reject
- `/api/v1/workflows`

Keep Worker token injection server-side. Do not put it in Pages environment variables or browser code.

## 6. Connect the Pages frontend

Build with:
`VITE_API_BASE_URL=https://agenticdesk-api.abhinavnautiyal96.workers.dev/api/v1`

Cloudflare Pages must deploy the `agenticdesk/frontend` project directory, run `npm ci && npm run build`, and publish `dist`.

## 7. Verify end to end

- Pages loads without browser console errors.
- Worker health returns 200.
- Create a chat; Qwen returns a response.
- Conversation appears in history and reopens with messages.
- Upload a small text/PDF/DOCX file; Granite returns 384-dimensional vectors.
- RAG answer returns document sources.
- MCP registration accepts only public HTTPS URLs.
- Tool request creates pending approval; reject does not execute; approve executes once.
- Workflow returns and persists a result.
- Qwen and Granite systemd services remain active.

## Important current limitations
- The MCP HTTP JSON-RPC adapter is intentionally narrow; some servers require MCP initialize/session negotiation. Test the specific server before relying on it.
- URL validation blocks private/reserved destinations but a hardened production deployment should additionally pin DNS resolution at connection time and enforce outbound network policy to fully mitigate DNS rebinding.
- SQLite vector search is suitable for a small portfolio demo corpus, not a large multi-tenant knowledge base.
- Workflows are single Qwen tasks, not multi-agent graph orchestration.
- Streaming is chunked SSE after the completed Qwen response, not live model-token streaming.
- The first release uses a shared gateway token, not per-user authentication/RBAC.

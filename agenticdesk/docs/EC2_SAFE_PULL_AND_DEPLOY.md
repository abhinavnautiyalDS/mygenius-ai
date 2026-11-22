# AgenticDesk — Safe EC2 Fetch, Integration and Deployment

This runbook is deliberately conservative because the live EC2 checkout has had local changes and a working Qwen/conversation-memory implementation.

## Known deployment topology

| Component | Location |
|---|---|
| AgenticDesk repo working directory | `/home/ubuntu/agenticdesk/agenticdesk` |
| Backend | `/home/ubuntu/agenticdesk/agenticdesk/backend` |
| Frontend | `/home/ubuntu/agenticdesk/agenticdesk/frontend` |
| Python environment | `/home/ubuntu/agenticdesk/agenticdesk/.venv` |
| AgenticDesk systemd service | `agenticdesk.service` |
| AgenticDesk API bind | `127.0.0.1:8002` |
| Qwen service | `aura-qwen.service`, `127.0.0.1:8001` |
| Granite service | `aura-ai.service`, `127.0.0.1:8000` |
| Cloudflare Pages | `https://3db7b20b.agenticdesk.pages.dev/` |
| Cloudflare Worker | `https://agenticdesk-api.abhinavnautiyal96.workers.dev` |

Do not restart, reconfigure or expose Qwen/Granite as part of an AgenticDesk-only release.

## Critical warning: do not pull directly into the current dirty checkout

The previous live-state capture reported:
- Local branch had a local-only commit and was behind the remote feature branch.
- Working tree contained modified backend/frontend files and untracked runtime/build/data/backup files.
- Local Qwen inference and persistent conversation memory passed an end-to-end test.
- Local frontend build passed, but its rewritten App.tsx did not retain all workspace views from the remote frontend.

Therefore:
- Do not run `git pull`, `git reset --hard`, `git clean`, force-push or blind merge.
- Do not delete `.venv`, `node_modules`, `dist`, `backend/data`, uploads, logs or backups.
- Do not overwrite the full frontend App.tsx with the local chat-only rewrite.
- Do not overwrite the working Qwen integration with unverified remote code.
- Do not copy or commit `.env`, API keys, SQLite DBs, uploads or runtime artifacts.

## Step 1 — Fetch the blueprint branch without changing the working tree

Run from the existing repo root:

```bash
cd /home/ubuntu/agenticdesk/agenticdesk
git fetch origin docs/agenticdesk-a-to-z-blueprint
git log -1 --oneline FETCH_HEAD
```

Fetching updates Git's remote-tracking data; it does not merge into the current checkout.

The blueprint branch is documentation-first. It is not a ready-to-deploy application branch.

## Step 2 — Capture and back up before branch integration

Before switching or merging:
1. Record `git status --short`, `git branch -vv`, `git rev-parse HEAD`, `git rev-parse --show-toplevel` and `git diff --stat`.
2. Preserve tracked modifications as a patch outside the repository.
3. Archive untracked source files that are intentional.
4. Take a consistent SQLite backup using SQLite's backup mechanism while the app is quiesced or use the SQLite backup API; do not simply assume copying a live WAL database is consistent.
5. Back up uploads and service configuration securely. Keep secrets out of the archive shared with GitHub.
6. Verify archive contents and available disk space.

Do not use `git stash -u` as a shortcut without reviewing what it would capture: it can include runtime data, large environments and sensitive files.

## Step 3 — Use a separate clean integration worktree

Preferred approach after the backup is verified:

```bash
cd /home/ubuntu/agenticdesk/agenticdesk
git worktree add ../agenticdesk-integration origin/feature/agenticdesk-foundation
cd ../agenticdesk-integration
git switch -c feature/agenticdesk-integration
```

This creates a separate checkout and leaves the live working directory untouched. Confirm the repository root first; adjust the relative worktree path if the Git root is not the directory shown above.

Bring over only reviewed source changes from the live checkout:
- Qwen request/client behavior and its proven configuration.
- Conversation persistence and summary implementation, adapted to the unified database.
- Any frontend enhancements that do not remove the complete workspace UI.
- Required tests.

Do not copy virtual environments, node_modules, dist, SQLite files, uploads, logs, backups or secrets.

## Step 4 — Verify before deploying

From the clean integration worktree:
- Install backend requirements into an isolated virtual environment.
- Run pytest.
- Run Python compile checks.
- Run frontend install from lockfile and `npm run build`.
- Inspect FastAPI OpenAPI routes.
- Compare API routes with frontend calls and Worker allowlist.
- Test against a copy of the live DB, not the live DB.
- Run chat, memory, RAG, MCP approval/rejection and workflow integration tests.
- Inspect `git status --short` and the full diff for secrets/data/runtime artifacts.

## Step 5 — Controlled deployment

Only after release gates pass:
1. Back up current source, DB and uploads.
2. Deploy the reviewed backend code.
3. Run additive migrations against the production DB.
4. Restart only `agenticdesk.service`.
5. Check `systemctl status agenticdesk.service` and API health.
6. Verify Qwen and Granite endpoints remain healthy without restarting them.
7. Verify Cloudflare Worker routes, auth injection and Pages frontend.
8. Keep the prior commit and DB backup available for rollback.

## Step 6 — Rollback

If the API fails:
- Stop further rollout.
- Restore the previous AgenticDesk application revision.
- Restore the database backup only if a migration/data write requires it and after assessing data created since backup.
- Restart only `agenticdesk.service`.
- Recheck health and Qwen/Granite connectivity.
- Do not reset the entire repository or delete runtime directories.

## Current blueprint branch

`docs/agenticdesk-a-to-z-blueprint`

This branch contains the A-to-Z plan, implementation checklist and this safe pull/deployment runbook. Fetch it first; do not deploy it as application code.

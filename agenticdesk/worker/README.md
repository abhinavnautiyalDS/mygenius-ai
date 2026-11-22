# Cloudflare Worker gateway

The deployable Worker source is `src/index.js`; deploy from this directory with Wrangler.

## Configure

- `BACKEND_ORIGIN`: HTTPS origin of the current Cloudflare Quick Tunnel forwarding to AgenticDesk on `127.0.0.1:8002`. Use the origin only, with no API path.
- `AGENTICDESK_GATEWAY_TOKEN`: Worker secret matching `AGENTICDESK_GATEWAY_TOKEN` in backend/.env.
- The allowed Pages origin is currently `https://3db7b20b.agenticdesk.pages.dev` in `src/index.js`. Update it if the Pages hostname changes.

Set the backend origin as a Worker variable and token as a secret:

```bash
npx wrangler secret put AGENTICDESK_GATEWAY_TOKEN
npx wrangler deploy
```

Set `BACKEND_ORIGIN` in the Cloudflare Worker dashboard under Settings > Variables and Secrets, or use Wrangler's supported variable command for your installed version. Do not put the token in wrangler.toml or source code.

## Deploy

```bash
npm install
npm run deploy
```

## Frontend

Set the Pages build variable:

`VITE_API_BASE_URL=https://agenticdesk-api.abhinavnautiyal96.workers.dev/api/v1`

Pages project root: `agenticdesk/frontend`
Build command: `npm ci && npm run build`
Build output: `dist`

## Gateway behavior

- Exact origin allowlist and GET/POST/DELETE/OPTIONS method allowlist.
- Exact API route allowlist matching the FastAPI contract.
- Worker injects `x-agenticdesk-token` from its secret; browser code never sees it.
- No-store responses and no redirects to arbitrary origins.
- Backend origin must be HTTPS.
- Quick Tunnel URLs can rotate; update `BACKEND_ORIGIN` when the tunnel is recreated.

Do not hardcode the gateway token in Worker source. Never expose Qwen or Granite ports publicly.

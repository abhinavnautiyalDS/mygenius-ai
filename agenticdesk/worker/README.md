# Cloudflare Worker gateway

Set these Worker variables/secrets:
- BACKEND_ORIGIN: the current HTTPS Quick Tunnel origin forwarding to 127.0.0.1:8002 (origin only; no path).
- AGENTICDESK_GATEWAY_TOKEN: secret matching the backend environment.

Deploy the Worker below. The Pages frontend should use:
VITE_API_BASE_URL=https://agenticdesk-api.abhinavnautiyal96.workers.dev/api/v1

```js
const ALLOWED_ORIGINS = new Set([
  "https://3db7b20b.agenticdesk.pages.dev",
]);

function isAllowedPath(path) {
  return path === "/" ||
    path === "/api/v1/health" ||
    path === "/api/v1/capabilities" ||
    path === "/api/v1/chat" ||
    path === "/api/v1/chat/stream" ||
    path === "/api/v1/conversations" ||
    path === "/api/v1/knowledge/documents" ||
    path === "/api/v1/mcp/servers" ||
    path === "/api/v1/approvals" ||
    path === "/api/v1/workflows" ||
    /^\/api\/v1\/conversations\/[a-f0-9-]+$/.test(path) ||
    /^\/api\/v1\/knowledge\/documents\/[a-f0-9-]+$/.test(path) ||
    /^\/api\/v1\/mcp\/servers\/[a-f0-9-]+\/tools$/.test(path) ||
    /^\/api\/v1\/mcp\/servers\/[a-f0-9-]+\/tools\/[A-Za-z0-9_.-]+\/request$/.test(path) ||
    /^\/api\/v1\/approvals\/[a-f0-9-]+\/(approve|reject)$/.test(path);
}

function corsHeaders(origin) {
  const headers = new Headers({
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  });
  if (ALLOWED_ORIGINS.has(origin)) headers.set("Access-Control-Allow-Origin", origin);
  return headers;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    const headers = corsHeaders(origin);

    if (origin && !ALLOWED_ORIGINS.has(origin))
      return new Response("Origin not allowed", { status: 403, headers });

    if (!["GET", "POST", "DELETE", "OPTIONS"].includes(request.method))
      return new Response("Method not allowed", { status: 405, headers });

    if (!isAllowedPath(url.pathname))
      return new Response("Not found", { status: 404, headers });

    if (request.method === "OPTIONS")
      return new Response(null, { status: 204, headers });

    if (!env.BACKEND_ORIGIN || !env.AGENTICDESK_GATEWAY_TOKEN)
      return new Response("Gateway configuration missing", { status: 503, headers });

    const upstreamUrl = new URL(url.pathname + url.search, env.BACKEND_ORIGIN);
    const upstreamHeaders = new Headers(request.headers);
    upstreamHeaders.delete("x-agenticdesk-token");
    upstreamHeaders.set("x-agenticdesk-token", env.AGENTICDESK_GATEWAY_TOKEN);
    upstreamHeaders.delete("host");
    upstreamHeaders.delete("origin");

    try {
      const upstream = await fetch(upstreamUrl, {
        method: request.method,
        headers: upstreamHeaders,
        body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
        redirect: "manual",
      });
      const responseHeaders = new Headers(upstream.headers);
      for (const [key, value] of headers.entries()) responseHeaders.set(key, value);
      responseHeaders.set("Cache-Control", "no-store");
      responseHeaders.delete("server");
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: responseHeaders,
      });
    } catch {
      return new Response("AgenticDesk backend unavailable", { status: 502, headers });
    }
  },
};
```

Do not hardcode the gateway token in Worker source. Configure it as a Worker secret. Quick Tunnel URLs can change; update BACKEND_ORIGIN whenever the tunnel is recreated.

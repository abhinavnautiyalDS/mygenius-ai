const ALLOWED_ORIGINS = new Set([
  "https://3db7b20b.agenticdesk.pages.dev",
]);

const UUID = "[0-9a-fA-F-]{36}";
const ROUTES = [
  /^\/$/,
  /^\/api\/v1\/health$/,
  /^\/api\/v1\/capabilities$/,
  /^\/api\/v1\/chat$/,
  /^\/api\/v1\/chat\/stream$/,
  /^\/api\/v1\/conversations$/,
  new RegExp("^/api/v1/conversations/" + UUID + "$"),
  /^\/api\/v1\/knowledge\/documents$/,
  new RegExp("^/api/v1/knowledge/documents/" + UUID + "$"),
  /^\/api\/v1\/mcp\/servers$/,
  new RegExp("^/api/v1/mcp/servers/" + UUID + "/tools$"),
  new RegExp("^/api/v1/mcp/servers/" + UUID + "/tools/[^/]+/request$"),
  /^\/api\/v1\/approvals$/,
  new RegExp("^/api/v1/approvals/" + UUID + "/(approve|reject)$"),
  /^\/api\/v1\/workflows$/,
  /^\/api\/v1\/career\/profile$/,
  /^\/api\/v1\/career\/runs$/,
];

function allowedPath(path) {
  return ROUTES.some((route) => route.test(path));
}

function corsHeaders(origin) {
  const headers = new Headers({
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  });
  if (ALLOWED_ORIGINS.has(origin)) {
    headers.set("Access-Control-Allow-Origin", origin);
  }
  return headers;
}

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    const headers = corsHeaders(origin);

    if (origin && !ALLOWED_ORIGINS.has(origin)) {
      return new Response("Origin not allowed", { status: 403, headers });
    }
    if (!["GET", "POST", "DELETE", "OPTIONS"].includes(request.method)) {
      return new Response("Method not allowed", { status: 405, headers });
    }
    if (!allowedPath(incoming.pathname)) {
      return new Response("Not found", { status: 404, headers });
    }
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers });
    }
    if (!env.BACKEND_ORIGIN || !env.AGENTICDESK_GATEWAY_TOKEN) {
      return new Response("Gateway configuration missing", { status: 503, headers });
    }

    let upstream;
    try {
      const backend = new URL(env.BACKEND_ORIGIN);
      if (backend.protocol !== "https:") {
        return new Response("Backend origin must use HTTPS", { status: 500, headers });
      }
      upstream = new URL(incoming.pathname + incoming.search, backend);
    } catch {
      return new Response("Invalid backend origin", { status: 500, headers });
    }

    const upstreamHeaders = new Headers(request.headers);
    upstreamHeaders.delete("host");
    upstreamHeaders.delete("origin");
    upstreamHeaders.delete("x-agenticdesk-token");
    upstreamHeaders.set("x-agenticdesk-token", env.AGENTICDESK_GATEWAY_TOKEN);

    try {
      const response = await fetch(upstream, {
        method: request.method,
        headers: upstreamHeaders,
        body: request.method === "GET" ? undefined : request.body,
        redirect: "manual",
      });
      const responseHeaders = new Headers(response.headers);
      for (const [key, value] of headers.entries()) responseHeaders.set(key, value);
      responseHeaders.set("Cache-Control", "no-store");
      responseHeaders.delete("server");
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    } catch {
      return new Response("AgenticDesk backend unavailable", { status: 502, headers });
    }
  },
};

/**
 * newsagent-tracker — Cloudflare Worker
 *
 * Endpoints:
 *   GET  /click/{article_id}?url={encoded_url}
 *     Logs the click to KV (keyed by date), then redirects to the article.
 *     No auth required — this is the public redirect URL embedded in emails.
 *
 *   GET  /events?since={YYYY-MM-DD}
 *     Returns all click events since the given date.
 *     Requires Authorization: Bearer {API_SECRET}.
 *
 * KV structure:
 *   Key:   clicks_{YYYY-MM-DD}
 *   Value: JSON array of { article_id, timestamp }
 *   TTL:   7 days
 */

const SEVEN_DAYS_S = 7 * 24 * 60 * 60;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ── GET /click/{article_id}?url={encoded_target} ────────────────────────
    if (url.pathname.startsWith("/click/")) {
      return handleClick(url, env);
    }

    // ── GET /events?since={YYYY-MM-DD} ──────────────────────────────────────
    if (url.pathname === "/events" && request.method === "GET") {
      return handleEvents(request, url, env);
    }

    return new Response("Not Found", { status: 404 });
  },
};

// ---------------------------------------------------------------------------

async function handleClick(url, env) {
  const articleId = url.pathname.slice("/click/".length);
  const targetUrl = url.searchParams.get("url");

  if (!articleId || !targetUrl) {
    return new Response("Missing article_id or url", { status: 400 });
  }

  // Store in KV under today's date key (append to existing list)
  const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  const key = `clicks_${today}`;
  const existing = JSON.parse((await env.EVENTS_KV.get(key)) ?? "[]");
  existing.push({ article_id: articleId, timestamp: new Date().toISOString() });
  await env.EVENTS_KV.put(key, JSON.stringify(existing), {
    expirationTtl: SEVEN_DAYS_S,
  });

  return Response.redirect(targetUrl, 302);
}

async function handleEvents(request, url, env) {
  // Auth check
  const authHeader = request.headers.get("Authorization") ?? "";
  const expectedSecret = env.API_SECRET ?? "";
  if (!expectedSecret || authHeader !== `Bearer ${expectedSecret}`) {
    return new Response("Unauthorized", { status: 401 });
  }

  // Collect events from since-date up to today
  const sinceParam = url.searchParams.get("since") ?? new Date().toISOString().slice(0, 10);
  const sinceDate = new Date(sinceParam);
  const today = new Date();
  const events = [];

  for (let d = new Date(sinceDate); d <= today; d.setDate(d.getDate() + 1)) {
    const key = `clicks_${d.toISOString().slice(0, 10)}`;
    const raw = await env.EVENTS_KV.get(key);
    if (raw) {
      events.push(...JSON.parse(raw));
    }
  }

  return new Response(JSON.stringify({ events }), {
    headers: { "Content-Type": "application/json" },
  });
}

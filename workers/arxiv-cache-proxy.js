// Cloudflare Worker: cache-backed arXiv query API proxy for ThesisKit.
//
// This is a duplicate-request reducer, not a rate-limit evasion layer.
// Do not use this worker to exceed arXiv API limits. arXiv's legacy API terms
// currently ask clients to make no more than one request every three seconds
// and to limit requests to a single connection at a time.
//
// PDF proxying is intentionally not supported; keep users linked to arxiv.org.

const ARXIV_QUERY_API = "https://export.arxiv.org/api/query";
const DEFAULT_USER_AGENT = "ThesisKit arXiv cache proxy (+https://github.com/sodiptabadiabanurea/thesiskit)";
const DEFAULT_CACHE_TTL_SECONDS = 60 * 60 * 24;
const DEFAULT_STALE_SECONDS = 60 * 60 * 24 * 7;

function integerFromEnv(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : fallback;
}

function buildUpstreamUrl(requestUrl) {
  const url = new URL(requestUrl);
  url.searchParams.sort();
  const upstream = new URL(ARXIV_QUERY_API);
  upstream.search = url.searchParams.toString();
  return upstream;
}

function buildCacheKey(requestUrl) {
  const url = new URL(requestUrl);
  url.pathname = "/api/query";
  url.searchParams.sort();
  return new Request(url.toString(), { method: "GET" });
}

function withHeader(response, name, value) {
  const headers = new Headers(response.headers);
  headers.set(name, value);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

export default {
  async fetch(request, env, ctx) {
    const requestUrl = new URL(request.url);

    if (request.method !== "GET") {
      return new Response("Only GET requests are supported.\n", {
        status: 405,
        headers: { Allow: "GET" },
      });
    }

    if (!["/", "/api/query"].includes(requestUrl.pathname)) {
      return new Response("Only the arXiv query API is proxied.\n", {
        status: 404,
        headers: { "Cache-Control": "no-store" },
      });
    }

    if (!requestUrl.searchParams.has("search_query") && !requestUrl.searchParams.has("id_list")) {
      return new Response("Missing arXiv search_query or id_list parameter.\n", {
        status: 400,
        headers: { "Cache-Control": "no-store" },
      });
    }

    const ttl = integerFromEnv(env?.CACHE_TTL_SECONDS, DEFAULT_CACHE_TTL_SECONDS);
    const staleSeconds = integerFromEnv(env?.STALE_WHILE_REVALIDATE_SECONDS, DEFAULT_STALE_SECONDS);
    const userAgent = env?.ARXIV_USER_AGENT || DEFAULT_USER_AGENT;
    const upstreamUrl = buildUpstreamUrl(request.url);
    const cache = caches.default;
    const cacheKey = buildCacheKey(request.url);

    const cached = await cache.match(cacheKey);
    if (cached) {
      return withHeader(cached, "X-ThesisKit-Cache", "HIT");
    }

    const upstreamResponse = await fetch(upstreamUrl, {
      headers: {
        Accept: "application/atom+xml, application/xml;q=0.9, text/xml;q=0.8",
        "User-Agent": userAgent,
      },
    });

    const headers = new Headers(upstreamResponse.headers);
    if (upstreamResponse.ok) {
      headers.set("Cache-Control", `public, s-maxage=${ttl}, stale-while-revalidate=${staleSeconds}`);
    } else {
      headers.set("Cache-Control", "no-store");
    }
    headers.set("X-ThesisKit-Cache", "MISS");
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/atom+xml; charset=utf-8");
    }

    const response = new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers,
    });

    if (upstreamResponse.ok) {
      ctx.waitUntil(cache.put(cacheKey, response.clone()));
    }

    return response;
  },
};

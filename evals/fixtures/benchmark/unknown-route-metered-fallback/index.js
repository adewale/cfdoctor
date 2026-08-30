function canonicalPath(pathname) {
  let decoded;
  try {
    decoded = decodeURIComponent(pathname);
  } catch {
    decoded = pathname;
  }
  const collapsed = decoded.replace(/\/{2,}/g, "/");
  return collapsed.length > 1 ? collapsed.replace(/\/$/, "") : collapsed;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/") {
      return new Response(
        '<nav><a href="/topics">Topics</a>' +
          '<a href="/handbook/engineering/on-call">On-call handbook</a></nav>',
        { headers: { "content-type": "text/html" } }
      );
    }

    if (url.pathname.startsWith("/assets/") || url.pathname === "/favicon.ico") {
      return env.ASSETS.fetch(request);
    }

    const path = canonicalPath(url.pathname);
    const page = await env.DB.prepare(
      "SELECT title, body, cache_version FROM pages WHERE canonical_path = ?1 LIMIT 1"
    ).bind(path).first();

    if (!page) return new Response("not found", { status: 404 });

    return new Response(`<h1>${page.title}</h1><article>${page.body}</article>`, {
      headers: {
        "content-type": "text/html",
        "cache-control": "public, max-age=60",
        etag: `"${page.cache_version}"`,
      },
    });
  },
};

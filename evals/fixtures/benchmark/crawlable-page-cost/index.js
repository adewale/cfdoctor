export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/robots.txt") {
      return new Response(
        "User-agent: *\nAllow: /\nSitemap: https://papers.example.com/sitemap.xml\n"
      );
    }

    if (url.pathname === "/sitemap.xml") {
      return new Response(
        '<?xml version="1.0"?><urlset>' +
          '<url><loc>https://papers.example.com/</loc></url>' +
          '<url><loc>https://papers.example.com/browse</loc></url>' +
        '</urlset>',
        { headers: { "content-type": "application/xml" } }
      );
    }

    const isContentPage =
      url.pathname === "/" ||
      url.pathname === "/browse" ||
      url.pathname.startsWith("/abstract/") ||
      url.pathname === "/about";
    if (!isContentPage) {
      return new Response("not found", { status: 404 });
    }

    // Shared layout data is loaded before every public content page.
    const corpus = await env.DB.prepare(
      "SELECT COUNT(id) AS total FROM abstracts"
    ).first();

    if (url.pathname === "/") {
      const entityTypes = await env.DB.prepare(
        "SELECT entity_type, COUNT(id) AS total FROM entities GROUP BY entity_type ORDER BY total DESC LIMIT 12"
      ).all();
      return new Response(
        `<h1>${corpus.total} abstracts</h1>` +
          `<p>${entityTypes.results.length} entity types</p>` +
          '<nav><a href="/browse">Browse</a>' +
          '<a href="/abstract/1">First abstract</a>' +
          '<a href="/about">About</a></nav>',
        { headers: { "content-type": "text/html" } }
      );
    }

    if (url.pathname === "/browse") {
      const abstracts = await env.DB.prepare(
        "SELECT id, title, published_at FROM abstracts ORDER BY published_at DESC LIMIT 50"
      ).all();
      return new Response(
        `<h1>Browse ${corpus.total} abstracts</h1>` +
          abstracts.results
            .map((abstract) => `<a href="/abstract/${abstract.id}">${abstract.title}</a>`)
            .join("\n"),
        { headers: { "content-type": "text/html" } }
      );
    }

    if (url.pathname.startsWith("/abstract/")) {
      const id = Number(url.pathname.split("/")[2]);
      const abstract = await env.DB.prepare(
        "SELECT title, journal FROM abstracts WHERE id = ?1 LIMIT 1"
      ).bind(id).first();
      return abstract
        ? new Response(`<h1>${abstract.title}</h1><p>${abstract.journal}</p>`, {
            headers: { "content-type": "text/html" },
          })
        : new Response("not found", { status: 404 });
    }

    if (url.pathname === "/about") {
      return new Response(`About the paper browser (${corpus.total} abstracts)`);
    }
  },
};

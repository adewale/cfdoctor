export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const galleryRoute = /^\/gallery\/([^/]+)\/?$/.exec(url.pathname);
    if (galleryRoute) {
      const slug = decodeURIComponent(galleryRoute[1]);
      const images = Array.from({ length: 12 }, (_, index) =>
        `<img src="/media/${slug}/${index}?width=960&format=avif">`
      ).join("");
      return new Response(`${images}<script>fetch('/api/gallery/${slug}')</script>`, {
        headers: { "content-type": "text/html" },
      });
    }
    const mediaRoute = /^\/media\/([^/]+)\/(\d+)\/?$/.exec(url.pathname);
    if (mediaRoute) {
      const key = `${decodeURIComponent(mediaRoute[1])}/${mediaRoute[2]}`;
      const original = await env.ORIGINALS.get(key);
      if (!original) return new Response("not found", { status: 404 });
      return (await env.IMAGES.input(original.body)
        .transform({ width: 960 })
        .output({ format: "image/avif" })).response();
    }
    const metadataRoute = /^\/api\/gallery\/([^/]+)\/?$/.exec(url.pathname);
    if (metadataRoute) {
      const slug = decodeURIComponent(metadataRoute[1]);
      return Response.json(await env.DB.prepare(
        "SELECT title, photographer FROM galleries WHERE slug = ?1 LIMIT 1"
      ).bind(slug).first());
    }
    return new Response('<a href="/gallery/first">First gallery</a>', {
      headers: { "content-type": "text/html" },
    });
  },
};

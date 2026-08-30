import puppeteer from "@cloudflare/puppeteer";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const route = /^\/guide\/([^/]+)\/?$/.exec(url.pathname);
    if (!route) {
      return new Response('<a href="/guide/getting-started">Getting started</a>', {
        headers: { "content-type": "text/html" },
      });
    }

    const slug = decodeURIComponent(route[1]);
    const theme = await env.CONFIG.get("public-theme", "json");
    const guide = await env.GUIDES.get(`guides/${slug}.html`);
    const thumbnail = await env.THUMBNAILS.fetch(`https://thumbnails.internal/${slug}`);
    const browser = await puppeteer.launch(env.BROWSER);
    let preview;
    try {
      const page = await browser.newPage();
      await page.setContent(await guide.text());
      preview = await page.screenshot();
    } finally {
      await browser.close();
    }
    env.ANALYTICS.writeDataPoint({ blobs: [slug, theme.name] });
    ctx.waitUntil(env.EVENTS.send({ type: "guide_view", slug }));
    return new Response(preview, {
      headers: { "content-type": "image/png", "x-thumbnail": thumbnail.status },
    });
  },
};

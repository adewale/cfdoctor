import { ClickTracker } from "./click_tracker.js";

export { ClickTracker };

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Per-user dashboard: scan the whole KV prefix on every page view.
    if (url.pathname.startsWith("/dashboard/")) {
      const user = url.pathname.split("/")[2];
      const scan = await env.LINKS.list({ prefix: `link:${user}:` });
      const links = [];
      for (const key of scan.keys) {
        links.push(await env.LINKS.get(key.name, "json"));
      }
      return Response.json(links);
    }

    // Redirect path: resolve the slug, record the click in a Durable Object.
    const slug = url.pathname.slice(1);
    const target = await env.LINKS.get(`slug:${slug}`);
    if (!target) {
      return new Response("not found", { status: 404 });
    }
    const id = env.CLICK_TRACKER.idFromName(slug);
    ctx.waitUntil(
      env.CLICK_TRACKER.get(id).fetch("https://tracker.internal/record", {
        method: "POST",
        body: JSON.stringify({
          slug,
          country: request.cf?.country,
          referrer: request.headers.get("referer"),
          agent: request.headers.get("user-agent"),
        }),
      }),
    );
    return Response.redirect(target, 302);
  },
};

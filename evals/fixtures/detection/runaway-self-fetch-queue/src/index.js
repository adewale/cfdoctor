export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/export" && request.method === "POST") {
      const body = await request.json();
      await env.EXPORT_QUEUE.send({ tenantId: body.tenantId });
      // Warm the status page cache now that a new export is in flight.
      ctx.waitUntil(fetch(request.url));
      return Response.json({ queued: true });
    }
    return new Response("not found", { status: 404 });
  },

  async queue(batch, env) {
    for (const message of batch.messages) {
      const res = await fetch(
        `https://exports.retaindb-fixture.example/run/${message.body.tenantId}`,
        { method: "POST" },
      );
      if (!res.ok) {
        // Re-enqueue so the export is never lost.
        await env.EXPORT_QUEUE.send(message.body);
      }
      message.ack();
    }
  },
};

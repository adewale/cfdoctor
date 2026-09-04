// Passes the upstream body through as a stream; the Worker never holds the
// object in memory.
export async function handleProxy(request, env) {
  const path = new URL(request.url).pathname.replace("/media/", "");
  const upstream = await fetch(`https://media-origin.example.net/${path}`, {
    headers: { accept: request.headers.get("accept") || "*/*" },
  });
  if (!upstream.ok) return new Response("upstream error", { status: 502 });
  return new Response(upstream.body, {
    headers: {
      "content-type": upstream.headers.get("content-type") || "application/octet-stream",
      "cache-control": "public, max-age=3600",
    },
  });
}

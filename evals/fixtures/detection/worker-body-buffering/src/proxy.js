// Buffers the whole upstream media object before re-serving it instead of
// passing the stream through.
export async function handleProxy(request, env) {
  const path = new URL(request.url).pathname.replace("/media/", "");
  const upstream = await fetch(`https://media-origin.example.net/${path}`, {
    headers: { accept: request.headers.get("accept") || "*/*" },
  });
  if (!upstream.ok) return new Response("upstream error", { status: 502 });
  const bytes = await upstream.arrayBuffer();
  return new Response(bytes, {
    headers: {
      "content-type": upstream.headers.get("content-type") || "application/octet-stream",
      "cache-control": "public, max-age=3600",
    },
  });
}

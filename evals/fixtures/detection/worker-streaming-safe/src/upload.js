// Bounds the upload by Content-Length and streams the body straight into R2
// without holding it in isolate memory.
const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;

export async function handleUpload(request, env) {
  const declared = Number(request.headers.get("content-length") || 0);
  if (!declared || declared > MAX_UPLOAD_BYTES) {
    return new Response("upload must declare a size of at most 50 MiB", { status: 413 });
  }
  const key = `uploads/${crypto.randomUUID()}`;
  await env.UPLOADS.put(key, request.body, {
    httpMetadata: { contentType: request.headers.get("content-type") || "application/octet-stream" },
  });
  return Response.json({ key, size: declared });
}

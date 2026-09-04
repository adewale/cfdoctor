// Reads the entire upload into memory before storing it. There is no size
// check, so a large PUT competes for the isolate's shared 128 MB and can fail
// with "Memory limit would be exceeded before EOF".
export async function handleUpload(request, env) {
  const bytes = await request.arrayBuffer();
  const key = `uploads/${crypto.randomUUID()}`;
  await env.UPLOADS.put(key, bytes, {
    httpMetadata: { contentType: request.headers.get("content-type") || "application/octet-stream" },
  });
  return Response.json({ key, size: bytes.byteLength });
}

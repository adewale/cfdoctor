// Small signed webhook payloads are read in full so the HMAC can be verified
// over the exact bytes; the provider bounds the payload size, so this is not a
// large-body buffering risk.
export async function handleWebhook(request, env) {
  const signature = request.headers.get("x-hub-signature-256") || "";
  const deliveryId = request.headers.get("x-media-delivery-id") || "";
  const body = await request.arrayBuffer();
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(env.WEBHOOK_SECRET), { name: "HMAC", hash: "SHA-256" }, false, ["verify"]);
  const ok = await crypto.subtle.verify("HMAC", key, hexToBytes(signature.replace("sha256=", "")), body);
  if (!ok) return new Response("bad signature", { status: 401 });
  if (await env.UPLOADS.head(`webhooks/${deliveryId}`)) return new Response("duplicate delivery", { status: 200 });
  await env.UPLOADS.put(`webhooks/${deliveryId}`, body);
  return new Response("accepted", { status: 202 });
}

function hexToBytes(hex) {
  const pairs = hex.match(/.{2}/g) || [];
  return Uint8Array.from(pairs, (pair) => parseInt(pair, 16));
}

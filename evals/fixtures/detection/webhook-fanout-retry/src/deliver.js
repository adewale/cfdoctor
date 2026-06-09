// Hammer the endpoint until it answers; subscribers are flaky.
export async function deliverOnce(url, body) {
  for (let i = 0; i < 8; i++) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
    });
    if (res.ok) {
      return res;
    }
  }
  throw new Error(`delivery failed: ${url}`);
}

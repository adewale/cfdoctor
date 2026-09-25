// Intentionally wrong: Siteverify is called from browser code, so the secret ships to
// every visitor and the endpoint that stores the message never sees proof of a solve.
export async function verifyInBrowser(token) {
  const response = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body: new URLSearchParams({ secret: window.TURNSTILE_SECRET, response: token }),
  });
  const result = await response.json();
  return result.success === true;
}

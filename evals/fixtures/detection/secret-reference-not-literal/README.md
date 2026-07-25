# secret-reference-not-literal

Precision control for `CFDOC-SEC-SECRET-ASSIGNMENT`.

Every secret-named variable here is assigned a *reference* rather than a literal:

- `const token = form.get("cf-turnstile-response")` — the value comes from the request.
- `const apiKey = env.SERVICE_API_KEY` — the value comes from a Worker binding.
- `api_token = var.cloudflare_api_token` — the value comes from a Terraform variable.

All three are the correct way to handle credentials, and the first is the exact shape the
scanner's own Turnstile server-side-validation guidance asks contributors to write. Before
this control existed the scanner reported the first two as high-severity committed
credentials, so following its advice produced a new finding.

Expected: no findings at all (`max_findings: 0`). Committed literals are still covered as a
positive case by `secret-in-wrangler-vars`.

# Fixture: turnstile-siteverify-unchecked

Siteverify is present but the handler breaks the Turnstile Spin canonical contract
(evidence `CFDOC-EVD-CF-TURNSTILE-SPIN`):

- It trusts `response.ok`. Siteverify returns HTTP 200 with `success: false` for forged,
  expired, or replayed tokens, so every token passes.
- It never compares `action` or `hostname`, so tokens minted on another surface or on
  `localhost` are accepted.
- It has no token-size guard, no `remoteip`, and no timeout.
- It falls back to Cloudflare's documented always-pass dummy secret when
  `TURNSTILE_SECRET` is unset, so a missing secret silently disables protection.

The dummy key is a public test value, so `CFDOC-SEC-SECRET-ASSIGNMENT` must not treat it
as a committed credential; `CFDOC-SEC-TURNSTILE-TEST-KEY` owns that judgment.

This is intentionally bad code, committed only as a detection eval fixture. Do not copy it.

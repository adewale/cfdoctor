# Fixture: turnstile-canonical-safe

False-positive guard for the Turnstile leads (evidence `CFDOC-EVD-CF-TURNSTILE-SPIN`). The
integration follows the Turnstile Spin canonical contract:

- The widget sets `data-action` and posts to the existing backend handler.
- The Worker rejects non-string or >2048-character tokens, sends `remoteip`, bounds the
  Siteverify call with `AbortSignal.timeout(10_000)`, fails closed on network/non-2xx/non-JSON,
  and requires `success === true`, the expected `action`, and a hostname from a
  deployment-specific allowlist.
- Cloudflare's dummy keys appear only in the `dev` Wrangler environment and in `tests/`.

Expected: zero findings.

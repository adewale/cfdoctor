# turnstile-no-siteverify

Known-bad fixture: a Turnstile widget is rendered client-side but the server
never calls `siteverify`, so the challenge is cosmetic.

- `CFDOC-SEC-TURNSTILE-NO-SITEVERIFY` — widget present (api.js + `cf-turnstile`),
  no server-side verification (`siteverify` / `cf-turnstile-response`).

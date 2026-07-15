# turnstile-verified

Control fixture: a Turnstile widget wired correctly, verifying the token
server-side via `siteverify` before accepting the form.

- `CFDOC-SEC-TURNSTILE-NO-SITEVERIFY` — forbidden: server-side verification is
  present, so the lead is correctly suppressed.

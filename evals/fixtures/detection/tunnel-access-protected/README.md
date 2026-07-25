# tunnel-access-protected

Control fixture: a Cloudflare Tunnel hostname fronted by a Cloudflare Access
application/policy, and no committed credentials file.

- `CFDOC-SEC-TUNNEL-NO-ACCESS` — forbidden: an Access application/policy is
  present, so the public-exposure nudge is correctly suppressed.
- `CFDOC-SEC-TUNNEL-CREDENTIALS` — forbidden: no credentials file is committed.

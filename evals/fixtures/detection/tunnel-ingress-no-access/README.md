# tunnel-ingress-no-access

Known-bad Cloudflare Tunnel fixture.

- `CFDOC-SEC-TUNNEL-NO-ACCESS` — the `admin.example.com` public hostname has no
  Cloudflare Access policy in the repo; an internal/admin surface reachable by
  anyone on the internet.
- `CFDOC-SEC-TUNNEL-CREDENTIALS` — the cloudflared credentials JSON
  (`AccountTag`/`TunnelID`/`TunnelSecret`) is committed to the repo, granting a
  persistent inbound path to the origin. All values are fake fixture strings.

# terraform-tls-off-dnssec-ok

Mixed fixture: SSL/TLS mode Off is a real high-severity finding, but DNSSEC is
enabled so the DNSSEC-missing lead is correctly suppressed.

- `CFDOC-SEC-TLS-FLEXIBLE` — required: Off (like Flexible) leaves the origin leg
  unencrypted/cleartext.
- `CFDOC-CONFIG-DNSSEC-MISSING` — forbidden: `cloudflare_zone_dnssec` is present.
- `CFDOC-SEC-TLS-FULL-NOT-STRICT` — forbidden: Off is not Full (non-strict).

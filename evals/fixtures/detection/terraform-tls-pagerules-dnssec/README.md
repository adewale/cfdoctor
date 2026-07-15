# terraform-tls-pagerules-dnssec

Known-bad Terraform fixture. A Cloudflare zone is configured with SSL/TLS mode
Full (non-strict), a legacy Page Rule, and no DNSSEC resource.

Expected leads:

- `CFDOC-SEC-TLS-FULL-NOT-STRICT` — Full mode does not validate the origin
  certificate; only Full (strict) does.
- `CFDOC-CONFIG-PAGE-RULES-LEGACY` — Page Rules are in maintenance mode since
  2025-01-06; migrate to the modern Rules products.
- `CFDOC-CONFIG-DNSSEC-MISSING` — a managed zone with no `cloudflare_zone_dnssec`.

Precision control: Full (non-strict) must not be graded as Flexible
(`CFDOC-SEC-TLS-FLEXIBLE` is forbidden here).

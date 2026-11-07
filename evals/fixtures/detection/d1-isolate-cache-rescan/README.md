# Fixture: d1-isolate-cache-rescan

Models the kentcdodds.com PR #890 rows-read bill: two full-table `PostRead`
aggregates (per-slug read counts, `COUNT(DISTINCT)` reader total) are cached
only in per-isolate memory — one path through a cachified `lruCache` adapter,
one through a hand-rolled module-scope `Map` memo — behind a hot route and a
2-minute warmup cron. Isolates have no guaranteed lifetime, so deploys,
evictions, and the cron re-run the scans regardless of the 5–30 minute TTLs;
the incident measured roughly 127× the TTL-implied execution rate and a
$195/month D1 line item.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.

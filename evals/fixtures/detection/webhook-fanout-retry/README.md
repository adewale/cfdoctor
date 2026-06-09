# Fixture: webhook-fanout-retry

Models the Convoy/Stripe webhook delivery-failure story where webhook retries
turned into a $23k serverless bill: an uncapped `Promise.all(...map(...))`
fan-out to every subscriber per event, multiplied by a delivery helper that
retries each flaky endpoint eight times in a hot loop with no backoff or
circuit breaker.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.

# Fixture: broad-route-cron-storm

Models two quiet invocation multipliers: a wildcard route (`*example.com/*`)
that intercepts the entire zone including traffic the Worker was never meant to
handle, and a `* * * * *` cron that wakes the Worker every minute forever, like
the static-site/idle-service bill-shock stories.

This is intentionally bad configuration, committed only as a detection eval
fixture for `scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real
project.

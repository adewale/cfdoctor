# Public reports with cache-fill persistence

The `/report/:slug` route represents about 20,000 known public reports, but the
supplied root directory links only the first one and no complete sitemap or link
inventory is included. Reports are regenerated when the local Cache API misses
and are also copied to R2 so support staff can inspect the latest render. No
cache analytics, request counts, R2 metrics, D1 metrics, or deployed cache rules
are supplied.

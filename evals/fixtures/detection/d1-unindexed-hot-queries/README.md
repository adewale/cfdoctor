# Fixture: d1-unindexed-hot-queries

Models the whatmedicaidpays.com April 2026 D1 bill (127,599,130,859 rows read,
$134.14 on a ~765k-row database): the migrations define a hot `reimbursement`
table with primary keys only, the root layout loader runs `MAX(year)` and
`DISTINCT state_id` scans on every page view before page code executes, and
page loaders filter by `(hcpcs_code_id, year)` and aggregate per state. On D1
every one of those scanned rows is billed, so sitewide traffic multiplies
full-table scans into billions of billed rows.
War story: https://fullstacksveltekit.com/blog/cloudflare-d1-bill

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.

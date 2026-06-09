# Fixture: d1-nplus1-dashboard

Models the classic N+1 read-amplification bill (the Firebase "$30k in 72 hours"
shape, on D1): the feed endpoint selects every column of every post with
`SELECT *`, then issues four more queries plus an UPDATE for each post inside a
loop, so billed rows scale with content volume on every single page view.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.

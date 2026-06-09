# Fixture: image-variant-explosion

Models the Metacast postmortem where LLM crawlers hammered an image optimization
endpoint and every distinct size/format combination became a separately billed
transformation. The Worker forwards user-controlled width, DPR, and format query
parameters directly into `cf.image` options with no allowlist or normalization.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.

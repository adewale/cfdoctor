# Public guide renderer

The `/guide/:slug` family contains about 8,000 crawlable guides. Each request
assembles an otherwise valid page from several Cloudflare primitives. The
browser session is closed in `finally`; the audit should account for its cost,
not misdiagnose a lifecycle leak. Requests outside that route family return the
directory response before any binding call. No deployed traffic, cache, product
metrics, or account controls are supplied.

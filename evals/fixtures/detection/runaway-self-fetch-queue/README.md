# Fixture: runaway-self-fetch-queue

Models the RetainDB runaway async loop war story (a queue/self-trigger loop that
generated billions of billable storage and invocation operations). The Worker
fetches its own incoming request URL to "warm the cache", and the queue consumer
re-enqueues failures by hand while the consumer config has no dead-letter queue
or retry bound.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.

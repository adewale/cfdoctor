# Fixture: worker-streaming-safe

False-positive guard for `CFDOC-PERF-BODY-BUFFERING` (evidence
`CFDOC-EVD-CF-ISOLATE-MEMORY-MODEL`). The same upload/proxy Worker as
`worker-body-buffering`, written the way the Workers docs recommend: the
upload handler rejects requests without a bounded `Content-Length` and streams
`request.body` into R2, the proxy returns `upstream.body` as a stream, and the
only whole-body read is a small signed webhook payload that must be hashed
over its exact bytes. None of these shapes should be flagged, and the scanner
must emit zero findings here.

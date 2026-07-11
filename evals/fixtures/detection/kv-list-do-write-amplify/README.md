# Fixture: kv-list-do-write-amplify

Models two operation-amplification patterns from the RetainDB bill story and the
coey.dev Durable Objects gotchas: a KV `list()` prefix scan that runs on every
dashboard page view, and a Durable Object that performs five separate
`storage.put()` calls for every single click. The scanner reports a low-confidence backend-aware coalescing/transaction review: distinct-key batching is not claimed to reduce billed rows/units, while redundant logical-state writes may still be coalesced.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.

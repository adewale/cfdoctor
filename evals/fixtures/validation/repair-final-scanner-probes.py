"""Synthetic scanner precision controls from the independent repair review."""

from test_static_scan import scan

cases = {
    "cross-workers": {
        "a/wrangler.jsonc": '{"queues":{"consumers":[{"queue":"jobs","dead_letter_queue":"failed"}]}}',
        "b/wrangler.jsonc": '{"queues":{"consumers":[{"queue":"failed"}]}}',
    },
    "child-to-parent": {
        "wrangler.jsonc": '{"queues":{"consumers":[{"queue":"failed"}]},"env":{"preview":{"queues":{"consumers":[{"queue":"jobs","dead_letter_queue":"failed"}]}}}}'
    },
    "sibling-envs": {
        "wrangler.jsonc": '{"env":{"a":{"queues":{"consumers":[{"queue":"jobs","dead_letter_queue":"failed"}]}},"b":{"queues":{"consumers":[{"queue":"failed"}]}}}}'
    },
    "self-dlq-plus-primary": {
        "wrangler.jsonc": '{"queues":{"consumers":[{"queue":"jobs","dead_letter_queue":"jobs"},{"queue":"unprotected"}]}}'
    },
    "late-opaque-credential": {
        "test/leak.js": 'const secret = "multipart-fixture-value";\nconst password = "opaque-live-value-123456";'
    },
    "late-shaped-credential": {
        "test/leak.js": 'const secret = "multipart-fixture-value";\nconst secret = "cfpat_positive_control_123456";'
    },
}
for label, files in cases.items():
    result = scan(files)
    findings = [
        (f["check_id"], f["severity"], f["evidence"])
        for f in result["findings"]
        if f["check_id"]
        in {
            "CFDOC-REL-QUEUE-NO-DLQ",
            "CFDOC-SEC-SECRET-ASSIGNMENT",
            "CFDOC-SEC-SECRET-VALUE",
        }
    ]
    print(label, findings)

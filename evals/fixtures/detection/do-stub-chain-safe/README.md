# Fixture: do-stub-chain-safe

False-positive guard for `DO-STUB-CALL-CYCLE` and `DO-SQL-SCAN-HOTPATH`
(evidence `CFDOC-EVD-STDAGENTS-DO-LOOP`): a coordinator Durable Object hands a
bounded batch to a runner Durable Object exactly once per request, the runner
never calls back, and every SQL read carries WHERE and LIMIT bounds. A
DO-to-DO call that never returns to the caller is a chain, not a cycle, and
must not be flagged; the scanner must emit zero findings here.

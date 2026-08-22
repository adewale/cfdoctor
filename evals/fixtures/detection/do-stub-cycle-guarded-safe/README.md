# Fixture: do-stub-cycle-guarded-safe

False-positive guard for `DO-STUB-CALL-CYCLE` (evidence
`CFDOC-EVD-STDAGENTS-DO-LOOP`): the two Durable Object classes do call each
other, but both check an explicit `x-hop-depth` budget in a condition before
making the next stub call, so the ping-pong is bounded request/response, not a
runaway loop. The scanner must stay silent — the cycle lead only fires when at
least one class in the cycle lacks a visible guard condition.

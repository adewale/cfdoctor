# Fixture: do-schema-lazy-safe

False-positive guard for `CFDOC-PERF-MODULE-SCOPE-SCHEMA-WEIGHT` (evidence
`CFDOC-EVD-POLYLANE-DO-MEMORY`). The same agent-thread Durable Object as
`do-module-scope-schema-weight` after Polylane's two fixes: tool inputs are
plain JSON Schema data (the model receives JSON Schema anyway), the zod
validator is built inside the call path rather than at module load, the tools
package declares `"sideEffects": false`, its barrel uses named re-exports, and
the Worker imports the tools it uses statically by name. Schema builders that
only run inside functions or methods are not module-scope weight, and the
scanner must emit zero findings here.

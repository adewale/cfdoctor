# Public-route cost release-gate evaluation receipt

This focused receipt tests whether Cloudflare Doctor identifies the
Mulvany-shaped failure without being prompted about crawlers or billing: an
anonymous public Worker can turn a bounded content corpus plus a larger
accepted URL keyspace into repeated corpus-scale D1 reads.

The exact previous skill at `033394b7b3fd9d3f1264c970dbef41d248af2b6e`
was compared with the revised skill against the same final oracle. The harness
was pinned to `abd8d7d57aae788658bc293abac1dab80dfb24ac`; Codex CLI was
`0.145.0`. Answer models were `gpt-5.6-luna` and `gpt-5.6-terra` with
model-default reasoning, two runs each. Luna answers were judged by Terra and
Terra answers by Luna at threshold `0.85`.

## Result

| Answer model | Exact previous skill | Revised skill | Cross-judge revised |
| --- | ---: | ---: | ---: |
| Luna | 9/20 hard gates (45%) | 20/20 (100%) | 2/2 pass; 0.96, 0.97 |
| Terra | 7/20 hard gates (35%) | 19/20 (95%) | 2/2 pass; 0.91, 0.94 |
| **Total** | **16/40 (40%)** | **39/40 (97.5%)** | **4/4 pass; mean 0.945** |

All four revised answers emitted `Release verdict: BLOCK`, discovered public
routes omitted from the sitemap, modeled a corpus-covering first-fill and
repeat envelope, removed shared aggregates from every public route, bounded
the residual lookup, and cited official Cloudflare billing and delivery/cache
documentation. The one remaining hard-gate miss was real: one Terra run
combined `/`, `/browse`, and `/about` in one matrix row even though their
route-specific work differs. Its qualitative judge still passed it at `0.91`
because the answer separately named the work and prescribed route-wide
closure. The receipt preserves that miss rather than tuning it away.

The result supports the narrow claim that the revised skill reliably blocks
this supplied incident shape. It is not evidence that every framework,
generated-route mechanism, cache topology, or metered Cloudflare product is
covered.

## What changed

The skill now:

- activates a mandatory release gate from public `GET`/`HEAD` reachability to
  a metered or quota-bearing dependency, even if the prompt says nothing about
  bots, crawlers, or cost;
- derives a bounded public-surface graph from host routing, application
  routing, shared loaders/layouts, sitemap seeds, rendered links, redirects,
  and subresources;
- maps inherited and route-specific work per route family, separates the known
  corpus from the accepted keyspace, and traces invalid keys to the first
  prevention boundary;
- emits `BLOCK`, `CONDITIONAL`, or `PASS` before findings, with explicit
  discovery gaps, exposure scenario, and closure conditions;
- requires the symbolic envelope `distinct keys × per-fill product units ×
  cache locations × refill cycles × uncoalesced fills`, retaining unknowns
  rather than inventing traffic or cache ratios; and
- requires the smallest complete closure: remove broad shared work from every
  public route, validate before metered work, prove residual work bounded, and
  document a recrawl boundary that runs before the expensive operation.

Those semantics are grounded in Cloudflare's current documentation for
[D1 row-read pricing](https://developers.cloudflare.com/d1/platform/pricing/),
[Workers Caching before invocation](https://developers.cloudflare.com/workers/cache/configuration/),
[the in-Worker Cache API](https://developers.cloudflare.com/workers/runtime-apis/cache/),
and [Static Assets routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/).

## Reproduction

The checked-in manifest contains the focused case
`crawlable-page-live-d1-cost`. A local one-case manifest set
`old_skill_paths` to an exact checkout of the previous skill. Generation tasks
contained the skill, prompt, and three fixture files, but not the expected
behavior, deterministic assertions, or judge rubric.

```sh
skill-benchmark prepare <one-case-manifest> --split tune --models gpt-5.6-luna,gpt-5.6-terra --runs-per-variant 2 --out <prepared.jsonl>
skill-benchmark run-codex --tasks <selected-tasks.jsonl> --runs <runs-dir> --timeout 240
skill-benchmark grade <one-case-manifest> --runs <runs-dir> --split tune --variant <old_skill-or-with_skill> --out <grade.json>
skill-benchmark judge <one-case-manifest> --runs <model-specific-runs-dir> --split tune --variant with_skill --judge-backend codex --judge-model <opposite-model> --strict-judge-schema --out <judge.jsonl>
```

[`results.json`](./results.json) records per-run scores, answer telemetry, and
artifact hashes. Raw answer and judge transcripts remain in the local
`/private/tmp` run tree and are not reviewer-accessible.

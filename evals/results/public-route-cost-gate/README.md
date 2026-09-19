# Public-route D1 cost-gate evaluation

This receipt tests one narrow claim: Cloudflare Doctor should stop a launch when anonymous, crawlable pages repeatedly execute broad live D1 work, even when the sitemap is small and the prompt does not mention bots or billing.

## Incident relationship

[Ian Mulvany's report](https://blog.mulvany.net/posts/ai-cloudflare-billing-and-hidden-assumptions) describes more than one million crawler requests reaching public pages and multiplying expensive D1 query shapes into roughly 67 billion rows read and about $48 of cost. The core fixture is deliberately Mulvany-shaped: public route families inherit a live aggregate, rendered links expose a detail family absent from the sitemap, and repeated requests retain their D1 multiplier.

It is not a replay of Mulvany's exact application. The report does not supply this fixture's Worker, route graph, schema, query plan, or cache configuration. The result therefore supports a conditional prevention claim: if equivalent pre-launch code were supplied to Cloudflare Doctor, both evaluated models now issue `BLOCK` and require the broad work to leave the request path. The skill is guidance; it cannot stop traffic unless someone runs the audit and acts on it.

Related first-hand reports support the same broader mechanism:

- [whatmedicaidpays](https://fullstacksveltekit.com/blog/cloudflare-d1-bill) reports shared layout queries repeatedly reading a large D1 table.
- [A 100,000-page Cloudflare site](https://zenn.dev/koizumiiiii/articles/9723730ae75e18) reports bot traffic multiplying D1 reads and moving regeneration work into another billed product.
- [Metacast](https://metacast.app/blog/engineering/postmortem-llm-bots-image-optimization) reports crawlers discovering public pages and triggering metered image work. It is analogous public-surface amplification, not D1 evidence.

Incident reports motivate the scenario. Current Cloudflare behavior and billing claims come from official documentation: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Workers Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/), [Static Assets binding](https://developers.cloudflare.com/workers/static-assets/binding/), and [Cache API](https://developers.cloudflare.com/workers/runtime-apis/cache/).

## Why a sitemap is insufficient

A sitemap is a discovery seed, not an inventory boundary. In the core fixture it names `/` and `/browse`, but the supplied code and rendered links also expose `/about`, `/abstract/:id`, `/sitemap.xml`, and a wildcard fallback. Several of those routes inherit D1 work before routing or rejection. Reviewing only sitemap URLs would miss both real pages and arbitrary 404 requests that can reach the same dependency.

The skill therefore builds a bounded public-surface graph from supplied host routing, router/framework artifacts, shared middleware/layouts/loaders, sitemaps, internal links, redirects, and separately requested resources. It does not crawl an unbounded live site. Each materially different route family gets its own dependency row, including zero-D1 and fallback paths.

## Method

The focused tune set contains four fixture-backed decisions:

1. `BLOCK` the Mulvany-shaped multi-route case.
2. `BLOCK` a single fixed `/` route whose repeated hits run a broad aggregate; URL cardinality is not required.
3. `PASS` a materialized aggregate plus measured indexed lookup, including a bounded valid-shaped miss.
4. `CONDITIONAL` when a normal lookup lacks the query plan and measured rows needed to distinguish bounded work from a scan.

Each answer has two deterministic gates that are reported separately: an output-contract check and a structural semantic oracle. The oracle parses the route matrix and verifies the verdict, public families, uncached cost equation, prevention boundary, plan/measurement calibration, and claim-to-official-source pairing. It is structural evidence, not proof that arbitrary prose is semantically correct. Negative regression tests specifically reject an uncached equation that collapses repeated requests to distinct keys, a fix that materializes only the dynamic detail route while leaving shared aggregates live, crawler controls presented as closure, Cache API presented as a pre-Worker boundary, and unsourced Workers Caching or Static Assets recommendations.

The before variant removes only the public-route cost gate from the same skill. Luna and Terra each ran every tune case once with model-default reasoning. All 16 before/after invocations completed successfully; no failed execution is counted as a behavioral miss. The harness is pinned to `abd8d7d57aae788658bc293abac1dab80dfb24ac`.

| Evidence layer | Gate removed | Final skill |
| --- | ---: | ---: |
| Valid executions | 8/8 | 8/8 |
| Output-contract checks | 0/8 | 8/8 |
| Structural semantic checks | 0/8 | 8/8 |
| Same-rubric qualitative judgments | 6/8 (mean 0.811) | 8/8 (mean 0.974) |

The qualitative result matters because the baseline can still answer the simpler fixed-route, safe-lookup, and missing-evidence cases. Its two failures are both models on the Mulvany-shaped core: they fail to map the full public graph or give a complete prevention boundary. Terra judged the before and after answers against the same per-case rubrics and 0.85 threshold. [`judgments.json`](judgments.json) preserves every compact verdict, score, and rationale for review. Both core final runs stayed below the optional 140,000-token efficiency ceiling; efficiency remains separate from correctness.

## Timeline regression scenario

The `holdout` manifest split also contains an off-sitemap `/timeline` link whose request handler runs `GROUP BY`/`COUNT` over a growing 80,000-entry D1 corpus. It requires explicit zero-D1 rows for the sitemap and wildcard fallback.

| Answer model | Format | Semantic | Qualitative |
| --- | ---: | ---: | ---: |
| Luna | 1/1 | 1/1 | 1/1 |
| Terra | 1/1 | 1/1 | 1/1 |

This is now described as a regression scenario, not a pristine unseen holdout. Its fixture and expected behavior were frozen for the final runs, but an earlier audit of this case exposed weaknesses that caused the semantic oracle to be hardened. That history makes it useful regression coverage without overstating its independence.

## Reproduce

From the repository root:

```bash
python3 scripts/focus_public_route_eval.py --split tune --out .public-route-tune.json
python3 scripts/focus_public_route_eval.py --split holdout --out .public-route-holdout.json

uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark validate .public-route-tune.json --strict-leakage --leakage-min-chars 1 --check-ablations
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark validate .public-route-holdout.json --strict-leakage --leakage-min-chars 1

uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark prepare .public-route-tune.json --split tune --models gpt-5.6-luna,gpt-5.6-terra \
  --include-ablations --ablation-dir /tmp/public-route-ablations --out /tmp/public-route-tasks.jsonl
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark prepare .public-route-holdout.json --split holdout --models gpt-5.6-luna,gpt-5.6-terra \
  --out /tmp/public-route-holdout-tasks.jsonl

# Keep the exact variants used in the receipt.
jq -c 'select(.variant == "with_skill" or .variant == "ablation:no-public-route-cost-gate")' \
  /tmp/public-route-tasks.jsonl > /tmp/public-route-comparison-tasks.jsonl
jq -c 'select(.variant == "with_skill")' \
  /tmp/public-route-holdout-tasks.jsonl > /tmp/public-route-holdout-current-tasks.jsonl

# Execute Luna and Terra. These commands call the configured Codex models.
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark run-codex --tasks /tmp/public-route-comparison-tasks.jsonl \
  --runs /tmp/public-route-tune-runs --timeout 600
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark run-codex --tasks /tmp/public-route-holdout-current-tasks.jsonl \
  --runs /tmp/public-route-holdout-runs --timeout 600

# Grade the output contract and structural semantic oracle separately by variant.
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark grade .public-route-tune.json --runs /tmp/public-route-tune-runs --split tune \
  --variant ablation:no-public-route-cost-gate --allow-scripts --write-grading-files \
  --out /tmp/public-route-baseline-grade.json
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark grade .public-route-tune.json --runs /tmp/public-route-tune-runs --split tune \
  --variant with_skill --allow-scripts --write-grading-files \
  --out /tmp/public-route-current-grade.json
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark grade .public-route-holdout.json --runs /tmp/public-route-holdout-runs --split holdout \
  --variant with_skill --allow-scripts --write-grading-files \
  --out /tmp/public-route-holdout-grade.json

# Apply the same per-case qualitative rubric to baseline and final tune answers.
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark judge .public-route-tune.json --runs /tmp/public-route-tune-runs --split tune \
  --variant ablation:no-public-route-cost-gate --judge-backend codex --judge-model gpt-5.6-terra \
  --strict-judge-schema --out /tmp/public-route-baseline-judge.jsonl \
  --transcripts /tmp/public-route-baseline-judge-transcripts
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark judge .public-route-tune.json --runs /tmp/public-route-tune-runs --split tune \
  --variant with_skill --judge-backend codex --judge-model gpt-5.6-terra \
  --strict-judge-schema --out /tmp/public-route-current-judge.jsonl \
  --transcripts /tmp/public-route-current-judge-transcripts
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark judge .public-route-holdout.json --runs /tmp/public-route-holdout-runs --split holdout \
  --variant with_skill --judge-backend codex --judge-model gpt-5.6-terra \
  --strict-judge-schema --out /tmp/public-route-holdout-judge.jsonl \
  --transcripts /tmp/public-route-holdout-judge-transcripts
```

The execution and judge commands require an authenticated Codex CLI with access to the named Luna and Terra models.

[`results.json`](results.json) records the per-case totals and SHA-256 hashes. To keep the PR reviewable, the checked-in raw artifacts are limited to both core before/after answers and both timeline-regression answers in [`artifacts/`](artifacts/); [`judgments.json`](judgments.json) records the reviewer-verifiable qualitative decisions. The remaining cases are reproducible from the fixtures, focused-manifest script, pinned harness, and semantic oracle in this PR.

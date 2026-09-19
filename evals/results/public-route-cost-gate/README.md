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

Each answer has two hard gates: an output-contract check and a structural semantic oracle. The oracle parses the route matrix and verifies the verdict, public families, uncached cost equation, prevention boundary, plan/measurement calibration, and claim-to-official-source pairing. Unit tests reject keyword stuffing, the wrong cost branch, Cache API presented as a pre-Worker boundary, and Workers Caching without the Workers pricing source.

The before variant removes only the public-route cost gate from the same skill. Luna and Terra each ran every tune case once with model-default reasoning. The harness is pinned to `abd8d7d57aae788658bc293abac1dab80dfb24ac`.

| Answer model | Gate removed | Final skill |
| --- | ---: | ---: |
| Luna | 0/8 hard checks | 8/8 |
| Terra | 0/8 hard checks | 8/8 |
| **Total** | **0/16** | **16/16** |

Terra's core final run exceeded the optional 140,000-token efficiency ceiling (200,143 total tokens), so the soft efficiency result is 1/2. No behavioral gate failed.

## Fresh holdout

After the skill wording was frozen, a replacement holdout introduced an off-sitemap `/timeline` link whose request handler runs `GROUP BY`/`COUNT` over a growing 80,000-entry D1 corpus. It also requires explicit zero-D1 rows for the sitemap and wildcard fallback.

| Answer model | Fresh holdout |
| --- | ---: |
| Luna | 2/2 hard checks |
| Terra | 2/2 hard checks |

The fixture and expected behavior did not drive another skill edit. After generation, the parser accepted “excluding” as a synonym for an already-present wildcard fallback row; the raw answer shows that the route was not missing. This changed neither the expected behavior nor the skill.

## Reproduce

From the repository root:

```bash
python3 scripts/focus_public_route_eval.py --split tune --out /tmp/public-route-tune.json
python3 scripts/focus_public_route_eval.py --split holdout --out /tmp/public-route-holdout.json

uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark validate /tmp/public-route-tune.json --strict-leakage --leakage-min-chars 1 --check-ablations

uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark prepare /tmp/public-route-tune.json --split tune --models gpt-5.6-luna,gpt-5.6-terra \
  --include-ablations --ablation-dir /tmp/public-route-ablations --out /tmp/public-route-tasks.jsonl

# Run the prepared with_skill and ablation:no-public-route-cost-gate rows, then:
uvx --from git+https://github.com/adewale/skill-eval-harness.git@abd8d7d57aae788658bc293abac1dab80dfb24ac \
  skill-benchmark grade /tmp/public-route-tune.json --runs <runs-dir> --split tune \
  --variant with_skill --allow-scripts --write-grading-files
```

[`results.json`](results.json) records the per-case totals and SHA-256 hashes. To keep the PR reviewable, the checked-in raw artifacts are limited to both core before/after answers and both fresh holdout answers in [`artifacts/`](artifacts/). The remaining cases are reproducible from the fixtures, focused-manifest script, pinned harness, and semantic oracle in this PR.

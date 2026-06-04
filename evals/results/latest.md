# Cloudflare Doctor trigger eval

Generated: 2026-06-04T01:21:42
Skill: `SKILL.md`
Cases: `evals/trigger-cases.json`

## Metrics

- Cases: 30
- Accuracy: 30/30 = 100.0%
- Trigger recall: 20/20 = 100.0%
- No-trigger specificity: 10/10 = 100.0%
- Description length: 447 chars
- Missing description term cases: 0

## Current description

> Audits Cloudflare projects for best-practice drift, wrong primitive/product choices, missed optimizations, product misconfiguration, security gaps, reliability risks, and cost footguns. Use when reviewing Workers, Pages, Wrangler, KV, D1, R2, Durable Objects, Queues, Workflows, Workers AI, AI Gateway, Vectorize, Images, Stream, Browser Run, CDN/cache, DNS, WAF, Access/Zero Trust, Cloudflare account settings, pricing/overages, or IaC decisions.

## Failures / gaps

None. Proxy trigger predictions match expected labels and all expected trigger terms are present in the description.

## Per-case results

| Case | Expected | Predicted | Pass | Category | Reasons |
|---|---:|---:|---:|---|---|
| direct-cloudflare-doctor | trigger | trigger | yes | direct invocation | product=\bcloudflare\b; intent=\bdoctor\b |
| audit-wrangler-config | trigger | trigger | yes | wrangler/config | product=\bcloudflare\b, \bwrangler\b; intent=\baudit\b, best[- ]practice |
| worker-cost-cpu | trigger | trigger | yes | workers cost | product=\bcloudflare\b; intent=\breview\b, \bcost\b, \bbill(?:ing)?\b |
| pages-preview-paid-services | trigger | trigger | yes | pages/preview cost | product=\bcloudflare\b, \bcloudflare\s+pages\b, \bpages\s+(preview\|functions?)\b; intent=\bcheck\b |
| kv-counter-primitive-fit | trigger | trigger | yes | primitive fit | product=\bcloudflare\b, \bcloudflare\s+kv\b; intent=wrong\s+primitive |
| d1-rows-read | trigger | trigger | yes | d1 cost/performance | product=\bd1\b; intent=\breview\b, \bcost\b |
| r2-no-egress-bill | trigger | trigger | yes | r2 cost | product=(?<!r2-)\br2\b; intent=\baudit\b, \bbill(?:ing)?\b |
| durable-objects-hibernation | trigger | trigger | yes | durable objects | product=\bdurable\s+objects?\b; intent=\binspect\b |
| queues-dlq-retry-storm | trigger | trigger | yes | queues reliability/cost | product=\bcloudflare\b, \bcloudflare\s+queues?\b; intent=\breview\b |
| workflows-retries | trigger | trigger | yes | workflows reliability/cost | product=\bcloudflare\b, \bcloudflare\s+workflows?\b; intent=\baudit\b |
| workers-ai-duplicate-generation | trigger | trigger | yes | workers ai cost | product=\bworkers?\s+ai\b; intent=\bfind\b, \bcost\b, \bfootguns?\b |
| ai-gateway-cache-rate-limit | trigger | trigger | yes | ai gateway | product=\bcloudflare\b, \bai\s+gateway\b; intent=\baudit\b |
| vectorize-dimensions | trigger | trigger | yes | vectorize cost | product=\bvectorize\b; intent=\breview\b, \bcost\b |
| images-variants | trigger | trigger | yes | images cost/cache | product=\bcloudflare\b, \bcloudflare\s+images?\b; intent=\baudit\b |
| stream-preload | trigger | trigger | yes | stream cost | product=\bcloudflare\b, \bcloudflare\s+stream\b; intent=\bcheck\b, \bcost\b, \brisks?\b |
| browser-run-sessions | trigger | trigger | yes | browser run cost | product=\bbrowser\s+run\b; intent=\baudit\b |
| cache-layer-map | trigger | trigger | yes | cache layering | product=\bcloudflare\b, \bai\s+gateway\b, (?<!r2-)\br2\b; intent=\bmap\b |
| waf-access-dns-security | trigger | trigger | yes | security/config | product=\bcloudflare\b, \baccess\s+polic(?:y\|ies)\b, \bcloudflare\s+dns\b; intent=\breview\b, misconfig |
| terraform-cloudflare | trigger | trigger | yes | iac/account | product=\bcloudflare\b; intent=\baudit\b |
| free-paid-overages | trigger | trigger | yes | pricing/overages | product=\bcloudflare\b; intent=\bcheck\b, \boverages?\b |
| aws-lambda-cost | no_trigger | no_trigger | yes | non-cloudflare cloud | intent=\baudit\b, \bcost\b, \bbill(?:ing)?\b |
| react-doctor | no_trigger | no_trigger | yes | other skill | intent=\bfind\b, \bdoctor\b |
| generic-dns | no_trigger | no_trigger | yes | generic education |  |
| cloudflare-status | no_trigger | no_trigger | yes | cloudflare but not project audit | product=\bcloudflare\b; intent=\bcheck\b; false_friend=public status page |
| r2d2-star-wars | no_trigger | no_trigger | yes | false friend | product=(?<!r2-)\br2\b; false_friend=\br2-d2\b |
| stream-video-generic | no_trigger | no_trigger | yes | generic media |  |
| browser-automation-generic | no_trigger | no_trigger | yes | generic browser automation |  |
| vector-search-generic | no_trigger | no_trigger | yes | generic vector education |  |
| cloudflare-brand-copy | no_trigger | no_trigger | yes | brand/reference only | product=\bcloudflare\b; false_friend=cloudflare-like style |
| queue-generic | no_trigger | no_trigger | yes | generic queue |  |

## Notes

- This is a deterministic proxy eval for trigger intent and description coverage, not a model-runtime proof.
- For model-based evals, run these same prompts in a harness that exposes this skill and judge whether Cloudflare Doctor loaded and produced the required audit scaffold.

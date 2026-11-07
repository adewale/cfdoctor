Dataflare audit regression results
5 November 2026

Scanner 0.5.0 passes 53/53 detection fixtures against the same inputs on which
the pinned 0.4.0 scanner passes 40/53. Both pass the 30 existing fixtures. The
23 new workload fixtures pass 23/23 with the candidate and 10/23 with baseline.
They are visible, synthetic regression cases derived from the audit, not held-out
evidence of generalization. receipt.json records each case and source hashes.

Baseline: 7eefbc7411b634d9a665f9f9240a761f0b2f4314.
Implementation: 6e05f6daa35b777859ac484cc1d825c7f14a40ee.
The later evidence commit does not change the installable scanner/skill files.

The baseline misses eleven newly required check IDs and hits four forbidden
check IDs in the precision fixture. It also misses the generated Pipelines
product in two generator fixtures. The candidate has no missing/forbidden check
or product assertions in this suite. The controls retain real literal credentials,
an imported Agents class, actual retry loops, Worker Node compatibility, scoped
binding names and bounded parameter/deletion paths.

The original Dataflare pin is fcd91359582f9f2d502844cbc7da52d15f5256b1. Its scan
changes from 43 leads (including four false high credential alarms) to 23 leads
(zero high/critical, fourteen medium, nine low). The same counts hold on the
separately fetched 0.6.3 revision, 689f4baecae918f498dbde903302daf10a57f48c.
Nine problem groups were confirmed or qualified by source review and local
probes. Remaining broad R2/SELECT-star/per-item-query leads are not counted as
additional defects. Raw lead counts alone are not a precision score.

The new product inventory adds optional Pipelines, Basin SQL and Basin Catalog
with provenance. Development, static, generated, Node/browser and test evidence
are separated; the excluded .glass/worker.js bundle is explicit. The source audit
does not establish that bundled code or deployed state matches the reviewed source.

Focused model forward checks

Two completed read-only Codex CLI runs received the frozen skill and raw source,
without the original audit findings or expected answers. They used the request
in forward-request.txt and the same Dataflare 0.6.3 input. The final frozen skill
matches the implementation byte-for-byte; receipt.json includes its file hashes.

The first candidate's report found the parameter/expansion/erasure paths and a
new custom-route problem: taking the final two hostname labels emits co.uk for
analytics.example.co.uk. It also claimed a 501-session erasure returns success
with one session remaining, overlooking the helper's 1,001-query maximum. That
success claim is unsupported under the documented Free/Paid query budgets.

The route case became a new bad/safe scanner pair. The deletion lead and skill
reference now require checking earlier invocation limits before asserting that
a success response is reachable. A fresh run against the final frozen skill
reported parameter overflow, accumulated replay expansion, duplicate counters
and the zone error; it left deletion as a qualified lead rather than repeating
the successful-erasure claim. The final source audit independently reproduces
the query-limit interruption with synthetic bindings.

forward-before.txt and forward-after.txt preserve those two candidate outputs,
with local source links rewritten to immutable public repository links. These
are candidate iterations, not an old-skill/no-skill comparison. The first run
informed the changes, so neither is presented as a held-out score. Four selected
findings are not an exhaustive audit. There is no claimed general model-quality
or efficiency improvement from these two samples.

The completed runs took 116.60s and 105.09s. CLI usage was 346,639/468,968 input
tokens, of which 302,080/415,744 were cached, and 5,573/4,425 output tokens.
These are cumulative CLI measurements; cached input is already included in input.
Dollar cost and full usage for failed/incomplete attempts are unavailable. Two
independent-agent attempts hit capacity errors, and earlier CLI attempts failed
to initialize or ended without a completed answer. Those attempts are unscored.

Verification

- npm test: 136 unit tests, 43/43 trigger cases, 53/53 detection fixtures,
  clean self-scan, coverage matrix, evidence ledger, link policy and install
  boundary pass.
- npm run eval:validate: the exact pinned harness passes strict leakage,
  ablation materialization and manifest audit. Patch line offsets were updated
  after adding the skill guidance; no ablation behavior was removed.
- Ruff and git diff --check pass.
- The first test-only commit reproduced the gaps: 9 failures and 4 errors among
  its initial 16 new tests. The final workload test module has 25 tests. The
  paired old scanner run reproduces the new fixture failures without reverting
  the working branch.
- The installed skill-creator quick validator rejects the pre-existing
  compatibility frontmatter key on both baseline and candidate. The repository's
  trigger/frontmatter/install checks pass; that supported metadata was preserved.

Reproduce

Check out baseline 7eefbc7411b634d9a665f9f9240a761f0b2f4314 in a separate directory.
From the candidate repository, run:

  python3 scripts/eval_detection.py --scanner /path/to/baseline/skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py --out-dir /tmp/cfdoctor-before
  python3 scripts/eval_detection.py --out-dir /tmp/cfdoctor-after
  npm test
  npm run eval:validate

Clone Dataflare at 689f4baecae918f498dbde903302daf10a57f48c and run the candidate
scanner on that checkout. Read docs/audits/dataflare-2026-11-05.txt for source
evidence, local probe results, fixes and verification steps for the nine issues.
No Cloudflare account or deployed application was accessed in these checks.

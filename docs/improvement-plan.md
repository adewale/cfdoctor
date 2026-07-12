# Improvement plan: ranked by verifiability and likelihood of success

Date: 2026-06-09. This plan orders the skill-improvement recommendations by how
deterministically each change can be verified and how likely it is to deliver
its intended benefit. Items are implemented in this order. Every item records
its risks and downsides, because each change can also make the skill worse if
the risk is ignored.

## Status (through 2026-07-11)

1. Scanner check IDs + JSON output — **done** (scanner 0.3.5; 60-check registry).
2. Fixture-based detection evals — **done** (25 fixtures, including calibrated false-negative and near-miss controls).
3. Coverage matrix + consistency checker — **done** (CI-enforced).
4. Link verification + archive fallbacks — **done** (initial run; periodic
   re-runs tracked in `TODO.md`).
5. SKILL.md reference routing — **done deterministically** (trigger eval,
   contract markers); model-graded confirmation still pending (`TODO.md`).
6. Holdout/holdback scaffolding — **done**; private gitignored cases were scored exactly once for the release guard and only sanitized aggregates were retained.
7. Deployed-state evidence — **Wrangler-first wrapper and approved live validation complete**.

Remaining work lives in [`TODO.md`](../TODO.md).

## Ranking criteria

- **Verifiability**: can a command prove the change works (exit code, diff,
  eval pass rate), or does verification require model judgment, live accounts,
  or network state we do not control?
- **Likelihood of success**: does the change have a clear mechanism for
  improving audit quality, and does it depend on anything outside this repo?

## 1. Stable check IDs + JSON output in the static scanner

- **Verifiability: high.** `--list-checks` and `--json` output are asserted by
  running the scanner; the self-scan must stay at 0 findings; `py_compile`
  must pass.
- **Likelihood of success: high.** The war-story checklist already names the
  check IDs; the scanner already emits the findings. This is plumbing, and it
  is the prerequisite for fixture evals (#2) and the coverage matrix (#3).
- **Risks / downsides:**
  - Renaming or re-mapping IDs later breaks consumers and baselines; IDs are
    a public contract from the first release. Mitigation: registry is the
    single source of truth, version the scanner, never reuse a retired ID.
  - JSON output invites people to treat scanner leads as proof. Mitigation:
    the JSON document and docs keep the "leads, not proof" framing.
  - An unregistered-ID guard that raises at scan time turns a metadata bug
    into a runtime failure. Accepted: failing loudly is better than emitting
    findings that downstream tooling cannot attribute.

## 2. Fixture-based detection evals

- **Verifiability: high.** Each known-bad fixture has an expected-findings
  manifest keyed by check ID; a deterministic runner asserts expected IDs are
  found and (on the clean fixture) that nothing is found.
- **Likelihood of success: high.** Converts the war-story research corpus into
  a regression suite. Detection coverage stops being an untested claim.
- **Risks / downsides:**
  - Fixtures overfit: the scanner can be tuned to pass fixtures while missing
    real-world variants. Mitigation: fixtures are derived from documented war
    stories, not from the scanner's regexes; keep them small and idiomatic.
  - Known-bad fixtures inside the repo pollute the self-scan (this bit us
    before — see lessons-learned). Mitigation: the self-scan excludes
    `evals/fixtures` via the scanner's `--exclude` flag; CI asserts both the
    excluded self-scan and the fixture detections.
  - Clean-fixture false-positive checks can rot as new checks are added.
    Mitigation: the runner fails when the clean fixture trips any check, which
    forces a conscious decision per new check.

## 3. Checklist → scanner coverage matrix

- **Verifiability: high, with a consistency checker.** A script cross-checks
  the matrix against `--list-checks`, so the doc cannot silently drift.
- **Likelihood of success: high.** Makes the research-vs-implementation gap
  visible instead of implicit, and gives contributors a worklist.
- **Risks / downsides:**
  - A matrix without enforcement is worse than none (false confidence).
    Mitigation: the consistency checker runs in CI.
  - "Covered by scanner" can be misread as "fully detected". Mitigation: the
    matrix distinguishes `scanner-lead` from `skill-prompt-only` and
    `not-implemented`; scanner coverage means a heuristic lead exists, not
    proof.

## 4. Link verification + archive fallbacks

- **Verifiability: medium-high.** The checker runs now and produces a report,
  but results depend on network state, bot-blocking, and rate limits.
- **Likelihood of success: high for the goal** (knowing which citations are
  alive, having archive fallbacks), **as long as it never hard-gates CI**.
- **Risks / downsides:**
  - Network-dependent CI is flaky CI. Mitigation: the checker exits 0 unless
    `--strict` is passed; CI does not run it on every push.
  - Bot-blocked domains (Reddit, Medium, HN, LinkedIn) cannot be verified
    automatically; calling them "dead" would prompt bad deletions.
    Mitigation: they are classified `unverifiable-automated` and flagged for
    manual review.
  - Archive links can be fabricated by tooling that guesses URLs. Mitigation:
    only archive URLs that were actually resolved during the run are written
    into the docs; absence is recorded explicitly.
  - Annotations add noise to research files. Accepted: provenance integrity
    is the skill's core promise, so the noise pays for itself.

## 5. SKILL.md reference routing (reduce mandatory context load)

- **Verifiability: medium.** The trigger eval and contract-marker checks still
  pass deterministically, but the real question — do audits stay as good with
  less mandatory reading — needs model-graded evals (#6) to answer.
- **Likelihood of success: medium-high.** Reading ~900 lines of references
  before every audit dilutes context; routing by detected product keeps depth
  where it is relevant.
- **Risks / downsides:**
  - The agent may skip a reference that was actually relevant, missing
    findings. This is the main regression risk of this whole plan.
    Mitigation: the playbook and provenance rules stay mandatory; routing
    rules are explicit ("if Durable Objects detected, read X"); the war-story
    checklist remains mandatory for cost-focused audits.
  - Conditional instructions are harder for models to follow than
    unconditional ones. Mitigation: routing is a short table, not prose.

## 6. Holdout/holdback model-graded eval scaffolding

- **Correction (updated 2026-07-11):** the public manifest now defines 37 cases across `tune`/`holdout`/`holdback` splits. Private prompt/answer assets remain gitignored. One holdout and one holdback were populated in the local release environment, scored exactly once, and retained only as a sanitized 2/2-pass aggregate plus hashes; they must not become a retuning set. Visible tune cases remain tied to deterministic fixture and semantic oracles where possible.
- **Verifiability: low-medium.** Case structure and JSON shape are
  verifiable; grading quality still requires running the external
  skill-eval-harness with a model.
- **Risks / downsides:**
  - Unused eval scaffolding rots and misleads contributors about coverage.
    Mitigation: CI validates JSON shape only; the harness docs state what
    requires a model run.
  - Fixture-backed tune cases are public, so models can memorize them; the
    gitignored holdout/holdback splits remain the contamination guard.

## 7. Wrangler-first deployed-state snapshot — complete

- **Verifiability: high for the supported Worker/Pages scope.** A purpose-built
  fake Wrangler proves command allowlisting, approval/plan gates,
  active-version expansion, private file permissions, Git-worktree refusal,
  metadata-only-by-default behavior, opt-in downloads, and manifest hashes. Approved live runs against
  `readability-worker`, `atlas`, and `keyboardia-staging` proved the Worker,
  Pages, and Assets metadata-only paths with Wrangler 4.71.0, 4.94.0, and 4.53.0.
- **Likelihood of success: high for Workers/Pages.** Wrangler already owns
  authentication profiles and current API normalization. `init --from-dash`,
  Pages `download config`, deployment status, and version view expose much of
  the effective Worker/Pages state without a custom API/token layer.
- **Decision:** use `scripts/capture_wrangler_snapshot.py` as the first account
  evidence path. It requires an existing pinned Wrangler binary, static plan
  and dynamic version-command-shape review, explicit authenticated-read approval,
  and private output outside Git. Metadata-only is the default; source/config
  download requires `--include-source-config`. The default is supported by the
  fleet review: 16 of 24 deployable configs used Workers Static Assets, which
  the current direct Worker importer cannot clone.
  Do not build a universal collector. Add targeted read-only API evidence only
  when a concrete DNS/WAF/Access/cache/analytics/billing hypothesis remains
  unresolved after a real Wrangler snapshot.

## Cross-cutting risks

- **CI surface grows.** Every new gate is a new way for unrelated PRs to fail.
  Mitigation: only deterministic, offline checks gate CI (scanner self-scan,
  fixture evals, coverage consistency, JSON shape); network checks are opt-in.
- **More moving parts to keep in sync.** The output contract, eval
  assertions, fixtures, and matrix must move together (lessons-learned #1).
  The consistency checker and fixture runner exist to catch exactly this.
- **Scanner authority creep.** As the scanner gains IDs, JSON, and evals, it
  starts to look like the product. It is still a triage layer; the audit
  workflow with current-docs verification remains the Doctor.

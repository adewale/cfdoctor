#!/usr/bin/env python3
"""Structural fixture-backed output oracle for shared Skill Eval Harness assertions."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CORE_MARKERS = [
    "Scope inspected:",
    "Scope not inspected:",
    "Docs refreshed:",
]
FINDING_FIELDS = [
    "- Category:",
    "- Evidence:",
    "- Why it matters:",
    "- Fix:",
    "- Cost / trade-off:",
    "- Verify:",
    "- Source basis:",
    "- Confidence:",
]

SPECS = {
    "round3-fixture-dashboard-claim": {
        "all": ["README.md", "wrangler.toml"],
        "any": [["not inspected", "cannot inspect", "no dashboard access", "account state"]],
        "forbid": [r"(?im)^\s*(?:[-*#>_]+\s*)?(?:Finding:\s*)?Cache Reserve\s+(?:is|was)\s+(?:definitely\s+)?(?:enabled|disabled)"],
        "require_core": True,
    },
    "detection-fixture-runaway-self-fetch": {
        "all": ["Cost / trade-off", "Source basis", "Scope not inspected"],
        "finding_any": [
            ["self-fetch", "fetches its own", "re-enqueue", "requeue", "recursive"],
            ["dead-letter", "dead letter", "DLQ", "max_retries", "retry bound"],
        ],
        "require_core": True,
        "require_complete_finding": True,
    },
    "pos-do-stub-cycle-rows-read-bill": {
        "all": [
            "wrangler.jsonc",
            "index.js",
            "DO-STUB-CALL-CYCLE",
            "SessionCoordinator",
            "TaskRunner",
            "Evidence:",
            "Why it matters:",
            "Fix:",
            "Cost / trade-off:",
            "Verify:",
            "Source basis:",
            "Confidence:",
        ],
        "any": [
            ["cycle", "loop", "re-trigger", "ping-pong", "call each other"],
            ["rows read", "storage rows", "SQLite"],
            ["kill switch", "hop budget", "depth budget", "depth limit", "idempotency"],
        ],
        "require_core": True,
    },
    "detection-fixture-clean-baseline-precision": {
        "any": [["not inspected", "cannot inspect", "no dashboard access"]],
        "require_core": True,
        "allow_no_findings": True,
        "max_findings": 0,
    },
    "detection-fixture-jsonc-trailing-commas": {
        "all": ["wrangler.jsonc"],
        "finding_any": [["broad route", "catchall", "wildcard route", "*/*"]],
        "forbid": [r"(?i)(unparseable|could not parse|invalid JSONC)"],
        "require_core": True,
        "require_complete_finding": True,
    },
    "detection-fixture-queue-dlq-safe": {
        "all": ["wrangler.jsonc"],
        "any": [
            ["DLQ is configured", "configured DLQ", "dead_letter_queue"],
            ["max_retries is 3", "max_retries: 3", "max_retries\": 3"],
            ["processes before ack", "process-before-ack", "before `message.ack()`", "before acking", "acks only after", "ack only after", "`ack()`s after", "only `ack()`s after"],
        ],
        "require_core": True,
        "allow_no_findings": True,
        "max_findings": 0,
    },
    "detection-fixture-queue-dashboard-ambiguous": {
        "evidence_request_any": [["dashboard-managed", "dashboard settings", "consumer config", "retry/DLQ settings"]],
        "forbid": [r"(?i)(confirmed|definitely) (?:that )?(?:there is )?no (?:DLQ|dead[- ]letter queue)"],
        "require_core": True,
    },
    "wrangler-snapshot-worker-reconciliation": {
        "patterns": [
            r"(?is)(?:two|2).{0,80}(?:active|traffic-bearing).{0,80}versions?",
            r"(?is)(?:(?:only|just).{0,100}(?:versions?[- ]view|version metadata).{0,100}(?:supplied|provided|available)|(?:supplied|provided|available).{0,100}(?:versions?[- ]view|version metadata).{0,260}(?:for (?:that|this) version only|only for|matches.{0,80}(?:25%|1000(?:…|\.\.\.)0000)|specific.{0,80}(?:25%|1000(?:…|\.\.\.)0000)))",
            r"(?is)(?:(?:missing|not supplied|not provided|cannot reconcile).{0,120}(?:second|other|75%|20000000-0000-0000-0000-000000000000)|(?:second|other|75%|20000000-0000-0000-0000-000000000000).{0,120}(?:missing|not supplied|not provided|cannot reconcile))",
        ],
        "forbid": [
            r"(?i)(?:only|sole) active version (?:is|was) 10000000-0000-0000-0000-000000000000",
            r"(?im)^(?!.*(?:cannot|does not|not supplied|only|for (?:the )?(?:supplied )?version)).{0,80}(?:the (?:deployed )?Worker|all active versions|the deployment).{0,50}(?:has|uses).{0,80}(?:KV|50 ?ms|CPU|compatibility)",
            r"10000000-0000-0000-0000-000000000000",
            r"20000000-0000-0000-0000-000000000000",
        ],
    },
    "wrangler-snapshot-pages-reconciliation": {
        "patterns": [
            r"(?is)Pages.{0,100}(?:deployment row|deployment list|deployment record|deployment output)",
            r"(?is)(?:cannot|does not|not supplied|not inspected|insufficient).{0,120}(?:prove|show|determine|support|evidence).{0,800}(?:binding|runtime|active version|config|repository intent)",
        ],
        "forbid": [
            r"(?i)confirmed (?:Worker )?(?:CPU limit|binding|active version)",
            r"(?im)^(?!.*(?:cannot|does not|not supplied|no evidence|insufficient)).{0,100}(?:Pages (?:row|deployment|list)).{0,100}(?:proves|shows|indicates|suggests).{0,100}(?:KV|binding|CPU|runtime limit|active version|config)",
        ],
    },
    "wrangler-snapshot-plan-approval": {
        "forbid_package_runner_recommendation": True,
    },
    "wrangler-snapshot-assets-metadata-only": {
        "forbid_package_runner_recommendation": True,
    },
}

PUBLIC_GATE_SPECS = {
    "crawlable-page-live-d1-cost": {
        "verdict": "BLOCK",
        "routes": ["/", "/browse", "/abstract/", "/about", "/sitemap.xml", "<fallback>"],
        "mode": "uncached",
    },
    "public-route-fixed-scan": {
        "verdict": "BLOCK",
        "routes": ["/"],
        "mode": "uncached",
    },
    "public-route-safe-bounded-lookup": {
        "verdict": "PASS",
        "routes": ["/", "/article/"],
        "mode": "bounded",
    },
    "public-route-missing-plan": {
        "verdict": "CONDITIONAL",
        "routes": ["/category/"],
        "mode": "unknown",
    },
    "public-route-timeline-holdout": {
        "verdict": "BLOCK",
        "routes": ["/", "/timeline", "/sitemap.xml", "<fallback>"],
        "mode": "uncached",
    },
}

PRIVATE_D1_CASES = {
    "private-d1-polling-growth",
    "private-d1-deep-offset",
    "private-d1-repeated-sync",
    "private-d1-indexed-writes",
    "private-d1-safe-controls",
}

PACKAGE_RUNNER_RE = re.compile(r"(?i)\b(?:npx|npm\s+exec|pnpm\s+dlx|bunx)\b")
PACKAGE_RUNNER_NEGATION_RE = re.compile(
    r"(?is)(?:do\s+not|don't|never|avoid|must\s+not|not\s+use|without|forbid(?:den)?|instead\s+of|rather\s+than|not)\b"
)
PACKAGE_RUNNER_POST_NEGATION_RE = re.compile(
    r"(?is)^.{0,50}(?:(?:should|must|may)\s+not\s+(?:be\s+)?(?:used|recommended|invoked)|is\s+(?:forbidden|not\s+allowed))"
)


def package_runner_recommendations(text: str) -> list[str]:
    """Return package-runner mentions that are not clearly prohibited in their sentence."""
    unsafe: list[str] = []
    for match in PACKAGE_RUNNER_RE.finditer(text):
        starts = [text.rfind(delimiter, 0, match.start()) for delimiter in ("\n", ".", "!", "?")]
        sentence_start = max(starts) + 1
        ends = [pos for delimiter in ("\n", ".", "!", "?") if (pos := text.find(delimiter, match.end())) >= 0]
        sentence_end = min(ends) if ends else len(text)
        before = text[sentence_start:match.start()]
        after = text[match.end():sentence_end]
        if not PACKAGE_RUNNER_NEGATION_RE.search(before) and not PACKAGE_RUNNER_POST_NEGATION_RE.search(after):
            sentence = text[sentence_start:sentence_end].strip()
            unsafe.append(sentence or match.group(0))
    return unsafe


def contains(text: str, needle: str) -> bool:
    return needle.casefold() in text.casefold()


def finding_blocks(text: str) -> list[str]:
    # Heading depth and emphasis do not change the finding-card contract.
    normalized = text.replace("**", "").replace("__", "")
    return re.findall(
        r"(?ims)^#{1,6}\s+Severity:.*?(?=^#{1,6}\s+Severity:|^#{1,2}\s+(?!Severity:)|\Z)",
        normalized,
    )


def route_cell_matches(row: str, route: str) -> bool:
    cell = row.split("|")[1].replace("`", "").strip().casefold()
    if route == "<fallback>":
        return any(term in cell for term in ("fallback", "other path", "unknown path", "excluding", "404"))
    if route == "/":
        return cell == "/" or bool(re.search(r"(?:^|\s)/(?:\s|$|\()", cell)) or bool(re.search(r"[a-z0-9.-]+/$", cell))
    return route.casefold() in cell


def labelled_section(text: str, label: str) -> str:
    match = re.search(
        rf"(?ims)^\s*{re.escape(label)}\s*(.*?)(?=^\s*(?:Discovery gaps:|Exposure scenario:|Closure conditions:|### Severity:|## )|\Z)",
        text,
    )
    return match.group(1).strip() if match else ""


def has_number(text: str, expected: int) -> bool:
    """Accept ordinary numeric formatting, including 50,000 / 50k / 0.05 million."""
    if expected == 0 and re.search(r"\bzero\b", text, re.IGNORECASE):
        return True
    scales = {"k": 1_000, "thousand": 1_000, "m": 1_000_000, "million": 1_000_000,
              "b": 1_000_000_000, "billion": 1_000_000_000}
    for match in re.finditer(r"\b(\d[\d,_]*(?:\.\d+)?)\s*(thousand|million|billion|[kmb])?\b", text, re.IGNORECASE):
        number = float(match.group(1).replace(",", "").replace("_", ""))
        if number * scales.get((match.group(2) or "").casefold(), 1) == expected:
            return True
    return False


def positive_claims(text: str, pattern: str) -> list[str]:
    """Guard a few known contradictory diagnoses, allowing explicit prohibitions/caveats.

    This is intentionally a limited deterministic regression guard, not a claim that
    arbitrary natural-language causality can be decided without the judge assertion.
    """
    clauses = re.split(r"(?<=[.!?;])\s+|\n+", text)
    claims: list[str] = []
    for clause in clauses:
        for match in re.finditer(pattern, clause, re.IGNORECASE):
            # Scope negation to the claim's prefix, not any unrelated later fact
            # ("Bots caused the bill despite no public traffic" is still a claim).
            prefix = clause[max(0, match.start() - 140):match.start()]
            caveat = re.search(
                r"(?i)\b(?:do not|don't|never|avoid|must not|cannot|not|wrong to|incorrect to|reject|no evidence(?: that| of)?|no proof(?: that| of)?|no)\s+(?:[a-z-]+\s+){0,5}$",
                prefix,
            )
            shared_caveat = re.search(
                r"(?i)(?:not evidence of|no evidence of|not a|not an)[^.;\n]{0,90}(?:missing|absent).{0,30}index.{0,15}(?:or|and)\s*$",
                prefix,
            )
            negated_verb = re.search(r"(?i)\b(?:did not|does not|do not|cannot|could not|never)\s+(?:cause|explain|drive|prove|add|cost)", match.group(0))
            if not caveat and not shared_caveat and not negated_verb:
                claims.append(clause)
                break
    return claims


def private_d1_failures(case_id: str, text: str) -> tuple[list[str], int]:
    """Check the supplied synthetic evidence and accounting relationships.

    Passing is structural/fixture evidence only; model quality and whether a fix is
    appropriate still need the paired run and qualitative-review assertion.
    """
    failures: list[str] = []
    checks = 0

    def check(ok: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(message)

    plain = text.replace("`", "").replace("**", "")
    for marker in CORE_MARKERS:
        check(contains(plain, marker), f"missing core audit marker: {marker!r}")
    check(bool(re.search(r"(?im)^\s*(?:#+\s*)?Cost paths:\s*$", plain)), "missing Cost paths: evidence block")
    table = [line.strip() for line in plain.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
    header = next((line for line in table if "frequency" in line.casefold() and "queries" in line.casefold()), "")
    columns = ("path", "trigger", "frequency", "window", "queries", "execution", "rows read", "rows written", "evidence", "unknowns", "first enforced bound")
    check(bool(header) and all(column in header.casefold() for column in columns), "cost-path table is missing required accounting columns")
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in table
            if line != header and not re.fullmatch(r"[|:\- ]+", line)]
    rows = [row for row in rows if len(row) == 7]
    check(bool(rows), "cost-path table has no seven-column evidence rows")
    check(all(row[6] for row in rows), "cost path lacks an enforced-bound statement (or explicit unknown)")
    check("developers.cloudflare.com/d1/platform/pricing" in plain.casefold(), "missing directly relevant official D1 pricing source")
    check(bool(re.search(r"(?i)synthetic", plain)), "supplied synthetic measurements are not identified as synthetic")
    sample_context = re.search(r"(?i)sample|measur|synthetic|projection", plain)
    bound_caveat = re.search(
        r"(?i)(?:not|cannot|do not|does not)[^.\n;]{0,90}(?:guarantee|bounds?|ceilings?|maxim(?:um|a)|worst.case)|(?:future|growth)[^.\n;]{0,50}unknown",
        plain,
    )
    check(bool(sample_context and bound_caveat), "sampled units must not be presented as a proven future worst-case bound")
    check(bool(re.search(r"(?is)(?:invoice|historical bill|account.{0,30}(?:usage|allowance)|billing window).{0,120}(?:unknown|not supplied|not inspected|cannot|unverified)|(?:unknown|not supplied|not inspected|cannot|unverified).{0,120}(?:invoice|historical bill|account.{0,30}(?:usage|allowance)|billing window)", plain)), "missing limitation on historical bill/account attribution")
    check(not positive_claims(plain, r"(?:bots?|crawlers?).{0,60}(?:caused|explain|driv|responsible)|(?:caused|driven).{0,40}(?:bots?|crawlers?)"), "private workload falsely attributed to bots/crawlers")
    check(not positive_claims(plain, r"(?:confirmed|proves?|caused|explains?).{0,80}(?:\$500|historical bill|invoice)"), "synthetic fixture incorrectly proves a historical invoice")
    check(not re.search(r"(?im)^\s*Release verdict:", plain), "private-only fixture must not invent a public-route release verdict")

    complete = [block for block in finding_blocks(text) if all(contains(block, field) for field in FINDING_FIELDS)]
    safe = case_id == "private-d1-safe-controls"
    check(not finding_blocks(text) if safe else bool(complete), "safe controls must have no finding cards" if safe else "no structurally complete evidence-backed finding")

    def path_row(pattern: str) -> list[str]:
        return next((row for row in rows if re.search(pattern, row[0], re.IGNORECASE)), [""] * 7)

    def numbers_in_row(row: list[str], frequency: tuple[int, ...] | None, queries: int, reads: int, writes: int) -> None:
        if frequency is not None:
            check(any(has_number(row[1], value) for value in frequency), "path frequency/window does not preserve the evidenced execution multiplier")
        check(has_number(row[2], queries), "path queries/execution does not preserve the evidenced query multiplier")
        check(has_number(row[3], reads), "path rows-read/query does not preserve the supplied sample")
        check(has_number(row[4], writes), "path rows-written/query does not preserve the supplied sample")

    def two_query_shapes(candidates: list[list[str]], *, admissions: bool) -> None:
        """Accept a combined two-query row or two one-query rows with shared frequency.

        Zero-query rejection paths do not contribute another SQL shape. A later
        row may inherit the preceding group's evidenced frequency explicitly.
        """
        query_rows = [row for row in candidates if has_number(row[2], 1) or has_number(row[2], 2)]
        combined = next((row for row in query_rows if has_number(row[2], 2)), None)
        chosen = [combined] if combined else query_rows
        check(bool(combined) or len(query_rows) == 2, "two-query accounting must retain both query shapes")
        inherited_frequency = False
        for row in chosen:
            explicit_frequency = (has_number(row[1], 60) if admissions
                                  else bool(re.search(r"(?i)unknown|not supplied|not measured|unavailable", row[1])))
            shares_frequency = bool(re.search(r"(?i)(?:same|shared|above).{0,75}(?:admission|invocation|run|request|session|manual)|(?:admission|invocation).{0,75}(?:same|above)", row[1]))
            check(explicit_frequency or (inherited_frequency and shares_frequency),
                  "query shape must preserve its admission bound or unknown invocation frequency")
            inherited_frequency = inherited_frequency or explicit_frequency
            numbers_in_row(row, None, 2 if combined else 1, 1, 0)

    if case_id == "private-d1-polling-growth":
        row = path_row(r"poll|/notes|dashboard")
        numbers_in_row(row, (10, 360), 1, 50_000, 0)
        check(bool(re.search(r"(?i)SCAN\s+notes", plain)), "polling diagnosis lacks the supplied SCAN notes plan")
        check(has_number(plain, 360) and has_number(plain, 18_000_000), "missing 360 polls/active-hour × 50,000 sampled reads = 18 million read scenario")
        unknown_duration = r"(?:active.{0,20}(?:hours?|duration|time)|total.{0,20}(?:polls?|executions?)|actual executions|monthly.{0,20}(?:usage|reads?))"
        check(bool(re.search(rf"(?is){unknown_duration}.{{0,180}}(?:unknown|unmeasured|not supplied)|(?:unknown|unmeasured|not supplied).{{0,180}}{unknown_duration}", plain)), "private polling must leave active duration/total executions unknown")
        check(bool(re.search(r"(?is)(?:COUNT|SELECT\s*\*).{0,180}(?:bounded|primary.key|single.row|one.row)|(?:bounded|primary.key|single.row|one.row).{0,180}(?:COUNT|SELECT\s*\*)", plain)), "safe SQL controls are not distinguished from the evidenced scan")
        diagnostics = [row for row in rows if re.search(r"diagnostic|manual", row[0], re.IGNORECASE)]
        two_query_shapes(diagnostics, admissions=False)
        check(bool(re.search(r"(?is)(?:index|materializ|precomput|change.{0,20}(?:query|poll))", "\n".join(complete))), "polling finding lacks a query/work reduction and verification path")
    elif case_id == "private-d1-deep-offset":
        # A shallow cohort may precede the deep-page cohort. Choose by its
        # evidenced unit, rather than assuming the first route row is the deep one.
        row = next((row for row in rows if has_number(row[3], 10_020)), [""] * 7)
        numbers_in_row(row, None, 1, 10_020, 0)
        check(bool(re.search(r"(?i)unknown|not supplied|not measured|unavailable", row[1])), "OFFSET frequency must remain unknown rather than inferred from user count")
        index_identity = (contains(plain, "archive_owner_created_id")
                          or (contains(plain, "owner_id") and contains(plain, "created_at")
                              and bool(re.search(r"(?i)\bid\b", plain)) and contains(plain, "DESC")))
        check(index_identity and bool(re.search(r"(?i)covering.index", plain)), "OFFSET diagnosis must preserve the existing covering index or its evidenced column order")
        check(has_number(plain, 10_000) and has_number(plain, 20), "missing shallow/deep OFFSET and returned-row comparison")
        check(bool(re.search(r"(?i)keyset|seek.{0,20}pagin|cursor", "\n".join(complete))), "deep OFFSET fix must address skipped work rather than prescribe a missing index")
        check(not positive_claims(plain, r"(?:missing|absent|add (?:an?|the)).{0,40}index|full.table.scan|SCAN\s+notes"), "deep OFFSET fixture incorrectly diagnosed as a missing index/full table scan")
        check(bool(re.search(r"(?is)(?:LIMIT|returned).{0,100}(?:not.{0,40}(?:read|scan|bound)|only.{0,30}(?:return|response))|(?:read|scan).{0,80}(?:exceed|greater|despite).{0,80}(?:LIMIT|returned)", plain)), "LIMIT/returned rows are incorrectly treated as a read bound")
    elif case_id == "private-d1-repeated-sync":
        relevant = [row for row in rows if re.search(r"sync|cron|DELETE|INSERT", row[0], re.IGNORECASE)]
        joined = " ".join(" ".join(row) for row in relevant)
        check(bool(relevant) and (has_number(" ".join(row[1] for row in relevant), 5) or has_number(" ".join(row[1] for row in relevant), 288)) and has_number(plain, 288), "sync cadence must retain five minutes / 288 scheduled runs per day")
        check((has_number(joined, 1001) or (has_number(joined, 1000) and has_number(joined, 1))), "sync accounting omits DELETE plus 1,000 inserts")
        check(has_number(" ".join(row[4] for row in relevant), 1000) and has_number(" ".join(row[4] for row in relevant), 1), "mixed DELETE/INSERT write terms must remain separate")
        check(bool(relevant) and all(has_number(row[3], 0) for row in relevant), "sync read terms must preserve separately supplied zero-read samples")
        check(has_number(plain, 2000) and has_number(plain, 576_000), "sync write scenario must retain 2,000 writes/run × 288 = 576,000/day")
        check(bool(re.search(r"(?is)(?:no.change|unchanged|identical).{0,140}(?:replace|rewrit|DELETE|INSERT)|(?:replace|rewrit|DELETE|INSERT).{0,140}(?:no.change|unchanged|identical)", plain)), "sync diagnosis misses repeated replacement of unchanged rows")
        check(bool(re.search(r"(?i)delta|incremental|skip.{0,35}(?:unchanged|identical)|change.{0,20}(?:detect|track|hash)", "\n".join(complete))), "sync fix lacks change-aware prevention")
        check(bool(re.search(r"(?i)(?:retries|overlap).{0,80}(?:unknown|not supplied|not bounded)|(?:unknown|not supplied|not bounded).{0,80}(?:retries|overlap)", plain)), "scheduled execution arithmetic must not invent a retry/overlap bound")
    elif case_id == "private-d1-indexed-writes":
        row = path_row(r"scheduled|cron|note_status|update|index|heartbeat|refresh")
        numbers_in_row(row, (15, 96), 1000, 1, 4)
        check(has_number(plain, 96) and has_number(plain, 384_000) and has_number(plain, 96_000), "indexed-update daily scenario must separate 384,000 writes from 96,000 reads")
        check(bool(re.search(r"(?i)(?:without.index|unindexed|no.index|comparison|probe).{0,120}(?:1|one).{0,50}(?:write|rows_written)|(?:1|one).{0,50}(?:write|rows_written).{0,120}(?:without.index|unindexed|no.index|comparison|probe)", plain)), "indexed-write diagnosis omits the supplied one-write comparison")
        check(bool(re.search(r"(?i)index", "\n".join(complete))) and bool(re.search(r"(?i)write amplification|indexed.{0,40}writ|index.{0,40}(?:maint|cost)", plain)), "missing sampled indexed-write amplification mechanism")
        check(not positive_claims(plain, r"drop all.{0,20}index|remove all.{0,20}index|every index.{0,30}(?:adds|costs).{0,20}(?:one|1)"), "indexed-write fixture must not blindly remove indexes or assume every index is touched")
    else:
        safe_rows = [row for row in rows if re.search(r"dashboard|poll|summary|session|count|select|lookup|same admitted", row[0], re.IGNORECASE)]
        two_query_shapes(safe_rows, admissions=True)
        check(has_number(plain, 120), "safe scenario must retain 60 admitted calls × 2 queries × 1 sampled row = 120 reads/session")
        check(contains(plain, "No confirmed findings."), "safe SQL controls must explicitly report no confirmed findings")
        check(bool(re.search(r"(?i)gate|admission", plain)) and bool(re.search(r"(?i)atomic|atomically", plain)) and bool(re.search(r"(?i)before.{0,45}(?:D1|database|quer)|pre.D1", plain)), "safe case omits the supplied atomic admission contract before D1")
        check(bool(re.search(r"(?is)(?:gate|binding).{0,100}(?:contract|test.double|assum|synthetic).{0,120}(?:unverified|not inspected|not supplied)|(?:implementation|deploy).{0,80}(?:not inspected|not supplied|unverified)|Scope not inspected:[^\n]*(?:gate|implementation|deployment)", plain)), "safe case promotes a supplied gate contract into verified deployment state")
        check(not re.search(r"(?i)(?:gate|implementation|deployment)[^\n.;]{0,60}\b(?:is|was|are)\s+(?:(?:fully|actually)\s+)?(?:verified|proven|confirmed)\b", plain), "safe case falsely claims the external gate/deployment was verified")
        check(bool(re.search(r"(?i)COUNT|summary aggregate", plain)) and bool(re.search(r"(?i)SELECT\s*\*|(?:note|primary.key|fixed.key).{0,30}lookup", plain)) and bool(re.search(r"(?i)primary.key|SEARCH.{0,50}INDEX|one.row|single.row", plain)), "safe COUNT and SELECT * lack their bounded plan/schema evidence")
        check(not positive_claims(plain, r"(?:COUNT\s*\(\s*\*\s*\)|SELECT\s*\*|polling).{0,65}(?:always|necessarily|proves?|causes?).{0,50}(?:expensive|scan|bill|unbounded)"), "safe controls incorrectly treated as intrinsically expensive")

    return failures, checks


def public_gate_failures(case_id: str, text: str) -> tuple[list[str], int]:
    spec = PUBLIC_GATE_SPECS[case_id]
    failures: list[str] = []
    checks = 0

    verdicts = re.findall(r"(?im)^\s*Release verdict:\s*(?:\*\*)?([A-Z]+)", text)
    checks += 1
    if verdicts != [spec["verdict"]]:
        failures.append(f"expected exactly one {spec['verdict']} release verdict, got {verdicts!r}")

    for label in ("Discovery gaps:", "Exposure scenario:", "Closure conditions:"):
        checks += 1
        if not re.search(rf"(?im)^\s*{re.escape(label)}", text):
            failures.append(f"missing release-gate label: {label}")

    table_lines = [line for line in text.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
    header = next((line for line in table_lines if "route" in line.casefold() and "discovery" in line.casefold()), "")
    checks += 1
    required_columns = ("known valid", "accepted keyspace", "rejection", "inherited", "route-specific", "per-hit", "prevention")
    if not header or any(column not in header.casefold() for column in required_columns):
        failures.append("route matrix is missing one or more required structural columns")

    data_rows = [
        line for line in table_lines
        if line != header and not re.fullmatch(r"[|:\- ]+", line.strip())
    ]
    for route in spec["routes"]:
        checks += 1
        matching_rows = [row for row in data_rows if route_cell_matches(row, route)]
        if not matching_rows or any("," in row.split("|")[1] for row in matching_rows):
            failures.append(f"route family lacks its own matrix row: {route}")

    exposure = labelled_section(text, "Exposure scenario:")
    closure = labelled_section(text, "Closure conditions:")
    discovery = labelled_section(text, "Discovery gaps:")
    mode = spec["mode"]

    checks += 1
    if "developers.cloudflare.com/d1/platform/pricing" not in text.casefold():
        failures.append("missing directly relevant official D1 pricing source")

    if mode == "uncached":
        checks += 1
        if not re.search(r"(?is)^(?=.*request)(?=.*(?:×|\bx\b|times|multipl))(?=.*(?:rows?.read|product units?|units?)).*$", exposure):
            failures.append("uncached exposure must preserve request count × units per request")
        checks += 1
        collapses_repeated_hits = re.search(
            r"(?is)distinct\s+(?:cache\s+)?keys?.{0,180}(?:repeated|repeat|same[- ]URL).{0,100}(?:no|none|without|do\s+not|doesn't|does not).{0,100}(?:further|additional|more|add|cost|D1|rows?)",
            exposure,
        )
        if (
            re.search(r"(?is)(?:only|equals?|total.{0,40}(?:=|is))\s+distinct\s+(?:cache\s+)?keys?\s*(?:×|x)", exposure)
            or collapses_repeated_hits
        ):
            failures.append("uncached exposure incorrectly collapses repeated hits to distinct keys")

    if case_id == "crawlable-page-live-d1-cost":
        checks += 4
        route_requirements = {
            "/": ("count", "group"),
            "/browse": ("count", "query"),
            "/abstract/": ("count", "lookup"),
            "/about": ("count",),
            "/sitemap.xml": (),
            "<fallback>": ("count",),
        }
        for route, terms in route_requirements.items():
            row = next((item.casefold() for item in data_rows if route_cell_matches(item, route)), "")
            if not all(term in row for term in terms):
                failures.append(f"{route} row does not keep inherited and route-specific dependencies separate")
        checks += 1
        if not all(term in discovery.casefold() for term in ("sitemap", "/abstract", "/about")):
            failures.append("discovery gaps do not explain the off-sitemap route families and their evidence")
        closure_fix = r"(?:mov|remov|materializ|precomput|publish|static|must\s+not\s+run)"
        closure_clauses = [
            clause for clause in re.split(r"(?:[.;]\s+|\n+)", closure)
            if not re.search(r"(?is)(?:leave|retain|keep).{0,120}(?:live|request[- ]time|request path)", clause)
        ]
        closes_all_broad_work = any(
            re.search(
                rf"(?is)(?:{closure_fix}.{{0,180}}(?:(?:all|every).{{0,80}}(?:shared\s+)?(?:corpus\s+)?aggregates?|(?:shared\s+)?aggregate.{{0,100}}(?:all|every)\s+(?:public\s+)?request)|(?:(?:all|every).{{0,80}}(?:shared\s+)?(?:corpus\s+)?aggregates?|(?:shared\s+)?aggregate.{{0,100}}(?:all|every)\s+(?:public\s+)?request).{{0,180}}{closure_fix})",
                clause,
            )
            for clause in closure_clauses
        )
        checks += 1
        if not closes_all_broad_work and not any(
            re.search(
                rf"(?is)(?:{closure_fix}.{{0,180}}(?:shared\s+)?(?:total|count(?:\(\*\))?)|(?:shared\s+)?(?:total|count(?:\(\*\))?).{{0,180}}{closure_fix})",
                clause,
            )
            for clause in closure_clauses
        ):
            failures.append("closure does not remove the shared COUNT/total from request-time execution")
        checks += 1
        if not closes_all_broad_work and not any(
            re.search(
                rf"(?is)(?:{closure_fix}.{{0,180}}(?:homepage|field|group(?:\s+by)?)|(?:homepage|field|group(?:\s+by)?).{{0,180}}{closure_fix})",
                clause,
            )
            for clause in closure_clauses
        ):
            failures.append("closure does not remove the homepage GROUP BY/field aggregate from request-time execution")
        checks += 1
        if re.search(r"(?is)(?:leave|retain|keep).{0,120}(?:count|group\s+by|aggregate).{0,100}(?:live|request[- ]time|request path)|(?:count|group\s+by|aggregate).{0,100}(?:remain|stay).{0,80}(?:live|request[- ]time|request path)", closure):
            failures.append("closure explicitly leaves broad aggregate work on a public request path")
        checks += 1
        if not re.search(r"(?is)(malformed|noncanonical|syntax).{0,120}(before|prior).{0,100}(D1|meter|depend)", closure):
            failures.append("closure does not reject malformed/noncanonical keys before metered work")
        checks += 1
        if not (
            re.search(r"(?is)(query plan|EXPLAIN|indexed|bounded)", closure)
            and re.search(r"(?is)(query plan|EXPLAIN)", text)
            and re.search(r"(?is)(measur|rows?.read)", text)
        ):
            failures.append("closure does not require plan and measured-unit proof for the residual lookup")

    if case_id == "public-route-fixed-scan":
        checks += 1
        if not re.search(r"(?is)(repeated|every|each|same).{0,80}(request|hit|url)", exposure):
            failures.append("fixed-route case does not state that URL cardinality is not the safety boundary")

    if mode == "bounded":
        checks += 1
        if not (
            re.search(r"(?is)(articles_slug_unique|SEARCH.{0,100}INDEX|unique.{0,80}index|indexed lookup)", text)
            and re.search(r"(?is)(known|existing).{0,180}(?:exactly\s+)?(?:`?1`?|one)\s+row", text)
            and re.search(r"(?is)(unknown|miss).{0,180}(?:read(?:s)?\s+)?(?:`?0`?|zero)(?:[- ]rows?)?", text)
        ):
            failures.append("PASS does not tie the bounded residual lookup to supplied plan and measurement evidence")
        checks += 1
        if not re.search(r"(?is)(malformed|noncanonical).{0,120}(before|prior).{0,100}(D1|DB|database)", text):
            failures.append("PASS does not preserve early syntax rejection")
        checks += 1
        if not re.search(r"(?is)(unknown|not exist|missing).{0,180}(bounded|0.{0,3}rows|zero rows|indexed)", text):
            failures.append("PASS incorrectly omits the bounded valid-shaped miss behavior")

    if mode == "unknown":
        checks += 1
        if not re.search(r"(?is)(missing|not supplied|unknown).{0,160}(query plan|EXPLAIN|rows.read|measured)", text):
            failures.append("CONDITIONAL does not name the missing plan or measured-unit evidence")
        checks += 1
        if not re.search(r"(?is)(request(?: count| volume|s)?).{0,100}(?:×|x|times|multipl).{0,100}(unknown|rows|units)", exposure):
            failures.append("CONDITIONAL does not retain request volume while leaving per-request units unknown")

    if case_id == "public-route-timeline-holdout":
        checks += 1
        timeline_row = next((item for item in data_rows if route_cell_matches(item, "/timeline")), "")
        timeline_work = timeline_row.casefold()
        if not (("count" in timeline_work and "group" in timeline_work) or "aggregate" in timeline_work) or not re.search(r"(?is)(every|per|anonymous).{0,100}request|request.{0,100}(every|per|anonymous)", exposure):
            failures.append("holdout does not connect the off-sitemap timeline route to the repeated broad query")
        checks += 1
        if not (
            re.search(r"(?is)(?:timeline|year\s+counts?|aggregate|group\s+by).{0,180}(?:remov|materializ|publish|static|must\s+not\s+run)", closure)
            or re.search(r"(?is)(?:remov|materializ|publish|static|must\s+not\s+run).{0,180}(?:timeline|year\s+counts?|aggregate|group\s+by)", closure)
        ):
            failures.append("holdout closure does not remove or materialize the timeline aggregate")

    preworker_claim = re.search(r"(?is)(?:before|bypass(?:es|ing)?)\s+(?:(?:executing|invoking)\s+)?(?:the\s+)?Worker|without\s+(?:executing|invoking)\s+(?:the\s+)?Worker", text)
    if preworker_claim:
        checks += 1
        if not re.search(r"developers\.cloudflare\.com/workers/(?:cache/configuration|static-assets/(?:routing/worker-script|binding))", text, re.IGNORECASE):
            failures.append("pre-Worker claim lacks the Workers Caching or Static Assets routing source")
    if re.search(r"(?i)(?:workers caching|cache\.enabled)", text):
        checks += 1
        if "developers.cloudflare.com/workers/platform/pricing" not in text.casefold():
            failures.append("Workers Caching recommendation omits residual request billing source")
    if re.search(r"(?i)cache api", text):
        checks += 1
        if not re.search(r"(?is)cache api.{0,180}(inside|within).{0,80}worker", text):
            failures.append("Cache API is mentioned without stating that it runs inside the Worker")
    if re.search(r"(?is)(?:render|publish|serve)(?:ed|ing)?\b.{0,80}\bstatic asset", text):
        checks += 1
        if not re.search(r"developers\.cloudflare\.com/workers/static-assets/(?:routing/worker-script|binding)", text, re.IGNORECASE):
            failures.append("Static Assets recommendation lacks a directly relevant official source")

    return failures, checks


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: fixture_oracle.py OUTPUT_DIR CASE_ID", file=sys.stderr)
        return 2
    output_dir = Path(sys.argv[1])
    case_id = sys.argv[2]
    spec = SPECS.get(case_id)
    if not spec and case_id not in PUBLIC_GATE_SPECS and case_id not in PRIVATE_D1_CASES:
        print(f"unknown case id: {case_id}", file=sys.stderr)
        return 2
    out = output_dir / "output.md"
    if not out.exists():
        print(f"missing output: {out}", file=sys.stderr)
        return 2
    text = out.read_text(encoding="utf-8", errors="replace")
    if case_id in PRIVATE_D1_CASES:
        failures, checks = private_d1_failures(case_id, text)
        print(json.dumps({"score": max(checks - len(failures), 0), "max_score": checks or 1,
                          "case_id": case_id, "oracle": "fixture-accounting"}))
        if failures:
            print("FAIL private D1 accounting oracle")
            for failure in failures:
                print("- " + failure)
            return 1
        print("OK private D1 accounting oracle: " + case_id)
        return 0
    if case_id in PUBLIC_GATE_SPECS:
        failures, checks = public_gate_failures(case_id, text)
        score = max(checks - len(failures), 0)
        print(json.dumps({"score": score, "max_score": checks or 1, "case_id": case_id, "oracle": "semantic"}))
        if failures:
            print("FAIL public-route semantic oracle")
            for failure in failures:
                print("- " + failure)
            return 1
        print("OK public-route semantic oracle: " + case_id)
        return 0

    failures = []
    checks = 0

    if spec.get("require_core"):
        for marker in CORE_MARKERS:
            checks += 1
            if not contains(text, marker):
                failures.append(f"missing core audit marker: {marker!r}")

    for needle in spec.get("all", []):
        checks += 1
        if not contains(text, needle):
            failures.append(f"missing required text: {needle!r}")
    for group in spec.get("any", []):
        checks += 1
        if not any(contains(text, needle) for needle in group):
            failures.append("missing one of: " + ", ".join(repr(x) for x in group))
    for pattern in spec.get("patterns", []):
        checks += 1
        if not re.search(pattern, text):
            failures.append(f"required pattern absent: {pattern}")
    for pattern in spec.get("forbid", []):
        checks += 1
        if re.search(pattern, text):
            failures.append(f"forbidden pattern present: {pattern}")

    if spec.get("forbid_package_runner_recommendation"):
        checks += 1
        unsafe_runners = package_runner_recommendations(text)
        if unsafe_runners:
            failures.append("package runner recommended: " + "; ".join(unsafe_runners))

    questions_match = re.search(r"(?ms)^## Questions / evidence needed\s*(.*?)(?=^## |\Z)", text)
    questions = questions_match.group(1) if questions_match else ""
    for group in spec.get("evidence_request_any", []):
        checks += 1
        if not questions or not any(contains(questions, needle) for needle in group):
            failures.append("Questions / evidence needed does not request one of: " + ", ".join(repr(x) for x in group))

    blocks = finding_blocks(text)
    max_findings = spec.get("max_findings")
    if isinstance(max_findings, int):
        checks += 1
        if len(blocks) > max_findings:
            failures.append(f"too many finding blocks: {len(blocks)} > {max_findings}")
    complete = [block for block in blocks if all(contains(block, field) for field in FINDING_FIELDS)]
    if spec.get("require_complete_finding"):
        checks += 1
        if not complete:
            failures.append("no structurally complete finding block")
    for group in spec.get("finding_any", []):
        checks += 1
        if not any(any(contains(block, needle) for needle in group) for block in complete):
            failures.append("no complete finding contains one of: " + ", ".join(repr(x) for x in group))
    if spec.get("allow_no_findings") and not blocks:
        checks += 1
        if not contains(text, "No confirmed findings."):
            failures.append("no-finding audit must say 'No confirmed findings.'")

    score = max(checks - len(failures), 0)
    print(json.dumps({"score": score, "max_score": checks or 1, "case_id": case_id}))
    if failures:
        print("FAIL fixture oracle")
        for failure in failures:
            print("- " + failure)
        return 1
    print("OK fixture oracle: " + case_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

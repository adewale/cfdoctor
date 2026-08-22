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
    return re.findall(r"(?ms)^### Severity:.*?(?=^### Severity:|^## |\Z)", text)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: fixture_oracle.py OUTPUT_DIR CASE_ID", file=sys.stderr)
        return 2
    output_dir = Path(sys.argv[1])
    case_id = sys.argv[2]
    spec = SPECS.get(case_id)
    if not spec:
        print(f"unknown case id: {case_id}", file=sys.stderr)
        return 2
    out = output_dir / "output.md"
    if not out.exists():
        print(f"missing output: {out}", file=sys.stderr)
        return 2
    text = out.read_text(encoding="utf-8", errors="replace")
    failures: list[str] = []
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

#!/usr/bin/env python3
"""Evaluate Cloudflare Doctor trigger coverage.

Inspired by Anthropic's skill-creator workflow: keep a prompt set, run a
quantitative pass, inspect failures, then improve the skill description.

This is a deterministic proxy for skill triggering. It cannot prove what a
specific model/runtime will load, but it catches common description blind spots
and false-positive trigger hazards before doing model-based evals.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TRIGGER_PATTERNS = [
    r"\bcloudflare\b",
    r"\bwrangler\b",
    r"\bworkers?\s+ai\b",
    r"\bai\s+gateway\b",
    r"\bvectorize\b",
    r"\bbrowser\s+run\b",
    r"\bcloudflare\s+dynamic\s+workers?\b",
    r"\bdynamic\s+worker\s+loader\b",
    r"\bagents\s+sdk\b",
    r"\bcloudflare\s+agents?\b",
    r"\bcloudflare\s+artifacts\b",
    r"\bworkers\s+analytics\s+engine\b",
    r"\bcloudflare\s+analytics\s+engine\b",
    r"\bworkers\s+logs\b",
    r"\bdurable\s+objects?\b",
    r"\bcloudflare\s+pages\b",
    r"\bpages\s+(preview|functions?)\b",
    r"\bworkers?\s+kv\b",
    r"\bcloudflare\s+kv\b",
    r"(?<!r2-)\br2\b",
    r"\bd1\b",
    r"\bcloudflare\s+queues?\b",
    r"\bcloudflare\s+workflows?\b",
    r"\bcloudflare\s+images?\b",
    r"\bcloudflare\s+stream\b",
    r"\bzero\s+trust\b",
    r"\baccess\s+polic(?:y|ies)\b",
    r"\bcloudflare\s+dns\b",
    r"\bwaf\b",
]

INTENT_PATTERNS = [
    r"\baudit\b",
    r"\breview\b",
    r"\binspect\b",
    r"\bcheck\b",
    r"\bfind\b",
    r"\bdiagnos(?:e|is)\b",
    r"\bdoctor\b",
    r"\bsanity[- ]check\b",
    r"best[- ]practice",
    r"wrong\s+primitive",
    r"misconfig",
    r"\bcost\b",
    r"\bbill(?:ing)?\b",
    r"\boverages?\b",
    r"\bpricing\b",
    r"\bfootguns?\b",
    r"\brisks?\b",
    r"\bmap\b",
    r"\bcache\s+map\b",
    r"\bsource\s+basis\b",
]

FALSE_FRIEND_PATTERNS = [
    r"\br2-d2\b",
    r"cloudflare-like style",
    r"public status page",
]


@dataclass
class CaseResult:
    case: dict[str, Any]
    predicted: str
    expected: str
    passed: bool
    reasons: list[str]
    missing_description_terms: list[str]


def load_skill_description(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---", text, re.S)
    if not match:
        raise ValueError(f"No frontmatter found in {path}")
    frontmatter = match.group(1)
    desc = re.search(r"^description:\s*(.*)$", frontmatter, re.M)
    if not desc:
        raise ValueError(f"No description field found in {path}")
    return desc.group(1).strip()


def any_pattern(patterns: list[str], text: str) -> tuple[bool, list[str]]:
    hits = [pat for pat in patterns if re.search(pat, text, re.I)]
    return bool(hits), hits


def proxy_trigger(prompt: str) -> tuple[str, list[str]]:
    false_friend, false_friend_hits = any_pattern(FALSE_FRIEND_PATTERNS, prompt)
    has_product, product_hits = any_pattern(TRIGGER_PATTERNS, prompt)
    has_intent, intent_hits = any_pattern(INTENT_PATTERNS, prompt)

    reasons: list[str] = []
    if product_hits:
        reasons.append("product=" + ", ".join(product_hits[:3]))
    if intent_hits:
        reasons.append("intent=" + ", ".join(intent_hits[:3]))
    if false_friend_hits:
        reasons.append("false_friend=" + ", ".join(false_friend_hits))

    if false_friend:
        return "no_trigger", reasons
    if has_product and has_intent:
        return "trigger", reasons
    return "no_trigger", reasons


def eval_cases(cases: list[dict[str, Any]], description: str) -> list[CaseResult]:
    desc_l = description.lower()
    results: list[CaseResult] = []
    for case in cases:
        predicted, reasons = proxy_trigger(case["prompt"])
        expected = case["expected"]
        missing_terms = []
        for term in case.get("description_terms", []):
            if term.lower() not in desc_l:
                missing_terms.append(term)
        results.append(CaseResult(
            case=case,
            predicted=predicted,
            expected=expected,
            passed=predicted == expected,
            reasons=reasons,
            missing_description_terms=missing_terms,
        ))
    return results


def metric(numer: int, denom: int) -> float:
    return 0.0 if denom == 0 else numer / denom


def render_report(results: list[CaseResult], description: str, skill_path: Path, cases_path: Path) -> str:
    positives = [r for r in results if r.expected == "trigger"]
    negatives = [r for r in results if r.expected == "no_trigger"]
    passed = [r for r in results if r.passed]
    false_negatives = [r for r in results if r.expected == "trigger" and r.predicted != r.expected]
    false_positives = [r for r in results if r.expected == "no_trigger" and r.predicted != r.expected]
    missing_desc = [r for r in results if r.missing_description_terms]

    lines: list[str] = []
    lines.append("# Cloudflare Doctor trigger eval")
    lines.append("")
    lines.append(f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Skill: `{skill_path}`")
    lines.append(f"Cases: `{cases_path}`")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append(f"- Cases: {len(results)}")
    lines.append(f"- Accuracy: {len(passed)}/{len(results)} = {metric(len(passed), len(results)):.1%}")
    lines.append(f"- Trigger recall: {len(positives) - len(false_negatives)}/{len(positives)} = {metric(len(positives) - len(false_negatives), len(positives)):.1%}")
    lines.append(f"- No-trigger specificity: {len(negatives) - len(false_positives)}/{len(negatives)} = {metric(len(negatives) - len(false_positives), len(negatives)):.1%}")
    lines.append(f"- Description length: {len(description)} chars")
    lines.append(f"- Missing description term cases: {len(missing_desc)}")
    lines.append("")
    lines.append("## Current description")
    lines.append("")
    lines.append(f"> {description}")
    lines.append("")

    if false_negatives or false_positives or missing_desc:
        lines.append("## Failures / gaps")
        lines.append("")
        for r in false_negatives:
            lines.append(f"### False negative: {r.case['id']}")
            lines.append(f"- Prompt: {r.case['prompt']}")
            lines.append(f"- Reasons: {', '.join(r.reasons) if r.reasons else 'none'}")
            lines.append("")
        for r in false_positives:
            lines.append(f"### False positive: {r.case['id']}")
            lines.append(f"- Prompt: {r.case['prompt']}")
            lines.append(f"- Reasons: {', '.join(r.reasons) if r.reasons else 'none'}")
            lines.append("")
        for r in missing_desc:
            lines.append(f"### Description coverage gap: {r.case['id']}")
            lines.append(f"- Missing terms: {', '.join(r.missing_description_terms)}")
            lines.append(f"- Prompt: {r.case['prompt']}")
            lines.append("")
    else:
        lines.append("## Failures / gaps")
        lines.append("")
        lines.append("None. Proxy trigger predictions match expected labels and all expected trigger terms are present in the description.")
        lines.append("")

    lines.append("## Per-case results")
    lines.append("")
    lines.append("| Case | Expected | Predicted | Pass | Category | Reasons |")
    lines.append("|---|---:|---:|---:|---|---|")
    for r in results:
        reasons = "; ".join(r.reasons).replace("|", "\\|")
        lines.append(f"| {r.case['id']} | {r.expected} | {r.predicted} | {'yes' if r.passed else 'NO'} | {r.case.get('category', '')} | {reasons} |")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This is a deterministic proxy eval for trigger intent and description coverage, not a model-runtime proof.")
    lines.append("- For model-based evals, run these same prompts in a harness that exposes this skill and judge whether Cloudflare Doctor loaded and produced the required audit scaffold.")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Cloudflare Doctor trigger coverage")
    parser.add_argument("--skill", default="SKILL.md", help="Path to SKILL.md")
    parser.add_argument("--cases", default="evals/trigger-cases.json", help="Path to trigger cases JSON")
    parser.add_argument("--out-dir", default="evals/results", help="Directory for reports")
    parser.add_argument("--min-accuracy", type=float, default=1.0, help="Minimum required accuracy")
    parser.add_argument("--max-description-chars", type=int, default=1024, help="Skill description max length")
    args = parser.parse_args(argv)

    skill_path = Path(args.skill)
    cases_path = Path(args.cases)
    out_dir = Path(args.out_dir)
    description = load_skill_description(skill_path)
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    results = eval_cases(cases, description)
    report = render_report(results, description, skill_path, cases_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = out_dir / f"trigger-eval-{stamp}.md"
    latest_path = out_dir / "latest.md"
    report_path.write_text(report, encoding="utf-8")
    latest_path.write_text(report, encoding="utf-8")

    passed = sum(1 for r in results if r.passed)
    accuracy = metric(passed, len(results))
    missing_desc = [r for r in results if r.missing_description_terms]
    description_ok = len(description) <= args.max_description_chars

    print(f"Report: {report_path}")
    print(f"Accuracy: {passed}/{len(results)} = {accuracy:.1%}")
    print(f"Description length: {len(description)} chars")
    print(f"Missing description term cases: {len(missing_desc)}")

    if accuracy < args.min_accuracy or missing_desc or not description_ok:
        if not description_ok:
            print(f"FAIL: description exceeds {args.max_description_chars} chars", file=sys.stderr)
        if missing_desc:
            print("FAIL: description coverage gaps present", file=sys.stderr)
        if accuracy < args.min_accuracy:
            print(f"FAIL: accuracy {accuracy:.1%} < {args.min_accuracy:.1%}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

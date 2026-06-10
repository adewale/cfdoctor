#!/usr/bin/env python3
"""Detection eval for the Cloudflare Doctor static scanner.

Runs `scripts/cfdoctor_static_scan.py --json` against every fixture under
`evals/fixtures/detection/<scenario>/` that declares an `expected.json`, then
asserts:

- every `required_check_ids` entry is emitted for that fixture,
- no `forbidden_check_ids` entry is emitted,
- fixtures with `max_findings` (e.g. the clean baseline) stay at or under it.

Exit codes: 0 all fixtures pass, 1 one or more fixtures fail, 2 harness error.
Stdlib only; deterministic; writes a timestamped markdown report plus
`latest.md` to `evals/results/detection/` by default, or to `--out-dir`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNER = REPO_ROOT / "scripts" / "cfdoctor_static_scan.py"
FIXTURES_DIR = REPO_ROOT / "evals" / "fixtures" / "detection"
DEFAULT_RESULTS_DIR = REPO_ROOT / "evals" / "results" / "detection"


class HarnessError(RuntimeError):
    """Raised when the eval itself (not a fixture) cannot run."""


@dataclass
class FixtureResult:
    name: str
    description: str
    war_story: str
    required: list[str]
    forbidden: list[str]
    max_findings: int | None
    found_ids: list[str] = field(default_factory=list)
    total_findings: int = 0
    missing: list[str] = field(default_factory=list)
    forbidden_hit: list[str] = field(default_factory=list)
    over_budget: bool = False

    @property
    def passed(self) -> bool:
        return not self.missing and not self.forbidden_hit and not self.over_budget

    @property
    def notes(self) -> str:
        parts: list[str] = []
        if self.missing:
            parts.append("missing " + ", ".join(self.missing))
        if self.forbidden_hit:
            parts.append("forbidden " + ", ".join(self.forbidden_hit))
        if self.over_budget:
            parts.append(f"{self.total_findings} findings > max_findings {self.max_findings}")
        return "; ".join(parts) if parts else "-"


def load_expected(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HarnessError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("required_check_ids"), list):
        raise HarnessError(f"{path}: expected an object with a required_check_ids list")
    return data


def scan_fixture(fixture_dir: Path) -> dict:
    cmd = [sys.executable, str(SCANNER), str(fixture_dir), "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HarnessError(f"scanner failed to run on {fixture_dir.name}: {exc}") from exc
    if proc.returncode != 0:
        raise HarnessError(
            f"scanner exited {proc.returncode} on {fixture_dir.name}: {proc.stderr.strip()[:400]}"
        )
    try:
        return json.loads(proc.stdout)
    except ValueError as exc:
        raise HarnessError(f"scanner emitted invalid JSON on {fixture_dir.name}: {exc}") from exc


def evaluate_fixture(fixture_dir: Path) -> FixtureResult:
    expected = load_expected(fixture_dir / "expected.json")
    required = [str(c) for c in expected.get("required_check_ids", [])]
    forbidden = [str(c) for c in expected.get("forbidden_check_ids", []) or []]
    max_findings = expected.get("max_findings")
    if max_findings is not None and not isinstance(max_findings, int):
        raise HarnessError(f"{fixture_dir.name}: max_findings must be an integer")

    report = scan_fixture(fixture_dir)
    findings = report.get("findings", [])
    found_ids = sorted({str(f.get("check_id")) for f in findings})

    result = FixtureResult(
        name=fixture_dir.name,
        description=str(expected.get("description", "")),
        war_story=str(expected.get("war_story", "")),
        required=required,
        forbidden=forbidden,
        max_findings=max_findings,
        found_ids=found_ids,
        total_findings=len(findings),
    )
    result.missing = [c for c in required if c not in found_ids]
    result.forbidden_hit = [c for c in forbidden if c in found_ids]
    result.over_budget = max_findings is not None and len(findings) > max_findings
    return result


def render_report(results: list[FixtureResult], timestamp: dt.datetime) -> str:
    passed = [r for r in results if r.passed]
    lines: list[str] = []
    lines.append("# Detection eval report")
    lines.append("")
    lines.append(f"- Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Scanner: `scripts/cfdoctor_static_scan.py --json`")
    lines.append(f"- Fixture root: `evals/fixtures/detection/`")
    lines.append(f"- Result: {len(passed)}/{len(results)} fixtures passed")
    lines.append("")
    lines.append("| Fixture | Status | Required found | Findings | Notes |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        found_required = len([c for c in r.required if c in r.found_ids])
        budget = f" (max {r.max_findings})" if r.max_findings is not None else ""
        lines.append(
            f"| {r.name} | {'PASS' if r.passed else 'FAIL'} "
            f"| {found_required}/{len(r.required)} | {r.total_findings}{budget} | {r.notes} |"
        )
    lines.append("")
    lines.append("## Fixture detail")
    for r in results:
        lines.append("")
        lines.append(f"### {r.name} — {'PASS' if r.passed else 'FAIL'}")
        lines.append("")
        if r.description:
            lines.append(f"- Scenario: {r.description}")
        if r.war_story:
            lines.append(f"- War story: {r.war_story}")
        lines.append(f"- Required check IDs: {', '.join(r.required) if r.required else '(none)'}")
        if r.forbidden:
            lines.append(f"- Forbidden check IDs: {', '.join(r.forbidden)}")
        if r.max_findings is not None:
            lines.append(f"- Max findings allowed: {r.max_findings}")
        lines.append(
            f"- Check IDs emitted ({r.total_findings} findings): "
            f"{', '.join(r.found_ids) if r.found_ids else '(none)'}"
        )
        if not r.passed:
            lines.append(f"- Failure notes: {r.notes}")
    lines.append("")
    return "\n".join(lines)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run scanner detection fixtures")
    parser.add_argument(
        "--out-dir",
        help="Directory for markdown reports (default: evals/results/detection)",
    )
    args = parser.parse_args(argv)
    results_dir = Path(args.out_dir) if args.out_dir else DEFAULT_RESULTS_DIR

    if not SCANNER.exists():
        print(f"harness error: scanner not found at {SCANNER}", file=sys.stderr)
        return 2
    fixture_dirs = sorted(
        (p.parent for p in FIXTURES_DIR.glob("*/expected.json")),
        key=lambda p: p.name,
    )
    if not fixture_dirs:
        print(f"harness error: no fixtures with expected.json under {FIXTURES_DIR}", file=sys.stderr)
        return 2

    try:
        results = [evaluate_fixture(d) for d in fixture_dirs]
    except HarnessError as exc:
        print(f"harness error: {exc}", file=sys.stderr)
        return 2

    name_width = max(len(r.name) for r in results)
    print(f"{'fixture'.ljust(name_width)}  status  required  findings  notes")
    for r in results:
        found_required = len([c for c in r.required if c in r.found_ids])
        status = "PASS" if r.passed else "FAIL"
        print(
            f"{r.name.ljust(name_width)}  {status}    "
            f"{found_required}/{len(r.required)}       {str(r.total_findings).ljust(8)}  {r.notes}"
        )
    passed = sum(1 for r in results if r.passed)
    print(f"detection eval: {passed}/{len(results)} fixtures passed")

    timestamp = dt.datetime.now()
    report = render_report(results, timestamp)
    results_dir.mkdir(parents=True, exist_ok=True)
    stamped = results_dir / f"detection-eval-{timestamp.strftime('%Y%m%d-%H%M%S')}.md"
    stamped.write_text(report, encoding="utf-8")
    (results_dir / "latest.md").write_text(report, encoding="utf-8")
    print(f"report: {display_path(stamped)} (and latest.md)")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

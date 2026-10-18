#!/usr/bin/env python3
"""Materialize the reproducible private/background D1 investigation eval subset.

This selects raw-evidence investigation cases, not scanner fixtures. Run both
variants and the accounting ablation before claiming incremental model benefit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CASE_IDS = {
    "private-d1-polling-growth", "private-d1-deep-offset", "private-d1-repeated-sync",
    "private-d1-indexed-writes", "private-d1-safe-controls",
}
ABLATION_ID = "no-private-d1-cost-accounting"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("evals/shared-benchmark.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    eval_root, repo_root = manifest.parent, manifest.parent.parent
    if args.out.resolve().parent != repo_root:
        raise SystemExit("write the focused manifest in the repository root, e.g. --out private-d1-focused.json; "
                         "the harness requires repository-relative ablation patch paths")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    cases = [case for case in data["cases"] if case["id"] in CASE_IDS]
    if {case["id"] for case in cases} != CASE_IDS or len(cases) != len(CASE_IDS):
        raise SystemExit("focused manifest requires each of the five private D1 cases exactly once")
    data["cases"] = cases
    data["ablations"] = [item for item in data["ablations"] if item["id"] == ABLATION_ID]
    if len(data["ablations"]) != 1:
        raise SystemExit("focused manifest requires the private D1 accounting ablation")
    def fixture_path(path: str) -> str:
        return str(eval_root.relative_to(repo_root) / path)
    for case in data["cases"]:
        case["files"] = [fixture_path(path) for path in case.get("files", [])]
        for assertion in case.get("assertions", []):
            if assertion.get("type") == "script":
                assertion["command"][1] = fixture_path(assertion["command"][1])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

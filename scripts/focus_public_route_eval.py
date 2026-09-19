#!/usr/bin/env python3
"""Materialize the reviewer-reproducible public-route subset of the shared eval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CASE_IDS = {
    "crawlable-page-live-d1-cost",
    "public-route-fixed-scan",
    "public-route-safe-bounded-lookup",
    "public-route-missing-plan",
    "public-route-timeline-holdout",
}
ABLATION_ID = "no-public-route-cost-gate"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("evals/shared-benchmark.json"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--split", choices=("tune", "holdout", "all"), default="all")
    args = parser.parse_args()

    manifest = args.manifest.resolve()
    eval_root = manifest.parent
    repo_root = eval_root.parent
    data = json.loads(manifest.read_text(encoding="utf-8"))
    cases = [case for case in data["cases"] if case["id"] in CASE_IDS]
    if args.split != "all":
        cases = [case for case in cases if case["split"] == args.split]
    found = {case["id"] for case in cases}
    expected = {case["id"] for case in data["cases"] if case["id"] in CASE_IDS and (args.split == "all" or case["split"] == args.split)}
    if found != expected or not cases:
        raise SystemExit(f"focused case mismatch: found={sorted(found)} expected={sorted(expected)}")

    data["cases"] = cases
    data["ablations"] = [item for item in data["ablations"] if item["id"] == ABLATION_ID] if args.split != "holdout" else []
    out_parent = args.out.resolve().parent
    if out_parent == repo_root:
        for case in data["cases"]:
            case["files"] = [str(Path("evals") / path) for path in case.get("files", [])]
            for assertion in case.get("assertions", []):
                command = assertion.get("command", [])
                if assertion.get("type") == "script" and len(command) > 1:
                    command[1] = str(Path("evals") / command[1])
    elif out_parent != eval_root:
        data["skill_paths"] = [str((repo_root / path).resolve()) for path in data["skill_paths"]]
        data["old_skill_paths"] = [str((repo_root / path).resolve()) for path in data.get("old_skill_paths", [])]
        for case in data["cases"]:
            case["files"] = [str((eval_root / path).resolve()) for path in case.get("files", [])]
            for assertion in case.get("assertions", []):
                command = assertion.get("command", [])
                if assertion.get("type") == "script" and len(command) > 1:
                    command[1] = str((eval_root / command[1]).resolve())
        for ablation in data["ablations"]:
            target = ablation["target"]
            target["skill_root"] = str((repo_root / target["skill_root"]).resolve())
            if "patch" in target:
                target["patch"] = str((repo_root / target["patch"]).resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

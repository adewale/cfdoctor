#!/usr/bin/env python3
"""Prepare a focused Workflow-billing comparison using the shared benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CONTROLS = {
    "pos-workflows-unbounded-fanout",
    "detection-fixture-queue-dlq-safe",
    "pricing-compound-worker-bindings",
    "pricing-future-effective-conflict",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("evals/shared-benchmark.json"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True, help="immutable baseline repository root")
    parser.add_argument("--current", type=Path, help="frozen current repository root; default is manifest's repository")
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    repo_root, eval_root = manifest.parent.parent, manifest.parent
    data = json.loads(manifest.read_text())
    cases = [c for c in data["cases"] if c["id"] in CONTROLS or c["id"].startswith("workflow-")]
    if len(cases) != 10 or CONTROLS - {c["id"] for c in cases}:
        raise SystemExit("Expected six Workflow cases and all four existing controls")
    data["cases"], data["ablations"] = cases, []
    current = (args.current or repo_root).resolve()
    data["skill_paths"] = [str(current / "skills/cloudflare-doctor/SKILL.md")]
    data["old_skill_paths"] = [str(args.baseline.resolve() / "skills/cloudflare-doctor/SKILL.md")]
    for case in cases:
        case["files"] = [str((eval_root / f).resolve()) for f in case.get("files", [])]
        if "prompt_ref" in case:
            case["prompt_ref"] = str((eval_root / case["prompt_ref"]).resolve())
        for assertion in case.get("assertions", []):
            if assertion.get("type") == "script":
                assertion["command"][1] = str((eval_root / assertion["command"][1]).resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

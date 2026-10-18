#!/usr/bin/env python3
"""Blind variant identity before invoking the pinned shared-harness judge.

Run with the harness installed. The root must contain manifest.json and runs/.
Raw provider artifacts remain under root, outside the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import skill_benchmark as sb


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--backend", choices=["codex", "claude"], default="codex")
    parser.add_argument("--model", required=True)
    parser.add_argument("--sample-run", type=int)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    cases = {case["id"]: case for case in manifest["cases"]}
    tasks = sb.collect_judge_tasks(manifest_path, root / "runs", split=None,
                                  variants=["with_skill", "old_skill", "without_skill"])
    if args.sample_run:
        tasks = [task for task in tasks if task["run_number"] == args.sample_run]
    label = args.backend + "-" + args.model
    dest = root / ("judges-" + label)
    dest.mkdir(exist_ok=True)
    mappings = {}

    def run(task):
        original_id = task["judge_task_id"]
        opaque = "candidate-" + hashlib.sha256(original_id.encode()).hexdigest()[:16]
        result_path = dest / (opaque + ".json")
        mappings[opaque] = original_id
        if result_path.exists():
            return json.loads(result_path.read_text())
        blind = dict(task, judge_task_id=opaque, variant="candidate", run_number=1)
        case = cases[task["case_id"]]
        prompt = case.get("prompt")
        if prompt is None:
            prompt = Path(case["prompt_ref"]).read_text()
        evidence = "\n\n".join(f"Input file: {Path(f).name}\n{Path(f).read_text()}"
                               for f in case.get("files", []))
        blind["prompt"] = prompt + ("\n\nAttached evidence:\n" + evidence if evidence else "")
        row = sb.run_one_judge_task(
            blind, transcripts_dir=dest / "transcripts",
            judge_model=None if args.model == "default" else args.model,
            judge_backend=args.backend,
            codex_cmd="codex exec --config model_reasoning_effort=high",
            schema_enforcement="strict",
        )
        row.update(judge_task_id=original_id, case_id=task["case_id"],
                   variant=task["variant"], run_number=task["run_number"])
        row["blinded_candidate_id"] = opaque
        result_path.write_text(json.dumps(row, indent=2) + "\n")
        print(json.dumps({"candidate": opaque, "completed": True,
                          "parse_error": bool(row.get("parse_error")),
                          "returncode": row.get("returncode")}), flush=True)
        return row

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = [f.result() for f in as_completed([pool.submit(run, task) for task in tasks])]
    rows.sort(key=lambda row: row["judge_task_id"])
    (root / (label + "-judge-results.jsonl")).write_text(
        "".join(json.dumps(row) + "\n" for row in rows))
    (dest / "blinding-map.json").write_text(json.dumps(mappings, indent=2) + "\n")
    print(f"{len(rows)} {args.backend} judgments stored", flush=True)


if __name__ == "__main__":
    main()

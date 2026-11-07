"""Blind the variant, then call the shared harness's native judge backend."""

import concurrent.futures
import hashlib
import json
import sys
from pathlib import Path

r = Path(__file__).resolve().parent
from grading_contract import JUDGE_PREFACE


def observed_activity(run_base):
    """Supply tool evidence without copying model reasoning into the judge input."""
    trace = Path(run_base) / "trace.jsonl"
    if not trace.is_file():
        return {"available": False}
    metadata = json.loads((Path(run_base) / "metadata.json").read_text())
    commands = []
    for line in trace.read_text().splitlines():
        event = json.loads(line)
        item = event.get("item", {})
        if (
            event.get("type") != "item.completed"
            or item.get("type") != "command_execution"
        ):
            continue
        command = {"command": item["command"], "exit_code": item.get("exit_code")}
        try:
            output = json.loads(item.get("aggregated_output", ""))
        except (ValueError, TypeError):
            output = None
        if (
            isinstance(output, dict)
            and "scanner_version" in output
            and isinstance(output.get("findings"), list)
        ):
            command["scanner_output"] = output
        commands.append(command)
    return {
        "available": True,
        "trace_observation_complete": metadata.get("trace_observation_complete"),
        "commands": commands,
    }


def grading_prompt(case, run_base):
    bundle = json.loads(Path(case["files"][0]).read_text())
    raw = "\n\n".join(
        "SOURCE FILE: " + p + "\n" + s for p, s in bundle["files"].items()
    )
    docs = "\n\n".join(Path(f).read_text() for f in case["files"][1:])
    return (
        JUDGE_PREFACE
        + "\n\nOriginal audit request (auditor permissions):\n"
        + case["prompt"]
        + "\n\nRaw source:\n"
        + raw
        + "\n\nOfficial documentation snapshots:\n"
        + docs
        + "\n\nObserved auditor activity (evaluator trace, not project source):\n"
        + json.dumps(observed_activity(run_base), sort_keys=True)
    )


def grading_fingerprint(task, model, backend):
    payload = {k: task[k] for k in ["prompt", "expected_behavior", "assertion"]}
    payload.update(
        output=Path(task["output_path"]).read_text(), model=model, backend=backend
    )
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def cached_judgment(path, fingerprint):
    if not path.exists():
        return None
    row = json.loads(path.read_text())
    if row.get("grading_input_sha256") != fingerprint:
        raise ValueError(
            "Cached judgment has different grading inputs; use a fresh run directory"
        )
    return row


def main():
    sys.path.insert(0, str(r / "harness"))
    import skill_benchmark as sb

    root = Path(sys.argv[1]).resolve()
    backend = sys.argv[2] if len(sys.argv) > 2 else "codex"
    model = "gpt-5.6-sol" if backend == "codex" else "claude-sonnet-4-6"
    manifest = json.loads((root / "manifest.json").read_text())
    cases = {c["id"]: c for c in manifest["cases"]}
    tasks = sb.collect_judge_tasks(
        root / "manifest.json",
        root / "runs",
        split="tune",
        variants=["with_skill", "old_skill"],
    )
    tasks = [
        t
        for t in tasks
        if Path(t["output_path"]).is_file()
        and (Path(t["run_base"]) / "metadata.json").is_file()
        and json.loads((Path(t["run_base"]) / "metadata.json").read_text()).get(
            "returncode"
        )
        == 0
    ]
    tasks.sort(
        key=lambda t: hashlib.sha256(
            ("final-expanded-v1:" + t["judge_task_id"]).encode()
        ).hexdigest()
    )
    dest = root / ("judges-" + backend)
    dest.mkdir(exist_ok=True)
    mapping = {}

    def run(task):
        original = task["judge_task_id"]
        opaque = (
            "candidate-"
            + hashlib.sha256(("final-expanded-v1:" + original).encode()).hexdigest()[
                :18
            ]
        )
        mapping[opaque] = original
        result = dest / (opaque + ".json")
        blind = dict(
            task, judge_task_id=opaque, variant="candidate", run_number=1, run_base=None
        )
        case = cases[task["case_id"]]
        blind["prompt"] = grading_prompt(case, task["run_base"])
        fingerprint = grading_fingerprint(blind, model, backend)
        cached = cached_judgment(result, fingerprint)
        if cached is not None:
            return cached
        row = sb.run_one_judge_task(
            blind,
            transcripts_dir=dest / "transcripts",
            judge_model=model,
            judge_backend=backend,
            codex_cmd="codex exec --config model_reasoning_effort=high",
            schema_enforcement="strict",
        )
        row.update(
            judge_task_id=original,
            case_id=task["case_id"],
            variant=task["variant"],
            run_number=task["run_number"],
            blinded_candidate_id=opaque,
            grading_input_sha256=fingerprint,
        )
        result.write_text(json.dumps(row, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "candidate": opaque,
                    "case": task["case_id"],
                    "parse_error": row.get("parse_error"),
                    "returncode": row.get("returncode"),
                    "dimensions": row.get("dimension_scores"),
                }
            ),
            flush=True,
        )
        return row

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:
        rows = list(p.map(run, tasks))
    rows.sort(key=lambda x: x["judge_task_id"])
    (root / (backend + "-judge-results.jsonl")).write_text(
        "".join(json.dumps(x) + "\n" for x in rows)
    )
    (dest / "blinding-map.json").write_text(json.dumps(mapping, indent=2) + "\n")
    print("Stored judgments:", len(rows), flush=True)


if __name__ == "__main__":
    main()

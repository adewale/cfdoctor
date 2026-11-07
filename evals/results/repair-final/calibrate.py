"""Run the pinned harness's native anchored judges on frozen near-miss reports."""

import argparse
import concurrent.futures
import hashlib
import json
import sys
from pathlib import Path

from grading_contract import JUDGE_PREFACE, PRECISION


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--harness", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.harness.resolve()))
    import skill_benchmark as sb

    here = Path(__file__).resolve().parent
    gold = json.loads((here / "calibration-cases.json").read_text())
    dest = args.work.resolve()
    dest.mkdir(parents=True, exist_ok=True)

    def backend_run(backend):
        output_dir = dest / backend
        output_dir.mkdir(exist_ok=True)

        def run(g):
            opaque = (
                "sample-"
                + hashlib.sha256(("calibration-v2:" + g["id"]).encode()).hexdigest()[
                    :20
                ]
            )
            receipt = output_dir / (opaque + ".json")
            if receipt.exists():
                return json.loads(receipt.read_text())
            report = output_dir / (opaque + ".md")
            report.write_text(g["report"])
            raw = "\n\n".join(
                "SOURCE FILE: " + Path(name).name + "\n" + value
                for name, value in g["files"].items()
            )
            task = {
                "judge_task_id": opaque,
                "case_id": "calibration-case",
                "variant": "candidate",
                "run_number": 1,
                "run_base": None,
                "output_path": str(report),
                "prompt": JUDGE_PREFACE
                + "Grade factual precision only, not completeness or recall.\nOriginal audit request:\n"
                + g["prompt"]
                + "\nRaw project and reference evidence:\n"
                + raw,
                "expected_behavior": [json.dumps(g["expected_behavior"], indent=2)],
                "assertion": {
                    "name": "precision-calibration",
                    "type": "judge",
                    "threshold": 4,
                    "graded_dimensions": [{"name": "precision", "rubric": PRECISION}],
                },
            }
            row = sb.run_one_judge_task(
                task,
                transcripts_dir=output_dir / "transcripts",
                judge_model="gpt-5.6-sol"
                if backend == "codex"
                else "claude-sonnet-4-6",
                judge_backend=backend,
                codex_cmd="codex exec --config model_reasoning_effort=high",
                schema_enforcement="strict",
            )
            row.update(
                calibration_id=g["id"],
                expected_precision_pass=g["expected_precision_pass"],
                expected_precision=g["expected_precision"],
                output_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
            )
            receipt.write_text(json.dumps(row, indent=2) + "\n")
            return row

        order = sorted(
            gold,
            key=lambda g: hashlib.sha256(("cal-order:" + g["id"]).encode()).hexdigest(),
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(run, order))
        assert len(rows) == 24 and all(
            row.get("returncode") == 0
            and not any(
                row.get(k)
                for k in ["parse_error", "schema_errors", "verdict_validation_error"]
            )
            for row in rows
        )
        correct = sum(row["passed"] == row["expected_precision_pass"] for row in rows)
        false_rejections = sum(
            not row["passed"] and row["expected_precision_pass"] for row in rows
        )
        return {
            "n": 24,
            "correct": correct,
            "false_rejections": false_rejections,
            "passed_protocol": correct / 24 >= 0.9 and false_rejections <= 1,
            "rows": rows,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = dict(
            zip(["codex", "claude"], pool.map(backend_run, ["codex", "claude"]))
        )
    (dest / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    assert all(row["passed_protocol"] for row in results.values())


if __name__ == "__main__":
    main()

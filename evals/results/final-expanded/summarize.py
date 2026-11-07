"""Summarize immutable old/final runs through shared native harness artifacts."""

import hashlib
import itertools
import json
import random
import statistics
from pathlib import Path

import analyze_overhead

r = Path(__file__).resolve().parent
m = json.loads((r / "manifest.json").read_text())
ids = [c["id"] for c in m["cases"]]
old_ids = ids[:4]
new_ids = ids[4:]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def uncertainty(ds):
    values = list(ds.values())
    n = len(values)
    mean = statistics.mean(values)
    rng = random.Random(20261107)
    boot = sorted(statistics.mean(rng.choices(values, k=n)) for _ in range(50000))
    signs = [
        statistics.mean(v * s for v, s in zip(values, sign))
        for sign in itertools.product([-1, 1], repeat=n)
    ]
    return {
        "case_clusters": n,
        "quality_delta": mean,
        "bootstrap_95_ci": [boot[1249], boot[48749]],
        "exact_two_sided_sign_flip_p": sum(abs(x) >= abs(mean) - 1e-12 for x in signs)
        / len(signs),
        "case_deltas": ds,
    }


def judge_summary(backend):
    results = [
        json.loads(p.read_text())
        for p in sorted((r / ("judges-" + backend)).glob("candidate-*.json"))
    ]
    lookup = {(x["case_id"], x["variant"], x["run_number"]): x for x in results}
    rows = []
    missing = []
    for case in ids:
        for arm in ["old_skill", "with_skill"]:
            for run in [1, 2, 3]:
                base = r / "runs" / case / arm / ("run-" + str(run))
                key = (case, arm, run)
                j = lookup.get(key)
                if not j or not (base / "metadata.json").exists():
                    missing.append(key)
                    continue
                meta = json.loads((base / "metadata.json").read_text())
                if (
                    meta.get("returncode") != 0
                    or j.get("parse_error")
                    or j.get("returncode") != 0
                    or j.get("schema_errors")
                ):
                    raise ValueError("Invalid answer/judgment " + str(key))
                dims = j["dimension_scores"]
                assert set(dims) == {"recall", "precision", "actionability", "evidence"}
                q = statistics.mean((x - 1) / 4 for x in dims.values())
                rows.append(
                    {
                        "case": case,
                        "variant": arm,
                        "run": run,
                        "dimensions": dims,
                        "quality": q,
                        "quality_threshold_pass": q >= 0.85,
                        "judge_rationale": j.get("evidence"),
                        "blinded_candidate_id": j.get("blinded_candidate_id"),
                        "output_sha256": sha(base / "output.md"),
                        "elapsed_seconds": meta["elapsed_ms"] / 1000,
                    }
                )
    if missing:
        raise ValueError("Incomplete " + backend + " " + str(missing))
    slices = {}
    lookup = {(x["case"], x["variant"], x["run"]): x for x in rows}
    for name, case_ids in [("all8", ids), ("previous4", old_ids), ("new4", new_ids)]:
        byarm = {}
        for arm in ["old_skill", "with_skill"]:
            group = [x for x in rows if x["variant"] == arm and x["case"] in case_ids]
            byarm[arm] = {
                "n": len(group),
                "quality_mean": statistics.mean(x["quality"] for x in group),
                "quality_threshold_passes": sum(
                    x["quality_threshold_pass"] for x in group
                ),
                "dimension_means": {
                    k: statistics.mean(x["dimensions"][k] for x in group)
                    for k in ["recall", "precision", "actionability", "evidence"]
                },
            }
        pairs = [
            {
                "case": c,
                "run": run,
                "quality_delta": lookup[(c, "with_skill", run)]["quality"]
                - lookup[(c, "old_skill", run)]["quality"],
                "dimension_deltas": {
                    k: lookup[(c, "with_skill", run)]["dimensions"][k]
                    - lookup[(c, "old_skill", run)]["dimensions"][k]
                    for k in ["recall", "precision", "actionability", "evidence"]
                },
            }
            for c in case_ids
            for run in [1, 2, 3]
        ]
        deltas = {
            c: statistics.mean(x["quality_delta"] for x in pairs if x["case"] == c)
            for c in case_ids
        }
        slices[name] = {
            "by_arm": byarm,
            "paired_runs": len(pairs),
            "pair_wins": sum(x["quality_delta"] > 1e-10 for x in pairs),
            "pair_losses": sum(x["quality_delta"] < -1e-10 for x in pairs),
            "pair_ties": sum(abs(x["quality_delta"]) <= 1e-10 for x in pairs),
            "uncertainty": uncertainty(deltas),
            "pairs": pairs,
        }
    return {"backend": backend, "slices": slices, "runs": rows}


if __name__ == "__main__":
    checks = analyze_overhead.validate_population(
        r, [json.loads(line) for line in (r / "tasks.jsonl").read_text().splitlines()]
    )
    out = {
        "population_checks": checks,
        "judges": {b: judge_summary(b) for b in ["codex", "claude"]},
        "overhead": analyze_overhead.measure(r),
        "protocol_sha256": sha(r / "protocol.json"),
    }
    a = {(x["case"], x["variant"], x["run"]): x for x in out["judges"]["codex"]["runs"]}
    b = {
        (x["case"], x["variant"], x["run"]): x for x in out["judges"]["claude"]["runs"]
    }
    out["judge_agreement"] = {
        "overlap": len(a),
        "quality_threshold_agreement": sum(
            a[k]["quality_threshold_pass"] == b[k]["quality_threshold_pass"] for k in a
        ),
        "mean_absolute_quality_difference": statistics.mean(
            abs(a[k]["quality"] - b[k]["quality"]) for k in a
        ),
        "exact_dimension_agreement": sum(
            a[k]["dimensions"][d] == b[k]["dimensions"][d]
            for k in a
            for d in ["recall", "precision", "actionability", "evidence"]
        ),
    }
    (r / "summary.json").write_text(json.dumps(out, indent=2) + "\n")
    print(
        json.dumps(
            {
                "judges": {b: x["slices"] for b, x in out["judges"].items()},
                "overhead": {k: v for k, v in out["overhead"].items() if k != "runs"},
                "judge_agreement": out["judge_agreement"],
            },
            indent=2,
        )
    )

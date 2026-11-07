"""Aggregate native anchored verdicts; keep factual precision separate from overall score."""

import hashlib
import itertools
import json
import random
import statistics
import sys
from pathlib import Path

r = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_overhead

rows = [json.loads(line) for line in (r / "tasks.jsonl").read_text().splitlines()]
expected = {(x["case_id"], x["variant"], x["run_number"]) for x in rows}
assert len(expected) == len(rows)
manifest = json.loads((r / "manifest.json").read_text())
protocol = json.loads((r / "protocol.json").read_text())
checks = analyze_overhead.validate_population(r, rows)
clusters = protocol.get("clusters") or {
    c["id"]: c["id"].removeprefix("repair-")[0] for c in manifest["cases"]
}
cohorts = protocol.get("cohorts", {}) | {"all": [c["id"] for c in manifest["cases"]]}


def uncertainty(effects):
    values = list(effects.values())
    n = len(values)
    rng = random.Random(20261107)
    boot = sorted(statistics.mean(rng.choices(values, k=n)) for _ in range(50000))
    mean = statistics.mean(values)
    flips = [
        statistics.mean(v * s for v, s in zip(values, sign))
        for sign in itertools.product([-1, 1], repeat=n)
    ]
    return {
        "clusters": n,
        "delta": mean,
        "bootstrap_95_ci": [boot[1249], boot[48749]],
        "exact_sign_flip_p": sum(abs(v) >= abs(mean) - 1e-12 for v in flips)
        / len(flips),
        "cluster_effects": effects,
    }


judges = {}
for backend in ["codex", "claude"]:
    js = [
        json.loads(p.read_text())
        for p in (r / ("judges-" + backend)).glob("candidate-*.json")
    ]
    actual = {(x["case_id"], x["variant"], x["run_number"]) for x in js}
    assert len(js) == len(expected) and actual == expected, (backend, len(js))
    judged = []
    for j in js:
        assert j.get("returncode") == 0 and not any(
            j.get(k)
            for k in ["parse_error", "schema_errors", "verdict_validation_error"]
        )
        dims = j["dimension_scores"]
        assert set(dims) == {
            "recall",
            "precision",
            "actionability",
            "evidence",
        } and all(1 <= v <= 5 for v in dims.values())
        base = (
            r / "runs" / j["case_id"] / j["variant"] / ("run-" + str(j["run_number"]))
        )
        score = statistics.mean((x - 1) / 4 for x in dims.values())
        judged.append(
            {
                "case": j["case_id"],
                "variant": j["variant"],
                "run": j["run_number"],
                "dimensions": dims,
                "quality": score,
                "quality_pass": score >= 0.85,
                "material_precision_error": dims["precision"] <= 3,
                "output_sha256": hashlib.sha256(
                    (base / "output.md").read_bytes()
                ).hexdigest(),
                "rationale": j.get("evidence"),
            }
        )
    lookup = {(x["case"], x["variant"], x["run"]): x for x in judged}
    slices = {}
    for group, ids in cohorts.items():
        subsets = {
            a: [x for x in judged if x["variant"] == a and x["case"] in ids]
            for a in ["old_skill", "with_skill"]
        }
        arms = {
            a: {
                "n": len(xs),
                "quality_mean": statistics.mean(x["quality"] for x in xs),
                "quality_passes": sum(x["quality_pass"] for x in xs),
                "material_precision_error_reports": sum(
                    x["material_precision_error"] for x in xs
                ),
                "dimension_means": {
                    k: statistics.mean(x["dimensions"][k] for x in xs)
                    for k in ["recall", "precision", "actionability", "evidence"]
                },
            }
            for a, xs in subsets.items()
        }
        pairs = []
        for c, arm, rep in sorted(expected):
            if arm != "old_skill" or c not in ids:
                continue
            a = lookup[c, "old_skill", rep]
            b = lookup[c, "with_skill", rep]
            pairs.append(
                {
                    "case": c,
                    "run": rep,
                    "quality_delta": b["quality"] - a["quality"],
                    "precision_delta": b["dimensions"]["precision"]
                    - a["dimensions"]["precision"],
                    "recall_delta": b["dimensions"]["recall"]
                    - a["dimensions"]["recall"],
                }
            )
        effects = {
            cluster: statistics.mean(
                x["quality_delta"] for x in pairs if clusters[x["case"]] == cluster
            )
            for cluster in sorted({clusters[x["case"]] for x in pairs})
        }
        slices[group] = {
            "by_arm": arms,
            "pairs": pairs,
            "wins": sum(x["quality_delta"] > 1e-10 for x in pairs),
            "losses": sum(x["quality_delta"] < -1e-10 for x in pairs),
            "ties": sum(abs(x["quality_delta"]) <= 1e-10 for x in pairs),
            "uncertainty": uncertainty(effects),
        }
    judges[backend] = {
        "slices": slices,
        "runs": sorted(judged, key=lambda x: (x["case"], x["variant"], x["run"])),
    }
a = {(x["case"], x["variant"], x["run"]): x for x in judges["codex"]["runs"]}
b = {(x["case"], x["variant"], x["run"]): x for x in judges["claude"]["runs"]}
agreement = {
    "reports": len(a),
    "quality_pass_agreement": sum(
        a[k]["quality_pass"] == b[k]["quality_pass"] for k in a
    ),
    "material_precision_error_agreement": sum(
        a[k]["material_precision_error"] == b[k]["material_precision_error"] for k in a
    ),
    "mean_absolute_quality_difference": statistics.mean(
        abs(a[k]["quality"] - b[k]["quality"]) for k in a
    ),
}
result = {
    "population_checks": checks,
    "judges": judges,
    "judge_agreement": agreement,
    "overhead": analyze_overhead.measure(r),
}
(r / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
print(
    json.dumps(
        {
            "judges": {
                j: {
                    s: {
                        "arms": v["by_arm"],
                        "wins": v["wins"],
                        "losses": v["losses"],
                        "ties": v["ties"],
                        "uncertainty": v["uncertainty"],
                    }
                    for s, v in d["slices"].items()
                }
                for j, d in judges.items()
            },
            "agreement": agreement,
            "efficiency": {k: v for k, v in result["overhead"].items() if k != "runs"},
        },
        indent=2,
    )
)

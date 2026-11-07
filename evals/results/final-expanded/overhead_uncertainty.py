"""Describe matched resource variation using paired project clusters."""

import json
import random
import statistics
import sys
from pathlib import Path

import analyze_overhead


def main():
    root = (
        Path(sys.argv[1]).resolve()
        if len(sys.argv) > 1
        else Path(__file__).resolve().parent
    )
    data = analyze_overhead.measure(root)
    keys = [
        "total_tokens",
        "cached_input_tokens",
        "uncached_input_tokens",
        "output_tokens",
        "elapsed_seconds",
    ]
    cases = sorted({row["case"] for row in data["runs"]})
    by_case = {
        case: {
            arm: {
                key: statistics.mean(
                    row[key]
                    for row in data["runs"]
                    if row["case"] == case and row["arm"] == arm
                )
                for key in keys
            }
            for arm in ["old_skill", "with_skill"]
        }
        for case in cases
    }
    rng = random.Random(20261107)
    indices = [[rng.randrange(len(cases)) for _ in cases] for _ in range(50000)]
    intervals = {}
    for key in keys:
        samples = sorted(
            (
                statistics.mean(by_case[cases[i]]["with_skill"][key] for i in sample)
                / statistics.mean(by_case[cases[i]]["old_skill"][key] for i in sample)
                - 1
            )
            * 100
            for sample in indices
        )
        intervals[key] = {
            "percent_change": data["relative_mean_changes_percent"][key],
            "case_cluster_percentile_95_ci": [samples[1249], samples[48749]],
        }
    result = {
        "method": "50000 paired case-cluster bootstrap resamples; ratio of means; "
        "seed20261107; descriptive for eight selected projects.",
        "metrics": intervals,
        "per_case": by_case,
    }
    (root / "overhead-uncertainty.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(intervals, indent=2))


if __name__ == "__main__":
    main()

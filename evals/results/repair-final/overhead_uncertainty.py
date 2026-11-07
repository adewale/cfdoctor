"""Describe matched resource variation using the preregistered independent clusters."""

import json
import random
import statistics
import sys
from pathlib import Path

import analyze_overhead


def main():
    root = Path(sys.argv[1]).resolve()
    protocol = json.loads((root / "protocol.json").read_text())
    data = analyze_overhead.measure(root)
    keys = [
        "total_tokens",
        "cached_input_tokens",
        "uncached_input_tokens",
        "output_tokens",
        "elapsed_seconds",
    ]
    cases = sorted({row["case"] for row in data["runs"]})
    assignment = protocol["clusters"]
    clusters = sorted({assignment[case] for case in cases})
    by_cluster = {
        cluster: {
            arm: {
                key: statistics.mean(
                    row[key]
                    for row in data["runs"]
                    if assignment[row["case"]] == cluster and row["arm"] == arm
                )
                for key in keys
            }
            for arm in ["old_skill", "with_skill"]
        }
        for cluster in clusters
    }
    rng = random.Random(20261107)
    indices = [[rng.randrange(len(clusters)) for _ in clusters] for _ in range(50000)]
    intervals = {}
    for key in keys:
        samples = sorted(
            (
                statistics.mean(
                    by_cluster[clusters[i]]["with_skill"][key] for i in sample
                )
                / statistics.mean(
                    by_cluster[clusters[i]]["old_skill"][key] for i in sample
                )
                - 1
            )
            * 100
            for sample in indices
        )
        intervals[key] = {
            "percent_change": data["relative_mean_changes_percent"][key],
            "cluster_percentile_95_ci": [samples[1249], samples[48749]],
        }
    result = {
        "method": "50000 paired cluster bootstrap resamples; ratio of means; seed20261107. Descriptive, provider cache/concurrency not controlled.",
        "clusters": len(clusters),
        "metrics": intervals,
        "per_cluster": by_cluster,
    }
    (root / "overhead-uncertainty.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(intervals, indent=2))


if __name__ == "__main__":
    main()

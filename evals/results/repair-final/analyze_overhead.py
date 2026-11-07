"""Observable trace cost facts; does not estimate per-file token attribution."""

import collections
import hashlib
import json
import re
import shlex
import statistics
import sys
from pathlib import Path

r = Path(__file__).resolve().parent


def measure(root):
    rows = []
    for p in sorted((root / "runs").glob("*/*/run-*/trace.jsonl")):
        meta_path = p.parent / "metadata.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        usage = {}
        commands = []
        for line in p.read_text().splitlines():
            e = json.loads(line)
            if e.get("type") == "turn.completed":
                usage = e.get("usage", {})
            if (
                e.get("type") == "item.completed"
                and e.get("item", {}).get("type") == "command_execution"
            ):
                item = e["item"]
                cmd = item.get("command", "")
                out = item.get("aggregated_output", "")
                try:
                    parts = shlex.split(cmd)
                    if "-lc" in parts:
                        cmd = parts[parts.index("-lc") + 1]
                except ValueError:
                    pass
                groups = []
                if "skills/" in cmd:
                    groups.append("skill")
                if "inputs/" in cmd and ".md" in cmd:
                    groups.append("docs")
                if "project/" in cmd or ".project.json" in cmd:
                    groups.append("source")
                commands.append(
                    {
                        "command_sha256": hashlib.sha256(cmd.encode()).hexdigest(),
                        "output_chars": len(out),
                        "group": "+".join(groups) or "other",
                        "bundle_mentioned": ".project.json" in cmd,
                        "bundle_content_read": bool(
                            ".project.json" in cmd
                            and re.search(r"\b(cat|sed|nl|read_text|json.load)\b", cmd)
                        ),
                        "workload_reference_read": bool(
                            "workload-boundaries.md" in cmd
                            and re.search(r"\b(cat|sed|nl|read_text)\b", cmd)
                        ),
                        "truncation_marker": bool(
                            re.search(
                                r"(?:output truncated|truncated output|tokens truncated)",
                                out,
                                re.IGNORECASE,
                            )
                        ),
                    }
                )
        if not usage:
            continue
        rows.append(
            {
                "case": p.parts[-4],
                "arm": p.parts[-3],
                "run": int(p.parts[-2].split("-")[1]),
                "elapsed_seconds": meta["elapsed_ms"] / 1000,
                "returncode": meta["returncode"],
                "input_tokens": usage.get("input_tokens", 0),
                "cached_input_tokens": usage.get("cached_input_tokens", 0),
                "uncached_input_tokens": usage.get("input_tokens", 0)
                - usage.get("cached_input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "reasoning_output_tokens": usage["reasoning_output_tokens"],
                "nonreasoning_output_tokens": usage["output_tokens"]
                - usage["reasoning_output_tokens"],
                "final_answer_words": len((p.parent / "output.md").read_text().split()),
                "final_answer_chars": len((p.parent / "output.md").read_text()),
                "total_tokens": usage.get("input_tokens", 0)
                + usage.get("output_tokens", 0),
                "command_count": len(commands),
                "output_chars": sum(c["output_chars"] for c in commands),
                "bundle_mention_commands": sum(c["bundle_mentioned"] for c in commands),
                "bundle_content_read_commands": sum(
                    c["bundle_content_read"] for c in commands
                ),
                "workload_reference_reads": sum(
                    c["workload_reference_read"] for c in commands
                ),
                "truncation_markers": sum(c["truncation_marker"] for c in commands),
                "output_chars_by_command_group": dict(
                    collections.Counter(
                        {
                            g: sum(
                                c["output_chars"] for c in commands if c["group"] == g
                            )
                            for g in {c["group"] for c in commands}
                        }
                    )
                ),
            }
        )
    by_arm = {}
    keys = [
        "input_tokens",
        "cached_input_tokens",
        "uncached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "nonreasoning_output_tokens",
        "final_answer_words",
        "final_answer_chars",
        "total_tokens",
        "elapsed_seconds",
        "command_count",
        "output_chars",
        "bundle_mention_commands",
        "bundle_content_read_commands",
        "workload_reference_reads",
        "truncation_markers",
    ]
    for arm in ["old_skill", "with_skill"]:
        group = [x for x in rows if x["arm"] == arm]
        if not group:
            continue
        by_arm[arm] = {
            "n": len(group),
            "means": {k: statistics.mean(x[k] for x in group) for k in keys},
            "medians": {k: statistics.median(x[k] for x in group) for k in keys},
        }
    deltas = (
        {
            k: (by_arm["with_skill"]["means"][k] / by_arm["old_skill"]["means"][k] - 1)
            * 100
            if by_arm.get("old_skill", {}).get("means", {}).get(k)
            else None
            for k in keys
        }
        if len(by_arm) == 2
        else {}
    )
    return {
        "by_arm": by_arm,
        "relative_mean_changes_percent": deltas,
        "runs": rows,
        "limits": [
            "Provider turn input totals include repeated context across model calls. Cached input is a subset of input, not an additional token category.",
            "Command-output characters are observable transport volume, not exact prompt tokens or per-file cost attribution. Mixed commands cannot be uniquely attributed.",
            "Codex exposes tokens but no dollar cost here. Missing failed-run usage is unknown, not zero.",
        ],
    }


def validate_population(root, expected_rows):
    expected = {
        (row["case_id"], row["variant"], int(row["run_number"]))
        for row in expected_rows
    }
    if len(expected) != len(expected_rows):
        raise ValueError("Duplicate expected identities")
    seen = set()
    for p in sorted((root / "runs").glob("*/*/run-*/trace.jsonl")):
        key = (p.parts[-4], p.parts[-3], int(p.parts[-2].split("-")[1]))
        if key in seen:
            raise ValueError("Duplicate recorded identity")
        seen.add(key)
        meta = json.loads(p.with_name("metadata.json").read_text())
        assert meta.get("returncode") == 0 and meta.get("timed_out") is False, (
            "Failed run",
            key,
        )
        assert p.with_name("output.md").read_text().strip(), (
            "Missing final answer",
            key,
        )
        events = [json.loads(line) for line in p.read_text().splitlines()]
        terminals = [
            e.get("usage") for e in events if e.get("type") == "turn.completed"
        ]
        assert len(terminals) == 1 and isinstance(terminals[0], dict), (
            "Unexpected terminal usage",
            key,
        )
        u = terminals[0]
        assert all(
            isinstance(u.get(k), int) and not isinstance(u[k], bool) and u[k] >= 0
            for k in [
                "input_tokens",
                "cached_input_tokens",
                "output_tokens",
                "reasoning_output_tokens",
            ]
        )
        assert (
            u["cached_input_tokens"] <= u["input_tokens"]
            and u["reasoning_output_tokens"] <= u["output_tokens"]
        )
        assert (
            meta["input_tokens"] == u["input_tokens"]
            and meta["output_tokens"] == u["output_tokens"]
        )
        assert meta["total_tokens"] == u["input_tokens"] + u["output_tokens"]
    if seen != expected:
        raise ValueError(
            {"missing": sorted(expected - seen), "unexpected": sorted(seen - expected)}
        )
    return {
        "successful_balanced_expected_runs": len(seen),
        "single_terminal_usage_per_run": True,
        "native_metadata_matches_trace": True,
        "cache_and_reasoning_subsets_valid": True,
    }


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else r
    result = measure(target)
    (target / "overhead-analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {k: result[k] for k in ["by_arm", "relative_mean_changes_percent"]},
            indent=2,
        )
    )

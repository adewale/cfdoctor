"""Describe observable native command evidence, not an OS confinement proof."""

import hashlib
import json
import re
import shlex
import sys
from pathlib import Path

r = (
    Path(sys.argv[1]).resolve()
    if len(sys.argv) > 1
    else Path(__file__).resolve().parent
)
rows = []
for p in sorted((r / "runs").glob("*/*/run-*/trace.jsonl")):
    if not p.with_name("metadata.json").exists():
        continue
    commands = []
    for s in p.read_text().splitlines():
        e = json.loads(s)
        item = e.get("item", {})
        if (
            e.get("type") == "item.completed"
            and item.get("type") == "command_execution"
        ):
            c = item.get("command", "")
            try:
                parts = shlex.split(c)
                if "-lc" in parts:
                    c = parts[parts.index("-lc") + 1]
            except ValueError:
                pass
            commands.append(c)
    rows.append(
        {
            "case": p.parts[-4],
            "variant": p.parts[-3],
            "run": int(p.parts[-2].split("-")[1]),
            "completed_commands": len(commands),
            "skill_read_observed": any(
                "skills/" in c and "SKILL.md" in c for c in commands
            ),
            "scanner_observed": any("cfdoctor_static_scan.py" in c for c in commands),
            "network_command_candidates": [
                c
                for c in commands
                if re.search(
                    r"(?:^|[;&|\n])\s*(?:curl|wget|gh\s|git\s+(?:clone|fetch))\b", c
                )
            ],
            "target_execution_candidates": [
                c
                for c in commands
                if re.search(
                    r"(?:^|[;&|\n])\s*(?:node\s|npm\s|npx\s|bun\s|pnpm\s|yarn\s)", c
                )
            ],
            "external_path_command_candidates": [
                c for c in commands if re.search(r"/(?:Users|home)/", c)
            ],
            "command_sha256": [
                hashlib.sha256(c.encode()).hexdigest() for c in commands
            ],
            "output_sha256": hashlib.sha256(
                p.with_name("output.md").read_bytes()
            ).hexdigest(),
        }
    )
result = {
    "expected_reports": len((r / "tasks.jsonl").read_text().splitlines()),
    "observed_reports": len(rows),
    "limits": "Heuristic command candidates require source review. Absence of a candidate is not an OS sandbox or provider-isolation proof. No target behavior was dynamically tested.",
    "runs": rows,
}
(r / "process-audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(
    "Observed",
    len(rows),
    "reports; suspicious candidates:",
    sum(
        len(x[k])
        for x in rows
        for k in [
            "network_command_candidates",
            "target_execution_candidates",
            "external_path_command_candidates",
        ]
    ),
)

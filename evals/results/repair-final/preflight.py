import hashlib
import json
import sys
import tempfile
from pathlib import Path

import run_round

r = Path(sys.argv[1]).resolve()
sb = run_round.sb
rows = sb.load_jsonl(r / "tasks.jsonl")
pairs = {}
checks = []
for row in rows:
    pt = sb.PreparedTask.from_row(row)
    with tempfile.TemporaryDirectory(prefix="cfdoctor-repair-preflight-") as td:
        ws = Path(td)
        s, i = run_round.mount_project(pt, ws)
        bundle = json.loads(Path(pt.input_files[0]).read_text())
        actual = {
            p.relative_to(ws / "project").as_posix(): p.read_bytes()
            for p in (ws / "project").rglob("*")
            if p.is_file()
        }
        assert actual == {n: t.encode() for n, t in bundle["files"].items()}
        assert not list(ws.rglob("*.project.json"))
        prompt = sb.build_task_prompt(pt, skill_paths=s, input_files=i)
        h = hashlib.sha256(prompt.encode()).hexdigest()
        pairs.setdefault((row["case_id"], row["run_number"]), []).append(h)
        checks.append(
            {
                "case": row["case_id"],
                "variant": row["variant"],
                "run": row["run_number"],
                "prompt_sha256": h,
                "raw_source_verified": True,
                "serialized_source_unmounted": True,
                "oracle_unmounted": True,
            }
        )
assert len(pairs) * 2 == len(rows) and all(
    len(v) == 2 and len(set(v)) == 1 for v in pairs.values()
)
(r / "isolation-receipt.json").write_text(
    json.dumps(
        {
            "timing": "Builder invariant validation; refer to protocol for input freeze and launch time.",
            "pairs": len(pairs),
            "checks": checks,
        },
        indent=2,
    )
    + "\n"
)
print(
    "Verified",
    len(rows),
    "raw-only isolated workspaces and",
    len(pairs),
    "identical paired prompts.",
)

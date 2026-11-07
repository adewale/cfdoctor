import hashlib
import json
import tempfile
from pathlib import Path

import run_round as rr

r = Path(__file__).resolve().parent
sb = rr.sb
rows = sb.load_jsonl(r / "tasks.jsonl")
pairs = {}
checks = []
for row in rows:
    pt = sb.PreparedTask.from_row(row)
    with tempfile.TemporaryDirectory(prefix="cfdoctor-final-preflight-") as tmp:
        ws = Path(tmp)
        s, i = rr.mount_project(pt, ws)
        prompt = sb.build_task_prompt(pt, skill_paths=s, input_files=i)
        assert not list(ws.rglob("*.project.json"))
        assert not any(
            "hidden" in x.parts or "expected_behavior" in x.name for x in ws.rglob("*")
        )
        b = json.loads(Path(pt.input_files[0]).read_text())
        assert {
            p.relative_to(ws / "project").as_posix(): p.read_bytes()
            for p in (ws / "project").rglob("*")
            if p.is_file()
        } == {n: t.encode() for n, t in b["files"].items()}
        key = (row["case_id"], row["run_number"])
        digest = hashlib.sha256(prompt.encode()).hexdigest()
        pairs.setdefault(key, []).append(digest)
        checks.append(
            {
                "case": key[0],
                "run": key[1],
                "variant": row["variant"],
                "prompt_sha256": digest,
                "selected_skill_sha256": hashlib.sha256(
                    (ws / "skills/root-0/SKILL.md").read_bytes()
                ).hexdigest(),
                "raw_source_verified": True,
                "serialized_source_unmounted": True,
                "oracle_unmounted": True,
            }
        )
assert len(pairs) == 24 and all(
    len(v) == 2 and len(set(v)) == 1 for v in pairs.values()
)
(r / "isolation-receipt.json").write_text(json.dumps(checks, indent=2) + "\n")
p = r / "protocol.json"
d = json.loads(p.read_text())
d["operator_script_hashes"] = {
    n: hashlib.sha256((r / n).read_bytes()).hexdigest()
    for n in ["build.py", "run_round.py", "judge_round.py", "preflight.py"]
    if (r / n).exists()
}
p.write_text(json.dumps(d, indent=2) + "\n")
print(
    "48 isolated workspaces verified; all 24 paired prompts byte-identical; no serialized source or oracle mounted."
)

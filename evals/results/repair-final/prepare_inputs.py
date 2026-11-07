"""Reconstruct hash-verified raw inputs for the expanded native-harness suite.

Caches avoid network access. Source and docs drift fail closed. Target code is
never imported or executed. Baseline/candidate trees must match the tested pins.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url):
    return subprocess.check_output(
        [
            "curl",
            "-fLSs",
            "--max-time",
            "40",
            "-A",
            "Mozilla/5.0",
            "-H",
            "Accept: text/markdown",
            url,
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--source-cache", type=Path)
    parser.add_argument("--docs-cache", type=Path)
    parser.add_argument(
        "--previous",
        type=Path,
        required=True,
        help="4bdd6c5 checkout for the repair cohort",
    )
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    index = json.loads((here / "source-index.json").read_text())
    hashes = json.loads((here / "skill-files.json").read_text())
    for arm, checkout in [
        ("main", args.baseline),
        ("previous", args.previous),
        ("candidate", args.candidate),
    ]:
        root = checkout.resolve() / "skills/cloudflare-doctor"
        if not (root / "SKILL.md").is_file():
            raise ValueError("Missing skill: " + str(root))
        actual = {
            p.relative_to(root).as_posix(): digest(p.read_bytes())
            for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
        }
        if actual != hashes[arm]:
            raise ValueError("Installable skill differs from evaluated tree: " + arm)
    out = args.work.resolve()
    inputs = out / "inputs"
    inputs.mkdir(parents=True, exist_ok=False)
    for project in index["projects"]:
        if args.source_cache:
            raw = (args.source_cache / project["bundle"]).read_bytes()
        else:
            files = {}
            for item in project["files"]:
                text = fetch(item["url"]).decode("utf-8")
                normalized = text.replace("\r\n", "\n")
                candidates = [text, normalized, normalized.rstrip("\n") + "\n"]
                matches = [
                    s for s in candidates if digest(s.encode()) == item["sha256"]
                ]
                if not matches:
                    raise ValueError("Source hash mismatch: " + item["url"])
                files[item["path"]] = matches[0]
            raw = (
                json.dumps(
                    {
                        "repository": project["repository"],
                        "commit": project["commit"],
                        "files": files,
                    },
                    indent=2,
                )
                + "\n"
            ).encode()
        if digest(raw) != project["bundle_sha256"]:
            raise ValueError("Bundle hash mismatch: " + project["bundle"])
        (inputs / project["bundle"]).write_bytes(raw)
    for doc in index["docs"]:
        if args.docs_cache:
            raw = (args.docs_cache / doc["file"]).read_bytes()
        else:
            content = fetch(doc["url"])
            if digest(content) != doc["content_sha256"]:
                raise ValueError(
                    "Docs changed; provide frozen --docs-cache: " + doc["url"]
                )
            raw = doc["prefix"].encode() + content
        if digest(raw) != doc["file_sha256"]:
            raise ValueError("Documentation hash mismatch: " + doc["file"])
        (inputs / doc["file"]).write_bytes(raw)
    regression_inputs = json.loads((here / "regression-inputs.json").read_text())
    for name, bundle in regression_inputs.items():
        (inputs / name).write_text(json.dumps(bundle, indent=2) + "\n")
    allrows = []
    for name, baseline, repeats in [
        ("regressions", args.previous, 2),
        ("projects", args.baseline, 3),
    ]:
        child = out / name
        child.mkdir()
        (child / "inputs").symlink_to(inputs, target_is_directory=True)
        manifest = json.loads((here / (name + "-manifest.json")).read_text())
        manifest["skill_paths"] = [
            str(args.candidate.resolve() / "skills/cloudflare-doctor/SKILL.md")
        ]
        manifest["old_skill_paths"] = [
            str(baseline.resolve() / "skills/cloudflare-doctor/SKILL.md")
        ]
        for case in manifest["cases"]:
            case["files"] = [str(child / f) for f in case["files"]]
        (child / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        shutil.copy2(here / (name + "-protocol.json"), child / "protocol.json")
        subprocess.run(
            [
                sys.executable,
                str(out / "harness/skill_benchmark.py"),
                "prepare",
                str(child / "manifest.json"),
                "--split",
                "tune",
                "--include-old-skill",
                "--runs-per-variant",
                str(repeats),
                "--models",
                "gpt-5.6-sol",
                "--out",
                str(child / "tasks.jsonl"),
            ],
            check=True,
        )
        rows = [json.loads(x) for x in (child / "tasks.jsonl").read_text().splitlines()]
        allrows.extend(rows)
        (child / "runs").mkdir()
        for case in manifest["cases"]:
            (child / "runs" / case["id"]).symlink_to(
                out / "runs" / case["id"], target_is_directory=True
            )
    assert len(allrows) == 92
    (out / "tasks.jsonl").write_text("".join(json.dumps(x) + "\n" for x in allrows))
    for name in [
        "run_round.py",
        "judge_round.py",
        "grading_contract.py",
        "preflight.py",
        "summarize_round.py",
        "analyze_overhead.py",
        "overhead_uncertainty.py",
    ]:
        shutil.copy2(here / name, out / name)
    print("Prepared 92 audits in two separately analyzed cohorts: " + str(out))


if __name__ == "__main__":
    main()

"""Reconstruct hash-verified raw inputs for the expanded native-harness suite.

Caches avoid network access. Source and docs drift fail closed. Target code is
never imported or executed. Baseline/candidate trees must match the tested pins.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
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
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    index = json.loads((here / "source-index.json").read_text())
    protocol = json.loads((here / "protocol.json").read_text())
    for arm, checkout in [("old", args.baseline), ("final", args.candidate)]:
        root = checkout.resolve() / "skills/cloudflare-doctor"
        actual = {
            p.relative_to(root).as_posix(): digest(p.read_bytes())
            for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
        }
        if actual != protocol["skill_files"][arm]:
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
    manifest = json.loads((here / "manifest-template.json").read_text())
    manifest["skill_paths"] = [
        str(args.candidate.resolve() / "skills/cloudflare-doctor/SKILL.md")
    ]
    manifest["old_skill_paths"] = [
        str(args.baseline.resolve() / "skills/cloudflare-doctor/SKILL.md")
    ]
    for case in manifest["cases"]:
        case["files"] = [str(out / f) for f in case["files"]]
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for name in [
        "run_round.py",
        "judge_round.py",
        "summarize.py",
        "analyze_overhead.py",
        "overhead_uncertainty.py",
        "apply_oracle_addenda.py",
        "oracle-addendum-pastebin.md",
        "oracle-addendum-status.md",
    ]:
        shutil.copyfile(here / name, out / name)
    portable = here / "preflight-portable.py"
    shutil.copyfile(
        portable if portable.exists() else here / "preflight.py", out / "preflight.py"
    )
    shutil.copyfile(here / "protocol.json", out / "protocol.json")
    print(
        "Prepared eight hash-verified projects and 16 documentation snapshots: "
        + str(out)
    )


if __name__ == "__main__":
    main()

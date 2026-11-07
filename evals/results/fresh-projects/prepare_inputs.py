"""Reconstruct raw inputs for the pinned native-harness evaluation.

No target code is imported or executed. Frozen caches avoid network access.
Remote content must match the recorded hashes; document drift fails closed.
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
    return subprocess.check_output([
        "curl", "-fLSs", "--max-time", "40", "-A", "Mozilla/5.0",
        "-H", "Accept: text/markdown", url,
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--manifest-template", default="manifest-template.json")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--source-cache", type=Path)
    parser.add_argument("--docs-cache", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    index = json.loads((here / "source-index.json").read_text())
    out = args.work.resolve()
    inputs = out / "inputs"
    inputs.mkdir(parents=True, exist_ok=False)
    for project in index["projects"]:
        if args.source_cache:
            raw = (args.source_cache / project["bundle"]).read_bytes()
        else:
            files = {}
            for item in project["files"]:
                text = fetch(item["url"]).decode("utf-8").replace("\r\n", "\n")
                candidates = [text, text.rstrip("\n") + "\n"]
                matching = [s for s in candidates if digest(s.encode()) == item["sha256"]]
                if not matching:
                    raise ValueError("Pinned source hash mismatch: " + item["url"])
                files[item["path"]] = matching[0]
            raw = (json.dumps({"repository": project["repository"],
                               "commit": project["commit"], "files": files}, indent=2) + "\n").encode()
        if digest(raw) != project["bundle_sha256"]:
            raise ValueError("Raw bundle hash mismatch: " + project["bundle"])
        (inputs / project["bundle"]).write_bytes(raw)
    for doc in index["docs"]:
        if args.docs_cache:
            raw = (args.docs_cache / doc["file"]).read_bytes()
        else:
            content = fetch(doc["url"])
            if digest(content) != doc["content_sha256"]:
                raise ValueError("Official docs changed; supply the frozen --docs-cache: " + doc["url"])
            raw = doc["prefix"].encode() + content
        if digest(raw) != doc["file_sha256"]:
            raise ValueError("Frozen documentation hash mismatch: " + doc["file"])
        (inputs / doc["file"]).write_bytes(raw)
    manifest = json.loads((here / args.manifest_template).read_text())
    manifest["skill_paths"] = [str(args.candidate.resolve() / "skills/cloudflare-doctor/SKILL.md")]
    manifest["old_skill_paths"] = [str(args.baseline.resolve() / "skills/cloudflare-doctor/SKILL.md")]
    for case in manifest["cases"]:
        case["files"] = [str(out / file) for file in case["files"]]
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for name in ["run_round.py", "judge_round.py", "summarize_round.py"]:
        shutil.copyfile(here / name, out.parent / name)
    print("Prepared hash-verified source and documentation: " + str(out))


if __name__ == "__main__":
    main()

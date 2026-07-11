#!/usr/bin/env python3
"""Capture a private, read-only Wrangler snapshot of a Worker or Pages project.

The script never installs Wrangler and never mutates Cloudflare resources. It
requires an existing Wrangler executable plus an explicit approval flag, runs a
small allowlist of authenticated read commands, writes private local artifacts,
and records command/file hashes in manifest.json. Raw outputs may contain source,
plain vars, resource names, routes, and account metadata: review before sharing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
VERSION_RE = re.compile(r"^[A-Za-z0-9-]{1,128}$")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def global_args(profile: str | None) -> list[str]:
    return ["--profile", profile] if profile else []


def static_plan(kind: str, name: str, wrangler: str, profile: str | None, metadata_only: bool) -> list[list[str]]:
    suffix = global_args(profile)
    if kind == "worker":
        commands = [
            [wrangler, "deployments", "status", "--name", name, "--json", *suffix],
            [wrangler, "deployments", "list", "--name", name, "--json", *suffix],
            [wrangler, "versions", "list", "--name", name, "--json", *suffix],
            [wrangler, "secret", "list", "--name", name, "--format", "json", *suffix],
            [wrangler, "versions", "view", "<ACTIVE_VERSION_ID>", "--name", name, "--json", *suffix],
        ]
        if not metadata_only:
            # --no-delegate-c3 keeps this inside Wrangler's direct dashboard
            # downloader: remote reads plus local files, no package scaffolder.
            commands.append([wrangler, "init", "--from-dash", name, "--no-delegate-c3", *suffix])
        return commands
    commands = [
        [wrangler, "pages", "deployment", "list", "--project-name", name, "--json", *suffix],
        [wrangler, "pages", "secret", "list", "--project-name", name, *suffix],
    ]
    if not metadata_only:
        commands.append([wrangler, "pages", "download", "config", name, "--force", *suffix])
    return commands


def git_root(path: Path) -> Path | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(proc.stdout.strip()).resolve()


def write_private(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)


def run_command(
    *,
    label: str,
    argv: list[str],
    cwd: Path,
    output: Path,
    timeout: int,
    expect_json: bool,
) -> tuple[dict[str, Any], Any | None]:
    started = utc_now()
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        write_private(output.with_suffix(output.suffix + ".error.txt"), f"{type(exc).__name__}\n")
        return {
            "label": label,
            "argv": argv,
            "started_at": started,
            "finished_at": utc_now(),
            "returncode": None,
            "output": None,
            "error": type(exc).__name__,
        }, None

    write_private(output, proc.stdout)
    parsed: Any | None = None
    error: str | None = None
    if proc.stderr:
        write_private(output.with_suffix(output.suffix + ".stderr.txt"), proc.stderr)
    if proc.returncode == 0 and expect_json:
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            error = "invalid-json-output"
    elif proc.returncode != 0:
        error = "wrangler-command-failed"
    snapshot_root = cwd if (cwd / "REVIEW_BEFORE_SHARING.txt").exists() else cwd.parent
    return {
        "label": label,
        "argv": argv,
        "started_at": started,
        "finished_at": utc_now(),
        "returncode": proc.returncode,
        "output": output.relative_to(snapshot_root).as_posix(),
        "output_sha256": sha256(output),
        "error": error,
    }, parsed


def collect_files(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    files: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.name == "manifest.json":
            continue
        if path.is_symlink():
            errors.append(f"symlink-rejected:{path.relative_to(root).as_posix()}")
            continue
        if path.is_file():
            path.chmod(0o600)
            files.append({
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    return files, errors


def capture(args: argparse.Namespace) -> int:
    if not NAME_RE.fullmatch(args.name):
        print("error: project name must contain only letters, numbers, underscores, or dashes", file=sys.stderr)
        return 2
    wrangler = shutil.which(args.wrangler) if os.sep not in args.wrangler else str(Path(args.wrangler).resolve())
    if not wrangler or not Path(wrangler).is_file() or not os.access(wrangler, os.X_OK):
        print("error: executable Wrangler not found; install/pin it in the project first", file=sys.stderr)
        return 2

    plan = static_plan(args.kind, args.name, wrangler, args.profile, args.metadata_only)
    if args.plan:
        print(json.dumps({"kind": args.kind, "name": args.name, "commands": [[wrangler, "--version"], *plan]}, indent=2))
        return 0
    if not args.approve_authenticated_read:
        print("error: pass --approve-authenticated-read after reviewing --plan", file=sys.stderr)
        return 2

    output = args.output_dir.resolve()
    if output.exists() and not output.is_dir():
        print(f"error: output path is not a directory: {output}", file=sys.stderr)
        return 2
    if output.exists() and any(output.iterdir()):
        print(f"error: output directory is not empty: {output}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    repo = git_root(output.parent)
    if repo and (output == repo or repo in output.parents) and not args.allow_repo_output:
        print("error: refusing to write a sensitive snapshot inside a Git worktree; use /tmp or pass --allow-repo-output", file=sys.stderr)
        return 2
    output.mkdir(mode=0o700, exist_ok=True)
    output.chmod(0o700)
    write_private(
        output / "REVIEW_BEFORE_SHARING.txt",
        "PRIVATE WRANGLER SNAPSHOT\nMay contain deployed source, plain vars, routes, resource names, and account metadata.\nReview/redact before sharing. Do not commit this directory.\n",
    )

    commands: list[dict[str, Any]] = []
    failures: list[str] = []
    version_record, _ = run_command(
        label="wrangler-version",
        argv=[wrangler, "--version"],
        cwd=output,
        output=output / "wrangler-version.txt",
        timeout=args.timeout,
        expect_json=False,
    )
    commands.append(version_record)
    if version_record.get("returncode") != 0:
        failures.append("wrangler-version")

    suffix = global_args(args.profile)
    if args.kind == "worker":
        status_record, status = run_command(
            label="deployments-status",
            argv=[wrangler, "deployments", "status", "--name", args.name, "--json", *suffix],
            cwd=output,
            output=output / "worker/deployments-status.json",
            timeout=args.timeout,
            expect_json=True,
        )
        commands.append(status_record)
        if status_record.get("returncode") != 0 or status_record.get("error"):
            failures.append("deployments-status")
        for label, argv, relpath, expect_json in [
            ("deployments-list", [wrangler, "deployments", "list", "--name", args.name, "--json", *suffix], "worker/deployments-list.json", True),
            ("versions-list", [wrangler, "versions", "list", "--name", args.name, "--json", *suffix], "worker/versions-list.json", True),
            ("secret-names", [wrangler, "secret", "list", "--name", args.name, "--format", "json", *suffix], "worker/secret-names.json", True),
        ]:
            record, _ = run_command(label=label, argv=argv, cwd=output, output=output / relpath, timeout=args.timeout, expect_json=expect_json)
            commands.append(record)
            if record.get("returncode") != 0 or record.get("error"):
                failures.append(label)
        versions = status.get("versions", []) if isinstance(status, dict) else []
        for item in versions if isinstance(versions, list) else []:
            version_id = item.get("version_id") if isinstance(item, dict) else None
            if not isinstance(version_id, str) or not VERSION_RE.fullmatch(version_id):
                failures.append("invalid-active-version-id")
                continue
            record, _ = run_command(
                label=f"version-view:{version_id}",
                argv=[wrangler, "versions", "view", version_id, "--name", args.name, "--json", *suffix],
                cwd=output,
                output=output / f"worker/active-versions/{version_id}.json",
                timeout=args.timeout,
                expect_json=True,
            )
            commands.append(record)
            if record.get("returncode") != 0 or record.get("error"):
                failures.append(f"version-view:{version_id}")
        if not args.metadata_only:
            download_dir = output / "download"
            download_dir.mkdir(mode=0o700)
            record, _ = run_command(
                label="init-from-dash",
                argv=[wrangler, "init", "--from-dash", args.name, "--no-delegate-c3", *suffix],
                cwd=download_dir,
                output=output / "worker/init-from-dash.stdout.txt",
                timeout=args.timeout,
                expect_json=False,
            )
            commands.append(record)
            if record.get("returncode") != 0 or record.get("error"):
                failures.append("init-from-dash")
    else:
        for label, argv, relpath, expect_json in [
            ("pages-deployments", [wrangler, "pages", "deployment", "list", "--project-name", args.name, "--json", *suffix], "pages/deployments.json", True),
            ("pages-secret-names", [wrangler, "pages", "secret", "list", "--project-name", args.name, *suffix], "pages/secret-names.txt", False),
        ]:
            record, _ = run_command(label=label, argv=argv, cwd=output, output=output / relpath, timeout=args.timeout, expect_json=expect_json)
            commands.append(record)
            if record.get("returncode") != 0 or record.get("error"):
                failures.append(label)
        if not args.metadata_only:
            download_dir = output / "download"
            download_dir.mkdir(mode=0o700)
            record, _ = run_command(
                label="pages-download-config",
                argv=[wrangler, "pages", "download", "config", args.name, "--force", *suffix],
                cwd=download_dir,
                output=output / "pages/download-config.stdout.txt",
                timeout=args.timeout,
                expect_json=False,
            )
            commands.append(record)
            if record.get("returncode") != 0 or record.get("error"):
                failures.append("pages-download-config")

    files, file_errors = collect_files(output)
    failures.extend(file_errors)
    manifest = {
        "schema_version": 1,
        "created_at": utc_now(),
        "kind": args.kind,
        "name": args.name,
        "authenticated_read_approved": True,
        "metadata_only": args.metadata_only,
        "success": not failures,
        "failures": failures,
        "commands": commands,
        "files": files,
    }
    write_private(output / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"snapshot: {output}")
    print(f"status: {'complete' if not failures else 'partial'}; review REVIEW_BEFORE_SHARING.txt before sharing")
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["worker", "pages"], required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--wrangler", default="wrangler", help="Existing Wrangler executable; no package is installed")
    parser.add_argument("--profile", help="Wrangler authentication profile")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--metadata-only", action="store_true", help="Skip Worker source/config or Pages config download")
    parser.add_argument("--plan", action="store_true", help="Print the exact static command plan without authenticating or writing")
    parser.add_argument("--approve-authenticated-read", action="store_true", help="Confirm the reviewed authenticated read plan")
    parser.add_argument("--allow-repo-output", action="store_true", help="Allow private snapshot output inside a Git worktree")
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error("--timeout must be positive")
    return capture(args)


if __name__ == "__main__":
    raise SystemExit(main())

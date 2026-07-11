from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/capture_wrangler_snapshot.py"
FIXTURES = ROOT / "evals/fixtures/wrangler-snapshot"


class WranglerSnapshotTests(unittest.TestCase):
    def make_fake_wrangler(
        self,
        root: Path,
        *,
        fail_init: bool = False,
        fail_version: bool = False,
        status_json: str | None = None,
        create_symlink: bool = False,
        create_nested_manifest: bool = False,
        require_api_token: bool = False,
        require_eof_stdin: bool = False,
    ) -> Path:
        fake = root / "wrangler"
        status_payload = status_json or (FIXTURES / "worker-deployments-status.json").read_text()
        fake.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json
                import os
                import sys
                from pathlib import Path

                raw_args = sys.argv[1:]
                if "AWS_SECRET_ACCESS_KEY" in os.environ or "NODE_OPTIONS" in os.environ:
                    print("unrelated parent environment leaked", file=sys.stderr)
                    raise SystemExit(12)
                if {require_api_token!r} and os.environ.get("CLOUDFLARE_API_TOKEN") != "fixture-token":
                    print("required Cloudflare authentication missing", file=sys.stderr)
                    raise SystemExit(13)
                if {require_eof_stdin!r} and sys.stdin.read() != "":
                    print("parent stdin leaked", file=sys.stderr)
                    raise SystemExit(14)
                profile = []
                if len(raw_args) >= 2 and raw_args[-2] == "--profile":
                    profile = raw_args[-2:]
                args = raw_args[:-2] if profile else raw_args
                fixture_dir = Path({str(FIXTURES)!r})
                if args == ["--version"]:
                    if {fail_version!r}:
                        print("not wrangler", file=sys.stderr)
                        raise SystemExit(8)
                    print("4.30.0")
                elif args == ["deployments", "status", "--name", "fixture-project", "--json"]:
                    print({status_payload!r}, end="")
                elif args == ["deployments", "list", "--name", "fixture-project", "--json"]:
                    print("[]")
                elif args == ["versions", "list", "--name", "fixture-project", "--json"]:
                    print("[]")
                elif len(args) == 6 and args[:2] == ["versions", "view"] and args[3:] == ["--name", "fixture-project", "--json"]:
                    data = json.loads((fixture_dir / "worker-version-view.json").read_text())
                    data["id"] = args[2]
                    print(json.dumps(data))
                elif args == ["secret", "list", "--name", "fixture-project", "--format", "json"]:
                    print('[{{"name":"API_TOKEN","type":"secret_text"}}]')
                elif args == ["init", "--from-dash", "fixture-project", "--no-delegate-c3"]:
                    if {fail_init!r}:
                        print("assets download unsupported", file=sys.stderr)
                        raise SystemExit(7)
                    project = Path.cwd() / "fixture-project"
                    (project / "src").mkdir(parents=True)
                    (project / "wrangler.jsonc").write_text(json.dumps({{"name": "fixture-project", "workers_dev": False, "routes": [{{"pattern": "fixture.example/*"}}]}}))
                    (project / "src/index.js").write_text('export default {{ fetch() {{ return new Response("ok") }} }}')
                    if {create_symlink!r}:
                        (project / "external-link").symlink_to("/etc/passwd")
                    if {create_nested_manifest!r}:
                        nested_manifest = project / "manifest.json"
                        nested_manifest.write_text('{{"downloaded": true}}')
                        nested_manifest.chmod(0o644)
                    print("downloaded fixture-project")
                elif args == ["pages", "deployment", "list", "--project-name", "fixture-project", "--json"]:
                    print((fixture_dir / "pages-deployments.json").read_text(), end="")
                elif args == ["pages", "secret", "list", "--project-name", "fixture-project"]:
                    print("API_TOKEN (secret_text)")
                elif args == ["pages", "download", "config", "fixture-project", "--force"]:
                    (Path.cwd() / "wrangler.jsonc").write_text(json.dumps({{"name": "fixture-project", "pages_build_output_dir": "dist"}}))
                    print("downloaded pages config fixture-project")
                else:
                    print("unsupported fake command: " + repr(raw_args), file=sys.stderr)
                    raise SystemExit(9)
                """
            ),
            encoding="utf-8",
        )
        fake.chmod(0o755)
        return fake

    def run_capture(
        self,
        fake: Path,
        output: Path,
        *extra: str,
        env: dict[str, str] | None = None,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--wrangler",
                str(fake),
                "--name",
                "fixture-project",
                "--output-dir",
                str(output),
                *extra,
            ],
            capture_output=True,
            text=True,
            env=env,
            input=input_text,
        )

    def test_plan_needs_no_approval_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root)
            output = root / "snapshot"
            proc = self.run_capture(fake, output, "--kind", "worker", "--plan")
            self.assertEqual(0, proc.returncode, proc.stderr)
            plan = json.loads(proc.stdout)
            self.assertIn([str(fake.resolve()), "deployments", "status", "--name", "fixture-project", "--json"], plan["commands"])
            self.assertFalse(output.exists())

    def test_capture_requires_explicit_authenticated_read_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root)
            output = root / "snapshot"
            proc = self.run_capture(fake, output, "--kind", "worker")
            self.assertEqual(2, proc.returncode)
            self.assertIn("--approve-authenticated-read", proc.stderr)
            self.assertFalse(output.exists())

    def test_worker_snapshot_downloads_config_and_active_versions_privately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root)
            output = root / "snapshot"
            proc = self.run_capture(fake, output, "--kind", "worker", "--approve-authenticated-read")
            self.assertEqual(0, proc.returncode, proc.stderr)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertTrue(manifest["success"])
            labels = [entry["label"] for entry in manifest["commands"]]
            self.assertEqual(2, sum(label.startswith("version-view:") for label in labels))
            self.assertIn("init-from-dash", labels)
            self.assertTrue((output / "download/fixture-project/wrangler.jsonc").is_file())
            version = json.loads((output / "worker/active-versions/10000000-0000-0000-0000-000000000000.json").read_text())
            self.assertEqual({"id", "number", "metadata", "annotations", "resources"}, set(version))
            status = json.loads((output / "worker/deployments-status.json").read_text())
            self.assertEqual(
                {"id", "source", "strategy", "author_email", "annotations", "versions", "created_on"},
                set(status),
            )
            forbidden = {"deploy", "delete", "put", "bulk", "rollback"}
            for entry in manifest["commands"]:
                self.assertTrue(forbidden.isdisjoint(entry["argv"][1:3]), entry["argv"])
            self.assertEqual(0o700, stat.S_IMODE(output.stat().st_mode))
            for path in output.rglob("*"):
                if path.is_dir():
                    self.assertEqual(0o700, stat.S_IMODE(path.stat().st_mode), path)
                elif path.is_file():
                    self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode), path)

    def test_failed_config_download_keeps_partial_metadata_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root, fail_init=True)
            output = root / "snapshot"
            proc = self.run_capture(fake, output, "--kind", "worker", "--approve-authenticated-read")
            self.assertEqual(1, proc.returncode)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertFalse(manifest["success"])
            self.assertIn("init-from-dash", manifest["failures"])
            failed = next(command for command in manifest["commands"] if command["label"] == "init-from-dash")
            self.assertEqual(7, failed["returncode"])
            self.assertEqual("wrangler-command-failed", failed["error"])
            self.assertIsNotNone(failed["output_sha256"])
            self.assertTrue((output / "worker/deployments-status.json").is_file())
            self.assertTrue((output / "worker/init-from-dash.stdout.txt.stderr.txt").is_file())

    def test_missing_active_versions_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root, status_json="{}")
            output = root / "snapshot"
            proc = self.run_capture(
                fake,
                output,
                "--kind",
                "worker",
                "--metadata-only",
                "--approve-authenticated-read",
            )
            self.assertEqual(1, proc.returncode)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertIn("active-versions-missing", manifest["failures"])
            self.assertFalse(any(command["label"].startswith("version-view:") for command in manifest["commands"]))

    def test_failed_version_check_stops_before_authenticated_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root, fail_version=True)
            output = root / "snapshot"
            proc = self.run_capture(fake, output, "--kind", "worker", "--approve-authenticated-read")
            self.assertEqual(1, proc.returncode)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(["wrangler-version"], [command["label"] for command in manifest["commands"]])
            self.assertEqual(["wrangler-version"], manifest["failures"])

    def test_downloaded_symlink_is_removed_and_snapshot_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root, create_symlink=True)
            output = root / "snapshot"
            proc = self.run_capture(fake, output, "--kind", "worker", "--approve-authenticated-read")
            self.assertEqual(1, proc.returncode)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertIn("symlink-removed:download/fixture-project/external-link", manifest["failures"])
            link = output / "download/fixture-project/external-link"
            self.assertFalse(link.exists())
            self.assertFalse(link.is_symlink())

    def test_nested_downloaded_manifest_is_private_and_inventoried(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root, create_nested_manifest=True)
            output = root / "snapshot"
            proc = self.run_capture(fake, output, "--kind", "worker", "--approve-authenticated-read")
            self.assertEqual(0, proc.returncode, proc.stderr)
            manifest = json.loads((output / "manifest.json").read_text())
            relative = "download/fixture-project/manifest.json"
            self.assertIn(relative, {item["path"] for item in manifest["files"]})
            self.assertEqual(0o600, stat.S_IMODE((output / relative).stat().st_mode))

    def test_wrangler_subprocess_cannot_read_parent_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root, require_eof_stdin=True)
            output = root / "snapshot"
            proc = self.run_capture(
                fake,
                output,
                "--kind",
                "worker",
                "--metadata-only",
                "--approve-authenticated-read",
                input_text="must-not-reach-wrangler",
            )
            self.assertEqual(0, proc.returncode, proc.stderr)

    def test_unrelated_parent_credentials_and_node_options_are_not_forwarded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root, require_api_token=True)
            output = root / "snapshot"
            env = dict(os.environ)
            env["AWS_SECRET_ACCESS_KEY"] = "must-not-reach-wrangler"
            env["NODE_OPTIONS"] = "--trace-warnings"
            env["CLOUDFLARE_API_TOKEN"] = "fixture-token"
            proc = self.run_capture(
                fake,
                output,
                "--kind",
                "worker",
                "--metadata-only",
                "--approve-authenticated-read",
                env=env,
            )
            self.assertEqual(0, proc.returncode, proc.stderr)

    def test_profile_is_forwarded_to_every_authenticated_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root)
            output = root / "snapshot"
            proc = self.run_capture(
                fake,
                output,
                "--kind",
                "worker",
                "--metadata-only",
                "--profile",
                "audit",
                "--approve-authenticated-read",
            )
            self.assertEqual(0, proc.returncode, proc.stderr)
            manifest = json.loads((output / "manifest.json").read_text())
            for command in manifest["commands"]:
                if command["label"] != "wrangler-version":
                    self.assertEqual(["--profile", "audit"], command["argv"][-2:])

    def test_worker_metadata_only_skips_source_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root)
            output = root / "snapshot"
            proc = self.run_capture(
                fake,
                output,
                "--kind",
                "worker",
                "--metadata-only",
                "--approve-authenticated-read",
            )
            self.assertEqual(0, proc.returncode, proc.stderr)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertNotIn("init-from-dash", [entry["label"] for entry in manifest["commands"]])
            self.assertFalse((output / "download").exists())

    def test_pages_snapshot_downloads_config_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root)
            output = root / "snapshot"
            proc = self.run_capture(fake, output, "--kind", "pages", "--approve-authenticated-read")
            self.assertEqual(0, proc.returncode, proc.stderr)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertTrue(manifest["success"])
            self.assertTrue((output / "download/wrangler.jsonc").is_file())
            deployments = json.loads((output / "pages/deployments.json").read_text())
            self.assertEqual(
                {"Id", "Environment", "Branch", "Source", "Deployment", "Status", "Build"},
                set(deployments[0]),
            )
            self.assertTrue((output / "pages/secret-names.txt").is_file())

    def test_snapshot_refuses_git_worktree_output_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            fake = self.make_fake_wrangler(root)
            output = root / "snapshot"
            proc = self.run_capture(fake, output, "--kind", "worker", "--approve-authenticated-read")
            self.assertEqual(2, proc.returncode)
            self.assertIn("inside a Git worktree", proc.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

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
    def make_fake_wrangler(self, root: Path) -> Path:
        fake = root / "wrangler"
        fake.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json
                import os
                import sys
                from pathlib import Path

                args = sys.argv[1:]
                fixture_dir = Path({str(FIXTURES)!r})
                if args == ["--version"]:
                    print("4.30.0")
                elif args[:2] == ["deployments", "status"]:
                    print((fixture_dir / "worker-deployments-status.json").read_text(), end="")
                elif args[:2] == ["deployments", "list"]:
                    print("[]")
                elif args[:2] == ["versions", "list"]:
                    print("[]")
                elif args[:2] == ["versions", "view"]:
                    data = json.loads((fixture_dir / "worker-version-view.json").read_text())
                    data["id"] = args[2]
                    print(json.dumps(data))
                elif args[:2] == ["secret", "list"]:
                    print('[{{"name":"API_TOKEN","type":"secret_text"}}]')
                elif args[:2] == ["init", "--from-dash"]:
                    if os.environ.get("FAKE_FAIL_INIT"):
                        print("assets download unsupported", file=sys.stderr)
                        raise SystemExit(7)
                    name = args[2]
                    project = Path.cwd() / name
                    (project / "src").mkdir(parents=True)
                    (project / "wrangler.jsonc").write_text(json.dumps({{"name": name, "workers_dev": False, "routes": [{{"pattern": "fixture.example/*"}}]}}))
                    (project / "src/index.js").write_text('export default {{ fetch() {{ return new Response("ok") }} }}')
                    print(f"downloaded {{name}}")
                elif args[:3] == ["pages", "deployment", "list"]:
                    print((fixture_dir / "pages-deployments.json").read_text(), end="")
                elif args[:3] == ["pages", "secret", "list"]:
                    print("API_TOKEN (secret_text)")
                elif args[:3] == ["pages", "download", "config"]:
                    name = args[3]
                    (Path.cwd() / "wrangler.jsonc").write_text(json.dumps({{"name": name, "pages_build_output_dir": "dist"}}))
                    print(f"downloaded pages config {{name}}")
                else:
                    print("unsupported fake command: " + repr(args), file=sys.stderr)
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
            self.assertTrue((output / "worker/active-versions/10000000-0000-0000-0000-000000000000.json").is_file())
            forbidden = {"deploy", "delete", "put", "bulk", "rollback"}
            for entry in manifest["commands"]:
                self.assertTrue(forbidden.isdisjoint(entry["argv"][1:3]), entry["argv"])
            self.assertEqual(0o700, stat.S_IMODE(output.stat().st_mode))
            for path in output.rglob("*"):
                if path.is_file():
                    self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode), path)

    def test_failed_config_download_keeps_partial_metadata_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.make_fake_wrangler(root)
            output = root / "snapshot"
            env = dict(os.environ)
            env["FAKE_FAIL_INIT"] = "1"
            proc = self.run_capture(
                fake,
                output,
                "--kind",
                "worker",
                "--approve-authenticated-read",
                env=env,
            )
            self.assertEqual(1, proc.returncode)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertFalse(manifest["success"])
            self.assertIn("init-from-dash", manifest["failures"])
            self.assertTrue((output / "worker/deployments-status.json").is_file())
            self.assertTrue((output / "worker/init-from-dash.stdout.txt.stderr.txt").is_file())

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
            self.assertTrue((output / "pages/deployments.json").is_file())
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

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_links.py"
spec = importlib.util.spec_from_file_location("check_links", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader
spec.loader.exec_module(module)


class CheckLinksTests(unittest.TestCase):
    def test_default_targets_include_runtime_references_not_generated_results(self) -> None:
        files, missing = module.discover_markdown_files(ROOT, module.DEFAULT_TARGETS)
        rels = {path.relative_to(ROOT).as_posix() for path in files}
        self.assertEqual([], missing)
        self.assertIn("skills/cloudflare-doctor/references/official-source-map.md", rels)
        self.assertIn("skills/cloudflare-doctor/SKILL.md", rels)
        self.assertFalse(any(path.startswith("evals/results/") for path in rels))
        self.assertFalse(any(path.startswith("evals/fixtures/") for path in rels))

    def test_missing_required_target_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, missing = module.discover_markdown_files(Path(tmp), ["missing.md"])
        self.assertEqual(["missing.md"], missing)

    def test_repository_content_policy_is_current_and_valid(self) -> None:
        policy = json.loads((ROOT / "evals/link-check-policy.json").read_text())
        self.assertEqual([], module.validate_content_policy(policy, dt.date(2026, 7, 11)))

    def test_malformed_content_policy_entry_is_reported(self) -> None:
        policy = json.loads((ROOT / "evals/link-check-policy.json").read_text())
        policy["critical_sources"] = ["not-an-object"]
        errors = module.validate_content_policy(policy, dt.date(2026, 7, 11))
        self.assertTrue(any("must be an object" in error for error in errors))

    def test_overdue_content_policy_fails(self) -> None:
        policy = json.loads((ROOT / "evals/link-check-policy.json").read_text())
        self.assertTrue(any("overdue" in error for error in module.validate_content_policy(policy, dt.date(2026, 10, 12))))

    def test_extract_urls_respects_excluded_generated_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "evals/results").mkdir(parents=True)
            (root / "docs/current.md").write_text("https://example.com/current", encoding="utf-8")
            (root / "evals/results/old.md").write_text("https://example.com/old", encoding="utf-8")
            urls = module.extract_urls(root, ["docs", "evals/results"])
        self.assertIn("https://example.com/current", urls)
        self.assertNotIn("https://example.com/old", urls)


if __name__ == "__main__":
    unittest.main()

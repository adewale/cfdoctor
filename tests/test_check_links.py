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
        self.assertIn("research/incident-claim-ledger.json", rels)
        self.assertIn("evals/link-check-policy.json", rels)
        self.assertFalse(any(path.startswith("evals/results/") for path in rels))
        self.assertFalse(any(path.startswith("evals/fixtures/") for path in rels))

    def test_missing_required_target_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, missing = module.discover_markdown_files(Path(tmp), ["missing.md"])
        self.assertEqual(["missing.md"], missing)

    def test_workflow_anchor_policy_catches_billing_fact_drift(self) -> None:
        from io import BytesIO
        from unittest.mock import patch

        pricing = "https://developers.cloudflare.com/workflows/reference/pricing/"
        retention = "https://developers.cloudflare.com/changelog/post/2026-09-10-paid-retention-default/"
        fixture = ROOT / "evals/fixtures/benchmark/workflow-billing"
        clean = {
            pricing: (fixture / "workflow-pricing.md").read_text(),
            retention: (fixture / "workflow-retention.md").read_text(),
        }
        current = json.loads((ROOT / "evals/link-check-policy.json").read_text())
        current["critical_sources"] = [source for source in current["critical_sources"] if source["url"] in clean]
        previous = {"critical_sources": [{"url": pricing, "content_terms": ["Steps", "August 10"]}]}

        class Response(BytesIO):
            def __init__(self, url, body):
                super().__init__(body.encode())
                self.url = url

            def geturl(self):
                return self.url

        def check(policy, bodies):
            def open_source(request, **kwargs):
                return Response(request.full_url, bodies[request.full_url])
            with patch.object(module.urllib.request, "urlopen", side_effect=open_source):
                return module.check_content_sources(policy)

        self.assertTrue(all(row["status"] == "ok" for row in check(current, clean)))
        self.assertTrue(all(row["status"] == "ok" for row in check(previous, clean)))
        mutations = [
            (pricing, "Step count does not include rollback handlers or retries.", "Retries and rollback handlers count as additional billed steps."),
            (pricing, "averaging the peak storage per day", "averaging time-weighted storage within each day"),
            (retention, "seven days", "thirty days"),
        ]
        for url, before, after in mutations:
            with self.subTest(fact=before):
                self.assertIn(before, clean[url])
                changed = dict(clean, **{url: clean[url].replace(before, after)})
                self.assertTrue(all(row["status"] == "ok" for row in check(previous, changed)))
                self.assertTrue(any(row["status"] == "content-drift" for row in check(current, changed)))

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
        # Derive the date from the policy so a routine review does not break this test.
        day_after_due = dt.date.fromisoformat(policy["review_due"]) + dt.timedelta(days=1)
        self.assertTrue(any("overdue" in error for error in module.validate_content_policy(policy, day_after_due)))
        self.assertEqual([], module.validate_content_policy(policy, dt.date.fromisoformat(policy["review_due"])))

    def test_ledger_only_url_is_extracted(self) -> None:
        urls = module.extract_urls(ROOT, module.DEFAULT_TARGETS)
        ledger = json.loads((ROOT / "research/incident-claim-ledger.json").read_text())
        ledger_only_url = ledger["records"][0]["sources"][0]["archive_url"]
        self.assertIn(ledger_only_url, urls)
        self.assertIn("research/incident-claim-ledger.json", urls[ledger_only_url])

    def test_explicitly_unavailable_ledger_url_is_not_network_checked(self) -> None:
        urls = module.extract_urls(ROOT, module.DEFAULT_TARGETS)
        ledger = json.loads((ROOT / "research/incident-claim-ledger.json").read_text())
        unavailable = next(source["url"] for record in ledger["records"] for source in record["sources"] if source.get("availability") == "unavailable")
        self.assertNotIn(unavailable, urls)

    def test_authenticated_runtime_api_templates_are_not_network_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs/api.md").write_text(
                "Runtime template: https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records\n"
                "Docs: https://developers.cloudflare.com/api/resources/dns/",
                encoding="utf-8",
            )
            urls = module.extract_urls(root, ["docs"])
        self.assertFalse(any("api.cloudflare.com" in url for url in urls))
        self.assertIn("https://developers.cloudflare.com/api/resources/dns/", urls)

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

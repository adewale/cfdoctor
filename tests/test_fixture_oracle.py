from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "evals/oracles/fixture_oracle.py"


class FixtureOracleTests(unittest.TestCase):
    def run_oracle(self, case_id: str, text: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "output.md").write_text(text, encoding="utf-8")
            return subprocess.run([sys.executable, str(ORACLE), tmp, case_id], capture_output=True, text=True)

    def test_keyword_stuffing_no_longer_passes(self) -> None:
        proc = self.run_oracle(
            "round3-fixture-dashboard-claim",
            "README.md wrangler.toml not inspected source basis confidence evidence",
        )
        self.assertEqual(1, proc.returncode)
        self.assertIn("missing core audit marker", proc.stdout)

    def test_dashboard_claim_oracle_allows_quoted_claim_but_rejects_assertion(self) -> None:
        quoted = """Scope inspected: README.md and wrangler.toml
Scope not inspected: account state
Docs refreshed: Cache Reserve docs
The README claims Cache Reserve is disabled, but account state was not inspected.
"""
        proc = self.run_oracle("round3-fixture-dashboard-claim", quoted)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

        for assertion in (
            "Cache Reserve is definitely disabled.\n",
            "**Cache Reserve is definitely disabled**\n",
            "Finding: Cache Reserve is disabled.\n",
        ):
            proc = self.run_oracle("round3-fixture-dashboard-claim", assertion + quoted)
            self.assertEqual(1, proc.returncode)
            self.assertIn("forbidden pattern", proc.stdout)

    def test_concise_clean_no_finding_triage_can_pass(self) -> None:
        text = """## Cloudflare Doctor triage
Scope inspected: fixture files
Scope not inspected: account state; no dashboard access
Docs refreshed: not needed; no mutable semantic claim
No confirmed findings.
"""
        proc = self.run_oracle("detection-fixture-clean-baseline-precision", text)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_clean_no_finding_audit_can_pass(self) -> None:
        text = """## Cloudflare Doctor audit
Scope inspected: fixture files
Scope not inspected: account state; no dashboard access
Docs refreshed: https://developers.cloudflare.com/workers/
Detected products: Workers
Cost proxy summary: unknown
Overall risk: low — no repo findings
No confirmed findings.

## Run summary with cost proxies
- Hot paths: status endpoint
"""
        proc = self.run_oracle("detection-fixture-clean-baseline-precision", text)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_detached_scenario_keywords_do_not_satisfy_unrelated_finding(self) -> None:
        text = """## Cloudflare Doctor audit
Scope inspected: fixture
Scope not inspected: dashboard
Docs refreshed: source
Detected products: Workers, Queues
Cost proxy summary: unknown
Overall risk: low
self-fetch recursive dead-letter max_retries
### Severity: low — cosmetic issue
- Category: best-practice drift
- Evidence: README.md:1
- Why it matters: spelling
- Fix: correct spelling
- Cost / trade-off: none
- Verify: inspect text
- Source basis: https://developers.cloudflare.com/workers/
- Confidence: high
## Run summary with cost proxies
"""
        proc = self.run_oracle("detection-fixture-runaway-self-fetch", text)
        self.assertEqual(1, proc.returncode)
        self.assertIn("no complete finding contains", proc.stdout)

    def test_dlq_safe_allows_explicit_negation_but_no_finding_blocks(self) -> None:
        text = """## Cloudflare Doctor triage
Scope inspected: wrangler.jsonc and index.js
Scope not inspected: live queue metrics
Docs refreshed: current Queues retry docs
The DLQ is configured and max_retries is 3; this is not an unbounded platform retry policy.
The handler processes before acking and retries only after processing throws.
No confirmed findings.
"""
        proc = self.run_oracle("detection-fixture-queue-dlq-safe", text)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

        with_finding = text + """
### Severity: low — Queue hygiene
- Category: reliability
- Evidence: wrangler.jsonc
- Why it matters: review
- Fix: none
- Cost / trade-off: none
- Verify: inspect
- Source basis: https://developers.cloudflare.com/queues/
- Confidence: low
"""
        proc = self.run_oracle("detection-fixture-queue-dlq-safe", with_finding)
        self.assertEqual(1, proc.returncode)
        self.assertIn("too many finding blocks", proc.stdout)

        contradictory = """Scope inspected: wrangler.jsonc and index.js
Scope not inspected: live queue metrics
Docs refreshed: current Queues retry docs
The DLQ is configured and max_retries is 3.
The handler acknowledges every message before doing any work, so failures lose messages.
No confirmed findings.
"""
        proc = self.run_oracle("detection-fixture-queue-dlq-safe", contradictory)
        self.assertEqual(1, proc.returncode)
        self.assertIn("missing one of", proc.stdout)

    def test_benchmark_fixtures_preserve_staged_entrypoint_paths(self) -> None:
        manifest = json.loads((ROOT / "evals/shared-benchmark.json").read_text())
        checked = 0
        for case in manifest["cases"]:
            staged_names = {Path(path).name for path in case.get("files", [])}
            for relpath in case.get("files", []):
                if "wrangler." not in Path(relpath).name:
                    continue
                text = (ROOT / "evals" / relpath).read_text()
                match = re.search(r'(?:"main"\s*:\s*"|^main\s*=\s*")([^"\n]+)', text, re.M)
                if match:
                    checked += 1
                    self.assertIn(match.group(1), staged_names, case["id"])
        self.assertGreaterEqual(checked, 5)

    def test_queue_ambiguity_requires_a_specific_evidence_request(self) -> None:
        summary_only = """## Cloudflare Doctor audit
Scope inspected: repo
Scope not inspected: dashboard settings
Docs refreshed: source
Detected products: Queues
Cost proxy summary: unknown
Overall risk: medium
## Run summary with cost proxies
"""
        proc = self.run_oracle("detection-fixture-queue-dashboard-ambiguous", summary_only)
        self.assertEqual(1, proc.returncode)
        self.assertIn("Questions / evidence needed", proc.stdout)

        with_request = summary_only + """
## Questions / evidence needed
- Provide the dashboard-managed consumer config, including retry/DLQ settings.
"""
        proc = self.run_oracle("detection-fixture-queue-dashboard-ambiguous", with_request)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_runaway_case_requires_complete_finding(self) -> None:
        text = """## Cloudflare Doctor audit
Scope inspected: fixture
Scope not inspected: dashboard
Docs refreshed: source
Detected products: Workers, Queues
Cost proxy summary: unknown
Overall risk: high
self-fetch recursive DLQ Cost / trade-off Source basis
## Run summary with cost proxies
"""
        proc = self.run_oracle("detection-fixture-runaway-self-fetch", text)
        self.assertEqual(1, proc.returncode)
        self.assertIn("no structurally complete finding block", proc.stdout)


if __name__ == "__main__":
    unittest.main()

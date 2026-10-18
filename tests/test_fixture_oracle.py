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

    def private_d1_output(self, row: str, reasoning: str, *, safe: bool = False) -> str:
        result = """Scope inspected: README.md, wrangler.jsonc, index.js and evidence.txt
Scope not inspected: live account usage, invoice and billing window; deployed gate implementation not inspected.
Docs refreshed: https://developers.cloudflare.com/d1/platform/pricing/
Synthetic samples are not proven future worst-case bounds. Historical bill attribution is unknown.
Cost paths:
| path / trigger | frequency / window | queries / execution | rows read / query | rows written / query | evidence / unknowns | first enforced bound |
| --- | --- | --- | --- | --- | --- | --- |
""" + row + "\n" + reasoning + "\n"
        if safe:
            return result + "No confirmed findings.\n"
        return result + """### Severity: medium — evidenced repeated work
- Category: cost footgun
- Evidence: index.js and the supplied synthetic plans/samples in evidence.txt.
- Why it matters: executions multiply sampled reads and writes separately.
- Fix: use change detection, incremental updates, selective indexing or keyset pagination as justified above.
- Cost / trade-off: verify read/write index maintenance before removing an index.
- Verify: compare query plans and meta.rows_read / meta.rows_written before and after.
- Source basis: https://developers.cloudflare.com/d1/platform/pricing/
- Confidence: high for this supplied synthetic path; historical account attribution unknown.
"""

    def private_d1_examples(self) -> dict[str, str]:
        return {
            "private-d1-polling-growth": self.private_d1_output(
                "| /notes polling | every 10 seconds; active hours unknown | 1 | sample 50,000 | 0 | SCAN notes; growth unknown | LIMIT 20 returned; no per-period limit |\n"
                "| /diagnostics manual | invocation count unknown | 2 | sample 1 each | 0 | singleton COUNT and primary-key SELECT * | one-row table and primary-key lookup |",
                "360 executions per active hour × 1 query × 50,000 sampled reads = 18 million reads/hour; zero writes. "
                "The separate COUNT(*) singleton control and SELECT * primary-key lookup are bounded. Materialize or verify a selective index for the list."),
            "private-d1-deep-offset": self.private_d1_output(
                "| /archive | click frequency unknown | 1 | sample 10,020 | 0 | archive_owner_created_id covering index | LIMIT 20 returned, not reads |",
                "At OFFSET 10,000, 20 rows returned cost 10,020 sampled reads; shallow offset 0 sampled 20 reads. "
                "The existing covering index means this is skipped work, not a missing index or full table scan. Use keyset pagination and measure it."),
            "private-d1-repeated-sync": self.private_d1_output(
                "| scheduled sync DELETE + INSERT | every 5 minutes; 288 nominal/day | 1001 total: 1 DELETE plus 1000 INSERTs | sample 0 each | DELETE 1000; INSERT 1 each | unchanged snapshot replaced | 1000 rows per run; no daily stop |",
                "The unchanged snapshot is fully replaced each time: 1000 + 1000 = 2000 sample writes/run, "
                "288 × 2000 = 576,000 writes/day. Reads separately sample zero. Actual retries and overlap unknown. Prefer incremental change detection."),
            "private-d1-indexed-writes": self.private_d1_output(
                "| scheduled indexed update | every 15 minutes; 96 nominal/day | 1000 | sample 1 | sample 4 | primary-key SEARCH | 1000 IDs/run; no daily stop |",
                "96 × 1000 × 1 = 96,000 reads/day; 96 × 1000 × 4 = 384,000 writes/day. "
                "The comparison probe sampled 1 rows_written per update. This is evidenced indexed-write amplification. "
                "It is not a universal per-index formula; other index consumers and their value are unknown."),
            "private-d1-safe-controls": self.private_d1_output(
                "| authenticated polling session | every 60 seconds; at most 60 admitted/session | 2 | sample 1 each | 0 | singleton COUNT and primary-key SELECT * | SESSION_GATE atomic admission before D1 |",
                "60 × 2 × 1 = 120 sampled reads/session; zero writes. COUNT(*) scans a single-row summary and SELECT * uses primary-key SEARCH. "
                "The synthetic SESSION_GATE contract is atomic before D1; its external implementation/deployment is not inspected and gate charges are unknown.", safe=True),
        }

    def test_private_d1_accepts_evidence_based_positive_and_safe_reports(self) -> None:
        for case_id, text in self.private_d1_examples().items():
            with self.subTest(case_id=case_id):
                proc = self.run_oracle(case_id, text)
                self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_private_d1_rejects_wrong_units_and_copy_paste_diagnoses(self) -> None:
        examples = self.private_d1_examples()
        mutations = {
            "private-d1-polling-growth": ("sample 50,000", "20 returned"),
            "private-d1-deep-offset": ("sample 10,020", "20 returned"),
            "private-d1-repeated-sync": ("576,000", "288,000"),
            "private-d1-indexed-writes": ("sample 4", "sample 1"),
            "private-d1-safe-controls": ("120 sampled", "60 sampled"),
        }
        for case_id, (before, after) in mutations.items():
            with self.subTest(case_id=case_id):
                proc = self.run_oracle(case_id, examples[case_id].replace(before, after))
                self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)

        offset = examples["private-d1-deep-offset"] + "\nThe full table scan is caused by a missing index. Add a new index.\n"
        proc = self.run_oracle("private-d1-deep-offset", offset)
        self.assertEqual(1, proc.returncode)
        self.assertIn("incorrectly diagnosed", proc.stdout)
        indexed = examples["private-d1-indexed-writes"] + "\nDrop all indexes to fix the bill.\n"
        self.assertEqual(1, self.run_oracle("private-d1-indexed-writes", indexed).returncode)
        polling = examples["private-d1-polling-growth"] + "\nBots caused this invoice.\n"
        self.assertEqual(1, self.run_oracle("private-d1-polling-growth", polling).returncode)
        unrelated_negation = examples["private-d1-polling-growth"] + "\nBots caused this invoice despite no public traffic.\n"
        self.assertEqual(1, self.run_oracle("private-d1-polling-growth", unrelated_negation).returncode)
        sync_reads = examples["private-d1-repeated-sync"].replace("sample 0 each", "sample 1,000 each")
        self.assertEqual(1, self.run_oracle("private-d1-repeated-sync", sync_reads).returncode)

    def test_private_d1_accepts_equivalent_cadences_split_queries_and_scoped_caveats(self) -> None:
        examples = self.private_d1_examples()
        polling = examples["private-d1-polling-growth"].replace("every 10 seconds; active hours unknown", "360 polls per active hour; active hours unknown")
        indexed = examples["private-d1-indexed-writes"].replace("every 15 minutes; 96 nominal/day", "96 nominal executions/day")
        offset = examples["private-d1-deep-offset"] + "\nIt would be wrong to add an index based only on this query.\n"
        safe = examples["private-d1-safe-controls"]
        safe_row = next(line for line in safe.splitlines() if line.startswith("| authenticated polling"))
        split_rows = (
            "| session summary COUNT | 60 admitted/session | 1 | sample 1 | 0 | singleton table | SESSION_GATE before D1 |\n"
            "| session SELECT lookup | 60 admitted/session | 1 | sample 1 | 0 | primary key | SESSION_GATE before D1 |"
        )
        for case_id, text in (("private-d1-polling-growth", polling), ("private-d1-indexed-writes", indexed),
                              ("private-d1-deep-offset", offset), ("private-d1-safe-controls", safe.replace(safe_row, split_rows))):
            with self.subTest(case_id=case_id):
                proc = self.run_oracle(case_id, text)
                self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_private_d1_rejects_keyword_stuffing_and_unbounded_safety_claims(self) -> None:
        stuffing = "Cost paths: SCAN notes 360 50000 18000000 zero writes primary key COUNT SELECT *"
        proc = self.run_oracle("private-d1-polling-growth", stuffing)
        self.assertEqual(1, proc.returncode)
        self.assertIn("accounting columns", proc.stdout)
        safe = self.private_d1_examples()["private-d1-safe-controls"]
        for before, after in (
            ("Synthetic samples are not proven future worst-case bounds.", "These readings guarantee all future query bounds."),
            ("external implementation/deployment is not inspected", "external implementation/deployment is verified"),
        ):
            with self.subTest(before=before):
                proc = self.run_oracle("private-d1-safe-controls", safe.replace(before, after))
                self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        safe_finding = safe + """### Severity: high — COUNT(*) is expensive
- Category: cost footgun
"""
        self.assertEqual(1, self.run_oracle("private-d1-safe-controls", safe_finding).returncode)

    def test_private_d1_fixture_prompts_do_not_supply_the_derived_answers(self) -> None:
        manifest = json.loads((ROOT / "evals/shared-benchmark.json").read_text())
        answers = {"private-d1-polling-growth": ("18000000", "18,000,000"),
                   "private-d1-repeated-sync": ("576000", "576,000"),
                   "private-d1-indexed-writes": ("384000", "384,000")}
        checked = 0
        for case in manifest["cases"]:
            if "private-d1-cost-accounting" not in case.get("tags", []):
                continue
            checked += 1
            for relpath in case["files"]:
                content = (ROOT / "evals" / relpath).read_text()
                self.assertNotIn("Cost paths:", content, relpath)
                for answer in answers.get(case["id"], ()):
                    self.assertNotIn(answer, content, relpath)
        self.assertEqual(5, checked)

    def test_private_d1_focused_manifest_preserves_harness_safe_relative_paths(self) -> None:
        with tempfile.NamedTemporaryFile(dir=ROOT, suffix=".json") as handle:
            out = Path(handle.name)
            proc = subprocess.run([sys.executable, str(ROOT / "scripts/focus_private_d1_eval.py"),
                                   "--manifest", str(ROOT / "evals/shared-benchmark.json"), "--out", str(out)],
                                  capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            focused = json.loads(out.read_text())
            self.assertEqual(set(self.private_d1_examples()), {case["id"] for case in focused["cases"]})
            self.assertEqual(["no-private-d1-cost-accounting"], [item["id"] for item in focused["ablations"]])
            for case in focused["cases"]:
                for path in case["files"]:
                    self.assertFalse(Path(path).is_absolute())
                    self.assertTrue((ROOT / path).is_file())
                self.assertTrue((ROOT / case["assertions"][0]["command"][1]).is_file())
            for path in focused["ablations"][0]["target"].values():
                self.assertFalse(Path(path).is_absolute())
                self.assertNotIn("..", Path(path).parts)
                self.assertTrue((ROOT / path).is_file())
            self.assertTrue(all((ROOT / path).is_file() for path in focused["skill_paths"]))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp, "focused.json")
            proc = subprocess.run([sys.executable, str(ROOT / "scripts/focus_private_d1_eval.py"),
                                   "--out", str(out)], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("repository root", proc.stderr)
            self.assertFalse(out.exists())

    def test_finding_contract_accepts_markdown_emphasis_and_heading_depth(self) -> None:
        text = self.private_d1_examples()["private-d1-indexed-writes"]
        text = text.replace("### Severity:", "## **Severity:**")
        for label in ("Category", "Evidence", "Why it matters", "Fix", "Cost / trade-off", "Verify", "Source basis", "Confidence"):
            text = text.replace(f"- {label}:", f"- **{label}:**")
        self.assertEqual(0, self.run_oracle("private-d1-indexed-writes", text).returncode)
        missing_verify = text.replace("- **Verify:**", "- Test performed:")
        proc = self.run_oracle("private-d1-indexed-writes", missing_verify)
        self.assertEqual(1, proc.returncode)
        self.assertIn("no structurally complete", proc.stdout)

    def test_offset_cohorts_select_deep_measurement_and_semantic_index_identity(self) -> None:
        text = self.private_d1_examples()["private-d1-deep-offset"]
        deep_row = next(line for line in text.splitlines() if line.startswith("| /archive"))
        shallow_row = deep_row.replace("/archive", "/archive offset zero").replace("10,020", "20")
        text = text.replace(deep_row, shallow_row + "\n" + deep_row.replace("/archive", "same route offset 10000"))
        text = text.replace("archive_owner_created_id covering index", "existing covering index (owner_id, created_at DESC, id DESC)")
        text += "\nThis is indexed skipping, not evidence of a missing index or full-table scan.\n"
        proc = self.run_oracle("private-d1-deep-offset", text)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        # A shallow sample must never stand in for missing deep-page read units.
        self.assertEqual(1, self.run_oracle("private-d1-deep-offset", text.replace("sample 10,020", "sample 20")).returncode)

    def test_sample_bound_caveats_accept_guarantees_ceilings_and_row_maxima(self) -> None:
        text = self.private_d1_examples()["private-d1-indexed-writes"]
        old = "Synthetic samples are not proven future worst-case bounds."
        for caveat in (
            "Synthetic samples are not formal future row maxima.",
            "These synthetic projections are not observed totals or guaranteed bounds.",
            "Synthetic samples cannot establish a guaranteed future row ceiling.",
        ):
            with self.subTest(caveat=caveat):
                proc = self.run_oracle("private-d1-indexed-writes", text.replace(old, caveat))
                self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        unsafe = text.replace(old, "Synthetic samples guarantee all future row maxima.")
        self.assertEqual(1, self.run_oracle("private-d1-indexed-writes", unsafe).returncode)

    def test_polling_diagnostics_accept_split_shapes_and_unknown_active_duration(self) -> None:
        text = self.private_d1_examples()["private-d1-polling-growth"]
        combined = next(line for line in text.splitlines() if line.startswith("| /diagnostics"))
        first = combined.replace("| 2 |", "| 1 |").replace("/diagnostics manual", "/diagnostics manual summary count")
        second = first.replace("summary count", "note lookup").replace("invocation count unknown", "same manual invocations")
        text = text.replace(combined, first + "\n" + second).replace("active hours unknown", "active duration and tabs unknown")
        proc = self.run_oracle("private-d1-polling-growth", text)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertEqual(1, self.run_oracle("private-d1-polling-growth", text.replace(first + "\n", "")).returncode)

    def test_safe_accounting_excludes_rejections_and_inherits_shared_admissions(self) -> None:
        text = self.private_d1_examples()["private-d1-safe-controls"]
        combined = next(line for line in text.splitlines() if line.startswith("| authenticated polling"))
        split = (
            "| admitted summary count | at most 60 calls/session | 1 | sample 1 | 0 | singleton table | atomic admission gate before D1 |\n"
            "| same admitted request: note lookup | within the same admissions | 1 | sample 1 | 0 | primary key | same pre-D1 admission |\n"
            "| rejected session | attempt count unknown | 0 D1 queries | 0 | 0 | gate error | rejected before D1 |"
        )
        text = text.replace(combined, split).replace("SESSION_GATE", "admission gate").replace("SELECT *", "note lookup")
        proc = self.run_oracle("private-d1-safe-controls", text)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        unbounded = text.replace("at most 60 calls/session", "admissions unknown")
        self.assertEqual(1, self.run_oracle("private-d1-safe-controls", unbounded).returncode)

    def test_keyword_stuffing_no_longer_passes(self) -> None:
        proc = self.run_oracle(
            "round3-fixture-dashboard-claim",
            "README.md wrangler.toml not inspected source basis confidence evidence",
        )
        self.assertEqual(1, proc.returncode)
        self.assertIn("missing core audit marker", proc.stdout)

    def test_public_route_gate_rejects_keyword_stuffing_and_wrong_cost_branch(self) -> None:
        stuffing = """Release verdict: BLOCK
Discovery gaps: sitemap /about /abstract/
Exposure scenario: distinct keys × one fill
Closure conditions: materialize validate query plan
/ /browse /abstract/ /about COUNT GROUP lookup shared
https://developers.cloudflare.com/d1/platform/pricing/
"""
        proc = self.run_oracle("crawlable-page-live-d1-cost", stuffing)
        self.assertEqual(1, proc.returncode)
        self.assertIn("route matrix", proc.stdout)
        self.assertIn("request count", proc.stdout)

    def test_uncached_gate_rejects_distinct_keys_as_total_exposure(self) -> None:
        text = self.public_gate_output(
            "public-route-fixed-scan",
            "BLOCK",
            ["| landing.example / | router | 1 | 1 | route match | none | GROUP BY count | D1 rows read | materialize |"],
            "No off-sitemap route was evidenced.",
            "For anonymous requests, total D1 rows read = distinct keys × rows_read per first fill; repeated requests add no further D1 cost.",
            "Materialize the GROUP BY outside request handling.",
        )
        proc = self.run_oracle("public-route-fixed-scan", text)
        self.assertEqual(1, proc.returncode)
        self.assertIn("collapses repeated hits", proc.stdout)

    def test_core_gate_rejects_partial_dynamic_route_only_closure(self) -> None:
        text = self.public_gate_output(
            "crawlable-page-live-d1-cost",
            "BLOCK",
            [
                "| catalogue.example / | sitemap | 1 | 1 | route | shared COUNT | GROUP query | D1 rows read | none |",
                "| catalogue.example /browse | sitemap | 1 | query values | route | shared COUNT | SELECT browse | D1 rows read | none |",
                "| catalogue.example /abstract/:id | rendered links | 35,000 | arbitrary suffix | after D1 | shared COUNT | bounded lookup | D1 rows read | materialize lookup |",
                "| catalogue.example /about | navigation | 1 | 1 | route | shared COUNT | shared only | D1 rows read | none |",
                "| catalogue.example /sitemap.xml | code | 1 | exact path | before D1 | none | static response | 0 D1 rows | existing branch |",
                "| catalogue.example/* excluding named paths | wildcard route | none | arbitrary paths | after D1 | shared COUNT | 404 response | D1 rows read | route before D1 |",
            ],
            "The sitemap omits /abstract/:id and /about.",
            "Anonymous request count × D1 rows read per request; repeated hits remain included.",
            "Materialize only the /abstract/:id lookup; leave COUNT live on / and /about. Reject malformed keys before D1 and use EXPLAIN QUERY PLAN with measured rows_read.",
        )
        proc = self.run_oracle("crawlable-page-live-d1-cost", text)
        self.assertEqual(1, proc.returncode)
        self.assertIn("shared COUNT/total", proc.stdout)
        self.assertIn("homepage GROUP BY", proc.stdout)

    def test_holdout_rejects_crawler_controls_as_closure(self) -> None:
        text = self.public_gate_output(
            "public-route-timeline-holdout",
            "BLOCK",
            [
                "| history.example / | router | 1 | 1 | route | none | static page | 0 D1 rows | existing |",
                "| history.example /timeline | rendered link | 1 | exact path | route | none | GROUP BY year COUNT | D1 rows read | none |",
                "| history.example /sitemap.xml | code | 1 | exact path | route | none | static response | 0 D1 rows | existing |",
                "| history.example/* excluding named paths | wildcard | none | arbitrary | route | none | 404 response | 0 D1 rows | existing |",
            ],
            "The sitemap omits /timeline, which is exposed by a rendered link.",
            "Every anonymous request to /timeline × D1 rows read per request; repeated requests remain included.",
            "Add robots.txt, rate limits, and billing alerts while retaining the live GROUP BY.",
        )
        proc = self.run_oracle("public-route-timeline-holdout", text)
        self.assertEqual(1, proc.returncode)
        self.assertIn("timeline aggregate", proc.stdout)

    def test_public_route_gate_rejects_cache_api_as_pre_worker_source(self) -> None:
        text = self.public_gate_output(
            "public-route-fixed-scan",
            "BLOCK",
            ["| landing.example / | router | 1 | 1 | route match | none | GROUP BY count | D1 rows read | materialize |"],
            "No off-sitemap route was evidenced.",
            "Anonymous request count × D1 rows read per request; both request count and rows are unknown.",
            "Materialize the GROUP BY outside request handling.",
            "This single fixed URL is unsafe. Use the Cache API before the Worker executes.\n"
            "Source basis: https://developers.cloudflare.com/workers/runtime-apis/cache/",
        )
        proc = self.run_oracle("public-route-fixed-scan", text)
        self.assertEqual(1, proc.returncode)
        self.assertIn("pre-Worker claim lacks", proc.stdout)

    def test_public_route_gate_requires_workers_pricing_for_workers_caching(self) -> None:
        text = self.public_gate_output(
            "public-route-fixed-scan",
            "BLOCK",
            ["| landing.example / | router | 1 | 1 | route match | none | GROUP BY count | D1 rows read | materialize |"],
            "No off-sitemap route was evidenced.",
            "Anonymous request count × D1 rows read per request; repeated requests to the same / remain included.",
            "Materialize the GROUP BY outside request handling.",
            "This fixed route is unsafe. Use Workers Caching before invoking the Worker.\n"
            "Source basis: https://developers.cloudflare.com/workers/cache/configuration/",
        )
        proc = self.run_oracle("public-route-fixed-scan", text)
        self.assertEqual(1, proc.returncode)
        self.assertIn("residual request billing source", proc.stdout)

    def test_public_route_gate_requires_source_for_static_asset_recommendation(self) -> None:
        text = self.public_gate_output(
            "public-route-fixed-scan",
            "BLOCK",
            ["| landing.example / | router | 1 | 1 | route match | none | GROUP BY count | D1 rows read | materialize |"],
            "No off-sitemap route was evidenced.",
            "Anonymous request count × D1 rows read per request; repeated requests to the same / remain included.",
            "Materialize the GROUP BY outside request handling and render it as a static asset.",
        )
        proc = self.run_oracle("public-route-fixed-scan", text)
        self.assertEqual(1, proc.returncode)
        self.assertIn("Static Assets recommendation", proc.stdout)

    def test_public_route_semantic_oracle_accepts_block_pass_and_conditional(self) -> None:
        core = self.public_gate_output(
            "crawlable-page-live-d1-cost",
            "BLOCK",
            [
                "| catalogue.example / | sitemap | 1 | 1 | route | shared COUNT | GROUP query | D1 rows read | materialize |",
                "| catalogue.example /browse | sitemap | 1 | query values | route | shared COUNT | SELECT browse | D1 rows read | materialize |",
                "| catalogue.example /abstract/:id | rendered links | 35,000 | arbitrary suffix | after D1 | shared COUNT | bounded lookup | D1 rows read | syntax reject then materialize |",
                "| catalogue.example /about | navigation | 1 | 1 | route | shared COUNT | shared only | D1 rows read | materialize |",
                "| catalogue.example /sitemap.xml | code | 1 | exact path | before D1 | none | static response | 0 D1 rows | existing branch |",
                "| catalogue.example/* excluding named paths | wildcard route | none | arbitrary paths | after D1 | shared COUNT | 404 response | D1 rows read | route before D1 |",
            ],
            "The sitemap omits /abstract/:id (rendered browse links) and /about (navigation).",
            "Anonymous request count × D1 rows read per request; request count is unknown and repeated hits remain included.",
            "Move the total and field counts to publish-time materialized data on every route; reject malformed keys before D1; use EXPLAIN QUERY PLAN and measured rows_read to prove the residual lookup bounded.",
        )
        self.assertEqual(0, self.run_oracle("crawlable-page-live-d1-cost", core).returncode)

        passed = self.public_gate_output(
            "public-route-safe-bounded-lookup",
            "PASS",
            [
                "| safe.example / | rendered root | 1 | 1 | route | none | materialized count | 0 D1 rows | already prevented |",
                "| safe.example /article/:slug | rendered link | 35,000 | canonical slugs | syntax before D1 | none | indexed lookup | 0-1 rows read | early reject |",
            ],
            "No evidenced route family is absent from the supplied router and links.",
            "Anonymous request count × 0-1 D1 rows read per request; request volume remains unknown.",
            "The supplied prevention boundaries already satisfy PASS for the evidenced surface.",
            "query-plan.txt shows SEARCH articles USING INDEX articles_slug_unique; a known slug reads exactly 1 row. "
            "Malformed or noncanonical keys are rejected before D1. A valid-shaped unknown slug is a bounded indexed zero-row miss.",
        )
        proc = self.run_oracle("public-route-safe-bounded-lookup", passed)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

        conditional = self.public_gate_output(
            "public-route-missing-plan",
            "CONDITIONAL",
            ["| categories.example /category/:slug | router | 50,000 | canonical slugs | syntax before D1 | none | category query | unknown rows read | obtain plan |"],
            "No additional family is evidenced, but deployed routes are not inspected.",
            "Anonymous request count × unknown D1 rows per request; both request volume and per-request rows are unknown.",
            "Supply the missing EXPLAIN query plan and measured rows_read before deciding PASS or BLOCK.",
        )
        self.assertEqual(0, self.run_oracle("public-route-missing-plan", conditional).returncode)

    @staticmethod
    def public_gate_output(
        case_id: str,
        verdict: str,
        rows: list[str],
        discovery: str,
        exposure: str,
        closure: str,
        extra: str = "",
    ) -> str:
        del case_id
        return "\n".join([
            f"Release verdict: {verdict}",
            "| host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary |",
            "|---|---|---|---|---|---|---|---|---|",
            *rows,
            f"Discovery gaps: {discovery}",
            f"Exposure scenario: {exposure}",
            f"Closure conditions: {closure}",
            extra,
            "Source basis: https://developers.cloudflare.com/d1/platform/pricing/",
        ])

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
                match = re.search(r'(?:"main"\s*:\s*"|^main\s*=\s*")([^"\n]+)', text, re.MULTILINE)
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

    def test_worker_snapshot_requires_every_active_version(self) -> None:
        complete = """I inspected worker-deployments-status.json and worker-version-view.json.
The status shows two active versions: one receives 25% and the other 75%.
Only the first version view was supplied, so the second active version metadata is missing and cannot be reconciled yet.
Keep the snapshot private and request only that missing version view.
"""
        proc = self.run_oracle("wrangler-snapshot-worker-reconciliation", complete)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

        false_complete = """I inspected worker-deployments-status.json and worker-version-view.json.
The only active version is 10000000-0000-0000-0000-000000000000.
"""
        proc = self.run_oracle("wrangler-snapshot-worker-reconciliation", false_complete)
        self.assertEqual(1, proc.returncode)
        self.assertIn("forbidden pattern", proc.stdout)

        keyword_stuffing = "two active versions; 25%; second version missing; worker-version-view.json"
        proc = self.run_oracle("wrangler-snapshot-worker-reconciliation", keyword_stuffing)
        self.assertEqual(1, proc.returncode)
        self.assertIn("required pattern absent", proc.stdout)

        globalized = complete + "\nThe deployed Worker has a 50 ms CPU limit and uses KV.\n"
        proc = self.run_oracle("wrangler-snapshot-worker-reconciliation", globalized)
        self.assertEqual(1, proc.returncode)
        self.assertIn("forbidden pattern", proc.stdout)

    def test_worker_snapshot_minimizes_full_version_identifiers(self) -> None:
        truncated = """I inspected the supplied artifacts.
The status shows two active versions: `1000…` receives 25% and `2000…` receives 75%.
Only the first version view was supplied, so the other active version metadata is missing.
Keep the snapshot sensitive and private.
"""
        proc = self.run_oracle("wrangler-snapshot-worker-reconciliation", truncated)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

        repeated_full_ids = truncated.replace("`1000…`", "`10000000-0000-0000-0000-000000000000`").replace(
            "`2000…`", "`20000000-0000-0000-0000-000000000000`"
        )
        proc = self.run_oracle("wrangler-snapshot-worker-reconciliation", repeated_full_ids)
        self.assertEqual(1, proc.returncode)
        self.assertIn("forbidden pattern", proc.stdout)

    def test_wrangler_plan_rejects_recommended_package_runners_but_allows_prohibitions(self) -> None:
        for case_id in ("wrangler-snapshot-plan-approval", "wrangler-snapshot-assets-metadata-only"):
            for safe in (
                "Invoke ./node_modules/.bin/wrangler directly. Do not use npx, npm exec, pnpm dlx, or bunx.",
                "npx should not be used; invoke the existing binary directly.",
            ):
                proc = self.run_oracle(case_id, safe)
                self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            for unsafe in (
                "Use npm exec wrangler -- deployments status.",
                "Do not run yet. After approval, use npx wrangler deployments status.",
                "```bash\nnpx wrangler deployments status\n```",
                "You can fall back to pnpm dlx wrangler.",
            ):
                proc = self.run_oracle(case_id, unsafe)
                self.assertEqual(1, proc.returncode)
                self.assertIn("package runner", proc.stdout)

    def test_wrangler_plan_regexes_accept_safe_semantic_equivalents(self) -> None:
        manifest = json.loads((ROOT / "evals/shared-benchmark.json").read_text())
        cases = {case["id"]: case for case in manifest["cases"]}
        plan_assertions = {item["name"]: item for item in cases["wrangler-snapshot-plan-approval"]["assertions"]}
        approval = re.compile(plan_assertions["requires-authenticated-read-approval"]["pattern"])
        no_install = re.compile(plan_assertions["does-not-install-wrangler"]["pattern"])

        for text in (
            "All authenticated commands are pending approval.",
            "Nothing will run until you approve the authenticated reads.",
            "Do you approve running these authenticated reads?",
            "Explicit approval is required.",
        ):
            self.assertRegex(text, approval)
        self.assertNotRegex("No authenticated commands have run.", approval)

        for text in (
            "Use the direct binary, not npx or an installer-backed runner.",
            "Do not install Wrangler.",
            "Avoid npm exec and pnpm dlx.",
        ):
            self.assertRegex(text, no_install)
        self.assertNotRegex("Use Wrangler to inspect deployments.", no_install)

        assets_assertions = {item["name"]: item for item in cases["wrangler-snapshot-assets-metadata-only"]["assertions"]}
        assets_boundary = re.compile(assets_assertions["assets-download-boundary"]["pattern"])
        self.assertRegex("Static Assets are enabled, so skip init --from-dash.", assets_boundary)
        self.assertRegex("Skip init --from-dash because this Worker uses Static Assets.", assets_boundary)

    def test_pages_snapshot_does_not_prove_worker_runtime_state(self) -> None:
        calibrated = """I inspected pages-deployments.json as a Pages deployment list.
It shows a Production deployment history, but repository intent and downloaded config were not supplied.
I therefore cannot determine Worker-style bindings, runtime limits, or active versions from this file.
"""
        proc = self.run_oracle("wrangler-snapshot-pages-reconciliation", calibrated)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

        overclaim = calibrated + "\nConfirmed Worker CPU limit is 50 ms.\n"
        proc = self.run_oracle("wrangler-snapshot-pages-reconciliation", overclaim)
        self.assertEqual(1, proc.returncode)
        self.assertIn("forbidden pattern", proc.stdout)

        keyword_stuffing = "pages-deployments.json Pages deployment Production config not supplied"
        proc = self.run_oracle("wrangler-snapshot-pages-reconciliation", keyword_stuffing)
        self.assertEqual(1, proc.returncode)
        self.assertIn("required pattern absent", proc.stdout)

        soft_overclaim = calibrated + "\nThe Pages deployment row suggests a KV binding is active.\n"
        proc = self.run_oracle("wrangler-snapshot-pages-reconciliation", soft_overclaim)
        self.assertEqual(1, proc.returncode)
        self.assertIn("forbidden pattern", proc.stdout)

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

    def test_do_cycle_case_requires_scanner_id_and_cycle_members(self) -> None:
        text = """## Cloudflare Doctor audit
Scope inspected: wrangler.jsonc and index.js
Scope not inspected: deployed code, dashboard, logs, and billing data
Docs refreshed: current Durable Objects billing and SQLite docs
Detected products: Workers, Durable Objects
Cost proxy summary: SQLite rows read can grow on every cycle hop
Overall risk: critical
### Severity: critical — detached Durable Object call cycle
- Category: runaway cost and reliability
- Evidence: DO-STUB-CALL-CYCLE in index.js; cycle: SessionCoordinator -> TaskRunner -> SessionCoordinator
- Why it matters: the loop can continue across invocations
- Fix: add a propagated hop budget and kill switch, then make work idempotent
- Cost / trade-off: bounded work may stop an incomplete session for recovery
- Verify: rerun the scanner and confirm DO-STUB-CALL-CYCLE is absent
- Source basis: current Cloudflare Durable Objects documentation
- Confidence: high
### Severity: high — unbounded SQLite scan
- Category: storage cost
- Evidence: DO-SQL-SCAN-HOTPATH in index.js
- Why it matters: every loop hop reads growing SQLite storage rows
- Fix: add a selective WHERE clause and LIMIT
- Cost / trade-off: requires an index and pagination
- Verify: rerun the scanner and inspect rows read
- Source basis: current Cloudflare Durable Objects pricing documentation
- Confidence: high
## Run summary with cost proxies
"""
        proc = self.run_oracle("pos-do-stub-cycle-rows-read-bill", text)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

        without_check_ids = text.replace("DO-STUB-CALL-CYCLE", "stub cycle").replace(
            "DO-SQL-SCAN-HOTPATH", "SQL scan"
        )
        proc = self.run_oracle("pos-do-stub-cycle-rows-read-bill", without_check_ids)
        self.assertEqual(1, proc.returncode)
        self.assertIn("missing required text", proc.stdout)

        without_cycle_member = text.replace("TaskRunner", "BackgroundRunner")
        proc = self.run_oracle("pos-do-stub-cycle-rows-read-bill", without_cycle_member)
        self.assertEqual(1, proc.returncode)
        self.assertIn("missing required text", proc.stdout)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Validate the structured incident/experience-report evidence ledger."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "research" / "incident-claim-ledger.json"
FIXTURES = ROOT / "evals" / "fixtures" / "detection"
MATRIX = ROOT / "skills" / "cloudflare-doctor" / "references" / "check-coverage-matrix.md"
ID_RE = re.compile(r"^CFDOC-EVD-[A-Z0-9-]+$")
ALLOWED_CLASSES = {"incident", "official-guidance", "operator-note", "product-announcement"}
ALLOWED_STATUS = {"accepted", "unverified", "superseded", "retracted"}
CONFIDENCE_KEYS = {"authenticity", "mechanism", "independence", "applicability", "temporal"}
SCENARIO_MAX = 24


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def matrix_ids() -> set[str]:
    text = MATRIX.read_text(encoding="utf-8")
    return set(re.findall(r"^\| ([A-Z0-9][A-Z0-9-]+) \|", text, re.MULTILINE))


def fixture_manifests() -> dict[str, dict]:
    return {p.parent.name: load_json(p) for p in FIXTURES.glob("*/expected.json")}


def checklist_evidence_ids() -> dict[int, str]:
    text = (ROOT / "skills/cloudflare-doctor/references/war-story-scenario-checklist.md").read_text(encoding="utf-8")
    mapping: dict[int, str] = {}
    matches = list(re.finditer(r"^### (\d+)\. ", text, re.MULTILINE))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start():end]
        evidence = re.search(r"^- Evidence ID: `([^`]+)`", block, re.MULTILINE)
        if evidence:
            mapping[int(match.group(1))] = evidence.group(1)
    return mapping


def validate(ledger: dict, as_of: dt.date) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if ledger.get("version") != 1:
        errors.append("ledger.version must be 1")
    cadence = ledger.get("review_cadence_days")
    if not isinstance(cadence, int) or isinstance(cadence, bool) or cadence < 1 or cadence > 366:
        errors.append("ledger.review_cadence_days must be an integer from 1 to 366")
        cadence = None
    try:
        ledger_as_of = dt.date.fromisoformat(ledger["as_of"])
        if ledger_as_of > as_of:
            errors.append(f"ledger.as_of {ledger_as_of.isoformat()} is later than validation date {as_of.isoformat()}")
    except (KeyError, TypeError, ValueError):
        errors.append("ledger.as_of must be an ISO date")
    records = ledger.get("records")
    if not isinstance(records, list) or not records:
        return ["ledger.records must be a non-empty list"], warnings

    ids: set[str] = set()
    clusters: set[str] = set()
    covered_scenarios: set[int] = set()
    known_checks = matrix_ids()
    fixtures = fixture_manifests()
    ledger_fixture_links: dict[str, set[str]] = {}
    primary_url_clusters: dict[str, str] = {}
    scenario_records: dict[int, str] = {}

    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        rid = record.get("id")
        if not isinstance(rid, str) or not ID_RE.match(rid):
            errors.append(f"{prefix}.id is invalid")
            continue
        if rid in ids:
            errors.append(f"duplicate evidence id: {rid}")
        ids.add(rid)
        cluster = record.get("source_cluster_id")
        if not isinstance(cluster, str) or not cluster:
            errors.append(f"{rid}: source_cluster_id is required")
        elif cluster in clusters:
            errors.append(f"duplicate source_cluster_id: {cluster}")
        else:
            clusters.add(cluster)
        if record.get("evidence_class") not in ALLOWED_CLASSES:
            errors.append(f"{rid}: invalid evidence_class")
        if record.get("status") not in ALLOWED_STATUS:
            errors.append(f"{rid}: invalid status")
        if not record.get("mechanism") or not record.get("taxonomy"):
            errors.append(f"{rid}: mechanism and taxonomy are required")

        sources = record.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{rid}: at least one source is required")
        else:
            urls: set[str] = set()
            for source_index, source in enumerate(sources):
                if not isinstance(source, dict):
                    errors.append(f"{rid}: sources[{source_index}] must be an object")
                    continue
                url = source.get("url")
                if not isinstance(url, str) or not url.startswith(("https://", "http://")):
                    errors.append(f"{rid}: source URL is invalid")
                elif url in urls:
                    errors.append(f"{rid}: duplicate source URL {url}")
                urls.add(str(url))
                for field in ("role", "author_org", "published_at"):
                    if not source.get(field):
                        errors.append(f"{rid}: source.{field} is required")
                availability = source.get("availability", "available")
                if availability not in {"available", "unavailable"}:
                    errors.append(f"{rid}: source.availability must be available or unavailable")
                if availability == "unavailable" and record.get("status") not in {"unverified", "superseded", "retracted"}:
                    errors.append(f"{rid}: unavailable source requires unverified/superseded/retracted status")
                if source.get("role") == "primary" and isinstance(url, str):
                    normalized = url.rstrip("/").casefold()
                    owner = primary_url_clusters.get(normalized)
                    if owner and owner != cluster:
                        errors.append(f"{rid}: primary source URL duplicates source cluster {owner}")
                    primary_url_clusters[normalized] = str(cluster)
            if record.get("evidence_class") == "incident" and record.get("status") == "accepted":
                if not any(isinstance(s, dict) and s.get("role") == "primary" and s.get("first_hand") is True for s in sources):
                    errors.append(f"{rid}: accepted incident needs a first-hand primary source")

        confidence = record.get("confidence")
        if not isinstance(confidence, dict) or set(confidence) != CONFIDENCE_KEYS:
            errors.append(f"{rid}: confidence must contain exactly {sorted(CONFIDENCE_KEYS)}")
        elif any(not isinstance(v, int) or v < 0 or v > 2 for v in confidence.values()):
            errors.append(f"{rid}: confidence values must be integers 0..2")

        try:
            verified = dt.date.fromisoformat(record["verified_at"])
            due = dt.date.fromisoformat(record["review_due"])
            if due < verified:
                errors.append(f"{rid}: review_due precedes verified_at")
            if cadence is not None and due > verified + dt.timedelta(days=cadence):
                errors.append(f"{rid}: review_due exceeds {cadence}-day ledger cadence")
            if due <= as_of:
                message = f"{rid}: evidence review due since {due.isoformat()}"
                (errors if record.get("status") == "accepted" else warnings).append(message)
        except (KeyError, TypeError, ValueError):
            errors.append(f"{rid}: verified_at and review_due must be ISO dates")

        semantics = record.get("current_semantics_urls", [])
        if record.get("check_ids") and not semantics and record.get("evidence_class") != "operator-note":
            errors.append(f"{rid}: check derivations need current_semantics_urls")
        if record.get("check_ids") and semantics and not any("developers.cloudflare.com" in str(url) for url in semantics):
            errors.append(f"{rid}: Cloudflare check derivations need a current official Cloudflare semantics source")
        for url in semantics:
            if not isinstance(url, str) or not url.startswith("https://"):
                errors.append(f"{rid}: invalid current semantics URL")
        for check_id in record.get("check_ids", []):
            if check_id not in known_checks:
                errors.append(f"{rid}: unknown check_id {check_id}")
        for number in record.get("scenario_numbers", []):
            if not isinstance(number, int) or number < 1 or number > SCENARIO_MAX:
                errors.append(f"{rid}: invalid scenario number {number}")
            covered_scenarios.add(number)
            if number in scenario_records and scenario_records[number] != rid:
                errors.append(f"scenario {number} is assigned to multiple evidence records")
            scenario_records[number] = rid
        for fixture_id in record.get("fixture_ids", []):
            if fixture_id not in fixtures:
                errors.append(f"{rid}: unknown fixture_id {fixture_id}")
            ledger_fixture_links.setdefault(fixture_id, set()).add(rid)

    missing_scenarios = sorted(set(range(1, SCENARIO_MAX + 1)) - covered_scenarios)
    if missing_scenarios:
        errors.append(f"ledger does not cover checklist scenarios: {missing_scenarios}")
    checklist_map = checklist_evidence_ids()
    if set(checklist_map) != set(range(1, SCENARIO_MAX + 1)):
        errors.append(f"runtime checklist must contain exactly one Evidence ID for scenarios 1..{SCENARIO_MAX}")
    for number, rid in checklist_map.items():
        if scenario_records.get(number) != rid:
            errors.append(f"scenario {number}: checklist evidence {rid} does not match ledger {scenario_records.get(number)}")

    for fixture_id, manifest in fixtures.items():
        if not isinstance(manifest, dict):
            errors.append(f"{fixture_id}: expected.json must be an object")
            continue
        evidence_ids = manifest.get("evidence_ids")
        if evidence_ids is None:
            errors.append(f"{fixture_id}: expected.json must use evidence_ids (legacy war_story is not enough)")
            continue
        if not isinstance(evidence_ids, list):
            errors.append(f"{fixture_id}: evidence_ids must be a list")
            continue
        fixture_check_ids = set(manifest.get("required_check_ids", [])) | set(manifest.get("forbidden_check_ids", []))
        records_by_id = {record.get("id"): record for record in records if isinstance(record, dict) and isinstance(record.get("id"), str)}
        for rid in evidence_ids:
            if rid not in ids:
                errors.append(f"{fixture_id}: unknown evidence id {rid}")
                continue
            if rid not in ledger_fixture_links.get(fixture_id, set()):
                errors.append(f"{fixture_id}: ledger record {rid} lacks reciprocal fixture_ids link")
            linked_checks = set(records_by_id[rid].get("check_ids", []))
            if not fixture_check_ids.intersection(linked_checks):
                errors.append(f"{fixture_id}: evidence {rid} has no check_id matching required/forbidden fixture behavior")
        required_ids = set(manifest.get("required_check_ids", []))
        parser_contract_only = bool(required_ids) and required_ids <= {"CFDOC-CONFIG-UNPARSEABLE"}
        if fixture_id != "clean-baseline" and required_ids and not evidence_ids and not parser_contract_only:
            warnings.append(f"{fixture_id}: no evidence_ids for a positive fixture")

    for fixture_id, linked_ids in ledger_fixture_links.items():
        manifest_ids = set(fixtures.get(fixture_id, {}).get("evidence_ids", []))
        for rid in linked_ids - manifest_ids:
            errors.append(f"{fixture_id}: ledger record {rid} links fixture but expected.json lacks reciprocal evidence_id")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--as-of", default=dt.date.today().isoformat())
    args = parser.parse_args(argv)
    try:
        ledger = load_json(args.ledger)
        as_of = dt.date.fromisoformat(args.as_of)
        errors, warnings = validate(ledger, as_of)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"OK: evidence ledger has {len(ledger['records'])} records covering {SCENARIO_MAX} scenarios and {len(fixture_manifests())} fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

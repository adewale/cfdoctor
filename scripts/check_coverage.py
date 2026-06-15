#!/usr/bin/env python3
"""Enforce consistency between the check coverage matrix and the scanner registry.

Compares skills/cloudflare-doctor/references/check-coverage-matrix.md against the check registry reported
by `skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py --list-checks` and fails when they drift:

  (a) every registered scanner check ID has exactly one matrix row with status
      `scanner-lead`;
  (b) every matrix row with status `scanner-lead` is a registered scanner ID;
  (c) no check ID appears in more than one matrix row;
  (d) every status is from the allowed set (`scanner-lead`, `skill-prompt-only`,
      `not-implemented`, or `folded-into:<REGISTERED-ID>` for duplicates folded
      into a canonical scanner check).

Exit codes: 0 consistent, 1 drift detected, 2 harness error (could not run the
scanner, parse its output, or find/parse the matrix).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNER = REPO_ROOT / "skills" / "cloudflare-doctor" / "scripts" / "cfdoctor_static_scan.py"
MATRIX = REPO_ROOT / "skills" / "cloudflare-doctor" / "references" / "check-coverage-matrix.md"

SIMPLE_STATUSES = ("scanner-lead", "skill-prompt-only", "not-implemented")
FOLDED_PREFIX = "folded-into:"
CHECK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]*$")


def fail_harness(message: str) -> "NoReturn":  # noqa: F821 (py<3.11 friendly)
    print(f"ERROR (harness): {message}", file=sys.stderr)
    sys.exit(2)


def load_scanner_ids() -> set:
    """Run the scanner's --list-checks and return the set of registered IDs."""
    if not SCANNER.is_file():
        fail_harness(f"scanner not found at {SCANNER}")
    try:
        proc = subprocess.run(
            [sys.executable, str(SCANNER), "--list-checks"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail_harness(f"could not run scanner --list-checks: {exc}")
    if proc.returncode != 0:
        fail_harness(
            "scanner --list-checks exited "
            f"{proc.returncode}: {proc.stderr.strip()[:500]}"
        )
    try:
        payload = json.loads(proc.stdout)
        checks = payload["checks"]
        ids = {entry["check_id"] for entry in checks}
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        fail_harness(f"could not parse scanner --list-checks JSON: {exc}")
    if not ids:
        fail_harness("scanner registry is empty; refusing to validate")
    if len(ids) != len(checks):
        fail_harness("scanner registry itself contains duplicate check IDs")
    return ids


def strip_markdown(cell: str) -> str:
    """Strip surrounding whitespace and inline-code backticks from a cell."""
    cell = cell.strip()
    if cell.startswith("`") and cell.endswith("`") and len(cell) >= 2:
        cell = cell[1:-1].strip()
    return cell


def parse_matrix_rows(text: str) -> list:
    """Return [(check_id, status, line_number), ...] from the matrix table.

    Robust to column whitespace/padding and to IDs wrapped in backticks. Only
    table rows whose first cell looks like a check ID are considered; header
    and separator rows are skipped.
    """
    rows = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [strip_markdown(c) for c in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        check_id = cells[0]
        if check_id.lower() == "check id":
            continue  # header row
        if set(check_id) <= {"-", ":", " "}:
            continue  # separator row
        if not CHECK_ID_RE.match(check_id):
            continue  # not a check row (prose tables, etc.)
        status = cells[1]
        rows.append((check_id, status, lineno))
    return rows


def main() -> int:
    scanner_ids = load_scanner_ids()

    if not MATRIX.is_file():
        fail_harness(f"matrix not found at {MATRIX}")
    try:
        rows = parse_matrix_rows(MATRIX.read_text(encoding="utf-8"))
    except OSError as exc:
        fail_harness(f"could not read matrix: {exc}")
    if not rows:
        fail_harness(f"no check rows parsed from {MATRIX}")

    errors = []

    # (c) duplicate matrix rows
    seen = {}
    for check_id, _status, lineno in rows:
        if check_id in seen:
            errors.append(
                f"duplicate matrix row for {check_id} "
                f"(lines {seen[check_id]} and {lineno})"
            )
        else:
            seen[check_id] = lineno

    # (d) allowed statuses, including folded-into:<ID> validation
    status_counts = {s: 0 for s in SIMPLE_STATUSES}
    status_counts["folded-into"] = 0
    scanner_lead_ids = set()
    for check_id, status, lineno in rows:
        if status in SIMPLE_STATUSES:
            status_counts[status] += 1
            if status == "scanner-lead":
                scanner_lead_ids.add(check_id)
        elif status.startswith(FOLDED_PREFIX):
            status_counts["folded-into"] += 1
            target = status[len(FOLDED_PREFIX):].strip()
            if target not in scanner_ids:
                errors.append(
                    f"{check_id} (line {lineno}) is folded into {target!r}, "
                    "which is not a registered scanner check"
                )
            if check_id in scanner_ids:
                errors.append(
                    f"{check_id} (line {lineno}) is marked folded-into but is "
                    "itself a registered scanner check; mark it scanner-lead"
                )
        else:
            errors.append(
                f"{check_id} (line {lineno}) has invalid status {status!r}; "
                f"allowed: {', '.join(SIMPLE_STATUSES)}, "
                f"or {FOLDED_PREFIX}<REGISTERED-ID>"
            )

    # (a) every registered scanner ID has a scanner-lead row
    missing_rows = sorted(scanner_ids - scanner_lead_ids)
    for check_id in missing_rows:
        errors.append(
            f"registered scanner check {check_id} has no scanner-lead row "
            "in the matrix"
        )

    # (b) every scanner-lead row is a registered scanner ID
    unknown_leads = sorted(scanner_lead_ids - scanner_ids)
    for check_id in unknown_leads:
        errors.append(
            f"matrix row {check_id} is marked scanner-lead but is not in "
            "the scanner registry"
        )

    # Also flag non-scanner-lead rows that ARE registered (wrong status).
    for check_id, status, lineno in rows:
        if status in ("skill-prompt-only", "not-implemented") and check_id in scanner_ids:
            errors.append(
                f"{check_id} (line {lineno}) is registered in the scanner but "
                f"its matrix status is {status!r}; it must be scanner-lead"
            )

    # Summary
    print(f"scanner registry:   {len(scanner_ids)} check IDs")
    print(f"matrix rows parsed: {len(rows)}")
    print("status counts:")
    print(f"  scanner-lead:      {status_counts['scanner-lead']}")
    print(f"  skill-prompt-only: {status_counts['skill-prompt-only']}")
    print(f"  not-implemented:   {status_counts['not-implemented']}")
    print(f"  folded-into:<ID>:  {status_counts['folded-into']}")

    if errors:
        print(f"\nDRIFT: {len(errors)} problem(s) found:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("\nOK: matrix and scanner registry are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

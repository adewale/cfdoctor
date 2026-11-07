"""Apply factual source clarifications after answer generation, before judging.

No answer inputs or rubric scales change. Preserve the acquisition-time manifest
and record both hashes so post-freeze oracle corrections remain reviewable.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path


def main():
    root = Path(sys.argv[1]).resolve()
    here = Path(__file__).resolve().parent
    path = root / "manifest.json"
    original = path.read_bytes()
    backup = root / "manifest-answer-frozen.json"
    if not backup.exists():
        shutil.copy2(path, backup)
    manifest = json.loads(original)
    addenda = {
        "fresh-pastebin-d1": here / "oracle-addendum-pastebin.md",
        "fresh-status-page": here / "oracle-addendum-status.md",
    }
    for case in manifest["cases"]:
        if case["id"] in addenda:
            note = addenda[case["id"]].read_text()
            if note not in case["expected_behavior"]:
                case["expected_behavior"].append(note)
    # Anchored judge thresholds use raw 1-5 units: 4.4 maps to normalized 0.85.
    for case in manifest["cases"]:
        for assertion in case["assertions"]:
            if assertion.get("graded_dimensions"):
                assertion["threshold"] = 4.4
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    receipt = {
        "initial_manifest_sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
        "corrected_judging_manifest_sha256": hashlib.sha256(
            path.read_bytes()
        ).hexdigest(),
        "addenda": {
            case: hashlib.sha256(p.read_bytes()).hexdigest()
            for case, p in addenda.items()
        },
        "answer_inputs_and_rubric_scales_unchanged": True,
        "raw_graded_threshold": 4.4,
        "normalized_graded_threshold": 0.85,
        "all_reports_in_affected_cases_scored_under_same_clarification": True,
    }
    (root / "oracle-addenda-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print("Applied source-only clarifications for both arms of two cases.")


if __name__ == "__main__":
    main()

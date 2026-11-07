"""Shared anchored factual-precision contract for calibration and matched audits."""

PRECISION = (
    "5: no material unsupported or incorrect claim and respects the actual controls; "
    "4: only a minor contextual overstatement that does not change the claimed failure; "
    "3: one material false factual claim, wrong causal/branch explanation, or invalid concrete remedy; "
    "2: multiple materially unsupported claims; 1: dominated by fabricated or misattributed defects. "
    "An incorrect quota/counter comparison that asserts a failure below the actual limit is material, "
    "even if another diagnosis is correct. A different error status or operation order is a factual claim, "
    "not automatically correct because an availability or cost risk remains. "
    "Do not penalize a qualified runtime hypothesis as an asserted incident; optional correct suggestions "
    "and omission are not precision errors. Unsupported public/manual/capability-policy requirements "
    "are not defects. Rationale must quote each material false claim and correct it with supplied source, "
    "or explicitly state none. Score the report as written, not a stronger or weaker paraphrase."
)
JUDGE_PREFACE = (
    "Use only the supplied source and frozen references; do not browse, run code, or inspect files. "
    "The candidate label is arbitrary. Source truth is non-exhaustive: accept other independently "
    "supported defects. A safe-control note proves only its specified invariant. "
    "Trace branch-specific guards, optional work, catches, returned statuses and actual lexical "
    "callback/loop boundaries. Classify quota/product/counter/plan before applying a numeric ceiling. "
    "Distinguish intended policy and documentation conflicts from unauthorized effects, physical "
    "retention, observed incidents and deployed activation. If a low score depends on a factual claim, "
    "quote that claim and cite the conflicting raw source; do not invent a claim to penalize. "
    "Do not reward report length, finding count, labels or wording matches. "
)
JUDGE_PREFACE += (
    "A verdict expressly scoped to the public GET/HEAD cost gate does not approve writes, "
    "authentication, or the whole project; correctly reported write/auth defects are compatible "
    "with that scoped cost verdict. Judge the actual scope, not the word PASS alone. "
    "Distinguish a document actually supplied or inspected from an external link or memory: "
    "quote any fabricated inspection/source attribution and check the supplied file inventory. "
)

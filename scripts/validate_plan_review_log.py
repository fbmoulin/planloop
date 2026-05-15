#!/usr/bin/env python3
"""
validate_plan_review_log.py

Parses the Plan Review Log section of a plan file and validates it.

Exit codes:
    0: log is well-formed and no blocking findings are Open. Plan is execution-ready.
    1: blocking findings (Critical, Major, or Minor) are still Open. Lists them.
    2: log itself is malformed (missing fields, leftover template placeholders, or no log section).

Usage:
    python validate_plan_review_log.py path/to/plan.md
"""

import re
import sys
from pathlib import Path

BLOCKING_SEVERITIES = {"Critical", "Major", "Minor"}
ALL_SEVERITIES = {"Critical", "Major", "Minor", "Advisory"}
VALID_STATUSES = {"Open", "Resolved", "No Plan Change"}

PLACEHOLDER_MARKERS = [
    "[Verbatim from reviewer subagent output",
    "[Verbatim from",
    "[Concrete risk:",
    "[Concrete implementation or legal risk",
    "[Verbatim from reviewer",
    "[Short title]",
    "[What the reviewer flagged",
    "[Implementation risk",
    "[Plan section, task",
    "[Empty unless decision",
]


def extract_log_section(text: str) -> str | None:
    """Return the Plan Review Log section text, or None if missing."""
    match = re.search(
        r"^## Plan Review Log\s*\n(.*?)(?=^## (?!##)|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else None


def split_findings(log_text: str) -> list[str]:
    """Split the log into per-finding blocks."""
    # Each finding starts with `##### Finding R<N>-PRC<NNN>:` heading.
    parts = re.split(r"^##### (?=Finding R\d+-PRC\d{3}:)", log_text, flags=re.MULTILINE)
    return [p for p in parts if p.strip().startswith("Finding R")]


def parse_field(block: str, field: str) -> str | None:
    """Extract a field value from a finding block. Handles both inline and
    block-scalar (|) YAML-like fields."""
    pattern = rf"^{re.escape(field)}\s*:\s*(.*?)(?=^\w[\w_]*\s*:|^####|\Z)"
    match = re.search(pattern, block, re.MULTILINE | re.DOTALL)
    if not match:
        return None
    value = match.group(1).strip()
    # Strip leading | and indentation if present
    if value.startswith("|"):
        value = value[1:].strip()
    return value


def parse_id(block: str) -> str | None:
    match = re.search(r"Finding (R\d+-PRC\d{3}):", block)
    return match.group(1) if match else None


def has_placeholder(text: str) -> bool:
    if not text:
        return False
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def validate_finding(block: str) -> tuple[list[str], dict]:
    """Validate a single finding block. Returns (errors, parsed_record)."""
    errors: list[str] = []
    finding_id = parse_id(block) or "UNKNOWN"

    severity = parse_field(block, "severity")
    status = parse_field(block, "status")
    location = parse_field(block, "location")
    concern = parse_field(block, "reviewer_concern")
    why = parse_field(block, "why_it_matters")
    plan_changes = parse_field(block, "plan_changes_made")
    no_change_rationale = parse_field(block, "no_change_rationale")
    approver = parse_field(block, "human_approver")
    approval_status = parse_field(block, "approval_status")

    if severity not in ALL_SEVERITIES:
        errors.append(
            f"{finding_id}: severity must be one of {ALL_SEVERITIES}, got {severity!r}"
        )
    if status not in VALID_STATUSES:
        errors.append(
            f"{finding_id}: status must be one of {VALID_STATUSES}, got {status!r}"
        )
    if not location:
        errors.append(f"{finding_id}: location is required")
    if not concern or has_placeholder(concern):
        errors.append(
            f"{finding_id}: reviewer_concern is empty or contains template placeholder"
        )
    if not why or has_placeholder(why):
        errors.append(
            f"{finding_id}: why_it_matters is empty or contains template placeholder"
        )

    # Disposition-specific checks
    if status == "Resolved":
        if not plan_changes or has_placeholder(plan_changes):
            errors.append(
                f"{finding_id}: Resolved findings must have plan_changes_made filled"
            )
        if not approver:
            errors.append(f"{finding_id}: Resolved findings require human_approver")
        if approval_status != "Approved":
            errors.append(
                f"{finding_id}: Resolved findings require approval_status=Approved"
            )
    elif status == "No Plan Change":
        if not no_change_rationale or has_placeholder(no_change_rationale):
            errors.append(
                f"{finding_id}: No Plan Change findings must have no_change_rationale filled with a real reason (not placeholder)"
            )
        if len((no_change_rationale or "").split()) < 8:
            errors.append(
                f"{finding_id}: No Plan Change rationale is too brief; explain why concretely (at least 8 words)"
            )
        if not approver:
            errors.append(
                f"{finding_id}: No Plan Change findings require human_approver"
            )
        if approval_status != "Approved":
            errors.append(
                f"{finding_id}: No Plan Change findings require approval_status=Approved"
            )

    record = {
        "id": finding_id,
        "severity": severity,
        "status": status,
        "approval_status": approval_status,
    }
    return errors, record


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: validate_plan_review_log.py <plan_path>", file=sys.stderr)
        return 2

    plan_path = Path(argv[1])
    if not plan_path.is_file():
        print(f"Plan file not found: {plan_path}", file=sys.stderr)
        return 2

    text = plan_path.read_text(encoding="utf-8")
    log = extract_log_section(text)
    if log is None:
        print(
            "ERROR: No '## Plan Review Log' section found in the plan.", file=sys.stderr
        )
        return 2

    findings = split_findings(log)
    if not findings:
        # An empty log is valid (no review rounds run yet, or a round with no findings).
        # But if the round was actually run, it should have a metadata block.
        # We accept an empty log as exit 0; the orchestrator decides whether a review is required.
        print("OK: Plan Review Log present, no findings recorded.")
        return 0

    all_errors: list[str] = []
    records: list[dict] = []
    for block in findings:
        errors, record = validate_finding(block)
        all_errors.extend(errors)
        records.append(record)

    if all_errors:
        print("MALFORMED LOG:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 2

    blocking_open = [
        r
        for r in records
        if r["status"] == "Open" and r["severity"] in BLOCKING_SEVERITIES
    ]
    if blocking_open:
        print("BLOCKING FINDINGS STILL OPEN:", file=sys.stderr)
        for r in blocking_open:
            print(f"  - {r['id']} [{r['severity']}] still Open", file=sys.stderr)
        return 1

    counts = {
        "total": len(records),
        "resolved": sum(1 for r in records if r["status"] == "Resolved"),
        "no_plan_change": sum(1 for r in records if r["status"] == "No Plan Change"),
        "advisory_open": sum(
            1 for r in records if r["status"] == "Open" and r["severity"] == "Advisory"
        ),
    }
    print(
        f"OK: plan is execution-ready. "
        f"Total findings: {counts['total']}, "
        f"Resolved: {counts['resolved']}, "
        f"No Plan Change: {counts['no_plan_change']}, "
        f"Advisory open (non-blocking): {counts['advisory_open']}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

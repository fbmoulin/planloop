"""Deterministic tests for validate_plan_review_log.py.

Each test writes a plan to a tmp file and asserts the validator's exit code.
Exit codes (from the script docstring):
    0 = log well-formed, no blocking findings open
    1 = blocking findings still Open
    2 = log malformed or missing
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate_plan_review_log.py"


def run_validator(plan_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(plan_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def write_plan(tmp_path: Path, body: str) -> Path:
    plan = tmp_path / "plan.md"
    plan.write_text(body, encoding="utf-8")
    return plan


def _resolved_finding_block(severity: str = "Critical") -> str:
    return f"""\
##### Finding R1-PRC001: Sample resolved finding

status: Resolved
severity: {severity}
location: Task 4, Step 2

reviewer_concern: |
  Migration has no rollback path documented.

why_it_matters: |
  Production outage if forward-only migration fails mid-flight.

decision: Change plan

plan_changes_made: |
  Added Task 4b documenting reversal SQL in plans/migration.md section Rollback.

no_change_rationale:

human_approver: felipe@lex
approval_status: Approved
approval_date: 2026-05-15
"""


def _open_finding_block(severity: str = "Critical") -> str:
    return f"""\
##### Finding R1-PRC001: Sample open finding

status: Open
severity: {severity}
location: Task 4

reviewer_concern: |
  Migration has no rollback path documented.

why_it_matters: |
  Production outage if forward-only migration fails mid-flight.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:
"""


def _no_change_finding_block(rationale: str, severity: str = "Major") -> str:
    return f"""\
##### Finding R1-PRC002: Sample no-change finding

status: No Plan Change
severity: {severity}
location: Task 7

reviewer_concern: |
  Reviewer flagged absence of integration tests for the new endpoint.

why_it_matters: |
  Regressions could ship undetected.

decision: No plan change

plan_changes_made:

no_change_rationale: |
  {rationale}

human_approver: felipe@lex
approval_status: Approved
approval_date: 2026-05-15
"""


def _wrap(findings: str) -> str:
    return f"""# Plan

Some plan content.

## Plan Review Log

### Review Round 1

reviewer_model: claude-opus-4-7
reviewer_prompt: code-plan-reviewer@v0.1
date: 2026-05-15
spec_reviewed: specs/sample.md
plan_reviewed: plans/sample.md
diverse_critics: false

#### Findings

{findings}
"""


def test_missing_log_section_exits_2(tmp_path: Path) -> None:
    plan = write_plan(tmp_path, "# Plan\n\nNo log section here.\n")
    result = run_validator(plan)
    assert result.returncode == 2
    assert "No '## Plan Review Log' section" in result.stderr


def test_empty_log_section_exits_0(tmp_path: Path) -> None:
    plan = write_plan(tmp_path, "# Plan\n\n## Plan Review Log\n")
    result = run_validator(plan)
    assert result.returncode == 0
    assert "no findings recorded" in result.stdout


def test_open_critical_finding_blocks(tmp_path: Path) -> None:
    plan = write_plan(tmp_path, _wrap(_open_finding_block("Critical")))
    result = run_validator(plan)
    assert result.returncode == 1
    assert "R1-PRC001" in result.stderr
    assert "Critical" in result.stderr


def test_open_major_finding_blocks(tmp_path: Path) -> None:
    plan = write_plan(tmp_path, _wrap(_open_finding_block("Major")))
    result = run_validator(plan)
    assert result.returncode == 1


def test_open_minor_finding_blocks(tmp_path: Path) -> None:
    plan = write_plan(tmp_path, _wrap(_open_finding_block("Minor")))
    result = run_validator(plan)
    assert result.returncode == 1


def test_open_advisory_does_not_block(tmp_path: Path) -> None:
    plan = write_plan(tmp_path, _wrap(_open_finding_block("Advisory")))
    result = run_validator(plan)
    assert result.returncode == 0
    assert "Advisory open (non-blocking): 1" in result.stdout


def test_resolved_finding_passes(tmp_path: Path) -> None:
    plan = write_plan(tmp_path, _wrap(_resolved_finding_block()))
    result = run_validator(plan)
    assert result.returncode == 0
    assert "Resolved: 1" in result.stdout


def test_no_change_with_concrete_rationale_passes(tmp_path: Path) -> None:
    rationale = (
        "Forward-only migrations are documented architecture policy in docs/adr/0007."
    )
    plan = write_plan(tmp_path, _wrap(_no_change_finding_block(rationale)))
    result = run_validator(plan)
    assert result.returncode == 0
    assert "No Plan Change: 1" in result.stdout


def test_no_change_with_brief_rationale_fails(tmp_path: Path) -> None:
    plan = write_plan(tmp_path, _wrap(_no_change_finding_block("Too short.")))
    result = run_validator(plan)
    assert result.returncode == 2
    assert "too brief" in result.stderr


def test_resolved_without_plan_changes_fails(tmp_path: Path) -> None:
    broken = _resolved_finding_block().replace(
        "plan_changes_made: |\n  Added Task 4b documenting reversal SQL"
        " in plans/migration.md section Rollback.",
        "plan_changes_made:",
    )
    plan = write_plan(tmp_path, _wrap(broken))
    result = run_validator(plan)
    assert result.returncode == 2
    assert "plan_changes_made" in result.stderr


def test_resolved_without_approval_fails(tmp_path: Path) -> None:
    broken = _resolved_finding_block().replace(
        "approval_status: Approved", "approval_status: pending"
    )
    plan = write_plan(tmp_path, _wrap(broken))
    result = run_validator(plan)
    assert result.returncode == 2
    assert "Approved" in result.stderr


def test_template_placeholder_rejected(tmp_path: Path) -> None:
    broken = _resolved_finding_block().replace(
        "Migration has no rollback path documented.",
        "[Verbatim from reviewer subagent output]",
    )
    plan = write_plan(tmp_path, _wrap(broken))
    result = run_validator(plan)
    assert result.returncode == 2
    assert "placeholder" in result.stderr


def test_invalid_severity_rejected(tmp_path: Path) -> None:
    broken = _resolved_finding_block().replace(
        "severity: Critical", "severity: Catastrophic"
    )
    plan = write_plan(tmp_path, _wrap(broken))
    result = run_validator(plan)
    assert result.returncode == 2
    assert "severity" in result.stderr


def test_invalid_status_rejected(tmp_path: Path) -> None:
    broken = _resolved_finding_block().replace("status: Resolved", "status: Maybe")
    plan = write_plan(tmp_path, _wrap(broken))
    result = run_validator(plan)
    assert result.returncode == 2
    assert "status" in result.stderr


def test_missing_plan_file_exits_2(tmp_path: Path) -> None:
    result = run_validator(tmp_path / "does-not-exist.md")
    assert result.returncode == 2
    assert "not found" in result.stderr


def test_no_args_exits_2() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Usage" in result.stderr


def test_multiple_findings_one_open_blocks(tmp_path: Path) -> None:
    body = _wrap(
        _resolved_finding_block()
        + "\n"
        + _open_finding_block("Major").replace("R1-PRC001", "R1-PRC003")
    )
    plan = write_plan(tmp_path, body)
    result = run_validator(plan)
    assert result.returncode == 1
    assert "R1-PRC003" in result.stderr


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

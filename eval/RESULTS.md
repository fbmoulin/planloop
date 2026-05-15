# Eval Results — Round 1 (2026-05-15)

Baseline RED/GREEN evaluation of `plan-review-cycle` v0.1 against a code
implementation plan seeded with 5 flaws. Methodology per SPEC §10.

## Setup

- **Skill location:** `~/.claude/skills/plan-review-cycle/` (user-level install).
- **Plan under review:** `eval/plan-jsoncheck-seeded.md`.
- **Spec:** `eval/spec-jsoncheck.md`.
- **Seeded flaws:** see `eval/SEEDS.md`.
- **Reviewer dispatched via:** Claude Code `Agent` tool, `subagent_type=general-purpose`, prompt = `reviewers/code-plan-reviewer.md` template filled.
- **Round number:** 1.

## RED state (no review yet)

Validator output before any review round:

```text
$ python3 scripts/validate_plan_review_log.py eval/plan-jsoncheck-seeded.md
ERROR: No '## Plan Review Log' section found in the plan.
exit=2
```

Hard gate triggered: a plan with no review log cannot be declared
execution-ready. As expected.

## GREEN state (Round 1 reviewer output)

Reviewer returned `Status: Issues Found` with 8 findings and 2 recommendations.
Full output captured in the appended Plan Review Log of
`plan-jsoncheck-seeded.md` (all findings recorded as Open pending
disposition).

## Score against seeds

| Seed | Expected severity | Surfaced as | Severity hit | Notes |
|---|---|---|---|---|
| C1 — Missing YAML schema support | Critical | R1-PRC001 Critical | ✓ exact | Perfect match |
| C2 — Exit code 99 contradicts spec | Critical | R1-PRC004 Major | soft -1 | Found, but downgraded one level |
| M1 — `--verbose` scope creep | Major or Minor | R1-PRC005 Minor | ✓ in range | Picked Minor |
| m1 — TDD violation + vague tests | Major or Minor | R1-PRC003 Major + R1-PRC006 Minor | ✓ split | Reviewer correctly separated the two concerns |
| A1 — Polish task (advisory bait) | Advisory or absent | R1-PRC007 Minor | soft +1 | Over-flagged by one level |

**Bonus finding (not seeded, legitimate):** R1-PRC008 — plan has no
verification of non-functional requirements (read-only, no network, LOC
limit). Real gap. Counts as bonus catch, not false positive.

**Recommendations (advisory):** `__main__.py` package layout reminder
and dependency-pinning task. Both legitimate observations.

## Metrics

- **Discovery rate:** 5/5 seeds surfaced = **100%** (target ≥ 75%).
- **False-positive rate:** 0/8 findings = **0%** (target ≤ 25%).
- **Sycophancy check:** PASS — reviewer raised 8 issues; did not return
  blanket Approved.
- **Severity calibration:** mostly correct. Two mild miscalibrations
  (C2 down by 1 level, A1 up by 1 level) net to roughly zero bias.
- **Cost:** one Opus 4.7 subagent dispatch, ~48k tokens, ~49s wall.

## Findings for the skill itself (meta-eval)

Things to consider for `code-plan-reviewer.md` v0.2:

1. **Critical-severity criteria for spec contradictions.** Strengthen the
   reviewer prompt's Severity guide so that "exit code contradicts the
   spec contract" reliably classifies as Critical, not Major. Suggested
   prompt edit: add an example under Critical reading "Spec contract
   violation (exit codes, return shapes, public API)".

2. **Advisory criterion clarity.** A polish-only task with no concrete
   failure mode should be Advisory or unflagged. The reviewer flagged
   it as Minor. Add explicit example: "A task whose entire body is
   subjective improvement language ('polish', 'improve', 'clearer')
   without naming a specific failure mode is at most Advisory."

3. **Recommendations slot is being used productively.** Both items
   surfaced under Recommendations were valid. Keep that section.

## Disposition (not run as part of this eval)

Per SKILL.md step 6, the orchestrator would now walk Felipe through
each finding one at a time and capture per-finding Resolved or
No Plan Change disposition. That interaction is the human-in-the-loop
phase and is outside the scope of this automated eval.

For demonstration purposes the appended Plan Review Log in
`plan-jsoncheck-seeded.md` leaves all 8 findings as Open. Running the
validator against the plan now returns exit code 1 (blocking findings
still open), which is the correct behavior.

## Conclusion

`plan-review-cycle` v0.1 GREEN run on the jsoncheck seeded plan passed
all eval criteria. The skill correctly:

- Loaded and dispatched the code-plan reviewer.
- Surfaced every seeded flaw (5/5).
- Produced zero false positives.
- Caught one legitimate non-seeded gap (NFR verification).
- Triggered the hard gate via validator (exit 1 with findings Open).

Mild calibration issues (1 severity-down, 1 severity-up) are
documented as candidate prompt edits for v0.2 but do not affect the
correctness of the workflow.

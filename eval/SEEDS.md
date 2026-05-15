# Seeded Flaws in `plan-jsoncheck-seeded.md`

Hidden problems intentionally planted to test the reviewer. The eval
measures whether the reviewer surfaces these (and at what severity), and
how many false positives it adds.

## Critical seeds

**C1 — Missing YAML schema support.** The spec (FR-2) requires schemas
loadable from both `.json` and `.yaml`/`.yml`. Task 2 (`load_schema`)
hardcodes `json.load` and ignores YAML entirely. No other task adds YAML
support. The plan, as written, cannot satisfy the spec.
- Expected severity: **Critical** (missing requirement, plan cannot be
  executed to satisfy spec).
- Expected location: Task 2.

**C2 — Contradictory exit code.** Spec FR-3 mandates exit codes `0/1/2`
only. Task 3 raises `SystemExit(99)` on engine errors. Task 4 routes
exceptions to exit 2 but only catches `FileNotFoundError` and
`JSONDecodeError` — a raw `SystemExit(99)` from Task 3 propagates and
violates the spec.
- Expected severity: **Critical** (spec contradiction, observable
  behavior wrong).
- Expected location: Task 3 vs Task 4 vs Spec FR-3.

## Major seed

**M1 — Spec violation: no-disk-writes vs `--verbose` introspection.**
Less clear-cut than the Criticals: Task 5 adds `--verbose` (writes
"intermediate parsing state to stderr"). The spec says "the tool MUST
NOT write to disk". Stderr is not disk, so it's not a strict spec
violation, but the flag is also out-of-scope (spec doesn't request it)
and is added mid-implementation rather than as a planned feature. This
is scope creep and adds a maintenance burden.
- Expected severity: **Major** or **Minor** depending on reviewer
  judgment. Major if reviewer reads it as scope creep with maintenance
  cost; Minor if reviewer treats it as a benign add.
- Expected location: Task 5.

## Minor seed

**m1 — Vague tests acceptance.** Task 6 says "Aim for adequate
coverage" with no concrete success criteria (no coverage threshold, no
list of cases). Spec demands TDD ("tests precede implementation") but
Task 6 is the **last** task — tests are written after the implementation
tasks. This is a TDD violation per spec non-functional requirements.
- Expected severity: **Major** (TDD violation per spec) OR **Minor**
  (vague acceptance criteria) — reviewer should pick one.
- Expected location: Task 6.

## Advisory bait

**A1 — Polish-only task.** Task 7 "Improve error messages" has no
concrete failure mode. It's purely cosmetic. The reviewer should
correctly classify this as **Advisory** (or not flag it at all). If the
reviewer marks it as Critical/Major, that's a calibration failure.
- Expected severity: **Advisory** or **not flagged**.
- Expected location: Task 7.

## Scoring rubric

For this eval (1 RED + 1 GREEN run):

- **Discovery rate:** % of intentional flaws surfaced (C1, C2, M1, m1).
  Target ≥ 75% (3 of 4).
- **Severity calibration:** C1 and C2 should be Critical; M1/m1 split
  between Major/Minor is acceptable; A1 should be Advisory or absent.
- **False positives:** any finding that does not map to a seed and
  does not name a real issue Felipe agrees with is a false positive.
  Target ≤ 2 per round.
- **Sycophancy check:** if the reviewer returns "Status: Approved" with
  zero findings, the reviewer is broken — escalate.

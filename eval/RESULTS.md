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

---

# Round 2 — calibration check on `code-plan-reviewer@v0.2`

Re-ran the same seeded plan against the calibrated reviewer prompt.
Goal: verify that v0.2's two added rules (spec-contract violations →
Critical; polish-only language → Advisory) correct the two mild
miscalibrations observed in Round 1.

## v0.1 vs v0.2 severity comparison (same plan, same seeds)

| Seed | v0.1 (Round 1) | v0.2 (Round 2) | Δ | Expected per SEEDS.md |
|---|---|---|---|---|
| C1 — YAML missing | Critical | Critical | — | Critical ✓ |
| C2 — exit 99 contradicts spec | Major | **Critical** | ↑ | Critical ✓ |
| Related — exit 2 mapping incomplete | Major | **Critical** | ↑ | (bonus contract finding) |
| m1 (TDD) — tests after impl | Major | Major | — | Major or Minor ✓ |
| m1 (vague) — adequate coverage | Minor | Minor | — | Major or Minor ✓ |
| M1 — `--verbose` scope creep | Minor | Minor | — | Major or Minor ✓ |
| A1 — Task 7 polish-only | Minor | **Advisory** | ↓ | Advisory or absent ✓ |
| Bonus — NFR verification gap | Minor | **Major** | ↑ | (legitimate uplift) |

Distribution shift:

|  | Critical | Major | Minor | Advisory | Total |
|---|---|---|---|---|---|
| v0.1 Round 1 | 1 | 3 | 4 | 0 | 8 |
| v0.2 Round 2 | 3 | 2 | 2 | 1 | 8 |

Both calibration targets hit. All 5 seeds now classify at the
expected severity exactly.

## Side effect: framing transfer

The v0.2 "spec contract is the contract" framing propagated beyond the
single target seed. Two additional findings whose underlying nature is
also contract-violation were promoted:

- R2-PRC003 (exit-2 mapping incomplete) → Major in v0.1, **Critical**
  in v0.2. This is correct: it is the same contract surface as C2.
- R2-PRC005 (NFR no-network silently violatable via `$ref`) → Minor in
  v0.1, **Major** in v0.2. This is correct: the spec's no-network MUST
  is also a contract, and the lack of any verification means it can be
  silently breached.

Conclusion: severity calibration on one rule reshapes the reviewer's
mental frame globally, not just on the target case. This is the
intended outcome of severity examples in prompts. Document the effect
for future calibration cycles.

## v0.3 candidate: output format ambiguity

In Round 2 the reviewer placed the Advisory finding (R2-PRC008) under
the `### Recommendations` heading while still numbering it as a Finding
block with full structure. The output template treats Recommendations
as a separate bullet section for brief advisory items, distinct from
numbered Findings. The reviewer's behavior is not wrong (the item is
correctly Advisory and the slot is for advisory content), but the
boundary between "numbered Finding with severity Advisory" and
"unnumbered Recommendations bullet" is ambiguous.

Suggested v0.3 prompt clarification: state explicitly that Advisory
items either appear as numbered Findings under `### Findings` with
severity Advisory, OR as brief bullets under `### Recommendations`,
but not as numbered Findings under `### Recommendations`. Pick one
convention.

## Metrics — Round 2

- **Discovery rate:** 5/5 seeds (100%, unchanged from R1).
- **False positives:** 0/8 (unchanged from R1).
- **Severity calibration:** 5/5 seeds at expected severity (R1: 3/5).
- **Sycophancy check:** PASS.
- **Cost:** 1 subagent dispatch, ~52k tokens, ~46s.

## Conclusion — v0.2

The two targeted calibration edits achieved their goal. Spec-contract
violations now reliably classify as Critical; polish-only language now
reliably classifies as Advisory. As a side effect, the reviewer's
overall framing is sharper around contract semantics. No regressions
detected. Recommend installing v0.2 as the default.

---

# Round 3 — `code-plan-reviewer@v0.3` (output-format fix)

Verification round after applying the family-wide v0.3 edit: removed
the `### Recommendations` section from all three reviewer prompts
(code, judicial, generic) and added an explicit inverse rule. All
findings — including Advisory — now go under `### Findings` with
explicit `Severity:`.

## What changed in v0.3

Single edit applied uniformly across `reviewers/code-plan-reviewer.md`,
`reviewers/judicial-plan-reviewer.md`, and `reviewers/generic-plan-reviewer.md`:

1. Version frontmatter bumped to `v0.3`.
2. Output template lost `### Recommendations` and gained an inverse
   rule in the "Output format" preamble: "Do NOT add a Recommendations
   section or any other section beyond Findings — every observation
   worth raising goes under Findings with explicit Severity, including
   advisory observations (Severity: Advisory)."
3. Output template's last-line guidance now reads "Advisory findings
   use the same structure with shorter prose, since they do not block
   execution."
4. `Reviewer prompt:` line in the output template bumped to `@v0.3`.

`SKILL.md` was checked and did not require changes (no references to
`Recommendations` section anywhere; Advisory severity was already
properly handled by the Plan Review Log schema and validator).

## R3 — Code reviewer v0.3 on jsoncheck seeded plan

8 findings, 2 Critical + 2 Major + 3 Minor + 1 Advisory. The reviewer
followed v0.3 exactly:

- No `### Recommendations` heading produced.
- R3-PRC008 (Task 7 polish) appears as a numbered Finding under
  `### Findings` with `Severity: Advisory` and full Concern / Why it
  matters / Suggested resolution structure.

## Comparison across the three rounds

| Seed | v0.1 R1 | v0.2 R2 | v0.3 R3 | Expected |
|---|---|---|---|---|
| C1 (YAML missing) | Critical | Critical | Critical | Critical ✓ |
| C2 (exit 99 contradiction) | Major | Critical | Critical | Critical ✓ |
| Related (exit 2 mapping incomplete) | Major | Critical | Major | (in range) |
| TDD ordering | Major | Major | Major | Major ✓ |
| m1 (vague coverage) | Minor | Minor | Minor | Minor ✓ |
| M1 (`--verbose` scope creep) | Minor | Minor | Minor | Minor ✓ |
| NFR verification gap | Minor | Major | Minor | (legitimate either way) |
| A1 (Task 7 polish) | Minor | Advisory | Advisory | Advisory ✓ |

Distribution shift across rounds (same plan):

|   | Critical | Major | Minor | Advisory | Total |
|---|---|---|---|---|---|
| v0.1 R1 | 1 | 3 | 4 | 0 | 8 |
| v0.2 R2 | 3 | 2 | 2 | 1 | 8 |
| v0.3 R3 | 2 | 2 | 3 | 1 | 8 |

Two minor downgrades in v0.3 vs v0.2 (exit-2 mapping and NFR
verification dropped one level each). Both still in range of their
v0.2 severity examples. Interpretation: v0.3's tighter Major/Minor
examples (added in v0.2) anchor the gradient more conservatively, so
the reviewer reserves Critical more strictly. The seed targets stay
exact at 5/5.

## Metrics — R3

- **Output format compliance:** PASS — no Recommendations section
  produced, Advisory finding correctly under Findings.
- **Discovery:** 5/5 seeds (100%).
- **Severity calibration on seeds:** 5/5 exact (same as R2).
- **False positives:** 0/8.
- **Cost:** 1 dispatch Opus 4.7, ~52k tokens, ~47s.

## Conclusion — v0.3

The output-format ambiguity is resolved. All three reviewer prompts now
have a single output namespace (Findings) and an explicit inverse rule
against producing a Recommendations section. Empirical verification on
the code reviewer confirms compliance and preserves v0.2's severity
calibration on the seed set.

The judicial and generic reviewers received the same edit pattern and
are expected to behave consistently. The judicial v0.2 → v0.3 ambiguity
in particular (Round 2 produced R2-PRC008 under `### Achados` then
duplicated it under `### Recomendações` as a bullet) is now structurally
impossible.

Note for v0.4: minor downgrades on lateral findings (R3-PRC003,
R3-PRC007) suggest the Major/Minor boundary could benefit from one
additional anchoring example. Not urgent; calibration is within
acceptable bounds.

---

# Round 4 — `code-plan-reviewer@v0.4` (silently-violatable MUST anchor)

Verification round after applying the v0.4 Major-tier anchor: "a spec
MUST without any verification step in the plan when the MUST can be
silently violated at runtime without test failure — silently-violatable
MUSTs are Major even when they look like non-functional polish."

## R4 vs prior rounds on jsoncheck seeded plan

| Seed | v0.1 R1 | v0.2 R2 | v0.3 R3 | v0.4 R4 | Expected |
|---|---|---|---|---|---|
| C1 (YAML missing) | Critical | Critical | Critical | Critical | Critical ✓ |
| C2 (exit 99 contradiction) | Major | Critical | Critical | Critical | Critical ✓ |
| Exit-2 mapping incomplete | Major | Critical | Major | **Critical** | range; v0.4 re-promoted via contract framing |
| TDD ordering | Major | Major | Major | Major | Major ✓ |
| m1 (vague coverage) | Minor | Minor | Minor | Minor | Minor ✓ |
| M1 (--verbose scope creep) | Minor | Minor | Minor | Minor | Minor ✓ |
| NFR verification gap | Minor | Major | Minor | **Major** | ✓ **FIXED** (v0.4 target) |
| A1 (polish) | Minor | Advisory | Advisory | Advisory | Advisory ✓ |
| NEW: 3-module layout vs single-file MUST | — | — | — | **Major** | bonus catch from v0.4 lens |

Distribution shift:

|   | Critical | Major | Minor | Advisory | Total |
|---|---|---|---|---|---|
| v0.1 R1 | 1 | 3 | 4 | 0 | 8 |
| v0.2 R2 | 3 | 2 | 2 | 1 | 8 |
| v0.3 R3 | 2 | 2 | 3 | 1 | 8 |
| v0.4 R4 | 3 | 3 | 2 | 1 | 9 |

## Key wins

1. **NFR verification gap restored to Major** (was Minor in v0.3 R3,
   matching v0.2 R2). The reviewer explicitly cited the v0.4 rule:
   "Per v0.4 calibration, a spec MUST without any verification step
   where the constraint can be silently violated at runtime without
   test failure is Major. Re-flagged from R1-PRC008; no plan change
   applied."

2. **NEW bonus finding R4-PRC006: single-file MUST vs 3-module layout
   contradiction.** The same "silently-violatable MUST" lens that
   v0.4 introduced led the reviewer to spot a Spec-vs-Plan contradiction
   in the Approach section that *no prior round had caught*. The spec
   says "single-file CLI under 200 LOC" but the plan creates
   `jsoncheck/{cli,loader,engine}.py` — the reviewer surfaced the
   inconsistency and noted "Implementer cannot tell whether to ship
   one file or three." Excellent emergent behavior from the new rule.

3. **A1 explicitly self-corrected**: "Re-flagged from R1-PRC007 with
   severity corrected from Minor to Advisory." The reviewer is now
   aware of the prior log and applies v0.4 rules retroactively.

4. **Exit-2 mapping re-promoted to Critical**: the v0.4 framing
   ("contract mismatch on exit codes") pulled it back from Major.
   Defensible — both v0.2 (Critical) and v0.4 (Critical) are within
   spec-contract framing.

## Metrics — R4

- **Discovery:** 5/5 seeds (100%)
- **Severity calibration on seeds:** 5/5 exact
- **False positives:** 0/9
- **Bonus catches:** 1 new finding (R4-PRC006) revealed by the new lens
- **Output format compliance:** PASS — no Recommendations section
- **Cost:** 1 dispatch Opus 4.7, ~48k tokens, ~29s

## Conclusion — v0.4 code

The "silently-violatable MUST" anchor achieved both targets:

- recalibrated NFR verification from Minor back to Major (the
  oscillation between v0.2 Major and v0.3 Minor stabilized)
- as side effect, the same lens revealed a Spec-vs-Plan contradiction
  (single-file vs 3-module layout) that earlier rounds missed

This is the second time we observe that a focused severity rule
propagates to surface new findings beyond its target (cf. v0.2's
"contract is the contract" lens promoting NFR and exit-2 mapping).
Severity prompts are not just calibration — they reshape the
reviewer's attention map.

No regressions on the seed targets. Calibration is now stable across
v0.2/v0.3/v0.4 on the core seeds, with deliberate improvement on the
NFR boundary in v0.4.

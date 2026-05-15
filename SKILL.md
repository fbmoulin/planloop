---
name: plan-review-cycle
description: Use when a written implementation plan, judicial draft plan, content plan, or any structured pre-execution document exists and needs independent verification before execution begins. Activates on user requests like "review the plan", "run a reviewer subagent", "verify this plan", "let's review before executing", "audit this plan", or "another review round". Especially required for large plans, plans with many constraints, plans involving AI-assisted judicial output subject to CNJ Resolução 615/2025 audit obligations, refactors touching multiple subsystems, AWS infrastructure changes, or any plan that will be executed by subagents. Always trigger this skill when the user mentions independent review, plan audit, plan verification, finding disposition, or wants to enforce a quality gate between plan-writing and execution. Do not use this skill for creating the initial plan, reviewing already-implemented code, or replacing the inline self-review inside writing-plans.
---

# Plan Review Cycle

## Quick Reference

1. Read the plan and infer domain. Confirm reviewer prompt with the human.
2. Dispatch a fresh reviewer subagent with the appropriate reviewer prompt and the existing Plan Review Log.
3. Parse findings into round-scoped IDs. Append to the Plan Review Log inside the plan file.
4. Present findings to the human one at a time, ordered by severity.
5. For each finding, capture decision and rationale. Update the plan only after explicit approval.
6. Run `scripts/validate_plan_review_log.py` against the plan. If it exits non-zero, fix what it reports.
7. Ask whether to run another round, capped at three. Escalate if round three still produces Critical findings.
8. Hand off to the next workflow step only after the validator passes.

## Overview

Run an independent verification loop on a written plan before execution begins. Every reviewer finding closes as either a plan change or a documented no-change rationale, each approved explicitly by the human partner. The Plan Review Log inside the plan file is the durable audit trail; the validator script is the programmatic gate.

Core invariant: no finding disappears. It is either resolved by changing the plan or preserved with an explicit rationale recorded in the plan and approved by the human partner.

State at the start of the cycle: "Running plan-review-cycle on [plan path] with [reviewer prompt name and version]. Round [N]."

## When to use

Use after a complete plan exists and before execution starts. The plan can be a writing-plans output, a hand-written spec, a judicial drafting plan (sentença, decisão, despacho), an architecture document, or a content plan.

Triggers:

- The human asks for plan verification, independent review, another review round, or a reviewer subagent.
- The plan involves AI-assisted judicial output and an audit trail is required.
- The plan touches multiple subsystems, multiple constraints, or will be executed by subagents.
- The plan is being submitted to a code review or to a publication process where independent verification is expected.

Do not use for:

- Creating the initial plan (use writing-plans).
- Reviewing implemented code (use requesting-code-review).
- Debugging a failing implementation.
- Replacing the inline self-review inside writing-plans.

## Required inputs

- Plan file path (required).
- Spec, requirements, or design document path (recommended; ask if missing).
- Any constraints, priorities, or non-goals the human wants the reviewer to respect.
- Round number (the orchestrator infers; defaults to 1 if no Plan Review Log exists yet).

If the spec path is missing, ask once before starting. Proceed only if the human confirms running without the spec.

## Domain selection

The skill ships three reviewer prompts in `reviewers/`:

- `code-plan-reviewer.md`: software implementation plans, refactors, infrastructure changes.
- `judicial-plan-reviewer.md`: judicial drafting plans (PT-BR, calibrated for CPC 489 and CNJ 615/2025).
- `generic-plan-reviewer.md`: fallback for product, content, research, or other plans.

Infer the domain from the plan content. Indicators of code: file paths, function names, test commands, Tasks structured as "Create X / Modify Y / Test Z". Indicators of judicial: "fundamentação", "dispositivo", "tese", "CDC", "CPC", "STJ", references to processos, partes, magistrate. Otherwise generic.

Present the inferred selection to the human in one line and ask for confirmation or override. Do not proceed silently.

## The cycle

1. **Dispatch a fresh reviewer subagent.** Use Task with the chosen reviewer prompt from `reviewers/`. Fill the input slots: plan path, spec path, prior Plan Review Log (if any), round number, and any human-provided constraints. Never pass your own session history, internal reasoning, or "why I wrote this plan" framing.

2. **Receive the structured output.** The reviewer returns a Status (Approved or Issues Found) and zero or more findings, each with severity, location, concern, why-it-matters, and a suggested resolution.

3. **If Status is Approved with no findings, skip to step 8.**

4. **Convert each reviewer issue into a tracked finding.** Assign round-scoped ID using the pattern `R<N>-PRC<NNN>` where N is the round number and NNN is the finding number within that round, three digits. Findings never share IDs across rounds.

5. **Append findings to the Plan Review Log** at the end of the plan file, in the format specified in the schema section below.

6. **Present findings to the human partner.** Use a checkbox list ordered by severity. Then walk through them one at a time. For each finding: state the concern and why-it-matters, ask the human's view before proposing anything, propose either a concrete plan change or a no-change rationale, ask for approval, update the plan only on explicit approval.

7. **Ensure every finding closes** as either Resolved (with plan changes recorded) or No Plan Change (with rationale recorded). Both require human approval. Open findings carry over to the next round.

8. **Run the validator.** Execute `python scripts/validate_plan_review_log.py [plan path]` via bash. Exit code 0 means the log is well-formed and no blocking findings are Open. Exit code 1 means blocking findings remain Open; address them. Exit code 2 means the log itself is malformed; fix the structural issue. Do not declare the cycle complete while the validator returns non-zero.

9. **Ask whether to run another round.** Use the recommendation rule below. Cap at three rounds total. If round three still surfaces a Critical finding, do not run round four; instead surface the escalation message in step 11.

10. **If yes, repeat from step 1** with the round number incremented and the existing Plan Review Log passed to the new reviewer.

11. **If no, or if escalation is triggered, hand off.** For escalation: "Round 3 surfaced new Critical findings. The plan keeps regenerating critical issues. Recommend returning to brainstorming or writing-plans rather than running another review round; the spec or scope may be wrong." For normal completion: ask whether to proceed to execution (using subagent-driven-development, executing-plans, or signing the judicial draft, as appropriate).

## Reviewer dispatch template

When dispatching, use the Task tool (general-purpose) with the appropriate reviewer prompt loaded as the prompt body. Fill these slots:

```
[PLAN_PATH]: absolute path to the plan file
[SPEC_PATH]: absolute path to the spec file, or "not provided"
[PRIOR_LOG]: contents of the existing Plan Review Log section, or "none (round 1)"
[ROUND_NUMBER]: 1, 2, or 3
[HUMAN_CONSTRAINTS]: any constraints the human stated, or "none"
```

Context isolation rule: do not include your own session history, your reasoning about the plan, or any preamble defending the plan's correctness. The reviewer's value is independent judgment; pollution breaks that.

## Plan Review Log schema

Append the log section near the end of the plan file, after implementation tasks and before any execution handoff notes. If the section already exists, append a new round block to it.

```markdown
## Plan Review Log

### Review Round N

reviewer_model: claude-opus-4-7
reviewer_prompt: code-plan-reviewer@v0.1
date: YYYY-MM-DD
spec_reviewed: path/to/spec.md
plan_reviewed: path/to/plan.md
diverse_critics: false

#### Findings

##### Finding R<N>-PRC<NNN>: Short title

status: Open
severity: Critical
location: Task 4, Step 2

reviewer_concern: |
  [Verbatim from reviewer subagent output.]

why_it_matters: |
  [Concrete risk: implementation, legal, contractual, or other.]

decision: pending

plan_changes_made: |

no_change_rationale: |

human_approver:
approval_status: pending
approval_date:
```

After the human approves a disposition, update the same finding block in place: set status to Resolved or No Plan Change, fill decision, fill either plan_changes_made or no_change_rationale, fill human_approver with the human's identifier, set approval_status to Approved, fill approval_date with the actual date.

For the judicial variant, add two optional fields below approval_date:

```markdown
cnj_615_relevance: alto_risco | baixo_risco | nao_aplicavel
contestabilidade_observada: true | false
```

Never leave template placeholder text like "[Verbatim from reviewer subagent output]" in a closed finding. The validator will reject it.

## Finding disposition rules

Every reviewer finding starts as Open.

**Resolved** requires that the plan was changed. Record the exact sections or tasks changed and a one-sentence summary of each change. The validator verifies that plan_changes_made references existing parts of the plan.

**No Plan Change** requires that the plan was not changed. Record an explicit rationale: the existing plan is already sufficient, the issue is out of scope, the concern is intentionally deferred to a named later phase, or the matter is superseded by a specifically-named other task. Vague rationales like "we will handle this later" fail the validator. The rationale must name what supersedes, defers, or scopes-out the concern.

**Open** is the default. A finding stays Open across rounds if disposition is pending. Open findings whose severity is Critical, Major, or Minor block execution.

Never silently discard a finding. Never decide a finding is invalid without recording the reasoning and obtaining human approval. Never update the plan unless the human partner explicitly confirms the disposition.

## Severity semantics

| Severity | Blocks execution while Open? | Use for |
|---|---|---|
| Critical | Yes, always | Missing required content, contradictions, unsafe paths, tasks that cannot be executed, omissões geradoras de nulidade |
| Major | Yes, unless human explicitly accepts the risk in writing | Issues likely to cause rework, incomplete behavior, or significant downstream cost |
| Minor | Yes, until closed | Worth addressing or documenting; should not require large plan changes |
| Advisory | No, never blocks | Non-blocking suggestions; record only if human wants them tracked |

Do not allow severity downgrade without an independent rebuttal. If the human asks to reduce a Critical to Advisory, that decision becomes itself a No Plan Change finding requiring its own rationale and approval.

## Diverse critics option

For plans flagged as high-stakes, run two reviewers in parallel with different role prompts and merge findings before disposition. Use this option when:

- The plan involves judicial output in a CNJ 615/2025 alto-risco category.
- The plan is a large refactor (more than five files or more than one subsystem).
- The plan affects production infrastructure or paying customers.
- The human partner requests diverse critics explicitly.

For judicial plans, the two roles are typically "magistrado garantista" and "magistrado conservador" (or "perspectiva da parte autora" and "perspectiva da parte ré"). For code plans, the two roles are typically "implementer focused on shipping correctly" and "architect focused on long-term cost." Define the role variation by prefacing the reviewer prompt with the role line.

Record `diverse_critics: true` in the round metadata. Merge findings by union (every concern from either reviewer becomes a finding); resolve ID collisions by appending suffix.

## Bounded rounds and escalation

Maximum three rounds per cycle. Recommend another round when:

- Round produced Critical or Major findings that caused substantial plan changes.
- The plan structure changed significantly (new tasks, new files, new dependencies).
- The human partner explicitly wants another round.

Recommend stopping when:

- The round returned no findings or only Advisory.
- Findings were closed as No Plan Change with clear documented rationale.
- Plan changes were small and localized.

**Escalation rule (mandatory):** if round 3 produces a Critical finding, do not propose round 4. State explicitly: "Round 3 surfaced a Critical finding (R3-PRC###: [title]). Three rounds have not converged. Recommend returning to brainstorming or writing-plans to revisit the spec or scope rather than running another review round." Then stop.

## Human partner interaction templates

After findings are returned, present:

```
Review Round N found [count] issue(s):

- [ ] R<N>-PRC001 [Critical] [short title]
- [ ] R<N>-PRC002 [Major] [short title]
- [ ] R<N>-PRC003 [Advisory] [short title]

Would you like to walk through them in order of severity?
```

For each finding, after presenting concern and why-it-matters:

```
What are your thoughts on this? Do you see it the same way, or is there context I'm missing?
```

After the human responds, propose a concrete disposition, then:

```
Approve this disposition?
- Resolved (change the plan as proposed)
- No Plan Change (record the rationale as proposed)
- Reject (re-propose)
- Defer (leave Open, revisit next round)
```

Mark the checkbox only after explicit approval.

## Hard gate via validator

After every round and before declaring the cycle complete, run:

```bash
python scripts/validate_plan_review_log.py [plan_path]
```

Exit codes:
- 0: log is well-formed, no blocking findings Open. Cycle may complete.
- 1: blocking findings Open. List the offending IDs and return to disposition.
- 2: log is malformed. Fix structural issues (missing fields, leftover template placeholders, malformed YAML).

Do not declare the cycle complete on validator non-zero. Do not propose execution while findings remain Open.

## Red flags

Stop and fix if any of these occur:

- A finding is discussed in chat but not recorded in the Plan Review Log.
- A finding's `status` is set to Resolved without `plan_changes_made` filled.
- A finding's `status` is set to No Plan Change without `no_change_rationale` filled and `human_approver` recorded.
- The orchestrator decides a finding is invalid without human approval.
- A review round repeats a finding already closed in a prior round (the reviewer should be instructed not to; if it does, surface it for human review rather than silently dropping).
- Execution is proposed while the validator returns non-zero.
- The Plan Review Log contains unresolved template placeholders or empty required fields.
- A batch approval is requested (all findings approved in one action without per-finding interaction).
- Round 3 produces a Critical finding and round 4 is proposed instead of escalation.

## Handoff

On normal completion: ask the human whether to proceed to execution. For code plans, that typically means subagent-driven-development or executing-plans. For judicial plans, that typically means finalizing the draft for signing or for further internal review.

On escalation: state the escalation message and stop. Do not propose further rounds. Suggest returning to brainstorming or writing-plans.

Do not start execution until the human partner explicitly confirms and the validator has returned 0 on the most recent round.

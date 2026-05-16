# plan-review-cycle

A Claude Skill for running an independent, iterative review of any written plan before execution. Domain-neutral orchestration; reviewer prompt swaps per domain (code, judicial PT-BR, generic). Includes a deterministic Python validator that acts as a hard gate against the LLM rationalizing past open findings.

Designed for dual use: software implementation plans (Kratos, KCP, monorepo, AWS CDK) and judicial drafting plans (sentenças, decisões, despachos) subject to CNJ Resolução 615/2025 audit obligations.

## What's in this folder

```
plan-review-cycle/
├── SPEC.md                                 The design rationale and research synthesis
├── SKILL.md                                The skill itself; this is what Claude reads
├── reviewers/
│   ├── code-plan-reviewer.md               Dispatch prompt for software plans (EN)
│   ├── judicial-plan-reviewer.md           Dispatch prompt for judicial plans (PT-BR)
│   └── generic-plan-reviewer.md            Fallback prompt for other domains (EN)
├── scripts/
│   └── validate_plan_review_log.py         Deterministic validator; exits non-zero if open blocking findings remain
├── schema/
│   └── plan_review_log.schema.json         JSON schema documenting the log structure
└── README.md                               This file
```

## Install

This repository is named `planloop`; the Claude skill inside is named
`plan-review-cycle` (the `name:` field in `SKILL.md`). The install
copies the skill contents into a directory named after the skill, not
the repo.

For personal use across all your projects:

```bash
git clone https://github.com/fbmoulin/planloop.git
mkdir -p ~/.claude/skills/plan-review-cycle
cp -r planloop/SKILL.md planloop/reviewers planloop/scripts planloop/schema ~/.claude/skills/plan-review-cycle/
```

For project-local use only:

```bash
mkdir -p .claude/skills/plan-review-cycle
cp -r planloop/SKILL.md planloop/reviewers planloop/scripts planloop/schema .claude/skills/plan-review-cycle/
```

For Lex Intelligentia ecosystem integration, vendor it next to your transversal skills:

```bash
mkdir -p lex-skills/transversal/plan-review-cycle
cp -r planloop/SKILL.md planloop/reviewers planloop/scripts planloop/schema lex-skills/transversal/plan-review-cycle/
```

## Quick start

After a plan is written, ask Claude:

> "Run plan-review-cycle on plans/2026-05-11-my-plan.md against specs/2026-05-11-my-spec.md."

Or, more loosely (the skill description is calibrated to trigger on these too):

> "Review this plan before we start coding."
> "Audita esse plano de sentença antes que eu finalize."
> "Verify this plan with an independent reviewer."

The skill will infer the domain, confirm the reviewer prompt with you, dispatch a fresh subagent, collect findings, walk through them with you one at a time, update the plan only on your explicit approval, and run the validator as the hard gate.

For each finding, the orchestrator follows a **didactic 4-part standard** (inspired by the ADR pattern from Microsoft / AWS / adr.github.io):

1. Plain-language explanation of what is missing or wrong
2. Practical consequence (anchored in observable cost — hours of rework, regulatory exposure, production bug)
3. **Researched options** (2-4 alternatives, with sources cited for non-trivial technical decisions)
4. Explicit **recommendation** marked `(Recommended)` with 1-2 sentences of justification

Recommendations apply an **anti-overengineering filter** (prefer local edits, existing patterns, 80% solution + documented gap over 100% solution + sprawl) and a **propagation checklist** for findings that touch multiple sections or files.

**See [`USAGE.md`](USAGE.md) for the complete walkthrough** — domain selection, the 4-part disposition standard (§4), propagation checklist for multi-section findings (§4.1), severity semantics, diverse-critics option, manual validator runs, and a troubleshooting table.

## Manual validation

After any review round, you can run the validator yourself:

```bash
python3 scripts/validate_plan_review_log.py path/to/plan.md
```

Exit codes:
- `0`: log is well-formed, no blocking findings open, plan is execution-ready
- `1`: one or more blocking findings still Open; the script names them
- `2`: log is malformed (missing fields, vague rationale, leftover template placeholders, or no log section)

## CI integration

Add to your pre-commit or CI pipeline:

```yaml
- name: Validate Plan Review Log
  run: |
    for plan in plans/*.md; do
      python3 ~/.claude/skills/plan-review-cycle/scripts/validate_plan_review_log.py "$plan" || exit 1
    done
```

A failing validator blocks the merge. This converts "we should review plans" into "the build fails if we don't."

## See also

- `SPEC.md` for the full design rationale, research synthesis, and CNJ 615/2025 compliance mapping. SPEC.md §17 (appendix) traces the calibration history derived from real-world use.
- `USAGE.md` for the day-to-day operational guide.
- `eval/RESULTS-*.md` for empirical evidence from seeded + real evals across all three reviewer domains.
- The obra/superpowers PR #1473 that inspired this work, with the four corrections documented in `SPEC.md` section 1.

## Open questions (resolved during use)

The original open questions from `SPEC.md` section 16 have been resolved during real-world use:

1. **Skill name:** `plan-review-cycle` confirmed (matches obra/superpowers PR familiarity; user-level install lives at `~/.claude/skills/plan-review-cycle/`).
2. **Dispatch mechanism:** general-purpose Task with prompt template inlined (current SKILL.md approach; chosen for portability across Claude Code surfaces).
3. **Diverse critics for judicial plans:** opt-in only for high-stakes plans (CNJ 615/2025 alto-risco categories, sentenças repetitivas), not default.
4. **Round cap:** three rounds with mandatory escalation if round 3 still surfaces a Critical.

Newer evolutionary candidates (from real-use evidence) are tracked in `eval/RESULTS-real-*.md`. Recent applied calibrations:

- **Didactic 4-part disposition standard** (commit `abad346`): orchestrator translates technical reviewer output into plain language + practical consequence + researched options + explicit recommendation. Triggered by operator feedback that pre-calibration presentations were too technical and lacked justified recommendations.
- **Propagation checklist for multi-section findings** (commit `a511f8c`): when a resolution touches 2+ sections or external files, the `plan_changes_made` field MUST contain explicit `- [x]` checklist enumerating every location. Triggered by 4 second-order findings in the pje-mcp SQLite plan eval (R2-PRC002/004/005/008) caused by auto-Resolved acceleration without propagation discipline.
4. Round cap (current default: 3, with mandatory escalation at round 3 if Critical still appearing).

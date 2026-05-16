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

**See [`USAGE.md`](USAGE.md) for the complete walkthrough** — domain selection, finding disposition (Resolved / No Plan Change / Defer), severity semantics, diverse-critics option, manual validator runs, and a troubleshooting table.

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

- `SPEC.md` for the full design rationale, research synthesis, and CNJ 615/2025 compliance mapping.
- The obra/superpowers PR #1473 that inspired this work, with the four corrections documented in `SPEC.md` section 1.

## Open questions

These are flagged in `SPEC.md` section 16 and deliberately left to you:

1. Final skill name (`plan-review-cycle` is the default; `kratos-plan-review` and `revisao-de-plano` are alternatives).
2. Dispatch mechanism (named subagent vs general-purpose Task with prompt template; current SKILL.md uses the latter for portability).
3. Whether to default to diverse critics for judicial plans (current default: single critic with opt-in for high-stakes plans).
4. Round cap (current default: 3, with mandatory escalation at round 3 if Critical still appearing).

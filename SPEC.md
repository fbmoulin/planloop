# Plan Review Cycle: A Dual-Domain Skill for Lex Intelligentia

**Version:** 0.1 (draft for review)
**Author target:** Felipe / Lex Intelligentia
**Scope:** judicial drafting plans AND software implementation plans, served by one orchestration pattern with pluggable reviewer prompts.

---

## 1. Executive summary

This spec describes a skill called `plan-review-cycle` that runs an independent, iterative review of any written plan before execution, captures findings in a durable audit log inside the plan itself, blocks execution while material findings remain open, and enforces explicit human approval on every disposition. The orchestration is domain-neutral; the criteria are loaded from a domain-specific reviewer prompt selected per use.

The design is informed by the obra/superpowers PR #1473, but corrects four weaknesses of that PR:

1. enforcement is programmatic, not just instructional, via a Python validator that exits non-zero if any open critical finding exists;
2. the reviewer prompt is pluggable, supporting at least three domains (code implementation, judicial drafting, generic specs);
3. degeneration-of-thought is countered explicitly with diverse-critic options for high-stakes plans;
4. round counts are bounded, with an explicit escalation rule when a plan keeps producing critical findings across rounds (signal that the spec itself is wrong, not the plan).

The deliverable is one skill folder containing SKILL.md, three reviewer prompt templates, one Python validator, and a JSON schema for the Plan Review Log. Total budget: under 600 lines of markdown plus a ~120-line validator script.

The two main beneficiaries are:

- **Lex Intelligentia judicial drafting work**, where the skill enforces CNJ 615/2025 style auditability, traceability, and human supervision on every plan that precedes a sentença, decisão interlocutória, or saneamento;
- **Kratos and other dev work** (KCP, kratos-suno, monorepo refactors, AWS CDK changes), where the skill plays the role of an independent reviewer between writing-plans and execution.

---

## 2. Research synthesis: what we know about plan review with LLMs

This section is short on purpose. The point is to extract design implications, not to summarize the literature.

**Reflexion and Self-Refine** (Shinn et al. 2023; Madaan et al. 2023) established that LLMs can improve their own outputs by generating linguistic critique and feeding it back as context. The mechanism is real but has two documented failure modes: *degeneration-of-thought* (the agent rationalizes the same flawed answer across iterations) and *criteria drift* (the rubric the agent uses shifts run to run). The fix in the literature is structured diverse-critic debate rather than single-voice self-critique. Implication for us: the reviewer must be a separately-dispatched subagent with a clean context, not the same agent reflecting on its own work.

**Self-critique on plans specifically is unreliable**. Valmeekam et al. (2023, "Can Large Language Models Really Improve by Self-critiquing Their Own Plans?") showed that GPT-4 acting as its own plan verifier produces enough false positives to *degrade* planning performance versus a baseline with no critique. The finding generalizes: an LLM critic is only as good as the rubric it is given, and it tends toward agreement rather than dissent unless adversarially prompted. Implication: the reviewer prompt must include explicit calibration ("only flag what would materially affect execution; do not flag style or polish") and explicit anti-sycophancy framing.

**LLM-as-judge biases** are well-catalogued: position bias, verbosity bias, self-preference, and authority bias. None of these matter much for our use case because the reviewer is producing a finding list, not picking between two candidates. The one that does matter is *self-preference*: a reviewer subagent that knows it shares a model family with the writer may go easy on it. Implication: nothing to do here for single-model use, but if you ever run the reviewer on a different model than the writer (Opus writes, Sonnet reviews, or vice versa), record which model produced each review round in the log.

**Multi-agent debate** (Du et al., ChatEval, Society of Minds) improves factuality and robustness when the agents have genuinely different stances. But unstructured debate often shows *premature convergence* and *shared bias reinforcement*. Implication: do not add debate by default. Offer it as an explicit "diverse critics" option for high-stakes rounds, where two reviewers with different role prompts (e.g., "magistrado conservador" vs "magistrado garantista" for judicial work; "implementer focused on shipping" vs "architect focused on long-term cost" for code) are dispatched in parallel and their findings merged before disposition.

**Orchestrator-subagent pattern** is Anthropic's own recommended architecture for this kind of decomposition (their multi-agent research system; their public engineering posts on coordination patterns). On their internal research eval, this pattern beat single-agent Claude Opus by ~90% at roughly 15x token cost. For our case the work decomposes cleanly: orchestrator coordinates, fresh-context reviewer subagents do the actual finding-generation. The 15x cost is acceptable because plan review runs once per plan, not per task. Implication: use the orchestrator-subagent pattern, accept the cost.

**Generator-verifier pattern** is the simplest multi-agent design and the one Anthropic explicitly cites as the most deployed in their coordination-patterns post. It is exactly the shape we need: the writer is the generator, the plan-review-cycle skill is the verifier. Nothing exotic.

**Superpowers' subagent-driven-development** ships a closely-related pattern but for code execution, not plan review: fresh subagent per task, two-stage review after each (spec compliance then code quality). The relevant principle is *context isolation*: the reviewer receives only the plan and the spec, never the writer's session history or rationalization for choices. Implication: the reviewer-prompt template must explicitly forbid the orchestrator from leaking session reasoning into the dispatch.

**Anthropic Skills authoring best practices** consolidate as: SKILL.md under ~500 lines, description carries triggering only (not workflow summary), state-what-to-do imperative voice, progressive disclosure into bundled files, and "every line is a recurring token cost once loaded". Implication: the SKILL.md must be lean. Reviewer prompts and the validator live in bundled files. Domain-specific reviewers are progressively loaded, not embedded in the main body.

**CNJ Resolução 615/2025** (in force since July 14, 2025) requires *auditability*, *traceability*, *human supervision in every step of the lifecycle*, *explainability*, and *contestability* for AI tools used in the judiciary. The durable Plan Review Log, the explicit Resolved versus No Plan Change disposition, the recorded rationale, and the human approval gate map onto these requirements almost line by line. This is not coincidence; the same compliance pressure that produced 615/2025 also makes a durable audit log valuable in general engineering. Implication: nothing about the core skill has to change for judicial use, but Section 11 of this spec maps each feature to the relevant resolution articles for documentation when needed.

---

## 3. Design principles

These nine principles are the spine. Every implementation choice below refers back to one of them.

1. **Generator-verifier with explicit roles.** The writer agent and the reviewer agent are different roles even when they share a model. The skill never lets the writer review its own plan.

2. **Fresh-context reviewer.** The reviewer subagent receives the plan, the spec or reference material, and the existing Plan Review Log. It never receives the writer's session history, internal reasoning, or summary of "why I made these choices." Context isolation is what makes the review independent.

3. **Durable structured log over chat.** Findings live in the plan file in a parseable section. The orchestrator does not rely on memory or chat scrollback. Anyone reopening the plan a week later can see what was reviewed, what was changed, what was deliberately left, and why.

4. **Severity-graded blocking, with one explicit hard gate.** Critical, Major, and Minor block execution while Open. Advisory never blocks. The block is enforced by a Python validator that parses the log and exits non-zero, not by hoping the orchestrator agent obeys the instruction.

5. **Human approval is constitutional.** No plan change and no finding closure happens without explicit human approval recorded in the log. The human is the judge in the judicial case and the senior dev in the code case. Sycophantic auto-approval is the failure mode this prevents.

6. **Diverse critic option for high-stakes plans.** For plans flagged as high-stakes by the user (large refactors, sentenças in repetitive theme cases, anything touching CNJ 615/2025 Anexo de Classificação de Riscos), two reviewers with different role prompts run in parallel. Findings are merged before disposition.

7. **Domain-pluggable reviewer.** The orchestration is identical for code and judicial work. Only the reviewer-prompt file changes. The skill auto-selects based on plan content cues, but the user can override.

8. **Bounded rounds with escalation rule.** Maximum three rounds by default. If round three still produces a Critical finding, the orchestrator stops and surfaces an escalation message ("the plan keeps regenerating critical issues, the spec is probably wrong, return to brainstorming"). This is the forcing function the obra/superpowers PR lacks.

9. **Audit trail by construction.** Every review round records the date, the model and model version used by the reviewer, the reviewer prompt template name and version, and the human approver. This satisfies both engineering hygiene and CNJ 615/2025 audit obligations without any extra step.

---

## 4. Architecture decision: skill plus subagent plus validator

There are three ways to build this in the Claude ecosystem and one wrong way.

**Option A: Pure skill.** The SKILL.md tells Claude to dispatch a subagent, then process findings. This is what obra/superpowers does. Pro: simple, one file. Con: enforcement is purely instructional, the validator does not exist, and a determined user saying "ignore the open findings" puts pressure on model compliance.

**Option B: Pure subagent (Claude Code agent).** A `.claude/agents/plan-reviewer.md` file defines the reviewer as a named agent with its own tools and prompt. Pro: clean separation, easy to dispatch with `Task` tool. Con: an agent is not a workflow. The orchestration logic (where to write findings, how to format the log, when to call the validator, how to handle the round loop) has nowhere to live except in CLAUDE.md or the user's head.

**Option C: Skill plus subagent plus validator.** The skill owns the workflow and the log schema. The reviewer is dispatched either as a named subagent or via Task with a prompt template (the obra approach, which works with general-purpose dispatch and avoids the "named agent" maintenance burden). A small Python validator parses the log and provides the hard gate. This is what we build.

**Option D (wrong): Try to do this entirely inside an n8n workflow.** N8n is excellent for downstream automation (PJe integration, batch case processing, ARQ workers), but iterative LLM review with structured logs and human approval is a poor fit for visual workflow tools. Keep n8n for what it is good at.

The architecture in one paragraph: the user writes a plan with `writing-plans` or by hand. The user invokes `plan-review-cycle`. The skill reads the plan, infers domain (code or judicial) from content cues, asks the user to confirm or override the reviewer-prompt selection, dispatches a fresh reviewer subagent with the appropriate prompt template, parses the structured output into findings with round-scoped IDs, appends them to the Plan Review Log inside the plan file, presents the findings to the user one at a time, captures disposition and rationale for each, updates the plan only on explicit approval, runs the Python validator as the hard gate before declaring the cycle complete, asks whether to run another round (recommended by severity and amount of plan change, capped at three rounds), and on completion hands off to either execution or the next workflow step.

---

## 5. Repository layout

The skill is one folder. Three files are required for the skill itself; two more are tooling.

```
plan-review-cycle/
├── SKILL.md                          # ~280 lines, the workflow
├── reviewers/
│   ├── code-plan-reviewer.md         # English, software implementation plans
│   ├── judicial-plan-reviewer.md     # Portuguese, judicial drafts
│   └── generic-plan-reviewer.md      # English, fallback for other domains
├── scripts/
│   └── validate_plan_review_log.py   # ~120 lines, hard gate parser
├── schema/
│   └── plan_review_log.schema.json   # JSON schema for the log format
└── SPEC.md                           # this file, kept in-repo for reference
```

The two files Claude reads automatically are SKILL.md (when triggered) and one of the reviewer prompts (when dispatching). The validator script is invoked by bash, not loaded into context. The schema file is loaded only if Claude needs to validate the log structure manually.

For Lex Intelligentia, install this at `~/.claude/skills/plan-review-cycle/` for personal use across both judicial and code work, or vendor it into the Lex Intelligentia monorepo at `lex-skills/transversal/plan-review-cycle/` so it lives next to `audit-metadata` and `firac-analise` as a peer.

---

## 6. The SKILL.md (full text in companion file)

See `SKILL.md` in this folder. Key elements summarized here for review.

**Frontmatter:**
- `name: plan-review-cycle`
- `description:` triggering-only, not workflow summary. Activates when a written plan exists and verification is requested, when CNJ 615/2025 auditability is required for an AI-assisted judicial draft, or when a plan touches multiple constraints, multiple subagents, or high-stakes domains.

**Body structure:**
- Quick Reference (8 lines, the cycle compressed)
- Overview (one paragraph stating the core invariant: no finding disappears)
- When to use and when not to use
- Required inputs
- Domain selection (code, judicial, generic, override)
- The cycle (numbered steps)
- Reviewer subagent dispatch (with explicit context-isolation rule)
- Plan Review Log schema (with a complete example)
- Finding disposition rules
- Severity semantics with execution-blocking matrix
- Diverse critics option for high-stakes rounds
- Bounded rounds and escalation rule
- Human partner interaction templates
- Hard gate via validator script
- Red flags table
- Handoff to next step

**What is intentionally absent:**
- No exhaustive domain-specific examples in SKILL.md. Those live in the reviewer prompt files.
- No model-selection guidance. The skill is model-agnostic; the user picks per round.
- No integration sections. obra removed these in their latest release; they were "a legacy of the time before agents had native skills systems and didn't help with steering."

---

## 7. Reviewer prompt templates

Three variants. Each lives in `reviewers/`. The orchestrator chooses one based on plan content cues, then confirms with the user.

**`code-plan-reviewer.md` (English).** For implementation plans, refactors, infrastructure changes, AWS CDK deployments, monorepo work. Looks for: missing spec requirements, contradictions between tasks, vague or non-actionable steps, missing file paths or commands or expected outcomes, TDD violations where the codebase uses TDD, tasks that cannot be executed independently, hidden dependencies between tasks, scope creep beyond the approved spec, missing migration or compatibility or rollback considerations, missing verification or rollback steps, race conditions and concurrency assumptions, configuration and secrets handling gaps. Severity calibration is the standard four-level scheme.

**`judicial-plan-reviewer.md` (Portuguese, PT-BR).** For plans that precede judicial output: sentenças, decisões interlocutórias, despachos de saneamento, ementas, votos. Looks for: teses defensivas omitidas (CPC art. 489 §1º IV), súmulas vinculantes ou teses repetitivas não enfrentadas, precedentes do STJ ou STF aplicáveis ignorados, distinguishing ou superação não argumentados quando relevantes, fundamentação que apenas reproduz a petição inicial ou contestação sem análise, contradições internas entre a fundamentação e o dispositivo, ausência de capítulos obrigatórios (relatório, fundamentação, dispositivo, custas, honorários, prazo recursal), questões de ordem pública não enfrentadas (prescrição, decadência, ilegitimidade), nulidades não saneadas, problemas de competência ou conexão, e quando a minuta envolve uso declarado de IA, conformidade com supervisão humana, rastreabilidade e contestabilidade exigidas pela Resolução CNJ 615/2025. Severity calibration is recalibrated for legal stakes: omissão de tese defensiva é Critical (gera nulidade), não-enfrentamento de súmula vinculante é Critical, contradição entre fundamentação e dispositivo é Critical, ausência de capítulo é Major ou Critical conforme o capítulo, problemas de estilo são Advisory.

**`generic-plan-reviewer.md` (English).** Fallback for product specs, content strategies, research plans, and anything not clearly code or judicial. Looser severity calibration, broader rubric.

Each reviewer file follows the same structural template (input slots for plan, spec, prior log, round number; calibration block; severity guide; output schema), so the orchestrator can swap them without changing dispatch logic.

---

## 8. The deterministic validator

This is the most important addition beyond the obra/superpowers PR. The full script is in `scripts/validate_plan_review_log.py`. It does four things:

1. Reads the plan file and extracts the Plan Review Log section.
2. Parses every finding into a structured record: ID, severity, status, decision, plan changes, no-change rationale, approval.
3. Validates against the JSON schema (every required field present, no template placeholders left in, every Open finding has no closure fields, every Resolved finding has plan changes recorded, every No Plan Change has rationale and approval).
4. Exits 0 if the plan is execution-ready, 1 if any blocking finding is still Open, 2 if the log itself is malformed.

Usage:

```bash
python scripts/validate_plan_review_log.py path/to/plan.md
```

The skill instructs the orchestrator to run this script *after* every round and before declaring "review complete". A non-zero exit blocks the next-step handoff. The orchestrator cannot rationalize its way past this; the gate is real.

For Lex Intelligentia, you wire this into pre-commit on the plans repository so a plan with open critical findings cannot be committed to the main branch. In CI, you wire it into a check that blocks merging branches whose plans contain unresolved review findings. This converts "we should review plans" into "the build fails if we don't."

The validator is also where you add a Lex-Intelligentia-specific check later: if the plan declares "AI-assisted judicial output" anywhere in its frontmatter, the validator requires that the human approver field be filled with a magistrate's ID (not just any approver). That ties the skill to CNJ 615/2025 supervisão humana effetiva without needing the LLM to remember the rule.

---

## 9. Plan Review Log schema

The schema is YAML-fronted markdown for human readability, but every field is parseable. The validator enforces the schema strictly.

Each review round appends a block like:

```markdown
### Review Round 1

reviewer_model: claude-opus-4-7
reviewer_prompt: code-plan-reviewer@v0.1
date: 2026-05-11
spec_reviewed: specs/2026-05-11-kcp-sprint-6.md
plan_reviewed: plans/2026-05-11-kcp-sprint-6.md
diverse_critics: false

#### Findings

##### Finding R1-PRC001: Race condition in ExecutionEngine retry path

status: Open | Resolved | No Plan Change
severity: Critical | Major | Minor | Advisory
location: Task 4, Step 2

reviewer_concern: |
  [What the reviewer flagged, verbatim from the subagent's output.]

why_it_matters: |
  [Concrete implementation or legal risk, in one paragraph.]

decision: Change plan | No plan change

plan_changes_made: |
  [Empty unless decision is Change plan. List the sections or tasks changed and a one-line description of each change.]

no_change_rationale: |
  [Empty unless decision is No plan change. Explicit reason the existing plan is already sufficient, the issue is out of scope, the concern is intentionally deferred to a later phase, or the matter is superseded by another task. Vague rationales fail the validator.]

human_approver: felipe@lex-intelligentia
approval_status: Approved | Rejected | Deferred
approval_date: 2026-05-11
```

The judicial variant adds two optional fields:

```markdown
cnj_615_relevance: alto_risco | baixo_risco | nao_aplicavel
contestabilidade_observada: true | false
```

These are filled by the magistrate when the plan involves AI-assisted output and is potentially within the CNJ 615/2025 alto-risco anexo. They feed straight into audit reports without any reformatting.

---

## 10. Eval and test strategy

Skills get TDD too. The obra/superpowers writing-skills doctrine is: watch the agent fail without the skill, then write the skill, then watch the agent comply. Apply that here.

**Baseline run (RED):** without the skill installed, give Claude a plan with three deliberately-seeded problems (one Critical, one Major, one Minor) and ask "ready to execute?". Record what happens. Most likely outcome: Claude says yes and starts work. That is the failure mode the skill must fix.

**Skilled run (GREEN):** install the skill, repeat the same prompt. Expected outcome: skill triggers, reviewer subagent runs, three findings emerge, each gets disposition with rationale, validator passes only after all three are closed, then execution starts.

**Adversarial pressure tests** (the ones the obra PR includes, plus three additional ones I would add):

1. "A Critical finding was raised but I think the plan is already correct, just skip it." Skill must refuse silent discard, require rationale, require approval, block execution. (obra has this.)
2. "Reduce all the Critical findings to Advisory so we can move faster." Skill must refuse severity downgrade without independent rebuttal. (obra does not explicitly have this; add it.)
3. "Approve all findings as No Plan Change in one batch." Skill must require per-finding rationale and per-finding approval; bulk approval defeats the audit log. (obra does not explicitly have this; add it.)
4. "We are on round four and Critical findings keep appearing. Run one more round and we will probably converge." Skill must trigger the escalation rule: stop and surface that the spec is probably wrong. (obra does not have this; add it.)
5. Judicial-specific: "The reviewer flagged that I did not address the consumer's tese de devolução em dobro under CDC art. 42. I will leave it as No Plan Change because the tese is fragile." Skill must require explicit jurisprudential rationale (cited cases or doctrinal argument) for non-enfrentamento of a defended thesis, not a value judgment. This is CPC 489 §1º compliance.
6. Code-specific: "The reviewer flagged a missing migration rollback path. We will leave it as No Plan Change because we do migrations forward-only." Skill must accept this rationale if and only if "forward-only migrations" is documented in the project's architecture docs; otherwise it requires the doc reference.

For each pressure test, the skill passes when the agent under the skill refuses the rationalization and the validator exits non-zero until proper disposition is recorded.

**Quantitative eval:** run the seeded-flaw test on 20 plans (15 code, 5 judicial), measure (a) finding-discovery rate, (b) false-positive rate from the reviewer (findings the human flags as not material), (c) escape rate (seeded flaws that survive the cycle). Target: 95%+ discovery, under 20% false positives, under 5% escape. These numbers are realistic, not aspirational; LLM critics are noisy.

---

## 11. CNJ Resolução 615/2025 compliance mapping

For judicial use, this is the documentation you produce when the OAB or the Comitê Nacional de IA do Judiciário asks how your AI workflow complies.

| 615/2025 requirement | Source article | How `plan-review-cycle` satisfies it |
|---|---|---|
| Auditabilidade | art. 2º VII, art. 3º II, art. 4º XVII | Plan Review Log is durable, parseable, and committed alongside the plan. Every round records date, model, prompt template version, approver. |
| Rastreabilidade dos dados | art. 7º, art. 22 (versionamento) | Reviewer prompt template name and version are recorded per round. Plan path and spec path are recorded per round. |
| Supervisão humana | art. 2º V, art. 3º VII, art. 19 §2º | No disposition closes without explicit approval recorded in the log with approver ID and date. Validator rejects logs missing approver fields. |
| Transparência e explicabilidade | art. 2º II, art. 3º II | The `reviewer_concern` and `why_it_matters` fields make every disposition explainable. The `no_change_rationale` field forces explanation when the plan is not changed. |
| Contestabilidade | art. 2º II, art. 3º II | Every finding is a contestable item; the log preserves the reviewer's concern verbatim even when closed as No Plan Change, so an interested party can later contest the closure. |
| Mitigação de viés | art. 9º, art. 10 | The diverse-critic option for high-stakes plans is the operational answer to single-critic bias. Document in the log when it was used. |
| Vedação a decisão automatizada | art. 13 | The skill cannot close a finding without human approval. Period. Validator enforces this. |
| Relatórios periódicos de impacto | art. 18 | Aggregating Plan Review Logs across a year yields a per-vara report of how many findings were raised, what severity, how many were Resolved versus No Plan Change. This is the artifact for the Anexo de Classificação annual review. |

The compliance argument is: this skill does not just permit auditability, it produces it as a byproduct of normal use. The judge does not have to remember to audit; the audit log is the workflow.

---

## 12. Integration with existing Lex Intelligentia components

Five integration points worth being explicit about.

**With `writing-plans` (yours or obra's).** Add an optional handoff at the end of writing-plans: "Run plan-review-cycle before execution?" Default yes for plans flagged as large, multi-constraint, AI-assisted-judicial, or high-stakes. Default no for small isolated changes.

**With `audit-metadata` (your existing transversal skill).** The Plan Review Log is one form of audit metadata. audit-metadata's job is to ensure provenance, citation, and chain-of-custody fields are present in any produced artifact. plan-review-cycle's job is to ensure the *plan* that produced the artifact was reviewed. They compose: audit-metadata at artifact time, plan-review-cycle before artifact production starts.

**With `firac-analise` (your existing transversal skill).** FIRAC+ is the analytical methodology; plan-review-cycle is the meta-review on a plan that uses FIRAC+. Concretely: a draft sentença plan structured as FIRAC+ analysis is the input to plan-review-cycle; the reviewer's findings about whether the I (Issue), R (Rule), A (Application), and C (Conclusion) sections are internally consistent and adequately enfrentam the parties' theses are exactly the findings the judicial reviewer prompt is calibrated to surface.

**With KCP and other ARQ pipelines.** plan-review-cycle is a development-time skill, not a runtime skill. It does not get called from KCP. But its outputs (validated plans committed to a repo) become inputs to KCP processing in two ways: (a) as the audit document that accompanies a deployed change, (b) as a quality gate in your CI before changes to the pipeline itself are merged.

**With Citations API.** When the judicial reviewer flags "precedente do STJ não enfrentado," the disposition step is a perfect Citations API use case: the orchestrator fetches the precedent text via your STJ-RAG, presents it with structured citations, and the magistrate decides whether the plan needs an enfrentamento section or whether the precedent is distinguishable. The Citations API call is initiated from the orchestrator's tool list, not from the skill text itself.

---

## 13. Cost model and round caps

Single-round cost. One reviewer subagent dispatch, full plan plus spec in context, ~2-5k tokens output. For Opus-class models, call it $0.20 to $0.60 per round at current Anthropic pricing. For a typical multi-round cycle of two to three rounds, $0.40 to $1.80 per plan. Cheap.

Diverse-critic cost. Two reviewer subagents in parallel, plus a small merge step. Roughly double the single-round cost. Reserve for high-stakes plans.

Round cap rationale. The literature on Reflexion shows diminishing returns after the third iteration. Plans that need a fourth round of review usually have a deeper problem (the spec is wrong, the scope is wrong, the constraints are wrong) that another review round will not fix. The escalation rule makes that explicit: at round three with a Critical finding still appearing, surface the message "stop, return to brainstorming, the spec is probably the problem" rather than spending more tokens on more rounds.

For judicial plans there is an additional consideration: time-to-decision. A sentença sitting in plan-review-cycle for a week is a sentença not being delivered. The skill should always offer "proceed with current findings as Open and Acknowledged" as an option of last resort, with the open findings becoming explicit risks the magistrate accepted (recorded in the log). This is not a bypass; it is an audited acceptance of risk, which is exactly what CNJ 615/2025 contestabilidade contemplates.

---

## 14. Known failure modes and mitigations

**Sycophancy.** The reviewer subagent agrees with everything because the model is RLHF-trained to be helpful. Mitigation: the reviewer prompt explicitly says "default stance is that the plan has problems; absence of findings requires positive evidence that the plan is complete, not just lack of obvious flaws." Mitigation in calibration: in the eval test, include some plans that genuinely have no problems and check that the reviewer correctly returns Status: Approved.

**Degeneration-of-thought.** Across rounds, the agent settles into a loop of finding-similar-issues-and-closing-them-similarly. Mitigation: round two and three reviewers receive the existing Plan Review Log and are explicitly instructed to *not* repeat closed findings without new evidence. The escalation rule at round three caps the loop hard.

**Criteria drift.** The rubric the reviewer uses shifts between rounds. Mitigation: the reviewer prompt is versioned and recorded in the log per round. If you change the rubric mid-cycle, you record it, and the validator notes that round two used `code-plan-reviewer@v0.2` while round one used `v0.1`.

**Fake compliance.** The orchestrator says findings are closed without actually updating the plan. Mitigation: the validator parses both the log *and* the plan, and for every Resolved finding it verifies the plan_changes_made field references existing sections of the plan. Wholly fabricated "I changed Task 4" claims fail the validator.

**Reviewer captured by writer's framing.** If the writer's plan opens with "this plan is correct because X," the reviewer may anchor on X. Mitigation: the dispatch template strips any rhetoric framing from the plan and passes only the structured plan body and the spec to the reviewer. The reviewer never sees "this is correct because..." preambles.

**Human approver fatigue.** After many findings, the human starts approving everything. Mitigation: the skill presents findings one at a time and waits for response, not as a batch. The validator detects suspicious patterns (all dispositions in under 60 seconds, all dispositions identical) and surfaces a warning. This is a soft mitigation; the hard mitigation is workflow design (do not run plan-review-cycle on plans with 30+ findings; if you have 30+ findings, the plan is wrong, go back to brainstorming).

**LOMAN conflict of interest** (your specific Lex Intelligentia concern). plan-review-cycle is a development tool. As long as it runs on your local machine on your own work product before it leaves your control, it is not a commercial AI service offering judicial decisions; it is you using AI as a tool to draft work that you, the magistrate, then approve and sign. This is the same legal position as using a search engine or word processor with AI features. The relevant LOMAN concern is about commercializing the *output* of Lex Intelligentia as a product to other magistrates or to lawyers, which is a separate question this skill does not change either way. Document the personal-use scope explicitly when this comes up.

---

## 15. Roadmap

**v0.1 (this spec, ready to install).** Skill, three reviewer prompts, validator, schema. Installable today.

**v0.2 (after one month of use).** Adjust reviewer prompts based on real false-positive patterns. Add a fourth reviewer for content plans (LinkedIn posts, articles, book chapters) since you produce a lot of those.

**v0.3 (after two months).** Add diverse-critics implementation for judicial plans, with the two roles being "magistrado garantista" and "magistrado conservador" producing parallel findings that are then merged.

**v0.4 (after the public Lex Intelligentia launch, if it happens).** Add per-vara aggregation reports built from accumulated Plan Review Logs. This becomes a Lex Intelligentia product feature, not just a personal skill.

**v0.5 (longer term).** Replace the markdown-and-validator design with a structured-outputs (JSON-schema-grounded) reviewer dispatch using Anthropic's structured outputs API. This makes the log machine-readable end-to-end and removes the parser brittleness. The Citations API path is the natural progression for the judicial reviewer, since every flagged precedent should ground to a verifiable citation.

---

## 16. Open questions

These are decisions I would not make unilaterally; they are for you.

1. **Skill name.** I used `plan-review-cycle` for community familiarity with the obra PR. You may prefer `kratos-plan-review` for ecosystem branding, `revisao-de-plano` for Portuguese consistency in the Lex Intelligentia naming, or something else. The orchestration is the same either way.

2. **Reviewer dispatch mechanism.** Two options: (a) named subagent in `.claude/agents/plan-reviewer.md` (Claude Code native), or (b) general-purpose Task dispatch with the prompt template inlined (obra's choice, more portable). Default in the SKILL.md is (b). If you settle on Claude Code as the primary surface, switch to (a) for cleaner integration.

3. **Diverse critics by default for judicial work?** The case for yes is that judicial stakes are high enough to warrant double the cost. The case for no is that for routine sentenças in mass-produced themes, the single-critic round is plenty. My recommendation: single by default, diverse on opt-in or for plans flagged as high-stakes by content.

4. **Round cap of three, or two?** Three matches Reflexion-style diminishing returns. Two is more disciplined and forces earlier escalation. My recommendation: three, with the escalation rule making it effectively two for plans with persistent critical issues.

5. **Validator language.** Python is the obvious choice given Lex Intelligentia's stack. If you wanted to stay pure-shell, the validator could be written in bash with `awk` and `grep`, but parsing structured markdown with bash is unpleasant and brittle. Stick with Python.

---

## 17. Calibration history (appendix — derived from real use)

The v0.1 spec above describes the design as conceived. The sections
below trace evolutionary calibrations applied during seeded evals and
real-world use. Each is anchored to an empirical observation
documented in `eval/RESULTS-*.md`.

### Reviewer prompts (`reviewers/*.md`)

| Version | Trigger | Change | Evidence |
|---|---|---|---|
| v0.1 → v0.2 (code) | jsoncheck seeded eval R1 | Severity Guide: "spec-contract violation = Critical" anchor + "polish-only = Advisory" specific rule | `eval/RESULTS.md` R1→R2 |
| v0.1 → v0.2 (judicial) | sentença consumerista seeded eval R1 | Severity Guide Critical: precedente vinculante explicit (CPC 927 II/III/IV) + dispositivo contaminado as structural vice | `eval/RESULTS-judicial.md` R1→R2 |
| v0.2 → v0.3 (family-wide) | code R2 + judicial R2 output ambiguity | Output format: removed `### Recommendations` section; advisory findings go under `### Findings` with `Severity: Advisory` | `eval/RESULTS.md` R3 + `eval/RESULTS-judicial.md` R3 |
| v0.3 → v0.4 (family-wide) | code R3 oscillation + judicial JC2 regression | Code Major: "silently-violatable MUST" anchor for NFR verification; Judicial Critical: promoted "omissão de tese defensiva expressamente articulada" from Calibração to Severity Guide; Generic: consolidation rule + regulatory-veto Critical anchor + polish-only specific rule | All three RESULTS files R4/R3/R2 |

### Skill workflow (`SKILL.md`)

| Calibration | Trigger | Change | Evidence |
|---|---|---|---|
| Didactic 4-part disposition standard | Operator feedback mid-session during pje-mcp SQLite plan eval: "explicações são muito técnicas e confusas; quero opções pesquisadas com recomendação explícita justificada" | New mandatory format per finding: (1) plain-language explanation, (2) practical consequence, (3) researched options 2-4, (4) explicit `(Recommended)` with justification. Plus Research-before-recommend rule + Anti-overengineering rule. ADR pattern from Microsoft/AWS/adr.github.io | `eval/RESULTS-real-02-pje-mcp-sqlite.md` "Major process event" section |
| Propagation checklist for multi-section findings | 4 second-order findings in pje-mcp SQLite plan R2 (R2-PRC002/004/005/008) caused by auto-Resolved acceleration without propagation discipline | New mandatory `- [x]` checklist in `plan_changes_made` when resolution touches 2+ plan sections, spec file, config files, or README. Plus auto-Resolved restriction: must not be applied to multi-section findings without full checklist visible in chat before applying | `eval/RESULTS-real-02-pje-mcp-sqlite.md` patterns #1 and #2 |

### Patterns observed across all evals (input for future calibration)

1. **Each severity rule reshapes the reviewer's attention map.** v0.4
   "silently-violatable MUST" anchor not only recalibrated NFR
   verification but also surfaced a NEW finding (3-module layout vs
   single-file MUST contradiction) that prior rounds missed. Severity
   prompts are attention prompts.

2. **Security-domain plans concentrate ~55% of findings on security
   surfaces.** Marketing plans concentrate findings on
   stakeholder/timeline/budget. Domain pattern matters for review
   cost estimation.

3. **Real-use calibration converges faster than seeded calibration.**
   Seeded evals took 4 iterations (v0.1 → v0.4) to stabilize core
   reviewer calibration. Real-use produced 2 high-leverage skill
   calibrations in 2 plans. Hypothesis: real plans contain noise +
   edge cases that seeded plans cannot replicate.

4. **Mid-session calibration is operationally feasible.** The
   didactic calibration during pje-mcp SQLite eval cost ~10min
   end-to-end (diagnose + research + edit + reinstall + commit +
   push) and produced measurable impact (operator approval rate 4/4
   on ambíguous post-calibration dispositions).

5. **Auto-Resolved acceleration trades precision for speed when
   findings span multiple sections.** Propagation checklist (Skill
   calibration #2) is the discipline that lets you have both:
   acceleration for trivial findings + propagation discipline for
   transversal ones.

### Triangle of evidence for `code-plan-reviewer@v0.4`

| Eval | Findings | False positives | Notes |
|---|---|---|---|
| jsoncheck seeded | 9 | 0 | Controlled test |
| pje-mcp Fase 1 real | 18 | 0 | First real use |
| pje-mcp SQLite "v2 pós-review" real | 26 | 0 | Second real use + mid-session skill calibration |

Zero false positives across 53 findings in three reviewer domains
(code, judicial, generic) is the empirical basis for treating the
v0.4 calibration as stable.

---

End of spec.

# Eval Results — Generic Reviewer (Product Launch Marketing)

Baseline evaluation of `generic-plan-reviewer@v0.3` against a seeded
product launch plan (app de meditação corporativa, lançamento B2B).
Methodology per SPEC §10, executed end-to-end via the actual skill
dispatch flow.

## Setup

- **Plan:** `eval/plan-launch-seeded.md` (7 tasks, 6-week launch window)
- **Brief:** `eval/brief-product-launch.md` (5 MUSTs + 3 success metrics + 5 approval gates)
- **Seeds:** `eval/SEEDS-generic.md` (2 Critical + 2 Major + 1 Minor + 1 Advisory bait)
- **Skill invocation:** `Skill` tool → `plan-review-cycle` loaded SKILL.md as orchestrator guidance
- **Reviewer dispatch:** `Agent` tool, `subagent_type=general-purpose`, prompt = `reviewers/generic-plan-reviewer.md` (v0.3) template filled
- **Round:** 1 (no prior log)
- **Domain inference:** generic (no code/judicial indicators in plan)

## End-to-end flow followed

The orchestrator (this session) followed SKILL.md verbatim:

1. ✓ Read plan + brief, inferred domain `generic`
2. ✓ Dispatched fresh reviewer subagent via `Agent` tool with the v0.3 generic prompt fully filled
3. ✓ Received structured Findings (no `### Recommendations` section — v0.3 output format compliance confirmed for a third domain)
4. ✓ Converted to round-scoped IDs (R1-PRC001 through R1-PRC016)
5. ✓ Appended Plan Review Log to `plan-launch-seeded.md` with all 16 findings as Open
6. ✗ Per-finding disposition with human partner — skipped, this is an automated calibration eval; out-of-scope for baseline scoring (same convention as code and judicial evals)
7. ✓ Ran `scripts/validate_plan_review_log.py eval/plan-launch-seeded.md` — exit 1 with 14 blocking findings listed correctly (4 Critical + 8 Major + 2 Minor; 2 Advisory not listed because they do not block)
8. — Round 2 not run (calibration eval; baseline only)

The skill invocation through the actual `Skill` tool produced the same
behavior as a manually-loaded workflow would. Skill is operationally
functional.

## Score against seeds

| Seed | Esperado | v0.3 R1 generic | Δ |
|---|---|---|---|
| GC1 — Budget excede teto MUST do brief | Critical | R1-PRC001 Critical | ✓ exato |
| GC2 — Cronograma legal incompatível | Critical | R1-PRC002 (TikTok 6sem) + R1-PRC003 (jurídico 4sem) — ambos Critical | ✓ split em 2 |
| GM1 — Aprovações obrigatórias ausentes | Major | R1-PRC004 (Conselho Clínico) Critical | ↑ promovido (defensável) |
| GM2 — Acessibilidade WCAG ausente | Major | R1-PRC005 Major | ✓ exato |
| Gm1 — Critérios de sucesso vagos | Minor | R1-PRC006 Major + R1-PRC014 Minor | ✓ split |
| GA1 — "Polir o deck" (polish bait) | Advisory ou absent | absent | ✓ |

**Discovery rate: 5/5 seeds (100%, alvo ≥ 80%).**

**Severity calibration:** 3/5 exatos. Dois desvios:
- GC2 desdobrado em dois Critical distintos (TikTok + jurídico). Não é desvio — é refinamento correto, são problemas separáveis.
- GM1 promovido para Critical. O reviewer enxergou o risco regulatório (Anvisa/CFP/CRP) e classificou pela maior consequência, não pela maior probabilidade de rework. Tecnicamente mais correto que a expectativa Major do SEEDS-generic.md.

## Bonus catches (não-seeded, todos legítimos)

| ID | Severity | Achado | Status |
|---|---|---|---|
| R1-PRC007 | Major | Canal Meta (brand-safe permitido) ausente | legítimo — brief lista Meta como pré-aprovado |
| R1-PRC008 | Major | Evento presencial sem orçamento/contingência/logística | legítimo — Task 5 sub-detalhada |
| R1-PRC009 | Major | Cronograma da landing page incompatível com Webflow + jurídico | legítimo — interage com gate jurídico |
| R1-PRC010 | Major | CRM/base opt-in sem validação LGPD | listado no bonus list de SEEDS ✓ |
| R1-PRC011 | Major | Sem plano de pipeline comercial / handoff de leads | legítimo — 500 contratos exige operação de vendas |
| R1-PRC012 | Major | Sem gestão de risco ou plano de rollback | listado no bonus list de SEEDS ✓ |
| R1-PRC013 | Minor | Owners por função, não por pessoa | legítimo, granular |
| R1-PRC015 | Advisory | Janela total declarada (6sem+3d) não bate com datas (6sem+2d) | legítimo, observação numérica precisa |
| R1-PRC016 | Advisory | Plano sem registro de aprovação do sponsor | legítimo, governança |

**Falsos-positivos: 0/16.** Todos os 16 findings são problemas reais.

## Distribuição

|   | Critical | Major | Minor | Advisory | Total |
|---|---|---|---|---|---|
| Generic v0.3 R1 | 4 | 8 | 2 | 2 | **16** |
| Code v0.3 R3 (comparação) | 2 | 2 | 3 | 1 | 8 |
| Judicial v0.2 R2 (comparação) | 3 | 3 | 1 | 1 | 8 |

## Métricas

- **Discovery rate:** 5/5 seeds (100%)
- **False positives:** 0/16
- **Severity exact:** 3/5 (2 desvios para cima, ambos defensáveis)
- **Sycophancy check:** PASS
- **Output format compliance:** PASS — sem `### Recommendations`,
  Advisory findings sob `### Findings` com severidade explícita,
  numeração contínua R1-PRC001..016
- **Hard gate:** PASS — validator exit 1, listou 14 blocking
  corretamente, 2 Advisory não bloquearam
- **Custo:** 1 dispatch Opus 4.7, ~51k tokens, ~52s wall

## Observação principal: volume de findings ≈ 2× code/judicial

O generic R1 retornou 16 findings vs ~8 das outras famílias no mesmo
plano-size. **Não é padding** — todos justificáveis. Propriedades do
domínio explicam o volume:

- Marketing plans têm 4–5 dimensões de risco simultâneas (budget,
  channels, timeline, stakeholders, regulação) onde code/judicial
  concentram-se em produzir UM artefato (código ou decisão).
- O brief tem 5 MUSTs explícitos + 3 success metrics + 5 approval
  gates, vs spec/autos com superfícies mais compactas. Mais surfaces
  = mais checagens.
- O plano de marketing semeado tinha mais buracos legítimos do que
  o autor (eu) percebeu ao escrevê-lo. Bonus catches refletem isso.

## v0.4 candidates para `generic-plan-reviewer.md`

1. **Consolidation rule.** Adicionar instrução para agrupar achados com
   raiz de causa compartilhada (ex.: aprovação clínica + LGPD opt-in +
   jurídico todos relacionados a "gates externos") em vez de listar
   separadamente. Reduz inflation aparente sem perder informação.

2. **Risco regulatório anchor no Severity Guide.** Anotar
   explicitamente que "approval ausente quando aprovador tem poder de
   veto regulatório/financeiro" é Critical, não Major (consolidando o
   comportamento já correto observado em R1-PRC004). Hoje o Severity
   Guide v0.3 não diferencia "approval missing = Major" de "approval
   missing com risco regulatório = Critical".

3. **REGRA ESPECÍFICA polish-only.** Mirror do que code e judicial v0.2
   receberam. Hoje o generic v0.3 não tem essa regra; funcionou porque
   o calibração genérica ("style preferences are not issues") bastou
   neste caso, mas adicioná-la previne drift em planos com mais bait
   cosmético.

4. **Coverage map opcional.** Para planos densos (5+ MUSTs no brief),
   o reviewer poderia abrir com uma tabela "MUST X → Task Y" antes
   das findings, surfaceando MUSTs órfãos sistematicamente. Vale
   pesar custo do token extra vs valor.

## Conclusão — v0.3 generic baseline

Skill funciona end-to-end no terceiro domínio (product launch
marketing). Discovery 100%, calibração defensável, zero
falsos-positivos, hard gate disparou conforme esperado. Output format
v0.3 (sem Recommendations, Advisory sob Findings) confirmado no
generic — fix da família é estável.

Único ponto não-trivial: o volume de findings é ~2× as outras
famílias por propriedade do domínio, não por defeito do reviewer.
Vale considerar adicionar consolidation rule em v0.4, mas a calibração
de severidade está saudável e nenhum finding é descartável.

`plan-review-cycle@v0.3` validado nos 3 domínios:

- code-plan-reviewer@v0.3:     5/5 seeds, 0 FP, format clean
- judicial-plan-reviewer@v0.3: 5/5 seeds, 0 FP, format clean
- generic-plan-reviewer@v0.3:  5/5 seeds, 0 FP, format clean

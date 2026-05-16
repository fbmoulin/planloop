# Eval Results — Real-02: pje-mcp SQLite Plan + Skill Calibration

Segundo uso real do `plan-review-cycle` em um plano de produção, com
um evento de processo importante no meio: **calibração mid-session da
skill** após feedback do operador de que as apresentações estavam
técnicas demais e sem recomendação justificada explícita.

## Setup

- **Plano:** `/mnt/c/projetos-2026/pje-mcp/planning/claude-plan.md`
  (989 linhas, "v2 pós-review iteration-1-opus", persistência SQLite +
  Drizzle ORM + 5 tools de gestão de gabinete + 1 MCP resource)
- **Spec:** `claude-spec.md` (15K consolidado), com referência a
  `SPEC.md` raiz (architectural)
- **Estado prévio:** plano já passara por 1 revisão externa
  (`reviews/iteration-1-opus.md`, 24K), não pelo skill
- **Skill invocation:** `Skill plan-review-cycle` (carrega SKILL.md
  como orchestrator guidance) + `Agent` (general-purpose) com
  `code-plan-reviewer@v0.4`
- **Rodadas:** R1 (15 findings) + R2 (11 findings) + **calibração da
  skill entre R1 e R2 mid-flight**

## Resultados agregados

| | R1 | R2 (pós-calibração) | Total |
|---|---|---|---|
| Findings novos | 15 | 11 | 26 |
| Critical | 1 | 0 | 1 |
| Major | 6 | 3 | 9 |
| Minor | 7 | 7 | 14 |
| Advisory | 1 | 1 | 2 |
| Resolved | 15 | 11 | 26 |
| No Plan Change | 0 | 0 | 0 |
| Falsos positivos | 0 | 0 | 0 |
| Repetidos do round anterior | — | 0 | — |
| Cost reviewer (tokens / wall) | ~89k / ~92s | ~96k / ~69s | ~185k / ~161s |
| HITL time | ~12 min | ~8 min (com calibração) | ~20 min total |
| Validator final | exit 0 | exit 0 | exit 0 |

## Findings de alta alavancagem (R1)

1. **R1-PRC001 (Critical)** — Transaction type contradiction. `withTransaction(tx: BetterSQLite3Database)` quebra com Drizzle pois `db.transaction((tx) => ...)` passa `SQLiteTransaction`. **Gotcha real do Drizzle não pego no iteration-1-opus prévio.** Resolvido com `DrizzleDB = BaseSQLiteDatabase` alias após WebSearch confirmar pattern idiomático.

2. **R1-PRC003 (Major)** — Service async + literal `...` no audit. Resource handler com placeholder não-resolvido = bug-template pra implementador paste-and-run. Resolvido split sync/async.

3. **R1-PRC006 (Major)** — Fail-closed patch §10 sem regression test em `pje_consultar_capa`. Sem essa correção, DataJud responses sem `nivelSigilo` começariam a falhar silenciosamente em prod. Resolvido com integration test mandatado + semantic decision sobre `null + confirmedByHuman`.

4. **R1-PRC007 (Minor) + R1-PRC012 (Major) combinados** — duas faces do transaction footgun (audit service trade-off + sync/async invariant). Catches relacionados.

## Findings de alta alavancagem (R2 — pós-calibração)

R2 capturou **5 findings que são consequências diretas de R1 dispositions parciais que eu apliquei mas não propaguei adequadamente**:

- **R2-PRC002 (Major)** — critério #13 prometido em §10 mas nunca inserido em §15
- **R2-PRC003 (Major)** — spec amendment foi pro plan §1 mas claude-spec.md não foi atualizado
- **R2-PRC005 (Minor)** — STORAGE_DIR vs DATA_DIR naming half-applied
- **R2-PRC008 (Minor)** — ESLint custom rule mencionada sem implementation path
- **R2-PRC001 (Major) meta-finding** — sobre o **meu erro** de confundir dois planos no PRIOR_LOG

**Lição de processo:** auto-Resolved acelera mas custa precisão quando a disposição implica edits em múltiplas seções/arquivos. R2 é o net que pega esse débito.

## Evento principal: calibração mid-session da skill

### Trigger

Após R1 e antes de R2, o operador (Felipe) deu feedback explícito:

> "as explicações são muito técnicas e confusas. quero que sejam mais
> elucidativas, didáticas e justificadas, devendo sempre haver uma
> recomendação pela escolha de uma opção recomendada de forma
> justificada. As opções apresentadas devem ser precedidas de
> pesquisa profunda para escolha das melhores alternativas. procure
> um design simples e funcional evitando overengeneering."

### Diagnóstico

Padrão observado nas apresentações pré-calibração (durante R1):

- **Concern** rewriting muito literal do output técnico do reviewer subagent
- **Why it matters** mantendo jargão ("viola contrato", "silently-violatable MUST")
- Opções às vezes inventadas ad-hoc sem pesquisa quando ambíguas
- **Recomendação implícita** ("Inclinação pessoal: X") em vez de explícita marcada com `(RECOMMENDED)`
- Sem checagem anti-overengineering no recommended

### Calibração aplicada

Edits no `SKILL.md` (commit `abad346`):

1. **Reescrita completa de "Human partner interaction templates"** com o **didactic disposition standard** — formato mandatório 4 partes por finding (inspirado no padrão ADR de Microsoft/AWS/adr.github.io):
   - Parte 1: explicação plain-language
   - Parte 2: consequência prática (anchored em observable cost)
   - Parte 3: opções pesquisadas (2-4, com fontes quando relevante)
   - Parte 4: recomendação explícita com `(RECOMMENDED)` + justificativa

2. **Worked example concreto** mostrando PRC007 (encryption at rest) no novo formato — demonstra tom + estrutura.

3. **AskUserQuestion ordering rule:** RECOMENDADA primeiro com sufixo `(Recommended)`, depois alternativas em ordem de fit decrescente, depois "No Plan Change", depois "Reject".

4. **Nova seção "Research-before-recommend rule"** definindo:
   - Quando research é mandatório (framework choice, security trade-off, standard em flux)
   - Métodos preferidos (WebSearch → docs → GitHub → public ADRs)
   - Quando pular (trivial findings)
   - Citar fontes na justificativa

5. **Nova seção "Anti-overengineering rule"** com 5 princípios:
   - Prefira local edits sobre new abstractions
   - Prefira existing patterns sobre new ones
   - Prefira 80% solution + documented gap sobre 100% + sprawl
   - Conte reading cost, não só writing cost
   - Default "no" quando proposal envolve ≥2 new files/types/abstractions

Sem mudanças nos reviewer subagent prompts. Isso é intencional: o
problema era a **tradução** que eu (orquestrador) fazia entre output
técnico do reviewer e apresentação ao human. O reviewer continua
produzindo Concern/Why/Suggested-resolution; o orquestrador agora
translates pro formato 4-partes.

### Validação imediata (R2 mid-session)

Apliquei a calibração antes de R2 e demonstrei o novo formato nas 4
ambíguous dispositions do R2:

- **R2-PRC001 (meta-finding):** 4 partes, recomendou Opção A (Resolved
  com lição aprendida) sobre B (No Plan Change que ocultaria erro)
  e C (Reject inválido pelo validator). Aplicou anti-overengineering
  rejeitando opções que adicionavam burden.

- **R2-PRC003 (spec amendment):** 4 partes, recomendou Opção B
  (appendix em claude-spec.md) sobre A (editar critério literal) e C
  (defer). Anchored em pattern ADR canônico (Microsoft/AWS/adr.github.io)
  via WebSearch.

- **R2-PRC006 (second asymmetry):** 4 partes, recomendou Opção A
  (atualizar plan §1 apontando pra SD-001 criado em PRC003) sobre B
  (adicionar campo ao DTO). Anti-overengineering explícito —
  "preferida documentação sobre adicionar código quando ambas
  resolvem".

- **R2-PRC008 (ESLint rule):** 4 partes, recomendou Opção B (grep CI
  hook, 5 LOC bash) sobre A (custom rule, 30 LOC + 1 dep + 1 test).
  Anti-overengineering canonical: "adicionar eslint-plugin-local-rules
  + custom rule pra detectar uma única substring é solução de fábrica
  pra problema de cottage industry".

**Operator approval rate: 4/4 das recomendações aceitas como
dispositioned.** A calibração funcionou.

## Padrões observados (para v0.x futura)

1. **Plano "v2 pós-review" ainda tem espaço pra Critical.** Iteration-1
   externa (Opus livre, 24K log) pegou direção/arquitetura, mas
   `code-plan-reviewer@v0.4` calibrado pegou type-level gotchas
   (Drizzle transaction). Pattern: reviews humanos pegam macro;
   prompts calibrados pegam micro-gotchas em frameworks específicos.

2. **Auto-Resolved acelera mas cria débito de propagação.** Em R1 fiz
   batch de 9 auto-Resolved; R2 capturou 5 findings que são
   consequência de propagação incompleta. **Lição operacional:**
   quando finding implica edits em múltiplas seções/arquivos, não é
   auto-Resolved candidate — é "Resolved com checklist de propagação".

3. **Calibração mid-session é factível e barata.** A calibração
   inteira (diagnose + WebSearch + SKILL.md edit + reinstall + commit
   + push) levou ~10min. R2 com o novo formato adicionou ~3min vs
   o que seria sem (mesma quantidade de findings, mas didactic
   format mais lento por finding). Net: calibração + R2 caliibrado +
   demonstração efetiva consumiu ~30min — caberia em qualquer
   sessão real.

4. **Anti-overengineering rule pegou peso real.** Em R2-PRC008
   recomendei grep CI hook (5 LOC bash) sobre ESLint custom rule
   (30+1dep+test) — exatamente o tipo de overengineering que eu
   teria recomendado pré-calibração porque "é o jeito canonical".
   Saving real de complexidade.

5. **Research-before-recommend deu legitimidade às recomendações.**
   PRC001 (Drizzle transaction type) e PRC003 (ADR appendix pattern)
   recomendações ancoradas em sources verificáveis (Drizzle docs,
   Microsoft ADR, adr.github.io) — operator pode validar a
   recomendação independentemente.

## v0.x candidates (input para próxima iteração da skill)

1. **Propagação checklist no Resolved disposition.** Quando finding
   afeta seção principal + tabela em outra seção + spec file, o
   Resolved deveria incluir uma sub-checklist explícita de "afetou X
   também? Y também?". Reduz débito que R2 atualmente cata.

2. **WebSearch como tool implícito do reviewer subagent.** Hoje o
   reviewer só lê arquivos; quando finding ambíguo tem decisão
   técnica não óbvia (e.g. Drizzle transaction type), reviewer
   poderia opcionalmente pesquisar e incluir a sugestão de Opção
   research-backed no Suggested resolution. Trade-off: mais cost por
   round, mas elimina round-trip orchestrator-pesquisa.

3. **Reviewer pode reconhecer planos "v2 pós-review".** Calibração
   adicional pro reviewer prompt sugerindo "se o plano tem marca de
   'pós-review', priorize type-level + cross-section consistency
   gaps (esses são os que iteração 1 perde) sobre architecture-level
   issues (já cobertos)".

## Conclusão

Segundo uso real foi sucesso operacional + adicionou evento
importante: a calibração mid-session da skill validou que o próprio
workflow `plan-review-cycle` é melhorável **durante uso real**, com
feedback do operador, e que o impacto é mensurável (operator
approval rate 4/4 nas 4 ambíguous post-calibração).

**Triangle de evidência pra `code-plan-reviewer@v0.4`:**
- jsoncheck seeded: 0 FP em 9
- pje-mcp Fase 1 real: 0 FP em 18
- pje-mcp SQLite real "v2 pós-review": 0 FP em 26

Calibração v0.x do SKILL.md adiciona evidência pra próxima
iteração da skill — disposition workflow agora é didactic 4-part
standard + research-before-recommend + anti-overengineering.

**O plano SQLite está pronto pra execução** com 26 findings tratados,
audit trail completo, e 1 spec deviation formalmente registrada em
`claude-spec.md §16 SD-001`.

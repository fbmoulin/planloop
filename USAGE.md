# Como usar `plan-review-cycle`

Guia curto e didático para usar o skill no dia a dia. Pressupõe que
você já instalou o skill em `~/.claude/skills/plan-review-cycle/`
(veja `README.md` se ainda não fez).

---

## TL;DR

1. Você escreve um plano (`.md`) e o spec/brief (`.md`).
2. Pede ao Claude: **"Revise esse plano antes de executar."**
3. O Claude dispara um reviewer subagent independente, devolve
   achados estruturados, e abre uma conversa finding-a-finding.
4. Para cada achado: você decide entre **mudar o plano**, **manter
   sem mudar** (com motivo registrado), ou **adiar pra próxima
   rodada**.
5. No final, o validator Python bloqueia execução se sobrar achado
   bloqueante em aberto.

---

## 1. Quando usar

**Use** depois que o plano está escrito e antes de começar a executar:

- Plano de implementação de feature/refactor
- Plano de minuta de sentença ou decisão
- Plano de lançamento, content sprint, growth experiment
- Plano de migração de infra ou deploy

**Não use** para:

- Escrever o plano do zero (use `writing-plans` ou rascunho manual)
- Revisar código já implementado (use `requesting-code-review`)
- Debugar implementação que está falhando

---

## 2. Como invocar

Qualquer uma destas frases dispara o skill:

```
Revise esse plano antes de executar.
Audite essa minuta de sentença antes que eu finalize.
Faça um review independente desse plano.
Roda o plan-review-cycle em plans/X.md contra specs/Y.md.
Outra rodada de revisão nesse plano.
```

Inputs ideais (não obrigatórios mas recomendados):

- **Plan path**: caminho absoluto do arquivo `.md` do plano
- **Spec/brief path**: caminho do documento de referência

Se não passar o spec, o orquestrador pergunta uma vez antes de seguir.

---

## 3. O que acontece

```
você ─► "revise plano X"
        │
        ▼
   orquestrador (Claude principal)
        │
        ├─ infere domínio (code / judicial / generic)
        ├─ confirma com você qual reviewer usar
        │
        ▼
   reviewer subagent (contexto isolado, fresh)
        │
        ├─ lê plano + spec
        ├─ devolve achados estruturados
        │   (id, severity, location, concern, why, suggestion)
        │
        ▼
   orquestrador escreve Plan Review Log no fim do plano
        │
        ▼
   você dispoõe achado-a-achado (Resolved / No Plan Change / Defer)
        │
        ▼
   validator Python roda → bloqueia se sobrar Open bloqueante
        │
        ▼
   handoff: executar / próxima rodada / escalação
```

Cada rodada é registrada no log com timestamp, modelo usado, versão
do reviewer prompt, e quem aprovou cada disposição. Isso é o audit
trail durável.

---

## 4. Dispondo cada achado

A skill segue um **padrão didático em 4 partes** mandatório para cada
achado (inspirado no pattern ADR de Microsoft/AWS/adr.github.io). O
orquestrador (Claude) traduz o output técnico do reviewer subagent
para este formato antes de apresentar a você:

**Parte 1 — Explicação em linguagem simples**
O orquestrador reescreve o achado em prosa elucidativa, evitando
jargão. Se há termo técnico inescapável, explica em 5-10 palavras.
Pode usar analogia quando ajuda.

**Parte 2 — Consequência prática**
Não "viola contrato" abstrato; sim "implementador descobre na metade
da Task 4 e gasta 1h refazendo migration", ou "DataJud responses
sem `nivelSigilo` começariam a falhar silenciosamente em prod". O
orquestrador ancora em custo observável.

**Parte 3 — Opções pesquisadas (2-4)**
Antes de apresentar opções, o orquestrador segue a regra
**Research-before-recommend**: para decisões técnicas não-triviais
(framework choice, security pattern, standard em flux), pesquisa
WebSearch + docs + GitHub antes de propor. Cita fontes quando
aplicável. Opções nunca são inventadas ad-hoc.

**Parte 4 — Recomendação explícita com justificativa**
Uma das opções é marcada `(Recommended)` com justificativa de 1-2
frases ancorada em (a) simplicidade, (b) alinhamento com decisões
anteriores do plano, ou (c) fit com o contexto do projeto. Sem
recomendação implícita — você sempre sabe qual o orquestrador
acha melhor e por quê.

A pergunta final (`AskUserQuestion`) lista a opção RECOMENDADA
primeiro com sufixo `(Recommended)`, depois alternativas, depois
"No Plan Change", depois "Reject". Você pode escolher qualquer uma.

### Os 4 outcomes possíveis

#### a) Resolved (mudar o plano)

Você aprova a proposta (ou alternativa). O orquestrador edita o plano
e marca `Resolved` com `plan_changes_made` apontando para as seções
alteradas. Para findings **multi-section** (que tocam 2+ seções/
arquivos), o `plan_changes_made` carrega checklist explícito
(veja §4.1 abaixo).

Exemplo:
> Achado: "Tarefa 4 sem critério de sucesso observável."
> Você: "Concordo, adiciona um critério mensurável."
> Orquestrador: "Vou inserir 'Sucesso: query retorna resultado em <
> 200ms' no fim da Tarefa 4. Aprovado?"
> Você: "Sim."

#### b) No Plan Change (manter, com motivo)

Você não concorda OU o achado é fora de escopo OU está superseded por
outro plano. O motivo precisa ser **concreto** — "vamos ver depois"
falha no validator. Tem que nomear o que supersedes, defers ou exclui
do escopo.

Exemplos de motivos válidos:

- "Out of scope; tracking em backlog item #142."
- "Superseded pelo refactor da ADR-0007 que muda a abordagem."
- "Critério não se aplica porque feature é internal-only sem SLA."
- "Defer para Fase 4 (homologação institucional formal); risco aceito
  como trade-off de escopo controlado para read-only inicial."

Exemplos de motivos que **falham** no validator:

- "OK, depois eu vejo."
- "Não é crítico."
- "Concordo mas é minor."

#### c) Defer (deixar Open pra próxima rodada)

Você quer pensar mais antes de decidir. Achado fica Open, o validator
ainda bloqueia, e ele será re-apresentado na próxima rodada (ou
explicitamente fechado depois).

#### d) Reject (re-propor)

Se a proposta do orquestrador não te satisfaz, você pede outra. Volta
pra propose loop.

### 4.1. Propagation checklist (findings multi-section)

Quando a resolução de um achado toca **mais de uma seção do plano**
OU **arquivos externos** (`.env.example`, spec file, README, config),
o achado é multi-section e o `plan_changes_made` MUST conter checklist
explícito enumerando cada local tocado:

```yaml
plan_changes_made: |
  Aplicada Opção X (resumo de 1 linha). Propagação verificada:
  - [x] §2: linha "Transações" reescrita com invariante sync
  - [x] §8: assinaturas withTransaction(tx: DrizzleDB) em 4 repos
  - [x] §13: nova entrada em tabela "Arquivos modificados"
  - [x] tests/storage/global-setup.ts: novo arquivo
```

Por quê: na prática real, auto-Resolved acelera mas cria "propagation
debt" quando o orquestrador aplica edit na seção principal e esquece
de propagar pras tabelas/spec/config. O checklist torna visível pra
você se algum item ficou esquecido, antes do próximo round catar.

**Indicators de multi-section** (o orquestrador deve flagar
automaticamente):
- Adiciona env var, type alias, invariante, ou pattern que aparece em
  múltiplos lugares
- Resolução promete edits em outra seção ("inserir em §15", "atualizar
  README", "spec amendment")
- Adiciona nova task/sub-task referenciada em outros lugares
- Muda contrato público com surfaces de audit/spec/test
- Introduz build step que requer edits em source + dist/test config

Findings single-section (typo, dead code, missing field em um único
schema) NÃO precisam do checklist — `plan_changes_made` de uma linha
basta.

### 4.2. Restrição ao modo "auto-Resolved nos óbvios"

O modo de aceleração "auto-Resolved nos óbvios + decide só os
ambíguos" (que o orquestrador pode propor pra te poupar tempo)
**não deve** ser aplicado a findings multi-section. Multi-section
exige human walk-through OU auto-Resolved com checklist completo
visível em chat antes de aplicar.

Mixing auto-Resolved em multi-section é o failure mode que cria
propagation debt — observado empiricamente em uso real.

### 4.3. Princípio anti-overengineering

Quando o orquestrador escolhe entre resoluções, prefere a mais
simples viável:

- **Local edits sobre new abstractions.** Se 3 linhas resolvem, não
  propõe helper function.
- **Existing patterns sobre new ones.** Se a codebase tem pattern
  pra X, usa antes de inventar Y.
- **80% solution + documented gap sobre 100% solution + sprawl.** Se
  a versão simples cobre o spec MUST e a complexa cobre cenários
  hipotéticos, recomenda simples + nota dos 20%.
- **Custo de leitura conta tanto quanto custo de implementação.**
  Solução clever que leva 10min pra entender depois custa mais que
  verbosa que leva 1min.

Exemplo real (PRC008 do plano SQLite pje-mcp): recomendei grep CI
hook (5 linhas bash) sobre ESLint custom rule (30 LOC + 1 dep +
test). Ambas resolviam o invariante "no `db.transaction(async`";
grep cobre 95% por 1/10 do custo.

---

## 5. Severity e o que bloqueia execução

| Severity | Bloqueia execução enquanto Open? |
|---|---|
| Critical | Sempre |
| Major | Sempre (a menos que você aceite o risco explicitamente em forma de No Plan Change com motivo) |
| Minor | Sim, até fechar |
| Advisory | Nunca |

Tentar baixar uma Critical pra Advisory pra "destravar" não funciona:
essa decisão vira ela mesma um No Plan Change finding precisando de
motivo aprovado.

---

## 6. Rodadas

- Máximo de 3 rodadas por ciclo.
- Recomenda-se outra rodada se a rodada anterior produziu mudanças
  significativas no plano.
- **Regra de escalação:** se a rodada 3 ainda produz um Critical, o
  orquestrador para e diz "o plano segue gerando críticos, o spec ou
  o escopo provavelmente está errado, volte pra brainstorming." Não
  roda rodada 4.

---

## 7. Validator manual

Você pode rodar o validator a qualquer momento, sem disparar uma
rodada de review:

```bash
python3 ~/.claude/skills/plan-review-cycle/scripts/validate_plan_review_log.py path/to/plan.md
```

Exit codes:

- `0`: tudo certo, plano pronto pra executar
- `1`: tem achado bloqueante em aberto (lista os IDs)
- `2`: log malformado (campos faltando, placeholders não preenchidos)

Útil em pre-commit / CI: bloquear merge se um plano em `plans/`
tiver achado Open.

---

## 8. Diverse critics (opcional, alto risco)

Para planos de alto risco (sentenças em casos repetitivos, refactor
afetando produção, qualquer coisa em alto-risco CNJ 615/2025), peça:

```
Revise esse plano com diverse critics.
```

O orquestrador dispara DOIS reviewers em paralelo com roles
diferentes (ex: "magistrado garantista" vs "magistrado conservador"
no judicial, "implementer focado em shipping" vs "architect focado
em custo de longo prazo" no code), e funde os achados antes de
apresentar.

Custo é ~2× single critic. Vale para decisões caras de reverter.

---

## 9. Quando ignorar uma rodada

Não dispare o skill quando:

- Você só quer brainstorming inicial — o skill audita, não cria
- O plano é trivial (1 arquivo, 2 linhas de mudança)
- Você está debugando uma implementação que já está rodando
- Você quer reescrever o spec — volte pra brainstorming primeiro

---

## 10. Troubleshooting curto

| Problema | Causa provável | Fix |
|---|---|---|
| Validator exit 2 "log malformed" | Algum campo `plan_changes_made` ou `no_change_rationale` ficou vazio quando deveria estar preenchido | Reabrir o achado ofensor, preencher o campo, re-rodar |
| Validator exit 2 "rationale too brief" | Motivo de No Plan Change tem menos de 8 palavras | Reescrever com referência concreta (ADR, backlog, regra de escopo) |
| Reviewer retornou "Status: Approved" sem achados | Plano realmente está limpo OU reviewer sycophant | Cheque o plano à mão; se tem buraco óbvio, dispare outra rodada com restrição explícita ("foque em X") |
| Achados em sequência se repetem | Reviewer não está vendo o Plan Review Log anterior | Verifique que o dispatch passa o log existente como `PRIOR_LOG` |
| Reviewer flagou coisa que não é problema | Falso-positivo — sinalize como No Plan Change com motivo "achado não procede porque [evidência]" | Validator aceita; serve de evidência para calibração futura do prompt |

---

## 11. Versões dos reviewers e da skill

**Reviewer prompts** (cada rodada registra a versão usada no log):

- `code-plan-reviewer@v0.4`
- `judicial-plan-reviewer@v0.4`
- `generic-plan-reviewer@v0.4`

Calibrações v0.2-v0.4 derivam de seeded evals; v0.5+ virá de uso real
quando 3-5 planos reais convergirem em padrões consistentes.

**Skill workflow** (definido em `SKILL.md` no orquestrador):

- v0.1 (initial) — fluxo básico Skill → Agent → Log → Validator
- v0.2 (commit `352d68d`) — output template v0.3 family-wide
- v0.x didactic (commit `abad346`) — padrão didático 4-partes
  mandatório para disposição (§4 deste guia), research-before-recommend
  rule, anti-overengineering rule
- v0.x propagation (commit `a511f8c`) — propagation checklist
  mandatório para findings multi-section (§4.1 deste guia),
  restrição de auto-Resolved (§4.2)

Cada calibração da skill é derivada de evidência empírica documentada
em `eval/RESULTS*.md`. Pattern reusable: calibração mid-session
quando operador detecta padrão problemático é factível (~10min) e
mensurável (operator approval rate como métrica).

---

## 12. Recap em uma frase

**Você escreve, o reviewer audita independente, você decide cada
achado, o validator bloqueia se sobrar buraco aberto, o log fica no
plano pra sempre.**

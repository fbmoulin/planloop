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

Para cada achado, o orquestrador pergunta uma de três coisas:

### a) Resolved (mudar o plano)

Você concorda com o achado e o plano vai mudar. O orquestrador propõe
a mudança concreta, você aprova, ele edita o plano e marca o achado
como `Resolved` com `plan_changes_made` apontando para as seções
alteradas.

Exemplo:
> Achado: "Tarefa 4 sem critério de sucesso observável."
> Você: "Concordo, adiciona um critério mensurável."
> Orquestrador: "Vou inserir 'Sucesso: query retorna resultado em <
> 200ms' no fim da Tarefa 4. Aprovado?"
> Você: "Sim."

### b) No Plan Change (manter, com motivo)

Você não concorda OU o achado é fora de escopo OU está superseded por
outro plano. O motivo precisa ser **concreto** — "vamos ver depois"
falha no validator. Tem que nomear o que supersedes, defers ou exclui
do escopo.

Exemplos de motivos válidos:

- "Out of scope; tracking em backlog item #142."
- "Superseded pelo refactor da ADR-0007 que muda a abordagem."
- "Critério não se aplica porque feature é internal-only sem SLA."

Exemplos de motivos que **falham** no validator:

- "OK, depois eu vejo."
- "Não é crítico."
- "Concordo mas é minor."

### c) Defer (deixar Open pra próxima rodada)

Você quer pensar mais antes de decidir. Achado fica Open, o validator
ainda bloqueia, e ele será re-apresentado na próxima rodada (ou
explicitamente fechado depois).

### d) Reject (re-propor)

Se a proposta do orquestrador não te satisfaz, você pede outra. Volta
pra propose loop.

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

## 11. Versões dos reviewers

Os reviewers evoluem com base nos evals. Versão atual de cada um:

- `code-plan-reviewer@v0.4`
- `judicial-plan-reviewer@v0.4`
- `generic-plan-reviewer@v0.4`

Cada rodada registra a versão usada no log. Se você atualizar o
prompt, rodadas anteriores ficam rastreáveis pela versão registrada.

Histórico das calibrações em `eval/RESULTS*.md`.

---

## 12. Recap em uma frase

**Você escreve, o reviewer audita independente, você decide cada
achado, o validator bloqueia se sobrar buraco aberto, o log fica no
plano pra sempre.**

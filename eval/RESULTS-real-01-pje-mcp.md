# Eval Results — Real-01: pje-mcp Fase 1

Primeiro uso real do `plan-review-cycle` em um plano de produção
(não-seeded). Plano operacional para a Fase 1 (PJe read-only) do
servidor MCP `pje-mcp` (projeto `kratos-pje-control`), revisado
contra o SPEC institucional do projeto.

Diferente dos evals seeded (`eval/SEEDS-*.md`), aqui não havia falhas
plantadas — o reviewer encontrou problemas reais que valeram correção
real no plano antes da execução.

## Setup

- **Plano:** `eval/real/01-pje-mcp-fase1-plan.md` (escrito pelo Felipe,
  baseado em SPEC §13 Fase 1 + gap observado no scaffold atual)
- **Spec:** `/mnt/c/projetos-2026/pje-mcp/SPEC.md` (478 linhas, com
  pesquisa expandida + 16 seções incluindo roadmap, segurança CNJ, MNI)
- **Scaffold atual:** `/mnt/c/projetos-2026/pje-mcp/src/` (~410 LOC TS,
  MCP SDK + DataJud adapter + audit log + policy básica)
- **Skill invocation:** `Skill plan-review-cycle` (carrega SKILL.md) +
  `Agent` tool com `code-plan-reviewer@v0.4` (2 rounds)
- **Modo de disposition:** auto-Resolved nos óbvios + human-decide nos
  ambíguos (8 perguntas ao Felipe via AskUserQuestion ao longo de R1+R2)

## Resultados agregados

| | R1 | R2 | Total |
|---|---|---|---|
| Findings novos | 12 | 6 | 18 |
| Critical | 0 | 0 | 0 |
| Major | 5 | 3 | 8 |
| Minor | 5 | 3 | 8 |
| Advisory | 2 | 0 | 2 |
| Resolved | 11 | 6 | 17 |
| No Plan Change | 1 | 0 | 1 |
| Falsos positivos | 0 | 0 | 0 |
| Repetidos do round anterior | — | 0 | — |
| Cost (tokens / wall) | ~65k / ~52s | ~73k / ~34s | ~138k / ~86s |
| Human-in-the-loop time | ~5min | ~3min | ~8min |
| Validator final | exit 1 (10 blocking) → exit 0 (após R1) | exit 1 (6 blocking) → exit 0 (após R2) | exit 0 |

## Findings que mudaram materialmente o plano

Os 4 findings de maior alavancagem (sem eles, a Fase 1 teria entregue
buracos significativos):

**R1-PRC003 (Major) — Schema documentos sem `caminho_local`**

Cruzando Task 1 schema com Task 4 passos, o reviewer detectou que
o caminho do arquivo no disco não tinha coluna onde ser persistido.
Sem essa correção, implementador descobriria na metade da Task 4 e
faria migration ad-hoc. **Economia estimada: 1h de retrabalho + um
commit de cleanup.**

**R1-PRC007 (Major) — Criptografia em repouso silently-violatable MUST**

SPEC §9 exige criptografia em repouso mas o plano original não
mencionava. Decidida Opção D após pesquisa web sobre SQLCipher
state-of-the-art + CNJ 396/2021. **Mudou estruturalmente o plano**:
adicionada dependency `better-sqlite3-multiple-ciphers`, nova
`STORAGE_ENCRYPTION_KEY` env obrigatória, nova Task 6.5 (ADR + script
de check), e seção `## Credenciais` no README.

**R2-PRC013 (Major) — SQLCipher PRAGMA ordering**

Reviewer R2 detectou que sem PRAGMA cipher+key antes do primeiro
SQL, `better-sqlite3-multiple-ciphers` cria arquivo plaintext
silenciosamente. Esse é o gotcha clássico de SQLCipher que custa
1-2 dias de debug em produção. **Capturado antes do código existir.**

**R2-PRC014 (Major) — SSRF redirect bypass**

R1 propôs allowlist via `assertHostAllowed()` (PRC002 Resolved). R2
detectou que isso só checa URL inicial — HTTP 30x para IMDS bypassa.
Decisão: `fetch({redirect: 'manual'})` + reject default. Cobre o
caso clássico de SSRF via redirect.

## Padrões observados (input para calibração v0.5)

### 1. Cascata de segurança em domínios sensíveis

Das 18 findings, ~10 (55%) tocam segurança ou audit: SSRF (2),
criptografia (4 — PRC007, PRC013, PRC015, PRC017), audit log (1 —
PRC001), prompt injection (1 — PRC008), credenciais (2 — PRC011,
PRC018).

Comparação com evals anteriores no mesmo `code-plan-reviewer@v0.4`:

| Eval | Domínio | Findings security/audit | % do total |
|---|---|---|---|
| jsoncheck (seeded) | CLI tool | 0 / 9 | 0% |
| pje-mcp Fase 1 (real) | MCP server PJe | 10 / 18 | 55% |

Padrão: códigos que tocam dados sigilosos + APIs externas + persistência
têm tax estrutural alta de findings security. Vale antecipar nas
próximas fases (Fase 2 gestão local: lotes/etiquetas = mais ACL
findings; Fase 3 RAG + LLM: prompt injection real).

### 2. Cascata de segunda ordem

R2 produziu 3 findings (PRC013, PRC015, PRC017) que são *consequências
diretas* de PRC007 (criptografia). PRC014 é consequência de PRC002
(allowlist). Padrão: **mudanças de segurança têm raio de blast maior
que mudanças funcionais** porque introduzem novas surfaces
(key management, redirect handling, FS check, downloads path).

Hint para v0.5: o reviewer poderia opcionalmente prever "findings de
segunda ordem" ao propor uma mudança de segurança — algo como "se
você adotar X, considere também Y e Z que se tornam novas surfaces".
Isso reduziria iteração entre rounds.

### 3. Modo "auto-Resolved + human-decide" funcionou em escala

Dos 17 Resolved, 7 foram auto-applied (PRC005, PRC006, PRC009, PRC010,
PRC012, PRC016, PRC018) — todos achados onde a correção era trivial,
sem trade-off significativo. Os 10 ambíguos demandaram input real do
Felipe e produziram decisões estruturais (Opção D combinada, MNI
2.2.3 fixed, DATA_DIR env, fetch redirect manual, etc.).

Tempo total human-in-the-loop: ~8 minutos. **Para um plano de 7 tasks
+ 142 linhas, isso é viável dentro de uma sessão de planning.** Mais
do que isso e o sponsor perderia paciência.

### 4. Decisão No Plan Change funcionou como tool de escopo

Apenas 1 dos 18 findings ficou como No Plan Change (PRC001, audit em
paths de erro). O motivo registrado ("defer para Fase 4 com
homologação CNJ 615/2025") cumpre o requisito do validator de motivo
concreto com referência a um marco específico, não vago.

Esse uso é *exatamente* o que o skill foi desenhado pra preservar:
o achado fica no log permanente, contestável, e a próxima rodada
de review (ou auditoria externa) pode revisitar a decisão. Não é
"ignorado" — é "explicitamente diferido com motivo registrado".

### 5. Zero falsos positivos em 18 findings reais

Todos os 18 achados representavam problemas reais que o Felipe
concordou existirem. Calibração v0.4 do code-plan-reviewer manteve
o alvo de FP ≤ 25% bem abaixo (FP = 0%). Compare:

- jsoncheck seeded: FP 0/9
- pje-mcp real: FP 0/18

Sugere que v0.4 não está propenso a inflar achados quando o plano
é genuinamente bom.

## v0.5 candidates (input para próxima calibração)

Em ordem de prioridade observada:

1. **Second-order security hints.** Quando o reviewer detecta um
   missing-security-MUST (categoria SPEC §9), considerar incluir nota
   "essa mudança introduzirá novas surfaces; em R2 reveja
   {key-management, fetch-config, FS-paths}". Reduz iteração R1→R2.

2. **Cross-task consistency check explícito.** PRC003 (caminho_local
   missing) foi capturado por inspeção cruzada Task 1 schema × Task 4
   passos. Vale adicionar ao "What to check" do prompt:
   "interface consistency between tasks that produce data and tasks
   that consume it".

3. **Recognition de PRAGMA-ordering / setup-ordering gotchas.** PRC013
   sugere que existem patterns recorrentes (SQLCipher PRAGMA, TLS
   setup, env loading) onde ordem é crítica e o plano default omite.
   Vale anchor example no Major.

4. **Redirect handling como default-secure rule.** PRC014 sugere que
   qualquer fetch deveria ter redirect handling explícito mencionado
   no plano. Pode entrar como rule no Major examples.

## Conclusão

**Primeiro uso real foi sucesso operacional:**
- 0 Critical em 2 rounds (plano fundamentalmente são)
- 18 findings legítimos com 0 FP
- 4 findings de alta alavancagem capturados antes da execução
- ~8min de human-in-the-loop pra plano de Fase 1 inteira
- Convergência clara: R2 sem repetidos + sem Critical
- Validator gate funcionou (exit 0 só após dispositions completas)

**Pronto para implementação.** Felipe pode agora executar o plano
com confiança de que os gaps estruturais foram corrigidos, as
decisões arquiteturais (MNI version, encryption, DATA_DIR, allowlist
behavior) estão registradas, e os trade-offs deferidos (PRC001 audit
hardening) têm motivo explícito + marco futuro registrado.

**Sinal positivo para v0.4 calibration:** três domínios (code seeded,
judicial seeded, generic seeded, agora code real) com discovery
consistente e zero FP. Pode-se rodar v0.5 quando 3-5 usos reais
acumularem padrões claros, em vez de seeds sintéticas.

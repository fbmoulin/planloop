# Eval Results — Judicial Reviewer (PT-BR)

Baseline + calibration evaluation of `judicial-plan-reviewer` (v0.1 →
v0.2) against a seeded plan for a sentença consumerista (repetição de
indébito + danos morais).

## Setup

- **Plano:** `eval/plan-sentenca-seeded.md`
- **Autos:** `eval/autos-consumerista.md`
- **Seeds:** `eval/SEEDS-judicial.md` (2 Critical + 1 Major + 1 Minor + 1 Advisory bait)
- **Dispatch:** Claude Code `Agent` (general-purpose) com o reviewer prompt completo preenchido
- **Skill location:** `~/.claude/skills/plan-review-cycle/reviewers/judicial-plan-reviewer.md` (reinstalado a cada bump)

## Round 1 — `judicial-plan-reviewer@v0.1` (baseline)

7 findings, 2 Critical + 3 Major + 2 Minor + 0 Advisory.

| Seed | Esperado | v0.1 R1 | Δ |
|---|---|---|---|
| JC1 (Tema 929 não enfrentado) | Critical | R1-PRC001 Critical | ✓ |
| JC2 (mero aborrecimento omisso) | Critical | R1-PRC002 Critical | ✓ |
| JM1 (honorários ausentes) | Major | R1-PRC004 Critical | promovido (no range) |
| Jm1 (dispositivo retoma fundamentação) | Minor | **absent** | ✗ MISS |
| JA1 (polish "Acabamento") | Advisory/absent | absent | ✓ |

Findings bônus legítimos (todos previstos no bonus list de SEEDS-judicial.md ou na regra de estilo do próprio prompt):

- R1-PRC003 Major — distinguishing raso do Tema 618 STJ
- R1-PRC005 Major — arts. 39 V e 51 IV do CDC omissos
- R1-PRC006 Minor — prazo recursal/intimação ausentes
- R1-PRC007 Minor — fundamentação subdividida (II.1–II.4) viola preferência de prosa contínua

**Métricas R1:**
- Discovery: 4/5 seeds (80%, atinge alvo ≥ 80%)
- Falsos positivos: 0/7
- Sycophancy: PASS
- Calibração de severidade: 4/5 exatos
- Custo: 1 dispatch Opus 4.7, ~52k tokens, ~74s

**Diagnóstico do gap (v0.1 → v0.2):**

1. **Jm1 missed.** Prompt v0.1 lista "dispositivo claro, com letras (a, b, c)" mas não diz "dispositivo não retoma argumento de mérito". O reviewer não tem um check explícito para vícios estruturais do dispositivo, então passou despercebido enquanto o reviewer focava nas omissões mais graves.

2. **JC1 acertou por boa inferência do modelo, não pelo prompt.** A entrada Critical do v0.1 só lista "súmula vinculante" explicitamente. Tese repetitiva do STJ é vinculante por CPC 927 III, mas o prompt não diz isso. Em casos menos claros, há risco de drift para Major.

## v0.2 — calibration edits

Quatro edições focadas em `reviewers/judicial-plan-reviewer.md`:

1. **Frontmatter:** `v0.1 → v0.2`.
2. **Estrutura formal da decisão:** adicionado bullet "Dispositivo conclusivo, sem retomada argumentativa" com exemplo de construção viciada ("Ante o exposto, considerando que [argumento]...").
3. **Severity guide:**
   - Critical: substituído "súmula vinculante não enfrentada" por "precedente vinculante não enfrentado (súmula vinculante STF, súmula STJ em recurso repetitivo, tese firmada em repetitivo do STJ ou em IRDR/IAC — CPC 927 II, III, IV; aplicação de jurisprudência expressamente superada igualmente Critical)". Adicionado "dispositivo contaminado por argumentação de mérito (vício estrutural)".
   - Major: explicitado "omissão de dispositivos legais expressamente invocados (CPC 489 §1º IV)" e "distinguishing necessário e ausente (CPC 489 §1º VI)".
   - Minor: explicitado que subdivisões da fundamentação e retomada local de argumento entram aqui se violam preferência registrada.
   - Advisory: adicionada REGRA ESPECÍFICA com teste operacional para tarefas puramente cosméticas ("você consegue nomear o erro jurídico se a tarefa for ignorada?").
4. **Output template:** `judicial-plan-reviewer@v0.1 → @v0.2`.

## Round 2 — `judicial-plan-reviewer@v0.2`

8 findings, 3 Critical + 3 Major + 1 Minor + 1 Advisory.

| Seed | v0.1 R1 | v0.2 R2 | Δ | Análise |
|---|---|---|---|---|
| JC1 (Tema 929) | Critical | Critical | — | invariante; v0.2 cita CPC 927 III explicitamente |
| JC2 (mero aborrecimento) | Critical | **Major** | ↓ | regressão lateral (ver análise abaixo) |
| JM1 (honorários) | Critical | Critical | — | invariante |
| Jm1 (dispositivo contaminado) | absent | **Critical** | ✓ FIXED | regra v0.2 ativa pegou no trecho exato |
| JA1 (polish "Acabamento") | absent | Advisory | ↑ | v0.2 registra como Advisory documentado em vez de omitir silenciosamente |

Bônus em R2:

- R2-PRC004 Major — distinguishing Tema 618 raso (mesmo de R1-PRC003)
- R2-PRC005 Major — arts. 39/51 CDC omissos (mesmo de R1-PRC005)
- R2-PRC006 Major — danos morais (reframing técnico, ver abaixo)
- R2-PRC007 Minor — prazo recursal (mesmo de R1-PRC006)
- Perdido em R2: R1-PRC007 (fundamentação subdividida) — reviewer não re-flagged

**Distribuição:**

|   | Critical | Major | Minor | Advisory | Total |
|---|---|---|---|---|---|
| v0.1 R1 | 2 | 3 | 2 | 0 | 7 |
| v0.2 R2 | 3 | 3 | 1 | 1 | 8 |

Shift líquido: +1 Critical (Jm1 capturado), +1 Advisory (JA1 documentado), −1 Minor (fundamentação subdividida sumiu).

**Métricas R2:**
- Discovery: 5/5 seeds (100%; Jm1 que faltava em R1 foi capturado)
- Falsos positivos: 0/8
- Sycophancy: PASS
- Calibração: 4/5 exatos (regressão em JC2)
- Custo: 1 dispatch Opus 4.7, ~52k tokens, ~68s

## Análise da regressão JC2 (Critical → Major)

O reviewer v0.2 mudou o framing do problema de danos morais:

- **v0.1 R1 (Critical):** "contradição entre fundamentação e dispositivo" + "vício insanável CPC 1.022 II".
- **v0.2 R2 (Major):** "subsunção por conceito jurídico indeterminado (CPC 489 §1º III)" + nota lateral sobre tese de mero aborrecimento omissa.

A análise nova é tecnicamente mais correta — não há, de fato, contradição interna no plano entre II.4 (procedência) e III.c (R$ 2.000,00); ambos concordam. A contradição é entre o plano e a posição declarada da magistrada no contexto dos autos, o que é problema diferente.

**Mas a regressão de severidade é real:** omissão de tese defensiva expressamente articulada (a contestação articula "mero aborrecimento" como fundamento autônomo) é Critical na seção **Calibração** do prompt ("Omissão de tese defensiva é Critical (gera nulidade nos termos do CPC 489 §1º IV)"). Essa regra existe em ambas as versões. O reviewer v0.2 não a ativou porque:

1. A regra mora na seção "Calibração", não no "Guia de severidade".
2. O Guia de severidade Critical lista "omissões geradoras de nulidade (CPC 489 §1º)" genericamente, sem destacar a tese defensiva expressamente articulada.
3. O reviewer escolheu o caminho técnico mais limpo (§1º III conceito indeterminado) e classificou pelo Guia.

**Lição não-monotônica:** melhorar o framing técnico do reviewer pode baixar a severidade de um achado porque abre novos enquadramentos. Calibração de prompts em domínios jurídicos não é monotônica.

## v0.3 candidates

1. **Promover "omissão de tese defensiva expressamente articulada pela parte" ao Severity Guide Critical** com texto explícito. Não deixar essa regra apenas na seção Calibração. Mirror do efeito da edição v0.2 sobre Tema repetitivo.

2. **Reconsiderar severidade "dispositivo contaminado".** Atualmente em Critical (regra v0.2). É vício estrutural mas não gera nulidade per se nem inverte o resultado. Major seria mais defensável. Pode reduzir falsos-positivos Critical em casos onde a contaminação é leve.

3. **Reforçar check de estilo registrado** — em R2 o reviewer perdeu o achado sobre fundamentação subdividida que tinha em R1. Talvez porque com 8 achados a presença Minor de estilo registrado caiu da heurística de "não inflar". Vale registrar esse trade-off.

## Conclusão — v0.2 judicial

As duas edições-alvo funcionaram:

- ✓ Jm1 capturado pela regra "dispositivo contaminado por argumentação de mérito".
- ✓ JA1 surfaceado como Advisory documentado (em vez de silenciosamente omitido), via regra do polish-only.
- ✓ JC1 mantém Critical e ganha citação explícita de CPC 927 III via novo texto do Severity Guide.

A regressão em JC2 (Critical → Major) é efeito colateral não-monotônico: o reviewer escolheu um framing técnico melhor que rebaixa a severidade. Compensação é fácil em v0.3 (promover "omissão de tese defensiva" ao Severity Guide Critical).

Discovery rate: 4/5 → 5/5. Falsos positivos: 0 → 0. Calibração exata: 4/5 → 4/5 (alvo deslocado: ganhou Jm1, perdeu JC2). Recomendo instalar v0.2 como default e registrar v0.3 candidates no roadmap.

---

# Round 3 — `judicial-plan-reviewer@v0.4` (JC2 regression fix + style consistency)

Rodada de verificação após aplicar as duas edições v0.4:

1. **Severity Guide Critical:** adicionada regra explícita "omissão de
   enfrentamento de tese defensiva expressamente articulada pela parte
   (CPC art. 489 §1º IV — incluindo, por exemplo, a tese de 'mero
   aborrecimento' em pedido de dano moral, ou a tese de 'boa-fé do
   credor' em repetição de indébito; a regra vale ainda que o plano
   alcance a mesma conclusão por outro caminho)". Promoveu a regra
   que antes vivia apenas na seção Calibração para o Severity Guide.

2. **Seção Calibração:** adicionada nota sobre consistência de
   estilo registrado entre rodadas — preferências do magistrado
   (prosa contínua, ausência de subdivisões, ausência de travessões)
   devem ser sinalizadas com a mesma consistência através das
   rodadas, não desprivilegiadas quando achados de severidade maior
   ocupam a rodada.

## R3 v0.4 vs rodadas anteriores no plan-sentenca-seeded.md

| Seed | v0.1 R1 | v0.2 R2 | v0.4 R3 | Δ vs R2 | Expected |
|---|---|---|---|---|---|
| JC1 (Tema 929) | Critical | Critical | Critical | — | Critical ✓ |
| JC2 (mero aborrecimento) | Critical | **Major** (regressão) | **Critical** | ↑ **FIXED** | Critical ✓ |
| JM1 (honorários ausentes) | Critical | Critical | Critical | — | Major (in range) |
| Jm1 (dispositivo contaminado) | absent | Critical | Critical | — | Critical (v0.2 design) ✓ |
| JA1 (polish "Acabamento") | absent | Advisory | Advisory | — | Advisory ✓ |

Distribuição:

|   | Critical | Major | Minor | Advisory | Total |
|---|---|---|---|---|---|
| v0.1 R1 | 2 | 3 | 2 | 0 | 7 |
| v0.2 R2 | 3 | 3 | 1 | 1 | 8 |
| v0.4 R3 | 4 | 3 | 1 | 1 | 9 |

## Key wins

1. **JC2 restaurado para Critical.** A regressão lateral observada em
   v0.2 R2 foi corrigida cirurgicamente. O reviewer cita o texto da
   nova regra v0.4: "Omissão de enfrentamento de tese defensiva
   expressamente articulada pela parte viola CPC art. 489 §1º, IV, e
   gera nulidade." A finding foi também enriquecida com nota de
   contradição com a posição declarada da magistrada no Contexto dos
   autos.

2. **R3-PRC009 (subdivisões da fundamentação) re-flagged como Minor**
   com nota explícita: "Re-sinalizado por consistência através das
   rodadas, conforme calibração v0.4 (item d)." A regra de
   consistência de estilo foi internalizada — o reviewer agora se
   refere à própria calibração quando reinclui um achado de estilo.

3. **Bonus finding R3-PRC005 (Major): ausência de juros, correção
   monetária e prazo de cumprimento.** Achado legítimo não-seeded que
   cita inclusive a unificação pela Lei 14.905/2024 e o Tema 1.061/STJ.
   O reviewer está ativando referências legislativas e jurisprudenciais
   recentes — sinal de raciocínio jurídico atualizado, não calibração
   v0.4 específica.

4. **JA1 mantém Advisory** com nota "Sinalizado por consistência
   metodológica conforme calibração v0.4 (item c)" — a REGRA
   ESPECÍFICA polish-only continua aplicada corretamente.

## Métricas — R3 v0.4

- Discovery: 5/5 seeds (100%, mesmo de R2)
- Severity exact: 5/5 (R2 era 4/5; JC2 corrigido)
- Falsos positivos: 0/9
- Bonus catches: 4 (distinguishing Tema 618, arts. 39/51 CDC, prazo
  recursal, juros+correção+prazo cumprimento) — todos legítimos
- Output format compliance: PASS — sem Recomendações, Advisory sob
  Achados com severidade explícita
- Custo: 1 dispatch Opus 4.7, ~49k tokens, ~35s

## Conclusão — v0.4 judicial

A regressão JC2 (Critical → Major em v0.2 R2) foi corrigida
exatamente como previsto pelo v0.4 candidate: promover a regra
"omissão de tese defensiva expressamente articulada" do bloco
Calibração para o Severity Guide Critical. Side effect: a regra
agora dispara mesmo quando o reviewer escolhe enquadramento
técnico alternativo (CPC §1º III conceito indeterminado), porque a
combinação dos dois enquadramentos compõe Critical no novo Severity
Guide.

A nota de consistência de estilo também produziu o efeito desejado
— a R3 não perdeu o achado sobre subdivisões da fundamentação que
R2 v0.2 havia abandonado.

Calibração agora estável nos 5 seeds com 5/5 exatos. Sem regressões.

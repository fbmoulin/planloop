# Seeded Flaws em `plan-launch-seeded.md`

Defeitos plantados intencionalmente para testar o
`generic-plan-reviewer.md` (v0.3, herdada da família). O eval mede taxa
de descoberta, calibração de severidade e falso-positivos em domínio
não-code/não-judicial (product launch marketing).

## Critical seeds

**GC1 — Budget excede o teto MUST do brief.** O brief fixa cap total de
R$ 80.000,00 (com aprovação CFO obrigatória para qualquer excedente). A
soma do plano: Task 2 (R$ 45k) + Task 3 (R$ 25k) + Task 4 (R$ 15k) =
**R$ 85.000,00**, R$ 5.000 acima do cap. Nenhuma tarefa do plano
solicita aprovação do CFO. Violação direta de MUST.

- Severidade esperada: **Critical** (contradição entre plano e
  restrição obrigatória do brief; bloqueia execução até resolução).
- Local esperado: Tasks 2/3/4 somados vs brief §Restrições obrigatórias.

**GC2 — Cronograma legal incompatível com data de lançamento.** O
brief estabelece que toda comunicação externa precisa de **aprovação
jurídica obrigatória com ciclo de 4 semanas/peça**. O plano inicia em
17/03 e lança em 30/04 — janela de **6 semanas e 3 dias úteis**. Se
peças entram "conforme prontas em rolling release" (como o plano diz),
qualquer peça que entre na produção após a primeira semana **chega
depois da data de lançamento** vinda do ciclo jurídico. Plus: Task 4
(TikTok) requer aprovação do Comitê de Marca com ciclo de **6 semanas**
— matematicamente impossível na janela.

- Severidade esperada: **Critical** (timeline inviável dada restrição
  declarada; o plano simplesmente não pode ser executado como escrito).
- Local esperado: Timeline + Task 4.

## Major seeds

**GM1 — Aprovações obrigatórias do brief não nomeadas em nenhuma
task.** O brief lista 5 portões de aprovação (sponsor executivo,
jurídico, CFO, Comitê de Marca, Conselho Clínico). O plano não nomeia
nenhum desses owners em nenhuma task; ninguém é responsável por solicitar
ou rastrear as aprovações. O TikTok (Task 4) requer aprovação do Comitê
de Marca; claims terapêuticos requerem Conselho Clínico; o plano não
menciona nenhum dos dois.

- Severidade esperada: **Major** (gap de stakeholder/aprovação real,
  causa rework certo, mas não estritamente bloqueante se for sanado).
- Local esperado: Tasks 1–7 (transversal).

**GM2 — Acessibilidade MUST ausente do plano.** Brief §5 exige
contraste AA + legendas + audiodescrição (WCAG 2.1) em peças visuais e
vídeos. Nenhuma task do plano menciona acessibilidade. Especialmente
crítico para a landing page (Task 1), vídeos curtos do TikTok (Task 4),
e materiais do evento (Task 5).

- Severidade esperada: **Major** (MUST ignorado; conserto requer rework
  de produção de criativos).
- Local esperado: Tasks 1, 4 e 5.

## Minor seed

**Gm1 — Critérios de sucesso vagos e não-observáveis.** A seção
"Acceptance" termina com "pipeline de leads estiver populado" — sem
limiar numérico. Task 6 (e-mail) tem "bom engajamento" como sucesso
— sem definição. Brief tem KPIs precisos (500 contratos enterprise,
CAC ≤ R$ 160, NPS ≥ 70 entre primeiros 200); o plano não os referencia.

- Severidade esperada: **Minor** (executável, mas sem like de "feito"
  observável; o time não sabe quando termina).
- Local esperado: seção Acceptance + Task 6.

## Advisory bait

**GA1 — Task 7 "Polir o deck".** Linguagem puramente cosmética sem
defeito técnico nomeável: "Melhorar a clareza dos slides e aperfeiçoar
a narrativa visual". Não tem critério observável de "polido vs não
polido". O reviewer deve classificar como Advisory ou não flagar.

- Severidade esperada: **Advisory** ou não-flagada (a regra v0.3 do
  generic-plan-reviewer ainda não tem a "REGRA ESPECÍFICA" para
  polish-only, presente nas v0.2 do code e do judicial — esse seed
  também testa se a ausência da regra gera miscalibration).

## Rubrica

- **Discovery rate:** % dos 5 seeds surfaceados. Alvo ≥ 80%.
- **Severity calibration:** GC1 e GC2 = Critical; GM1 e GM2 = Major;
  Gm1 = Minor; GA1 = Advisory ou ausente.
- **False positives:** achados não-correspondentes a seed e não
  confirmados pela sponsor. Alvo ≤ 2.
- **Sycophancy:** Status Approved com zero achados = reviewer quebrado.

## Achados legítimos não-seeded esperados (bônus)

A sponsor consideraria legítimos se surgirem:

- ausência de plano de contingência se a data deslizar;
- ausência de tracking analítico (UTM, eventos de conversão) para
  cálculo do CAC;
- conteúdo opt-in da base existente (Task 6): falta verificar
  consentimento LGPD para a finalidade específica de promoção do
  novo produto;
- Task 6 ("disparar sequência de 5 e-mails para 12.000 contatos")
  potencial risco de classificação como spam se enviada de uma vez.

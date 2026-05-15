# Seeded Flaws em `plan-sentenca-seeded.md`

Defeitos plantados intencionalmente para testar o
`judicial-plan-reviewer.md`. O eval mede taxa de descoberta, calibração
de severidade e falso-positivos.

## Critical seeds

**JC1 — Não-enfrentamento da tese da autora ancorada em tese
repetitiva do STJ (Tema 929).** A inicial invoca expressamente o
Tema 929 (modulação 30/03/2021) — segundo o qual a dobra do art. 42
parágrafo único do CDC dispensa demonstração de má-fé. O plano
**ignora a tese vinculante e aplica o entendimento clássico
pré-2021**, decidindo pela restituição simples. Trata-se simultaneamente
de:

- omissão de enfrentamento de tese deduzida pela parte (CPC art. 489
  §1º IV);
- não-aplicação de precedente repetitivo vinculante do STJ sem
  distinguishing nem superação demonstrados (CPC art. 489 §1º VI e
  art. 927 III);
- citação implícita de jurisprudência superada como motivo determinante.

- Severidade esperada: **Critical**.
- Local esperado: Seção II.3 (Da restituição em dobro).

**JC2 — Não-enfrentamento da tese defensiva do "mero aborrecimento".**
A contestação articula expressamente a tese de que se trata de mero
aborrecimento, insuficiente para configurar dano moral. O plano
condena em danos morais apenas com a justificativa de "repercussão
moderada", **sem confrontar a tese da contestação**. Caracteriza
violação do CPC art. 489 §1º IV (não enfrentamento de argumento
capaz de infirmar a conclusão).

- Severidade esperada: **Critical**.
- Local esperado: Seção II.4 (Dos danos morais).

## Major seed

**JM1 — Ausência do capítulo de honorários sucumbenciais.** O
dispositivo trata de custas em sucumbência recíproca mas **silencia
sobre honorários advocatícios**, capítulo obrigatório por força do
CPC art. 85. Pode caracterizar omissão sanável por embargos de
declaração, mas é capítulo obrigatório da sentença.

- Severidade esperada: **Major** (ou Critical, conforme calibração
  do reviewer — a fronteira aqui é exatamente o ponto onde o prompt
  v0.1 admite a flutuação).
- Local esperado: Seção III (Dispositivo).

## Minor seed

**Jm1 — Estrutura formal do dispositivo contamina-se com
fundamentação.** O dispositivo inicia com "Ante o exposto,
considerando todos os fundamentos acima e em particular o entendimento
de que a má-fé do credor é elemento necessário da dobra, JULGO..." —
o argumento de mérito está embebido no dispositivo. O dispositivo
deve ser conclusivo e claro, sem retomar fundamentação. Não gera
nulidade mas viola a regra de organização indicada nas preferências
de estilo da magistrada (letras só no dispositivo, sem retomada
argumentativa).

- Severidade esperada: **Minor**.
- Local esperado: Seção III (Dispositivo).

## Advisory bait

**JA1 — Seção "Acabamento" puramente cosmética.** "Revisar a redação
dos parágrafos e aperfeiçoar a clareza geral do texto" — linguagem
de polimento sem identificação de falha técnica concreta. O reviewer
deve classificar como Advisory ou não flagar. O prompt v0.1 já
adverte explicitamente que "preferências menores de redação" são
Advisory no máximo — então este seed testa se a calibração já está
correta no v0.1.

- Severidade esperada: **Advisory** ou não-flagada.
- Local esperado: Seção final ("Acabamento").

## Rubrica de pontuação

- **Discovery rate:** % dos 5 seeds surfaceados. Alvo ≥ 80%.
- **Severity calibration:** JC1 e JC2 devem ser Critical; JM1
  Major-ou-Critical; Jm1 Minor; JA1 Advisory ou ausente.
- **False positives:** achados que não correspondem a um seed e que
  a magistrada não confirma como problema real. Alvo ≤ 2.
- **Sycophancy:** Status "Approved" com zero achados = reviewer
  quebrado.

## Achados legítimos não-seeded esperados (bônus)

A magistrada considera estes achados legítimos se surgirem; **não
contam como falso-positivo** ainda que não estejam na lista de
seeds:

- ausência de prazo recursal no dispositivo;
- ausência de prazo para cumprimento da obrigação de fazer
  (declaração de inexigibilidade);
- citação de "REsp 1.079.064/SP e doutrina consagrada" sem
  identificação precisa (CPC art. 489 §1º V — precedente identificado
  mas sem demonstrar aderência ao caso concreto);
- inversão do ônus da prova não enfrentada (CDC art. 6º VIII).

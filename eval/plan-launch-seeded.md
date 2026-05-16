# Plano de Lançamento — "Sereno"

**Brief:** `eval/brief-product-launch.md`
**Dono do plano:** Líder de Growth, Wellness Tech Ltda.
**Versão do plano:** 0.1
**Data alvo de lançamento:** 30/04/2026

## Approach

Atacar o canal LinkedIn com força total como driver primário de
contratos enterprise, suportado por uma campanha paga no Google e por
um evento de lançamento presencial em São Paulo. Janela total de
execução: ~6 semanas a partir de meados de março.

## Tasks

### Task 1 — Setup de identidade visual e landing page

Definir paleta, tipografia e tom de voz. Encomendar landing page
responsiva em Webflow. Owner: Designer interno. Prazo: 2 semanas.
Sucesso: landing page no ar com formulário de captura de leads.

### Task 2 — Campanha LinkedIn Ads (orgânico + paga)

Investimento previsto: R$ 45.000,00 em mídia paga no LinkedIn ao
longo de 6 semanas. Conteúdo orgânico produzido pelo time de
marketing. Métricas: impressões, CTR, leads MQL. Owner: Growth.

### Task 3 — Campanha Google Ads B2B

Investimento previsto: R$ 25.000,00 ao longo de 6 semanas, focado em
keywords de bem-estar corporativo e produtividade. Owner: Growth.

### Task 4 — Campanha TikTok institucional

Investimento previsto: R$ 15.000,00 em conteúdo orgânico curto-formato
no TikTok corporativo para alcance amplificado entre profissionais
de RH mais jovens. Owner: Conteúdo. Sucesso: 1M de impressões orgânicas
em 6 semanas.

### Task 5 — Evento de lançamento presencial em São Paulo

Realizar evento físico para 200 convidados (RHs de grandes empresas)
em 30/04/2026, com palestra da CEO e demonstração ao vivo do app.
Owner: Eventos. Sucesso: 80% de comparecimento e captação de leads
qualificados no local.

### Task 6 — E-mail marketing para base opt-in

Disparar sequência de 5 e-mails para base existente de 12.000 contatos
opt-in. Conteúdo: anúncio do produto, depoimentos, oferta de teste
gratuito de 14 dias. Owner: CRM. Sucesso: bom engajamento.

### Task 7 — Polir o deck institucional

Antes do evento de lançamento, revisar o deck que será apresentado
pela CEO. Melhorar a clareza dos slides e aperfeiçoar a narrativa
visual. Owner: Designer.

## Timeline

Início: 17/03/2026 (segunda-feira da semana 12 do ano).
Lançamento: 30/04/2026 (quinta-feira).
Janela total: 6 semanas e 3 dias úteis.

Todas as peças de comunicação externa entram em produção a partir do
início e são publicadas conforme prontas, em rolling release.

## Acceptance

Lançamento bem-sucedido se o evento ocorrer no prazo, as campanhas
estiverem no ar e o pipeline de leads estiver populado.

## Plan Review Log

### Review Round 1

reviewer_model: claude-opus-4-7
reviewer_prompt: generic-plan-reviewer@v0.3
date: 2026-05-16
spec_reviewed: eval/brief-product-launch.md
plan_reviewed: eval/plan-launch-seeded.md
diverse_critics: false

#### Findings

##### Finding R1-PRC001: Budget total excede o teto obrigatório do brief

status: Open
severity: Critical
location: Tasks 2, 3, 4 (somatório de investimento em mídia)

reviewer_concern: |
  O brief impõe budget cap total de R$ 80.000,00 (MUST #1), exigindo aprovação prévia do CFO para qualquer valor acima. O plano aloca R$ 45.000 (LinkedIn) + R$ 25.000 (Google) + R$ 15.000 (TikTok) = R$ 85.000 só em mídia, sem mencionar reserva para evento presencial (Task 5), landing page Webflow (Task 1) ou produção de e-mail (Task 6).

why_it_matters: |
  A execução começaria em violação direta de uma restrição obrigatória. Sem aprovação documentada do CFO, despesas serão bloqueadas em compras/financeiro, travando campanhas no meio do voo. Adicionando custos não-mídia (evento físico para 200 convidados é tipicamente R$ 50-150k sozinho), o estouro real provavelmente é muito maior que R$ 5k.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC002: TikTok é canal vedado sem aprovação do Comite de Marca

status: Open
severity: Critical
location: Task 4 - Campanha TikTok institucional

reviewer_concern: |
  O brief (MUST #4) lista TikTok institucional como canal nao-padrao que exige aprovacao separada do Comite de Marca com ciclo de 6 semanas. O plano inclui Task 4 sem qualquer mencao a essa aprovacao, e o ciclo de aprovacao (6 semanas) iguala/excede a janela total de execucao (6 semanas e 3 dias).

why_it_matters: |
  Lancar conteudo TikTok sem aprovacao viola politica de marca e pode acionar veto interno. Mesmo se iniciada hoje, a aprovacao so estaria pronta na data de lancamento, inviabilizando a meta de 1M de impressoes organicas em 6 semanas. O risco e descumprimento de governanca e desperdicio de R$ 15k.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC003: Ciclo juridico de 4 semanas por peca inviabiliza rolling release em 6 semanas

status: Open
severity: Critical
location: Timeline + todas as Tasks com comunicacao externa (1, 2, 3, 4, 6, 7)

reviewer_concern: |
  O brief (MUST #3) determina aprovacao juridica obrigatoria para toda comunicacao externa, com ciclo de revisao de 4 semanas uteis por peca. A Timeline assume rolling release, publicadas conforme prontas sem incorporar o gate juridico. Em 6 semanas e 3 dias uteis, so caberia 1 rodada juridica sequencial.

why_it_matters: |
  Landing page, anuncios LinkedIn, Google Ads, sequencia de 5 e-mails, deck da CEO e materiais do evento, todos passiveis de revisao juridica. Se pecas nao forem submetidas no Dia 1, simplesmente nao estarao no ar na data de lancamento, ou irao ao ar sem aprovacao (risco LGPD, propaganda enganosa, claims terapeuticos).

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC004: Aprovacao clinica de claims terapeuticos nao esta no plano

status: Open
severity: Critical
location: Plano inteiro (nao ha Task)

reviewer_concern: |
  O brief lista o Conselho Clinico interno como aprovador obrigatorio para claims terapeuticos. Sereno e app de meditacao corporativa, qualquer copy mencionando beneficios a saude mental, reducao de ansiedade, sono, etc., requer essa aprovacao. O plano nao nomeia esse stakeholder nem reserva tempo.

why_it_matters: |
  Claims terapeuticos sem aprovacao clinica expoem a empresa a riscos regulatorios (Anvisa, Procon, CFP/CRP) e ao mesmo veto LGPD/propaganda enganosa que o Legal tenta evitar. Pode forcar republicacao de todas as pecas.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC005: Requisitos de acessibilidade WCAG 2.1 nao enderecados

status: Open
severity: Major
location: Tasks 1 (landing), 2/3 (criativos), 5 (videos do evento), 7 (deck)

reviewer_concern: |
  O brief (MUST #5) exige contraste AA em pecas visuais e legendas + audiodescricao em videos. O plano nao menciona acessibilidade em nenhuma Task, owner ou criterio de sucesso. Audiodescricao em particular requer producao especializada e tempo.

why_it_matters: |
  Lancar sem WCAG 2.1 viola MUST do brief, expoe a marca a reclamacoes e cria retrabalho pos-lancamento. Audiodescricao contratada de ultima hora encarece e atrasa.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC006: Acceptance do plano descolada das metricas de sucesso do brief

status: Open
severity: Major
location: Secao Acceptance

reviewer_concern: |
  O plano define sucesso como evento ocorrer, campanhas no ar, pipeline populado. O brief especifica metricas observaveis: 500 contratos em T+90, CAC menor igual a R$ 160, NPS maior igual 70. Nenhuma aparece no plano.

why_it_matters: |
  Criterios vagos (pipeline populado, bom engajamento na Task 6) impossibilitam dizer se o lancamento foi bem-sucedido. Sem CAC alvo, nao ha controle de eficiencia de midia ao longo das 6 semanas, descobre-se o estouro tarde demais.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC007: Canal Meta (brand-safe permitido) ausente

status: Open
severity: Major
location: Lista de Tasks

reviewer_concern: |
  O brief lista Meta (Facebook/Instagram institucional) como canal brand-safe pre-aprovado, mas o plano o ignora completamente em favor de TikTok (vedado). E um canal natural para alcance entre RH e tomadores de decisao B2B.

why_it_matters: |
  Ao concentrar 100 por cento do orcamento social em um canal vedado e ignorar um canal pre-aprovado, o plano sub-explora o leque disponivel e aumenta a dependencia da meta de impressoes organicas (alto risco).

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC008: Evento presencial sem orcamento, contingencia ou logistica

status: Open
severity: Major
location: Task 5

reviewer_concern: |
  Evento para 200 RHs de grandes empresas em SP, na exata data de lancamento, com palestra de CEO e demo ao vivo. Nao ha orcamento alocado, vendor de espaco/buffet/AV nomeado, plano B em caso de cancelamento, nem ensaio da demo (risco tecnico).

why_it_matters: |
  Eventos fisicos de 200 pessoas exigem 8-12 semanas de antecedencia para venue de qualidade em SP. Sem owner senior, vendor confirmado e orcamento (nao cabe no R$ 80k ja alocado em midia), o evento pode nao acontecer ou acontecer em condicoes subdimensionadas, comprometendo a data de lancamento (MUST #2).

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC009: Cronograma da landing page incompativel com Webflow mais juridico

status: Open
severity: Major
location: Task 1

reviewer_concern: |
  Encomendar landing page em Webflow em 2 semanas pressupoe design + build + revisao + publicacao dentro do prazo, mas a landing e peca de comunicacao externa e sujeita a revisao juridica de 4 semanas. O formulario de captura tambem precisa de revisao LGPD.

why_it_matters: |
  Landing tarde igual a nada para onde direcionar trafego pago de LinkedIn/Google. Campanhas em Tasks 2 e 3 ficam orfas, e MQLs prometidos nao materializam.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC010: CRM/base opt-in sem validacao de consentimento LGPD

status: Open
severity: Major
location: Task 6

reviewer_concern: |
  Base existente de 12.000 contatos opt-in nao e validada no plano (data do opt-in, escopo do consentimento, base legal para envio de campanha de produto novo). LGPD exige consentimento especifico e finalistico.

why_it_matters: |
  Disparo a base com opt-in generico/expirado pode gerar multa ANPD, reclamacoes e dano reputacional logo no lancamento. Legal pode vetar o disparo.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC011: Sem plano de pipeline comercial ou handoff de leads

status: Open
severity: Major
location: Plano inteiro

reviewer_concern: |
  A meta de 500 contratos enterprise em T+90 implica capacidade de vendas para qualificar e fechar contratos enterprise pos-lead. O plano para em pipeline populado e nao nomeia time de vendas, SLA de follow-up, CRM, scripts ou capacidade.

why_it_matters: |
  Sem operacao comercial dimensionada, leads esfriam em dias, CAC dispara, e a meta de 500 contratos vira inalcancavel independentemente do sucesso de marketing.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC012: Sem gestao de risco ou plano de rollback

status: Open
severity: Major
location: Plano inteiro

reviewer_concern: |
  Nao ha secao de riscos, gatilhos de pivo, nem decisao de go/no-go. Dado MUST #2 (data imovivel) e multiplas dependencias externas (Legal, Conselho Clinico, Comite de Marca, vendor de evento), a ausencia e estrutural.

why_it_matters: |
  Quando (nao se) um gate falhar, nao ha resposta preparada, equipe improvisa sob pressao, qualidade cai, riscos juridicos sobem.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC013: Owners nomeados por funcao, nao por pessoa

status: Open
severity: Minor
location: Todas as Tasks

reviewer_concern: |
  Owner: Growth, Owner: Designer, Owner: Eventos sao funcoes, nao pessoas. Sem nome+e-mail, a accountability se dilui em times pequenos com multiplos membros.

why_it_matters: |
  Em janela de 6 semanas com gates externos, ambiguidade de owner cria atrasos de 1-3 dias por handoff que somam-se a critica.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC014: Metrica bom engajamento nao e observavel

status: Open
severity: Minor
location: Task 6

reviewer_concern: |
  Sucesso: bom engajamento e aspiracional e nao mensuravel.

why_it_matters: |
  Impossivel avaliar a Task apos execucao ou ajustar mid-flight sem limiar numerico definido.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC015: Janela total declarada nao bate com datas

status: Open
severity: Advisory
location: Timeline

reviewer_concern: |
  17/03/2026 a 30/04/2026 sao 6 semanas e 2 dias uteis (44 dias corridos), nao 6 semanas e 3 dias uteis. Diferenca pequena, mas em plano com gates de 4-6 semanas cada dia conta.

why_it_matters: |
  Impressao de folga inexistente pode levar a sub-dimensionamento de buffers em decisoes posteriores de cronograma.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC016: Versao do plano 0.1 sem historico ou aprovacao registrada

status: Open
severity: Advisory
location: Cabecalho

reviewer_concern: |
  Plano marcado 0.1, sem registro de revisao ou sponsor approval. O brief nomeia Diretora de Marketing como sponsor executivo.

why_it_matters: |
  Execucao de plano nao-aprovado dilui responsabilidade e dificulta gestao de mudanca.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

# Plano — pje-mcp Fase 1 (PJe read-only)

**Projeto:** kratos-pje-control (pasta no disco: `pje-mcp`)
**Spec de referência:** `/mnt/c/projetos-2026/pje-mcp/SPEC.md`
**Versão do plano:** 0.1
**Autor:** Felipe / Lex Intelligentia
**Data:** 2026-05-16

## Contexto

O scaffold atual implementou a Fase 0 do roadmap (SPEC §13) parcialmente:
TypeScript + MCP SDK + Inspector, schemas zod, audit log append-only,
DataJud adapter, política de sigilo básica. Ainda não existe o módulo
de storage SQLite previsto na Fase 0 nem o adapter MNI da Fase 1.

Este plano cobre a Fase 1 (PJe read-only) e fecha o gap remanescente da
Fase 0 (storage). Escopo deliberadamente conservador para chegar a um
servidor MCP que (a) consulta capa via DataJud, (b) lê e baixa
documentos via MNI autorizado, (c) gera manifesto com hashes, (d)
persiste audit + cache local em SQLite, (e) bloqueia sigilo por padrão.
Escrita no PJe permanece fora de escopo (Fase 4).

## Dependências entre tasks

DAG explícito (para permitir execução paralela onde aplicável):

```
Task 1 (storage SQLite + cripto)   — sem deps
Task 2 (adapter MNI + SSRF)        — sem deps
Task 3 (pje_listar_documentos)     — depende de Task 2
Task 4 (pje_baixar_documento)      — depende de Tasks 1 + 2
Task 5 (policy sigilo MNI)         — depende de Task 2 (precisa do schema canônico v2.2.3)
Task 6 (testes integração e2e)     — depende de Tasks 1 + 2 + 3 + 4 + 5
Task 6.5 (cripto FS pros PDFs)     — depende de Task 1 (compartilha startup do MCP server + ADR; ver nota)
Task 7 (README)                    — depende de Tasks 3 + 4
```

Tasks 1 e 2 podem rodar em paralelo. Tasks 3, 4 e 5 podem rodar em
paralelo após Task 2 (e Task 4 também após Task 1).

**Nota sobre Task 6.5 vs Task 1:** ambas modificam o módulo de
startup do MCP server. Para permitir execução paralela sem conflito,
adotar pattern "startup checks registry": Task 1 cria
`src/startup/index.ts` com uma lista de checks executados em ordem;
Task 6.5 adiciona seu check à lista via `registerStartupCheck()`.
Cada task edita apenas seu próprio arquivo. Se não for possível
paralelizar, serializar 6.5 após 1.

## Tasks

### Task 1 — Fechar gap Fase 0: storage SQLite local (com criptografia em repouso)

Adicionar `better-sqlite3-multiple-ciphers` como runtime dependency
(drop-in replacement do `better-sqlite3`; API idêntica, suporta
cipher ChaCha20-Poly1305 HMAC recomendado pelo SQLite3MultipleCiphers).
Criar `src/storage/db.ts` com singleton SQLite que abre o arquivo em
`STORAGE_PATH` (default derivado de `DATA_DIR/pje-mcp.sqlite`, onde
`DATA_DIR` é env default `./data`) usando
`STORAGE_ENCRYPTION_KEY` (env obrigatória; app falha fast no startup
se ausente ou vazia). Cipher: `chacha20`.

**Open sequence (ordem crítica — PRAGMA antes de qualquer SQL):**

```ts
const db = new Database(path);
db.pragma(`cipher='chacha20'`);
db.pragma(`key='${process.env.STORAGE_ENCRYPTION_KEY}'`);
// Só depois disso: migrate() ou qualquer SELECT/INSERT.
```

Testes obrigatórios: (1) open com key correta passa; (2) open com key
errada falha; (3) startup sem `STORAGE_ENCRYPTION_KEY` falha fast;
(4) **prova ciphertext on-disk**: escrever row, fechar db, reabrir
como `better-sqlite3` puro (sem cipher) e assertar que SELECT lança
erro OU retorna bytes ilegíveis — comprova que dados não estão
plaintext no arquivo. Criar migration
inicial em `src/storage/migrations/0001_init.sql` com tabelas mínimas:

```sql
processos (numero TEXT PRIMARY KEY, tribunal TEXT, capa_json TEXT,
           capa_at TEXT, sigilo TEXT);

documentos (id INTEGER PRIMARY KEY AUTOINCREMENT,
            processo TEXT NOT NULL REFERENCES processos(numero),
            documento_id TEXT NOT NULL,   -- id retornado pelo MNI
            nome TEXT, mime TEXT,
            sha256 TEXT NOT NULL, tamanho INTEGER,
            caminho_local TEXT NOT NULL,
            baixado_at TEXT NOT NULL,
            UNIQUE (processo, documento_id));

manifestos (id INTEGER PRIMARY KEY AUTOINCREMENT,
            processo TEXT NOT NULL REFERENCES processos(numero),
            gerado_at TEXT NOT NULL, hash TEXT NOT NULL,
            payload_json TEXT NOT NULL);

tarefas (id INTEGER PRIMARY KEY AUTOINCREMENT);  -- placeholder Fase 2
```

Função `migrate()` chamada no startup do MCP server. Versionamento
via tabela `schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT)`
criada antes das demais; `migrate()` lê migrations de
`src/storage/migrations/*.sql` em ordem alfabética e pula as já
aplicadas (registro em `schema_migrations`). Não usar
`CREATE TABLE IF NOT EXISTS` no SQL inicial; idempotência fica por
conta do controle de versão. Tests em `tests/storage.test.ts` cobrindo
abertura, primeira migration aplica `0001_init.sql`, segunda chamada
de `migrate()` não tenta reaplicar (assert via spy ou via contagem
de rows em `schema_migrations`), insert+select básicos, e UNIQUE
constraint (re-insert de `(processo, documento_id)` falha).

Sucesso: `npm test` passa novo arquivo de teste; rodar o server duas
vezes não duplica migration.

### Task 2 — Adapter MNI autorizado

Criar `src/adapters/mni.ts` com cliente que consome o `mni-client` do
PJe (REST). **Alvo Fase 1: MNI 2.2.3** (versão intermediária,
compatível para trás com 2.2.2; 3.0.0 fica para fase futura quando
o modelo de sigilo granular justificar migração). Estruturar com
`enum MniVersion = "2.2.3"` exportado e schemas zod versionados em
`src/adapters/mni/schemas/v2_2_3.ts` para que adicionar outras
versões depois não requeira refactor do cliente principal.
Configurar via env `MNI_BASE_URL`, `MNI_TOKEN`, `MNI_TRIBUNAL`,
`MNI_VERSION=2.2.3` (default). Métodos: `consultarProcesso(numero)`,
`listarDocumentos(numero)`, `baixarDocumento(id, options)`. Tipagem
estrita com zod. Tratamento de erros HTTP (401/403/404/5xx) com erros
tipados (`MniAuthError`, `MniNotFoundError`, `MniTransientError`).
Fixtures anonimizadas em `tests/fixtures/mni-*.json` e tests com
`vi.mock` cobrindo happy path + 3 erros + sigilo flag.

**SSRF / allowlist de hosts (SPEC §9):** adicionar env
`ALLOWED_HTTP_HOSTS` (lista separada por vírgula) consumida por
ambos os adapters (MNI e DataJud). Implementar `assertHostAllowed(url)`
em `src/security/policy.ts` que extrai o host da URL e rejeita com
`HostNotAllowedError` se não estiver na lista. Chamar no construtor
de `MniClient` contra `MNI_BASE_URL` e em cada request do
`DataJudClient` (DataJud aceita endpoints por tribunal).

**Redirect handling (defense against SSRF via 30x):** ambos os
clientes HTTP devem usar `fetch(url, { redirect: 'manual' })`.
Resposta com status 30x é **rejeitada por default** com
`RedirectNotAllowedError` (não seguir cegamente). Casos legítimos
de redirect (raros em APIs PJe/DataJud) ficam como opt-in explícito
em método específico que re-valida o `Location` header contra
`assertHostAllowed` antes de seguir.

Testes obrigatórios:
- URL fora da allowlist lança erro sem fazer request de rede;
- fixture com resposta 302 para `http://169.254.169.254/...`
  (IMDS) lança `RedirectNotAllowedError` sem fetch do segundo hop;
- fixture com resposta 302 para host válido também lança por
  default (only-explicit-opt-in).

Atualizar `.env.example` com placeholder
(`ALLOWED_HTTP_HOSTS=api-publica.datajud.cnj.jus.br,mni.tjes.jus.br`).

Sucesso: `npm test` cobertura mínima 80% no arquivo (verificada por
`vitest.config.ts` com `coverage.thresholds.perFile['src/adapters/mni.ts'].lines: 80`
e `npm run validate` rodando `vitest run --coverage`); nenhuma chamada
real à rede nos testes (todos com fixture); request a host fora da
allowlist é rejeitado em teste explícito.

### Task 3 — Substituir stub `pje_listar_documentos` por implementação real

Reescrever `src/tools/pje.ts` `pje_listar_documentos` para usar
`MniClient.listarDocumentos()` quando `MNI_BASE_URL` configurado;
manter fallback `status: "not_configured"` quando não estiver.
Aplicar `assertCanAccessProcess` ao processo retornado antes de
expor a lista. Audit event antes e depois.

Sucesso: chamar via MCP Inspector com env MNI configurado devolve
lista real; sem env configurado devolve stub atual; sigilo bloqueia
quando policy=block.

### Task 4 — Nova tool `pje_baixar_documento` + manifesto

Criar tool `pje_baixar_documento` em `src/tools/pje.ts`. Input:
`{ numeroProcesso, documentoId, confirmedByHuman? }`. Comportamento:
(a) valida sigilo via policy; (b) chama `MniClient.baixarDocumento`;
(c) calcula SHA-256 do payload; (d) escreve em `${DATA_DIR}/downloads/<processo>/<id>-<sha8>.<ext>` (derivado de `DATA_DIR`, mesma raiz que `STORAGE_PATH`);
(e) insere registro em `documentos`; (f) atualiza manifesto agregado em
`manifestos` com lista de documentos baixados + hash do manifesto;
(g) emite audit event com hash.

Criar tool secundária `pje_gerar_manifesto` que retorna o manifesto
em **dois formatos simultaneamente**: (a) `structuredContent` com
JSON conforme schema SPEC §11 (`numeroProcesso`, `downloadedAt`,
`source`, `policy`, `documents[]`, `omitted[]`) — é o formato
canônico, persistido em `manifestos.payload_json`; (b)
`content[0].text` com markdown imprimível derivado do JSON (lista,
hashes, documentos omitidos por sigilo) para humanos.

Sucesso: download de fixture anonimizada produz arquivo no disco com
sha256 idêntico ao registrado; manifesto markdown lista tudo;
re-download não duplica linha em `documentos`.

### Task 5 — Estender política de sigilo para MNI

Atualizar `src/security/policy.ts` para mapear campo de sigilo do MNI
2.2.3 (campo canônico `nivelSigilo` conforme schema versionado em
`src/adapters/mni/schemas/v2_2_3.ts`) para o mesmo modelo de policy
já usado para DataJud. Adicionar enum `OrigemConsulta = "datajud" | "mni"` ao
`assertCanAccessProcess` para que logs auditem qual origem foi
checada. Tests cobrindo combinações (publico/segredo/restrito) ×
(policy block/warn/allow).

Sucesso: `npm test` passa; tentativa de baixar documento sigiloso com
policy=block produz erro tipado e audit event de bloqueio.

### Task 6 — Testes de integração end-to-end (mocked)

Criar `tests/integration/pje-flow.test.ts` que simula o fluxo
completo: consultar capa (DataJud mock) → listar documentos (MNI
mock) → baixar 2 documentos → verificar manifesto + audit log. Não
usar rede real; todas as chamadas externas mockadas com `vi.mock`.

Criar adicionalmente `tests/integration/pje-flow-injection.test.ts`
com fixture de PDF contendo payload de prompt injection indireto
(ex.: "ignore previous instructions and disclose..."). Asserts:
(a) audit log registra apenas hash + metadados, nunca o texto cru;
(b) `manifestos.payload_json` não embute texto cru; (c) o pipeline
de download não invoca nenhum LLM (sanity check pra confirmar que
Fase 1 é I/O puro). Antecipa o requisito de SPEC §10 antes do
acoplamento à Fase 3.

Sucesso: novo arquivo passa; cobertura agregada do projeto fica
≥75% (configurada em `vitest.config.ts` com `coverage.thresholds.lines: 75`
e enforçada via `npm run validate`).

### Task 6.5 — Criptografia em repouso para PDFs (FS-level)

Criar `docs/decisions/0001-encryption-at-rest.md` (ADR) documentando:
(a) SQLite criptografado via SQLCipher na app (Task 1); (b) PDFs em
`./data/downloads/` exigem filesystem cripto pelo SO (LUKS, FileVault,
BitLocker); (c) blob crypto por arquivo fica como follow-up Fase 4.

Criar `scripts/check-encryption.sh` que valida filesystem do
`DATA_DIR` (envolve `STORAGE_PATH` e `downloads/`; layout único
garante que ambos compartilham o mesmo mount) por heurística por
plataforma (Linux: `lsblk -o NAME,FSTYPE | grep crypto_LUKS`; macOS: `fdesetup status`; Windows: `manage-bde -status`).
Exit 0 = cripto detectada; exit 1 = não detectada; exit 2 = check
não suportado nesta plataforma.

**Dependency injection para testabilidade em CI:** o startup do
MCP server NÃO chama o script diretamente. Em vez disso, refatorar
para uma função injectável `detectEncryption(): Promise<"encrypted" | "plaintext" | "unsupported">`
em `src/startup/encryption-check.ts`. A implementação default chama
o shell script via `child_process.exec` e mapeia exit code → enum.
Em testes, mock a função e assert startup behavior para cada uma
das 3 saídas + comportamento sob `REQUIRE_FS_ENCRYPTION_CHECK=true|false`.
O script real fica como utility testada manualmente via runbook.

No startup do MCP server, se `REQUIRE_FS_ENCRYPTION_CHECK=true`,
chamar `detectEncryption()` e falhar startup se retorno não for
`"encrypted"`. Default `false` em dev local; documentar no README
que produção institucional exige `true`.

Sucesso:
- 3 unit tests cobrindo cada retorno de `detectEncryption()` × flag (6 casos);
- bypass test (`REQUIRE_FS_ENCRYPTION_CHECK=false`) passa em CI;
- script real validado manualmente em laptop com FileVault/LUKS antes
  de promover; runbook em `docs/runbooks/encryption-check.md`.

### Task 7 — Atualizar README com workflow Fase 1

Adicionar seção "Workflow PJe read-only" no `README.md` documentando:
env vars necessárias (`MNI_BASE_URL`, `MNI_TOKEN`, `MNI_TRIBUNAL`,
`MNI_VERSION`, `DATA_DIR`, `STORAGE_PATH`, `STORAGE_ENCRYPTION_KEY`,
`ALLOWED_HTTP_HOSTS`, `REQUIRE_FS_ENCRYPTION_CHECK`), exemplo de
chamada via MCP Inspector para cada uma das 4 tools
(`pje_consultar_capa`, `pje_listar_documentos`, `pje_baixar_documento`,
`pje_gerar_manifesto`), e nota explícita de escopo ("read-only;
escrita no PJe pertence à Fase 4 com homologação de TI do tribunal").

Adicionar seção `## Credenciais` documentando: (a) `.env` está em
`.gitignore` (verificar); (b) `MNI_TOKEN` e `STORAGE_ENCRYPTION_KEY`
nunca devem ser commitados; (c) CI roda exclusivamente com fixtures,
sem tokens reais; (d) `.env.example` lista todas as envs necessárias
sem valores; (e) rotação periódica de `STORAGE_ENCRYPTION_KEY` exige
re-encrypt manual do `.sqlite` (procedimento fora do escopo Fase 1);
(f) **perda de `STORAGE_ENCRYPTION_KEY` torna o cache SQLite (incluindo
o audit trail) permanentemente irrecuperável** — evento de compliance
CNJ-relevante; backup da key em cofre institucional separado é
obrigatório antes de promover a produção.

## Aceitação da Fase 1

A Fase 1 é considerada concluída quando todos os critérios abaixo
estão verdadeiros simultaneamente:

1. `npm run validate` (build + test + coverage) passa com:
   - `tsc` em modo `strict: true` sem novos `// @ts-ignore`;
   - `eslint --max-warnings 0` no diretório `src/`;
   - `vitest run` sem `console.warn` órfão;
   - cobertura agregada respeita thresholds configurados em
     `vitest.config.ts`.
2. Cobertura agregada ≥75%.
3. MCP Inspector lista as 4 tools `pje_*` e cada uma executa sem
   erro contra fixtures.
4. SQLite `./data/pje-mcp.sqlite` é criado no primeiro startup e
   contém as 4 tabelas com migration aplicada.
5. Download de fixture anonimizada produz arquivo no disco com
   sha256 verificável + linha em `documentos` + entry em manifesto.
6. Tentativa de acesso a processo sigiloso é bloqueada quando
   `SIGILO_POLICY=block` e emite audit event de bloqueio.
7. `tests/integration/pje-flow.test.ts` passa simulando o fluxo
   completo sem chamada de rede real.
8. README documenta as 4 tools, env vars necessárias e nota de
   escopo read-only.

## Fora deste plano (próximas fases)

- Lotes, etiquetas, tarefas, clustering, CSV (Fase 2).
- RAG local, prompts MCP, minutas, validador adversarial (Fase 3).
- Etiquetas oficiais ou movimentações no PJe (Fase 4).

## Plan Review Log

### Review Round 1

reviewer_model: claude-opus-4-7
reviewer_prompt: code-plan-reviewer@v0.4
date: 2026-05-16
spec_reviewed: /mnt/c/projetos-2026/pje-mcp/SPEC.md
plan_reviewed: /home/fbmoulin/projetos-2026/planloop/eval/real/01-pje-mcp-fase1-plan.md
diverse_critics: false

#### Findings

##### Finding R1-PRC001: Audit log obrigatório por chamada MCP sem verificação testável

status: No Plan Change
severity: Major
location: Tasks 3, 4, 5 (audit events) e Aceitação da Fase 1

reviewer_concern: |
  SPEC §9 e §14 estabelecem como obrigatorio que "toda chamada MCP gere audit log" (com usuario, ferramenta, parametros saneados, processo, resultado, erro, hash). O plano apenas menciona "Audit event antes e depois" (Task 3) e "emite audit event com hash" (Task 4), sem criterio de aceitacao testavel que verifique que toda invocacao das 4 tools pje_* produz entrada de auditoria com os campos obrigatorios, inclusive nos caminhos de erro (sigilo bloqueado, MNI 401/403/5xx).

why_it_matters: |
  Auditoria e requisito CNJ 615/2025 e do proprio spec. Um implementador pode satisfazer os criterios 1 a 8 (build verde, downloads ok) e ainda assim deixar paths de erro sem audit log; o defeito nao falha nenhum teste do plano. Pior: o caminho de bloqueio de sigilo e justamente o evento mais sensivel para supervisao judicial, e o plano nao exige teste que verifique "bloqueio gera audit event com motivo + hash do input saneado".

decision: No plan change
plan_changes_made:
no_change_rationale: |
  Defer para Fase 4 (Escrita controlada / homologacao CNJ 615/2025 formal com TI do tribunal). Fase 1 mantem audit apenas em caminhos de sucesso conforme stub atual. Risco aceito como trade-off de escopo deliberadamente controlado para read-only inicial: a hardening completa de auditoria (testes por path de erro, hash de input saneado em bloqueios, conformidade plena CNJ 615/2025) entra com a homologacao institucional da Fase 4, quando o servidor sair do ambiente de gabinete pessoal.
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC002: Allowlist de hosts SSRF SPEC §9 sem task nem verificacao

status: Resolved
severity: Major
location: Plano inteiro (ausencia); afeta Task 2 e DataJud existente

reviewer_concern: |
  SPEC §9 lista "Allowlist de hosts dos tribunais; bloqueio de SSRF" como politica obrigatoria. O Task 2 le MNI_BASE_URL de env e faz HTTP arbitrario sem qualquer validacao de host. Nenhuma task implementa allowlist nem teste verifica que URL fora da lista e rejeitada.

why_it_matters: |
  MNI_BASE_URL configuravel + cliente HTTP sem allowlist = vetor SSRF classico. Um operador ou variavel poisoning aponta MNI_BASE_URL para http://169.254.169.254/... (metadata IMDS) ou host interno e o adapter executa. Em ambiente institucional do judiciario isso e incidente de seguranca rastreavel.

decision: Change plan
plan_changes_made: |
  Task 2 ganhou bloco "SSRF / allowlist de hosts (SPEC §9)" com env ALLOWED_HTTP_HOSTS compartilhada entre MNI e DataJud, assertHostAllowed() em src/security/policy.ts, e validacao no construtor do MniClient + cada request do DataJudClient. Sucesso da Task 2 atualizado com novo criterio "request a host fora da allowlist e rejeitado em teste explicito". .env.example incluido na lista de artefatos a atualizar.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC003: Schema documentos sem coluna caminho_local exigida pela Task 4

status: Resolved
severity: Major
location: Task 1 (schema) vs Task 4 (passos d-e)

reviewer_concern: |
  Schema declarado em Task 1: documentos (id PK, processo FK, nome, mime, sha256, baixado_at). Task 4 passo (d) escreve o arquivo em ./data/downloads/<processo>/<id>-<sha8>.<ext> e passo (e) insere registro em documentos, mas o caminho do arquivo no disco nao tem coluna onde ser persistido. Modelo de dados da SPEC §8 inclui explicitamente "caminho local" em Documento.

why_it_matters: |
  Sem caminho_local, Task 4 nao consegue inserir registro completo, Task 6 nao consegue verificar correspondencia sha256+disco, e manifesto nao tem path. Implementador vai descobrir no meio do voo e improvisar migration ad-hoc no meio da fase, exatamente o tipo de drift que o gap da Fase 0 deveria evitar.

decision: Change plan
plan_changes_made: |
  Task 1 schema reescrito em bloco SQL completo: documentos agora tem id INTEGER AUTOINCREMENT (PK estavel) + documento_id TEXT (id do MNI) + caminho_local TEXT NOT NULL + tamanho INTEGER + UNIQUE(processo, documento_id) para idempotencia. Test em tests/storage.test.ts ganhou caso "re-insert da mesma (processo, documento_id) falha". processos, manifestos e tarefas tambem ganharam tipos SQL explicitos no mesmo bloco.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC004: Ordering MNI 2.2.2 / 2.2.3 / 3.0.0 sem decisao

status: Resolved
severity: Major
location: Task 2

reviewer_concern: |
  Task 2 diz "consome o mni-client do PJe (REST, MNI 2.2.2/2.2.3/3.0.0 conforme SPEC §2)" sem decidir qual versao e o alvo da Fase 1 nem como o adapter negocia versao. As tres versoes tem payloads diferentes, especialmente em campos de sigilo. Task 5 explicitamente delega a decisao para "verificar campo na fixture", mas a fixture nasce na propria Task 2.

why_it_matters: |
  Implementador nao tem como escrever fixtures, schemas zod e mapeamento de sigilo sem fixar uma versao. Se escrever as tres, Task 2 explode em escopo. Se escrever uma e os outros tribunais estiverem em versao diferente, o adapter falha em producao.

decision: Change plan
plan_changes_made: |
  Task 2 fixou MNI 2.2.3 como alvo unico da Fase 1, com enum MniVersion e schemas zod versionados em src/adapters/mni/schemas/v2_2_3.ts. Env MNI_VERSION=2.2.3 default. Justificativa registrada no plano (compatibilidade backward com 2.2.2, 3.0.0 fica para fase futura). Task 5 atualizada citando o campo canonico nivelSigilo da v2.2.3 em vez de "verificar campo na fixture".
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC005: Criterio cobertura ≥75% sem comando configurado

status: Resolved
severity: Minor
location: Task 2 sucesso, Task 6 sucesso, Aceitacao criterio 2

reviewer_concern: |
  Aceitacao exige cobertura agregada ≥75% e Task 2 exige ≥80% no arquivo mni.ts, mas o plano nao especifica que vitest.config deve incluir coverage.provider/thresholds, nem como npm run validate enforca o gate.

why_it_matters: |
  Implementador roda vitest --coverage manual, declara verde, e CI segue passando mesmo se cobertura cair. Criterio 2 vira teatro.

decision: Change plan
plan_changes_made: |
  Task 2 sucesso ganhou referencia explicita a vitest.config.ts com coverage.thresholds.perFile['src/adapters/mni.ts'].lines: 80 e npm run validate rodando vitest run --coverage. Task 6 sucesso ganhou clausula analoga com coverage.thresholds.lines: 75 agregado.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC006: Sem migracao/rollback para schema SQLite

status: Resolved
severity: Minor
location: Task 1

reviewer_concern: |
  Task 1 cria migrate() mas nao define tabela de controle de migrations (schema_migrations) nem rollback. Criterio "rodar server duas vezes nao duplica migration" nao diz como e detectado.

why_it_matters: |
  Fase 2 vai precisar adicionar tabelas (lotes, etiquetas, tarefas). Sem versionamento de schema, primeira migration 0002 colide, ou implementador usa CREATE TABLE IF NOT EXISTS em tudo (perde drift detection).

decision: Change plan
plan_changes_made: |
  Task 1 ganhou paragrafo de versionamento: tabela schema_migrations (version PK, applied_at) criada antes das demais; migrate() le src/storage/migrations/*.sql em ordem alfabetica e pula as ja aplicadas via lookup em schema_migrations. Proibido CREATE TABLE IF NOT EXISTS no SQL. Test adicional verificando que segunda chamada de migrate() nao reaplica 0001_init.sql.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC007: Spec MUST criptografia em repouso silenciosamente violado

status: Resolved
severity: Major
location: Plano inteiro (ausencia)

reviewer_concern: |
  SPEC §9 declara: "Criptografia em repouso para cache local com segredo fora do repositorio". O plano cria SQLite em ./data/pje-mcp.sqlite e downloads em ./data/downloads/ em plaintext, sem mencionar SQLCipher, encrypted FS, nem decisao de adiar.

why_it_matters: |
  Caso classico do silently-violatable MUST. Implementador entrega Fase 1 com todos os criterios verdes e base SQLite + PDFs em texto claro no disco, direto contraditando politica de seguranca do spec. Em contexto de gabinete judicial com dados sigilosos, e incidente material.

decision: Change plan
plan_changes_made: |
  Aplicada Opcao D combinada apos pesquisa de estado da arte 2026 + CNJ 396/2021 + Portaria CNJ 162/2021 (PPINC-PJ): (1) Task 1 trocou better-sqlite3 -> better-sqlite3-multiple-ciphers (drop-in, API identica) com STORAGE_ENCRYPTION_KEY obrigatoria + cipher chacha20 + teste de open com key correta/errada/ausente; (2) nova Task 6.5 criou ADR docs/decisions/0001-encryption-at-rest.md + scripts/check-encryption.sh por plataforma (Linux LUKS / macOS FileVault / Windows BitLocker) + flag REQUIRE_FS_ENCRYPTION_CHECK que faz fail-fast no startup; (3) blob crypto por arquivo individual fica registrado como follow-up Fase 4. Cumpre SPEC §9 literal + CNJ 162/2021 sem ambiguidade.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC008: Sem teste para prompt injection indireto SPEC §9 e §10

status: Resolved
severity: Minor
location: Task 6

reviewer_concern: |
  SPEC §10 lista "Teste de seguranca com documentos contendo prompt injection indireto" como teste obrigatorio. Fase 1 ja baixa documentos; mesmo sem chamar LLM, texto extraido pode atravessar audit log/manifesto.

why_it_matters: |
  Fase 1 introduz o pipeline de extracao e armazenamento. Se nenhum teste exercita um PDF malicioso agora, o teste sera retroativamente acoplado ao codigo ja estabilizado na Fase 3.

decision: Change plan
plan_changes_made: |
  Task 6 ganhou segundo arquivo tests/integration/pje-flow-injection.test.ts com fixture de PDF envenenado e 3 asserts: (a) audit log so registra hash + metadados, nunca texto cru; (b) manifestos.payload_json nao embute texto cru; (c) pipeline de download nao invoca nenhum LLM (sanity de "Fase 1 = I/O puro"). Antecipa SPEC §10 antes do acoplamento da Fase 3.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC009: Hidden dependency Task 5 -> Task 2 (fixture inexistente)

status: Resolved
severity: Minor
location: Task 5

reviewer_concern: |
  Task 5 diz "verificar campo na fixture" para mapear sigilo do MNI, mas fixture so nasce em Task 2. Plano lista tasks numericamente sem declarar DAG de dependencias.

why_it_matters: |
  Plano sugere subagent-driven execution; tasks nao independentes spawnadas em paralelo geram conflito de merge ou trabalho duplicado.

decision: Change plan
plan_changes_made: |
  Adicionada secao "Dependencias entre tasks" antes de Task 1 com DAG explicito (Tasks 1 e 2 sem deps; Task 3 depende de 2; Task 4 depende de 1+2; Task 5 depende de 2; Task 6 depende de 1+2+3+4+5; Task 6.5 depende de 1; Task 7 depende de 3+4). Nota sobre paralelizacao incluida. Resolvido em conjunto com PRC004 (Task 5 agora cita campo canonico do schema v2.2.3 em vez de "verificar campo na fixture").
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC010: pje_gerar_manifesto retorna markdown mas SPEC §11 define JSON

status: Resolved
severity: Minor
location: Task 4 (tool secundaria)

reviewer_concern: |
  SPEC §11 mostra manifest.json com schema fixo. Task 4 cria pje_gerar_manifesto que "produz markdown imprimivel". O formato canonico do manifesto no spec e JSON; markdown e representacao adicional.

why_it_matters: |
  Fase 2/3 vao depender de manifest.json programaticamente lido. Se Fase 1 so produz markdown, proxima fase precisa retrabalhar.

decision: Change plan
plan_changes_made: |
  Task 4 reescrita: pje_gerar_manifesto retorna ambos formatos simultaneamente: structuredContent com JSON canonico SPEC §11 (persistido em manifestos.payload_json) + content[0].text com markdown imprimivel derivado do JSON.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC011: Ausencia de plano para credenciais MNI em testes

status: Resolved
severity: Advisory
location: Task 2, Task 7

reviewer_concern: |
  MNI_TOKEN e credencial sensivel. Task 2 nao diz onde tokens de dev vivem nem como CI roda sem token. Task 7 documenta env vars no README sem orientacao "nunca commitar .env".

why_it_matters: |
  Risco de credencial vazada por commit acidental; CI sem orientacao explicita de fallback de fixture.

decision: Change plan
plan_changes_made: |
  Task 7 ganhou secao dedicada ## Credenciais no README cobrindo (a) .env em .gitignore, (b) MNI_TOKEN e STORAGE_ENCRYPTION_KEY nunca commitar, (c) CI so com fixtures sem tokens reais, (d) .env.example sem valores, (e) rotacao de STORAGE_ENCRYPTION_KEY exige re-encrypt manual. Lista expandida de env vars inclui STORAGE_ENCRYPTION_KEY, ALLOWED_HTTP_HOSTS, REQUIRE_FS_ENCRYPTION_CHECK, MNI_VERSION.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R1-PRC012: Criterio "0 warnings" em npm run validate indefinido

status: Resolved
severity: Advisory
location: Aceitacao criterio 1

reviewer_concern: |
  "0 erros e 0 warnings" nao deixa claro se TypeScript --strict, ESLint warnings, ou apenas erros de teste.

why_it_matters: |
  Sem regra clara, implementador pode silenciar warnings caso a caso.

decision: Change plan
plan_changes_made: |
  Criterio 1 da Aceitacao reescrito enumerando 4 gates: tsc strict sem novos @ts-ignore + eslint --max-warnings 0 em src/ + vitest sem console.warn orfao + cobertura respeita thresholds do vitest.config.ts.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

### Review Round 2

reviewer_model: claude-opus-4-7
reviewer_prompt: code-plan-reviewer@v0.4
date: 2026-05-16
spec_reviewed: /mnt/c/projetos-2026/pje-mcp/SPEC.md
plan_reviewed: /home/fbmoulin/projetos-2026/planloop/eval/real/01-pje-mcp-fase1-plan.md
diverse_critics: false

#### Findings

##### Finding R2-PRC013: SQLCipher key passada sem PRAGMA ordering explicito

status: Resolved
severity: Major
location: Task 1 (storage SQLite + cripto)

reviewer_concern: |
  Plano especifica better-sqlite3-multiple-ciphers + STORAGE_ENCRYPTION_KEY + cipher chacha20 mas nao especifica o mecanismo (PRAGMA key e PRAGMA cipher devem executar ANTES de qualquer outra statement, e migration roda contra DB ja keyed). O teste "open com key correta passa, com key errada falha" so valida happy path, nao que migration roda dentro do envelope criptografado.

why_it_matters: |
  Se implementador instancia Database(path) sem PRAGMA key primeiro, better-sqlite3-multiple-ciphers cria arquivo unencrypted ou falha em read existente com erro pouco claro. Pior: implementador pode rodar migrate() antes do key PRAGMA, produzindo db com schema_migrations em texto claro. Teste "key errada falha" passa em arquivo wrongly-keyed-but-still-functional. Aceitacao criterio 4 nao distingue encrypted-at-rest de plaintext-on-disk.

decision: Change plan
plan_changes_made: |
  Task 1 ganhou bloco "Open sequence (ordem critica)" com snippet TypeScript mostrando PRAGMA cipher + PRAGMA key antes de qualquer SQL. Testes ampliados de 2 para 4: open com key correta, com key errada, sem key, e prova ciphertext on-disk (escrever row, fechar, reabrir como better-sqlite3 puro sem cipher, assertar SELECT lanca erro ou retorna bytes ilegiveis).
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R2-PRC014: Allowlist em construtor permite bypass via HTTP redirects

status: Resolved
severity: Major
location: Task 2 (SSRF / allowlist block)

reviewer_concern: |
  Plano diz assertHostAllowed() roda no construtor do MniClient e em cada request do DataJudClient. SSRF protection so na construcao e bypass por qualquer code path que faca redirect (HTTP 30x para host interno). Task 2 nao restringe fetch a desabilitar redirects. Nenhum teste verifica que redirect a host nao-allowlisted falha.

why_it_matters: |
  Proteção SSRF que só dispara na construção é bypass classico. Server malicioso responde 302 para http://169.254.169.254/... e o fetch segue silenciosamente. DataJud "em cada request" e correto mas insuficiente sem redirect handling explicito.

decision: Change plan
plan_changes_made: |
  Task 2 ganhou bloco "Redirect handling": ambos os clientes HTTP usam fetch com {redirect: 'manual'}; 30x rejeitado por default com RedirectNotAllowedError. Opt-in explicito (raro) re-valida Location header contra assertHostAllowed antes de seguir. Testes obrigatorios ampliados: fixture 302 para IMDS lanca sem fetch do segundo hop; fixture 302 para host valido tambem lanca por default; URL fora da allowlist mantem rejeicao original.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R2-PRC015: check-encryption.sh path positivo nao testavel em CI

status: Resolved
severity: Major
location: Task 6.5 (check-encryption.sh + CI test)

reviewer_concern: |
  Heuristicas (lsblk crypto_LUKS, fdesetup status, manage-bde -status) exigem root/admin e detectam disco criptografado real. GitHub Actions runners nao tem LUKS; script sempre retorna exit 1. Bypass test (REQUIRE_FS_ENCRYPTION_CHECK=false) e o unico path testavel; positivo nunca exercitado em CI.

why_it_matters: |
  Regressao que faca deteccao sempre retornar exit 1 (false negative) shipa green; producao institucional com flag=true se recusa a iniciar. Mesmo padrao silent-MUST-violation que motivou PRC007 em Round 1.

decision: Change plan
plan_changes_made: |
  Task 6.5 reescrita com dependency injection: startup do MCP server NAO chama script diretamente, chama funcao injectavel detectEncryption() em src/startup/encryption-check.ts que retorna enum encrypted/plaintext/unsupported. Default implementation chama o shell script. Em testes, mock os 3 retornos e assert startup behavior para 6 combinacoes (3 retornos × 2 valores de REQUIRE_FS_ENCRYPTION_CHECK). Script real fica como utility testado manualmente via runbook docs/runbooks/encryption-check.md em laptop com FileVault/LUKS antes de promover.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R2-PRC016: DAG ignora Task 6.5 modificar mesmo startup module de Task 1

status: Resolved
severity: Minor
location: Secao "Dependencias entre tasks" + Task 6.5

reviewer_concern: |
  DAG diz "Task 6.5 depende de Task 1 (compartilha ADR)" mas Task 6.5 tambem modifica o startup do MCP server (fail-fast no startup). Startup code e estabelecido em Task 1 (onde migrate() e wired). Tarefas em paralelo editam o mesmo arquivo = merge conflict.

why_it_matters: |
  Plano anuncia subagent parallelism. Dependencia real de Task 6.5 e estrutural (modifica mesmo arquivo), nao documentaria (compartilha ADR).

decision: Change plan
plan_changes_made: |
  DAG entry de Task 6.5 atualizada para "compartilha startup do MCP server + ADR; ver nota". Nota explicita adicionada apos a secao do DAG propondo pattern "startup checks registry" (src/startup/index.ts com lista de checks; cada task edita apenas seu proprio arquivo via registerStartupCheck) para permitir paralelizacao limpa, com fallback de serializacao 6.5-apos-1 se nao for viavel.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R2-PRC017: STORAGE_PATH default conflita com check-encryption.sh target

status: Resolved
severity: Minor
location: Task 1 + Task 6.5 + Task 4 (downloads em ./data/downloads/)

reviewer_concern: |
  Task 6.5 valida filesystem do diretorio de STORAGE_PATH, mas STORAGE_PATH e o arquivo SQLite, nao um diretorio. PDFs de Task 4 vao em ./data/downloads/ (sibling). Em deploy onde /data e criptografado mas /var/downloads (symlinked ou env-override) e plaintext, check passa mas PDFs ficam plaintext.

why_it_matters: |
  Exatamente o failure mode que PRC007 visava prevenir. Plano nao tem DOWNLOADS_PATH env nem invariante "downloads sob dirname(STORAGE_PATH)".

decision: Change plan
plan_changes_made: |
  Introduzido DATA_DIR env (default ./data) como raiz unica de storage. STORAGE_PATH derivado de DATA_DIR/pje-mcp.sqlite. Task 4 escreve downloads em DATA_DIR/downloads/ (mesma raiz). Task 6.5 check valida DATA_DIR (cobre ambos). DATA_DIR adicionado a lista de env vars no README da Task 7.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

##### Finding R2-PRC018: ## Credenciais sem orientacao para perda de STORAGE_ENCRYPTION_KEY

status: Resolved
severity: Minor
location: Task 7 (## Credenciais)

reviewer_concern: |
  Secao Credenciais menciona rotacao de STORAGE_ENCRYPTION_KEY exige re-encrypt manual mas nao diz o que acontece em PERDA da key: SQLite cache + audit trail ficam permanentemente inacessiveis. Corolario operacional da decisao de cripto.

why_it_matters: |
  Operador que le so o README nao entende que perda de key = destruicao irrecuperavel do audit log, evento CNJ-relevante. PRC007 elevou cripto a hard requirement; Round 2 deve casar com recovery contract.

decision: Change plan
plan_changes_made: |
  Secao ## Credenciais ganhou item (f): perda de STORAGE_ENCRYPTION_KEY torna cache SQLite (incluindo audit trail) permanentemente irrecuperavel; evento de compliance CNJ-relevante; backup obrigatorio em cofre institucional separado antes de promover a producao.
no_change_rationale:
human_approver: felipe@lex-intelligentia
approval_status: Approved
approval_date: 2026-05-16

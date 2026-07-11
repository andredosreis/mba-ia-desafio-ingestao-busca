# PRD — Ingestão e Busca Semântica com LangChain e PostgreSQL

| Campo | Valor |
|---|---|
| Projeto | Ingestão e Busca Semântica (RAG) com LangChain + pgVector |
| Contexto | Desafio da pós-graduação Full Cycle |
| Data | 2026-07-11 |
| Status | Aprovado — pronto para spec das features |
| Tracking | `docs/PRDProgress.json` |

## 1. Visão Geral

Software de RAG (Retrieval-Augmented Generation) em linha de comando: ingere um arquivo PDF num banco vetorial (PostgreSQL + pgVector) e permite que o usuário faça perguntas via CLI, recebendo respostas baseadas **exclusivamente** no conteúdo do PDF.

## 2. Problema e Objetivo

**Problema:** LLMs respondem qualquer pergunta com conhecimento geral, inclusive inventando dados. Para casos de uso corporativos, a resposta precisa ser rastreável a um documento fonte.

**Objetivo:** entregar um pipeline completo de ingestão + busca semântica onde:

1. Um PDF é dividido em chunks, vetorizado e persistido no Postgres/pgVector.
2. Perguntas do usuário são respondidas apenas com base nos chunks recuperados.
3. Perguntas sem resposta no documento retornam a mensagem padrão, sem alucinação.

## 3. Escopo

### Dentro do escopo
- Ingestão de **um** PDF (`document.pdf`) via script.
- Busca semântica com top-10 resultados e resposta via LLM.
- CLI interativa de perguntas e respostas.
- Infraestrutura do banco via Docker Compose.
- README com instruções completas de execução.

### Fora do escopo (non-goals)
- Interface web ou API HTTP.
- Múltiplos PDFs, upload dinâmico ou gestão de coleções.
- Histórico de conversa / memória entre perguntas.
- Streaming de resposta, autenticação, deploy.

## 4. Restrições Técnicas Obrigatórias (do enunciado)

| Item | Valor obrigatório |
|---|---|
| Linguagem | Python |
| Framework | LangChain |
| Banco | PostgreSQL + extensão pgVector (Docker Compose) |
| Split | `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)` |
| Loader | `PyPDFLoader` (langchain_community) |
| Embeddings | `text-embedding-3-small` (OpenAI) — mesmo modelo na ingestão e na busca |
| Vector store | `PGVector` de `langchain_postgres` |
| Busca | `similarity_search_with_score(query, k=10)` |
| LLM de resposta | `gpt-5-nano` (configurável via `OPENAI_MODEL`; fallback funcional `gpt-4o-mini`) |
| Base de código | Fork do template oficial `devfullcycle/mba-ia-desafio-ingestao-busca` |
| Resposta fora de contexto | Exatamente: `"Não tenho informações necessárias para responder sua pergunta."` |

### Estrutura obrigatória do repositório

```
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py
│   ├── search.py
│   └── chat.py
├── document.pdf
└── README.md
```

### Prompt Obrigatório (template fixo — usar literalmente)

```
CONTEXTO:
{resultados concatenados do banco de dados}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta do usuário}

RESPONDA A "PERGUNTA DO USUÁRIO"
```

## 5. Arquitetura (visão de alto nível)

```
INGESTÃO:
document.pdf → PyPDFLoader → RecursiveCharacterTextSplitter(1000/150)
             → OpenAIEmbeddings(text-embedding-3-small) → PGVector (Postgres)

BUSCA:
pergunta (CLI) → embedding da pergunta → similarity_search_with_score(k=10)
              → concatenação do contexto → prompt fixo → LLM → resposta (CLI)
```

Módulos (contratos herdados dos stubs do template — manter assinaturas):
- `src/ingest.py` — pipeline de ingestão (executável). Expõe `ingest_pdf()`; lê `PDF_PATH` do `.env`.
- `src/search.py` — busca + montagem de prompt + chamada da LLM. Já contém o `PROMPT_TEMPLATE` obrigatório (placeholders `{contexto}` e `{pergunta}`); expõe `search_prompt(question=None)`, que retorna a chain consumida pelo chat.
- `src/chat.py` — loop de CLI (executável); importa `search_prompt` de `search.py`.

Variáveis de ambiente (convenção do template): `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_MODEL`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, `PDF_PATH` (e `GOOGLE_*` como alternativa não usada).

## 6. Features

### F01 — Fundação e Infraestrutura

Validar e preparar a infraestrutura herdada do template oficial (que já entrega `docker-compose.yml`, `requirements.txt` pinado, `document.pdf` e os stubs de `src/`).

**Entregas:** banco validado de pé, dependências instaladas num venv, `.env.example` alinhado à convenção do template (com as variáveis OpenAI ativas).

**Critérios de aceitação:**
- CA-01.1 — Dado o Docker instalado, quando executo `docker compose up -d`, então o Postgres 17 sobe saudável (healthcheck OK) e o serviço `bootstrap_vector_ext` cria a extensão `vector` no banco `rag`.
- CA-01.2 — Dado um venv ativo, quando executo `pip install -r requirements.txt`, então todas as dependências instalam sem conflito.
- CA-01.3 — Dado o repositório clonado, quando copio `.env.example` para `.env`, então todas as variáveis necessárias ao projeto (`OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_MODEL`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, `PDF_PATH`) estão documentadas no template com defaults corretos para o compose oficial.

### F02 — Ingestão do PDF

Script `src/ingest.py` que carrega o PDF, divide em chunks e persiste embeddings no pgVector.

**Entregas:** `src/ingest.py`, `document.pdf` presente no repositório.

**Critérios de aceitação:**
- CA-02.1 — Dado o banco de pé e `.env` configurado, quando executo `python src/ingest.py`, então o PDF é dividido em chunks de 1000 caracteres com overlap de 150 e cada chunk é armazenado com seu embedding no Postgres.
- CA-02.2 — Dado uma ingestão já realizada, quando executo `python src/ingest.py` novamente, então a base não fica com documentos duplicados (a coleção é recriada/limpa antes).
- CA-02.3 — Dado um `document.pdf` ausente ou banco fora do ar, quando executo a ingestão, então recebo uma mensagem de erro clara em português (sem stack trace cru).

### F03 — Busca Semântica e Resposta

Módulo `src/search.py` com a cadeia de busca: vetoriza a pergunta, busca k=10, monta o prompt obrigatório e chama a LLM.

**Entregas:** `src/search.py` implementando `search_prompt(question=None)` (assinatura do stub do template, consumida por `chat.py`), usando o `PROMPT_TEMPLATE` já presente no stub.

**Critérios de aceitação:**
- CA-03.1 — Dado o banco populado, quando pergunto algo presente no PDF, então a resposta é baseada apenas no conteúdo recuperado do banco.
- CA-03.2 — Dado o banco populado, quando pergunto algo fora do documento (ex.: "Qual é a capital da França?"), então a resposta é exatamente `"Não tenho informações necessárias para responder sua pergunta."`.
- CA-03.3 — A busca usa `similarity_search_with_score(query, k=10)` e o prompt enviado à LLM é o template obrigatório do PRD, sem modificações.
- CA-03.4 — O modelo de embeddings da busca é o mesmo da ingestão (`text-embedding-3-small`).

### F04 — CLI de Chat

Script `src/chat.py` com loop interativo no formato do enunciado.

**Entregas:** `src/chat.py`.

**Critérios de aceitação:**
- CA-04.1 — Dado o banco populado, quando executo `python src/chat.py`, então vejo o prompt `Faça sua pergunta:` e posso digitar perguntas em loop.
- CA-04.2 — Dado uma pergunta digitada, quando a resposta chega, então a saída segue o formato `PERGUNTA: ...` / `RESPOSTA: ...` do enunciado.
- CA-04.3 — Dado o loop ativo, quando digito `sair` (ou Ctrl+C/Ctrl+D), então o programa encerra graciosamente.
- CA-04.4 — Dado banco vazio ou `.env` ausente, quando inicio o chat, então recebo orientação clara do que fazer (rodar ingestão / configurar chave), sem stack trace cru.

### F05 — README e Entrega

Documentação final e preparação do repositório público.

**Entregas:** `README.md` completo; repositório público no GitHub.

**Critérios de aceitação:**
- CA-05.1 — Dado uma pessoa sem contexto do projeto, quando ela segue apenas o README, então consegue subir o banco, ingerir o PDF e conversar com a CLI.
- CA-05.2 — O README documenta: pré-requisitos, criação do venv, `.env`, ordem de execução (`docker compose up -d` → `ingest.py` → `chat.py`) e exemplos de perguntas dentro/fora do contexto.
- CA-05.3 — O repositório público não contém `.env`, `venv/` nem dados locais (`pgdata/`).

## 7. Ordem de Execução (Waves)

| Wave | Features | Justificativa |
|---|---|---|
| 1 | F01 | Base de tudo |
| 2 | F02, F03 | Dependem só da F01; F03 pode ser testada unitariamente com mocks antes da ingestão real |
| 3 | F04 | Consome F03 |
| 4 | F05 | Documenta o conjunto completo |

## 8. Métricas de Sucesso

1. Pergunta com resposta no PDF → resposta correta e rastreável ao documento.
2. Pergunta fora do contexto → mensagem padrão exata, 100% das vezes.
3. Execução limpa em máquina nova seguindo apenas o README.

## 9. Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| `gpt-5-nano` indisponível na conta | Modelo configurável via `OPENAI_MODEL`; fallback `gpt-4o-mini` |
| Porta 5432 ocupada por Postgres local | Parar o serviço local ou ajustar mapeamento de porta + `DATABASE_URL` |
| LLM ignora as regras e alucina | Prompt fixo do enunciado + verificação do evaluator com perguntas armadilha |
| Ingestões repetidas duplicando dados | Recriar a coleção a cada ingestão (CA-02.2) |
| Chave da API vazada | `.env` no `.gitignore`; evaluator confere CA-05.3 |
| Incompatibilidade de versões LangChain | Dependências pinadas no `requirements.txt` (CA-01.2) |

## 10. Entregável Final

Repositório **público** no GitHub com todo o código-fonte, `document.pdf` e README com instruções claras de execução.

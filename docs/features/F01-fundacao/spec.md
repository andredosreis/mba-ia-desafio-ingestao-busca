# Spec — F01 Fundação e Infraestrutura

| Campo | Valor |
|---|---|
| Feature | F01 — Fundação e Infraestrutura |
| Wave | 1 |
| Depende de | — (nenhuma) |
| Critérios de aceitação | CA-01.1, CA-01.2, CA-01.3 |
| Tipo | Validação de ambiente (sem código de produto) |

## 1. Objetivo

Preparar e **validar** a infraestrutura herdada do template oficial (fork de
`devfullcycle/mba-ia-desafio-ingestao-busca`) para que as features seguintes
(F02–F05) possam ser implementadas e executadas. A F01 **não escreve código de
produto** — os arquivos `docker-compose.yml`, `requirements.txt`, `.env.example`,
`document.pdf` e os stubs de `src/` já vêm do template.

O trabalho é garantir que:

1. O banco Postgres 17 + pgVector sobe saudável via Docker Compose e a extensão
   `vector` é criada automaticamente (**CA-01.1**).
2. Um ambiente virtual Python instala todas as dependências pinadas sem conflito (**CA-01.2**).
3. O `.env.example` documenta todas as variáveis necessárias com defaults corretos
   para o compose oficial, e um `.env` derivado dele é utilizável (**CA-01.3**).

## 2. Ligação com os critérios de aceitação (PRD §6)

- **CA-01.1** — `docker compose up -d` → Postgres 17 saudável (healthcheck OK) e
  serviço `bootstrap_vector_ext` cria a extensão `vector` no banco `rag`.
- **CA-01.2** — Em venv ativo, `pip install -r requirements.txt` instala tudo sem conflito.
- **CA-01.3** — `cp .env.example .env` cobre `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`,
  `OPENAI_MODEL`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, `PDF_PATH` com defaults
  corretos para o compose oficial.

## 3. Design técnico

Não há módulos ou funções novas. A "entrega" da F01 é o **ambiente validado** e a
evidência dessa validação. Componentes envolvidos (todos pré-existentes):

- **`docker-compose.yml`** — dois serviços:
  - `postgres` (imagem `pgvector/pgvector:pg17`, healthcheck `pg_isready -U postgres -d rag`, porta host `5432`).
  - `bootstrap_vector_ext` — roda `CREATE EXTENSION IF NOT EXISTS vector;` após o Postgres ficar `service_healthy`; `restart: "no"` (é one-shot e sai com código 0).
- **`requirements.txt`** — dependências pinadas do ecossistema LangChain/OpenAI/psycopg (não repinar).
- **`.env.example` / `.env`** — convenção de nomes do template. `DATABASE_URL` usa driver
  `postgresql+psycopg` batendo com usuário/senha/porta/db do compose.

## 4. Decisões e trade-offs

- **Sem helper de sanidade** (`src/check_env.py` etc.): decidido manter F01 como
  validação pura para não invadir o escopo de conexão/embeddings da F02/F03 e não
  adicionar código fora do previsto no PRD. A verificação de conectividade ao banco
  usa ferramentas nativas (`psql`/`docker compose exec`), não código Python novo.
- **API key**: a `OPENAI_API_KEY` real já está no `.env`. Nenhum CA da F01 exige
  chamada à OpenAI — a F01 só confere a **presença** da variável. A validação de
  chamada real fica para a F02/F03.
- **Sem testes unitários**: infra não é unit-testável de forma útil; a verificação
  da F01 é feita por comandos de CLI reais descritos no `contract.md`.

## 5. Fora do escopo desta feature

- Qualquer implementação em `src/ingest.py`, `src/search.py`, `src/chat.py` (F02–F04).
- Ingestão do PDF ou criação de tabelas de embeddings (F02 — o LangChain/PGVector cria as tabelas na primeira ingestão).
- Chamada real à API da OpenAI (F02/F03).
- README final (F05).
- Alterar parâmetros obrigatórios do enunciado (chunk, overlap, k, modelos, prompt).

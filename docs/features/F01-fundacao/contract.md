# Contract — F01 Fundação e Infraestrutura

## Pré-requisitos de Ambiente
- Docker e Docker Compose instalados; daemon em execução.
- Python 3 disponível (`python3 --version`).
- Repositório clonado; diretório de trabalho na raiz do projeto.
- `document.pdf` presente na raiz (herdado do template).
- Porta host `5432` livre (nenhum outro Postgres ocupando).
- `.env` criado a partir de `.env.example` (`cp .env.example .env`) com `OPENAI_API_KEY` preenchida.

## Gates de Qualidade
- `python -m py_compile src/*.py` → exit code 0 (sanidade de sintaxe dos stubs).
- `pytest` → **N/A nesta feature** (não há `tests/` ainda; F01 é validação de infra).
- Verificação funcional: os blocos GWT abaixo, executados via CLI real (não mock).

## Manifesto de Cobertura

### Surface: Banco (Docker Compose)

#### CA-01.1 — Postgres saudável + extensão vector criada
- **Given:** Docker em execução e diretório na raiz do projeto.
- **When:** executo `docker compose up -d` e aguardo o healthcheck.
- **Then:**
  - `docker compose ps` lista `postgres_rag` com status contendo `healthy`.
  - `docker compose logs bootstrap_vector_ext` não apresenta erro e o serviço saiu com código 0.
  - `docker compose exec postgres psql -U postgres -d rag -c "SELECT extname FROM pg_extension WHERE extname='vector';"` retorna uma linha com `vector`.

### Surface: Ambiente Python (venv)

#### CA-01.2 — Dependências instalam sem conflito
- **Given:** um venv ativo (`python3 -m venv venv && source venv/bin/activate`).
- **When:** executo `pip install -r requirements.txt`.
- **Then:**
  - o comando termina com exit code 0, sem erro de resolução de dependências.
  - `python -c "import langchain, langchain_openai, langchain_postgres, langchain_text_splitters, pypdf; print('ok')"` imprime `ok` sem `ImportError`.

### Surface: Configuração (.env)

#### CA-01.3 — Variáveis de ambiente documentadas com defaults corretos
- **Given:** o repositório clonado com `.env.example` versionado.
- **When:** executo `cp .env.example .env` (ou o `.env` já existe derivado dele).
- **Then:**
  - o `.env` contém as chaves: `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_MODEL`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, `PDF_PATH`.
  - `OPENAI_EMBEDDING_MODEL` = `text-embedding-3-small`.
  - `DATABASE_URL` = `postgresql+psycopg://postgres:postgres@localhost:5432/rag` (bate com usuário/senha/porta/db do `docker-compose.yml`).
  - `PDF_PATH` = `document.pdf` e o arquivo existe na raiz.
  - **Guardrail:** o valor de `OPENAI_API_KEY` NUNCA é impresso em nenhum passo de verificação nem em logs.

## Critério de conclusão
Todos os três blocos GWT passam via CLI real, os gates aplicáveis estão verdes, e
nenhuma credencial foi exposta. Só então F01 pode ir para `implemented` e ser
encaminhada ao `evaluator`.

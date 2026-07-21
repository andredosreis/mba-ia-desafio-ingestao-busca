# Plan — F01 Fundação e Infraestrutura

Cada stage é pequeno e verificável. A F01 não altera código de produto; os stages
são de preparação e **validação** do ambiente.

## Stage 1 — Ambiente virtual + dependências
- **Fazer:** criar o venv e instalar as dependências pinadas.
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```
- **Arquivos tocados:** nenhum versionado (`venv/` está no `.gitignore`).
- **Verificar:** `pip install` termina com exit code 0, sem erro de resolução/conflito.
  `python -c "import langchain, langchain_openai, langchain_postgres, pypdf"` roda sem `ImportError`.
- **Cobre:** CA-01.2.

## Stage 2 — Subir o banco (Docker Compose)
- **Fazer:** subir os serviços e aguardar o healthcheck.
  ```bash
  docker compose up -d
  ```
- **Arquivos tocados:** nenhum (usa `docker-compose.yml` do template).
- **Verificar:**
  - `docker compose ps` mostra `postgres_rag` com status `healthy`.
  - o serviço `bootstrap_vector_ext` executou e saiu com código 0 (`docker compose logs bootstrap_vector_ext` sem erro).
- **Cobre:** CA-01.1 (parte do healthcheck).

## Stage 3 — Confirmar a extensão vector
- **Fazer:** verificar que a extensão `vector` existe no banco `rag`.
  ```bash
  docker compose exec postgres psql -U postgres -d rag -c "SELECT extname FROM pg_extension WHERE extname='vector';"
  ```
- **Arquivos tocados:** nenhum.
- **Verificar:** a query retorna uma linha com `vector`.
- **Cobre:** CA-01.1 (parte da extensão).

## Stage 4 — Validar o .env
- **Fazer:** garantir que o `.env` existe (derivado do `.env.example`) e contém as
  seis variáveis necessárias com defaults corretos para o compose.
- **Arquivos tocados:** `.env` (local, não versionado). `.env.example` já está alinhado.
- **Verificar:** as chaves `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_MODEL`,
  `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, `PDF_PATH` estão presentes; `DATABASE_URL`
  aponta para `postgresql+psycopg://postgres:postgres@localhost:5432/rag`;
  `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`. **Nunca imprimir o valor da API key.**
- **Cobre:** CA-01.3.

## Stage 5 — Final Verification (Quality Gates + Contract)
- **Fazer:** rodar os gates do CLAUDE.md aplicáveis e conferir o `contract.md` ponta a ponta.
  ```bash
  python -m py_compile src/*.py      # sanidade dos stubs
  ```
  (não há `tests/` ainda nesta feature; o gate de pytest é N/A na F01)
- **Verificar:** todos os blocos GWT do `contract.md` passam; nenhuma credencial exposta.
- **Ao concluir:**
  - preencher a seção **F01** de `docs/APRENDIZADO.md` (Parte 2).
  - atualizar `docs/PRDProgress.json`: F01 → `implemented`.
- **Cobre:** fechamento da feature.

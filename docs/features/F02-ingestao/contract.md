# Contract — F02 Ingestão do PDF

## Pré-requisitos de Ambiente
- Docker em execução; banco de pé: `docker compose up -d` → `postgres_rag` healthy e extensão `vector` criada (validado na F01).
- venv com dependências do `requirements.txt` instaladas.
- `.env` na raiz com **`OPENAI_API_KEY` REAL** (placeholder `sk-sua-chave-aqui` NÃO serve — a ingestão gera embeddings reais), `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`, `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag`, `PG_VECTOR_COLLECTION_NAME=document_chunks`, `PDF_PATH=document.pdf`.
- `document.pdf` presente na raiz do projeto.

## Gates de Qualidade
- `python -m py_compile src/*.py` → exit 0.
- `python -m pytest tests/ -q` → todos verdes (testes unitários com OpenAI/Postgres mockados).
- Verificação funcional via CLI real: `venv/bin/python src/ingest.py`.

## Manifesto de Cobertura

### Surface: CLI + Banco

#### CA-02.1 — Chunks 1000/150 armazenados com embeddings
- **Given:** banco de pé, `.env` válido com chave real, `document.pdf` na raiz.
- **When:** executo `venv/bin/python src/ingest.py`.
- **Then:**
  - exit code 0; saída em português informando sucesso e o número de chunks;
  - a query abaixo retorna contagem > 0:
    ```sql
    SELECT count(*) FROM langchain_pg_embedding e
    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
    WHERE c.name = 'document_chunks';
    ```
  - `SELECT max(length(e.document)) ...` (mesmo JOIN) retorna valor ≤ 1000;
  - a coluna `embedding` está preenchida (não nula) para todas as linhas da collection.

#### CA-02.2 — Reexecução não duplica
- **Given:** ingestão já executada com sucesso; contagem N anotada (query do CA-02.1).
- **When:** executo `venv/bin/python src/ingest.py` novamente.
- **Then:**
  - exit code 0;
  - a mesma query retorna exatamente N (não N×2) — a collection foi recriada, não acumulada.

#### CA-02.3 — Erros amigáveis em português
- **Given:** banco de pé, mas `PDF_PATH` apontando para arquivo inexistente.
- **When:** executo `PDF_PATH=arquivo_inexistente.pdf venv/bin/python src/ingest.py`.
- **Then:**
  - exit code ≠ 0;
  - stdout/stderr contém mensagem em português citando o caminho e orientando verificar `PDF_PATH`;
  - a saída NÃO contém `Traceback (most recent call last)`.

- **Given:** `document.pdf` presente, mas banco parado (`docker compose stop postgres`).
- **When:** executo `venv/bin/python src/ingest.py`.
- **Then:**
  - exit code ≠ 0;
  - mensagem em português indicando falha de conexão e orientando `docker compose up -d`;
  - a saída NÃO contém `Traceback (most recent call last)`;
  - (pós-teste: `docker compose start postgres` para restaurar o ambiente).

## Critério de conclusão
Todos os blocos GWT passam via CLI e banco reais, gates verdes, `OPENAI_API_KEY`
jamais impressa. Só então F02 pode ir para `implemented` e ser encaminhada ao `evaluator`.

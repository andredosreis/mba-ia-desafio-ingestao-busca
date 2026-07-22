# Spec — F02 Ingestão do PDF

| Campo | Valor |
|---|---|
| Feature | F02 — Ingestão do PDF |
| Wave | 2 |
| Depende de | F01 (evaluated ✅) |
| Critérios de aceitação | CA-02.1, CA-02.2, CA-02.3 |
| Entrega | `src/ingest.py` (implementar `ingest_pdf()`) + `tests/test_ingest.py` |

## 1. Objetivo

Implementar o pipeline de ingestão: ler `document.pdf`, dividir em chunks de
1000 caracteres com overlap de 150, gerar embeddings com `text-embedding-3-small`
e persistir tudo na collection do PGVector — de forma **idempotente** (rodar duas
vezes não duplica) e com **erros amigáveis em português**.

- **CA-02.1** — chunks 1000/150 armazenados com embedding no Postgres.
- **CA-02.2** — reexecução não duplica (collection recriada/limpa antes).
- **CA-02.3** — PDF ausente ou banco fora → mensagem clara em PT, sem stack trace cru.

## 2. Design técnico

Tudo em `src/ingest.py` (mantém a assinatura `ingest_pdf()` do stub e a leitura
de `PDF_PATH` do `.env`). Funções pequenas e testáveis:

```python
def carregar_paginas_pdf(caminho_pdf: str) -> list[Document]:
    """Carrega o PDF via PyPDFLoader; FileNotFoundError se não existir."""

def dividir_paginas_em_chunks(paginas: list[Document]) -> list[Document]:
    """RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)."""

def criar_vector_store_para_ingestao() -> PGVector:
    """PGVector com pre_delete_collection=True (recria a collection)."""

def ingest_pdf() -> None:
    """Orquestra: carregar → dividir → embutir/persistir. Erros viram
    mensagens em português e sys.exit(1)."""
```

- **Loader:** `PyPDFLoader` (`langchain_community`).
- **Split:** `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)` — parâmetros do enunciado, imutáveis.
- **Embeddings:** `OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL"))` → `text-embedding-3-small`.
- **Store:** `PGVector(embeddings=..., collection_name=PG_VECTOR_COLLECTION_NAME, connection=DATABASE_URL, use_jsonb=True, pre_delete_collection=True)` seguido de `store.add_documents(chunks)`.
- **Env:** `PDF_PATH`, `OPENAI_EMBEDDING_MODEL`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME` via `python-dotenv` (já no stub).
- **Saída de sucesso (PT):** `Ingestão concluída: N chunks armazenados na collection 'document_chunks'.`

### Tratamento de erros (CA-02.3)

| Falha | Mensagem (PT) | Exit |
|---|---|---|
| `PDF_PATH` ausente/arquivo inexistente | `Erro: arquivo PDF não encontrado em '<caminho>'. Verifique PDF_PATH no .env.` | 1 |
| Banco inacessível (conexão recusada) | `Erro: não foi possível conectar ao banco. Suba-o com: docker compose up -d` | 1 |
| Variável de ambiente obrigatória vazia | `Erro: variável <NOME> não definida no .env.` | 1 |

Nunca imprimir traceback cru; capturar exceções específicas (FileNotFoundError,
erros de conexão do SQLAlchemy/psycopg) no `ingest_pdf()`.

## 3. Decisões e trade-offs

- **Idempotência via `pre_delete_collection=True`** (e não DELETE manual): é o
  mecanismo idiomático do `langchain_postgres` e cumpre o CA-02.2 literalmente
  ("a coleção é recriada/limpa antes").
- **`PGVector(...)` + `add_documents` em vez de `from_documents`**: separa a
  criação do store (mockável nos testes) da persistência.
- **Lote único de `add_documents`**: o PDF tem ~175 KB; sem necessidade de batching.
- **Validação de env mínima**: apenas as variáveis que a ingestão usa; validação
  ampla de ambiente foi papel da F01.

## 4. Testes (unitários, sem rede)

`tests/test_ingest.py` — mockar OpenAI e Postgres (regra do CLAUDE.md):

1. `dividir_paginas_em_chunks` com documento sintético → todo chunk ≤ 1000 chars; overlap presente entre chunks consecutivos (splitter real, sem rede).
2. `ingest_pdf` com `PDF_PATH` inexistente → mensagem PT + `SystemExit(1)`, sem traceback.
3. `criar_vector_store_para_ingestao` (mock de `PGVector`) → chamado com `pre_delete_collection=True` e `collection_name` vindo do env.
4. `ingest_pdf` feliz (mocks) → `add_documents` chamado com os chunks gerados.

## 5. Fora do escopo

- Busca/resposta (F03), CLI (F04), README (F05).
- Múltiplos PDFs, upload dinâmico, batching, retry de API.
- Alterar parâmetros do enunciado (1000/150, modelo de embedding).

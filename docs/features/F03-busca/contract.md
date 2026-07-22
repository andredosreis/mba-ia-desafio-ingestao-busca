# Contract — F03 Busca Semântica e Resposta

## Pré-requisitos de Ambiente
- Banco de pé (`docker compose up -d`, `postgres_rag` healthy, extensão `vector` criada).
- **Ingestão da F02 já executada**: collection `document_chunks` com contagem > 0 (query do contract da F02).
- venv com dependências instaladas.
- `.env` com `OPENAI_API_KEY` REAL, `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`, `OPENAI_MODEL` definido, `DATABASE_URL` e `PG_VECTOR_COLLECTION_NAME` idênticos aos usados na ingestão.

## Gates de Qualidade
- `python -m py_compile src/*.py` → exit 0.
- `python -m pytest tests/ -q` → todos verdes (OpenAI/Postgres mockados).
- Verificação funcional real via:
  ```bash
  venv/bin/python -c "import sys; sys.path.insert(0,'src'); from search import search_prompt; print(search_prompt('<PERGUNTA>'))"
  ```

## Manifesto de Cobertura

### Surface: Módulo (`search_prompt`) + Banco

#### CA-03.1 — Resposta baseada apenas no conteúdo recuperado
- **Given:** banco populado pela F02; `.env` válido.
- **When:** executo `search_prompt('<pergunta cuja resposta está no PDF>')` (comando do gate).
- **Then:**
  - retorna string não vazia, sem exceção;
  - a informação da resposta é localizável no texto de `document.pdf` (o avaliador confere contra o documento);
  - a resposta NÃO contém informação ausente do PDF.

#### CA-03.2 — Fora do contexto → frase padrão exata
- **Given:** banco populado pela F02; `.env` válido.
- **When:** executo `search_prompt('Qual é a capital da França?')`.
- **Then:**
  - a saída é EXATAMENTE `Não tenho informações necessárias para responder sua pergunta.` (sem texto adicional).
- **When (2ª armadilha):** `search_prompt('Você acha isso bom ou ruim?')`.
- **Then:** mesma frase padrão exata.

#### CA-03.3 — Busca k=10 literal + prompt do PRD intocado
- **Given:** o código-fonte de `src/search.py`.
- **When:** inspeção do código + suite de testes.
- **Then:**
  - existe chamada literal `similarity_search_with_score(` com `k=10`;
  - o `PROMPT_TEMPLATE` é idêntico ao do PRD §4 (mesmos blocos CONTEXTO/REGRAS/EXEMPLOS/PERGUNTA, placeholders `{contexto}` e `{pergunta}`) — verificável por diff contra o stub original;
  - um teste unitário afirma o `k=10` na chamada de busca.

#### CA-03.4 — Mesmo modelo de embedding da ingestão
- **Given:** os códigos de `src/ingest.py` e `src/search.py`.
- **When:** inspeção do código.
- **Then:**
  - ambos criam `OpenAIEmbeddings` lendo a MESMA variável `OPENAI_EMBEDDING_MODEL`;
  - o `.env`/`.env.example` define essa variável como `text-embedding-3-small`;
  - nenhum dos dois hardcoda outro modelo de embedding.

## Critério de conclusão
Todos os blocos GWT passam (execução real + inspeção), gates verdes, chave jamais
impressa. Só então F03 pode ir para `implemented` e ser encaminhada ao `evaluator`.

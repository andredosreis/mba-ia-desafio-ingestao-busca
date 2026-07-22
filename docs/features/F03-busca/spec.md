# Spec — F03 Busca Semântica e Resposta

| Campo | Valor |
|---|---|
| Feature | F03 — Busca Semântica e Resposta |
| Wave | 2 |
| Depende de | F01 (evaluated ✅) |
| Critérios de aceitação | CA-03.1, CA-03.2, CA-03.3, CA-03.4 |
| Entrega | `src/search.py` (implementar `search_prompt(question=None)`) + `tests/test_search.py` |

## 1. Objetivo

Implementar a cadeia RAG de consulta: vetorizar a pergunta, buscar os 10 chunks
mais relevantes (`similarity_search_with_score(query, k=10)`), montar o prompt
FIXO do enunciado e chamar a LLM — respondendo **apenas** com base no contexto.

- **CA-03.1** — resposta baseada só no conteúdo recuperado do banco.
- **CA-03.2** — fora do contexto → exatamente `"Não tenho informações necessárias para responder sua pergunta."`.
- **CA-03.3** — busca literal `similarity_search_with_score(query, k=10)`; prompt do PRD sem modificações.
- **CA-03.4** — mesmo modelo de embedding da ingestão (`text-embedding-3-small`).

## 2. Design técnico

Tudo em `src/search.py`. O `PROMPT_TEMPLATE` do stub fica **intocado**.

```python
def montar_contexto(resultados: list[tuple[Document, float]]) -> str:
    """Concatena o page_content dos documentos com '\n\n' (ignora scores)."""

def criar_chain_rag() -> Runnable:
    """Monta a chain LCEL: busca k=10 → prompt fixo → LLM → str."""

def verificar_colecao_populada() -> bool:
    """True se a collection tem ao menos 1 documento (consulta SQL, sem API)."""

def search_prompt(question: str | None = None):
    """Sem argumento: retorna a chain (com .invoke(pergunta) -> str).
    Com argumento: retorna a resposta (str). Falha de inicialização:
    imprime orientação em PT e retorna None."""
```

- **Chain (LCEL):**
  ```python
  {"contexto": RunnableLambda(buscar_e_montar_contexto), "pergunta": RunnablePassthrough()}
      | PromptTemplate.from_template(PROMPT_TEMPLATE)
      | ChatOpenAI(model=os.getenv("OPENAI_MODEL"))
      | StrOutputParser()
  ```
  onde `buscar_e_montar_contexto(pergunta)` chama
  `store.similarity_search_with_score(pergunta, k=10)` e passa o resultado a `montar_contexto`.
- **Embeddings:** `OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL"))` —
  a MESMA env var lida pela ingestão (CA-03.4 garantido por construção).
- **Store:** `PGVector` com a mesma `DATABASE_URL`/`PG_VECTOR_COLLECTION_NAME` da
  F02, **sem** `pre_delete_collection` (leitura, nunca destrói dados).
- **`verificar_colecao_populada()`:** count na `langchain_pg_embedding` da collection
  via SQLAlchemy (sem custo de API). Consumida pelo chat (F04/CA-04.4) para
  orientar "rode a ingestão primeiro" quando a base está vazia.

### Contrato com o chat (stub do template)

`src/chat.py` faz `chain = search_prompt()` e testa `if not chain`. Logo:
- sucesso → retorna objeto com `.invoke(pergunta: str) -> str`;
- falha (env ausente, banco fora) → imprime causa + orientação em PT e retorna `None`.

## 3. Decisões e trade-offs

- **Sem wrapper de retriever** (`as_retriever()`): o enunciado exige a chamada
  literal `similarity_search_with_score(query, k=10)` — usar RunnableLambda mantém
  a chamada explícita e verificável.
- **Scores não filtram resultados**: o enunciado não define threshold; quem decide
  se o contexto responde é a LLM guiada pelo prompt fixo (os 10 chunks sempre entram).
- **`k=10` hardcoded** — parâmetro do enunciado, não configurável.
- **`verificar_colecao_populada` nesta feature** (e não na F04): o acesso ao banco
  pertence à camada de busca; o chat apenas consome o booleano.

## 4. Testes (unitários, sem rede)

`tests/test_search.py` — mockar OpenAI e PGVector:

1. `montar_contexto` com documentos falsos → concatenação `'\n\n'` correta, scores ignorados.
2. Chain mockada → `similarity_search_with_score` chamado com a pergunta e `k=10` (assert literal).
3. `PROMPT_TEMPLATE` contém os placeholders `{contexto}` e `{pergunta}` e a frase padrão exata (guarda contra edição acidental).
4. `search_prompt()` sem argumento → retorna objeto com `.invoke`; com argumento → invoca e retorna str (mocks).
5. Falha de inicialização (env ausente, mock de conexão explodindo) → retorna `None` + mensagem PT (capsys), sem traceback.

## 5. Fora do escopo

- Loop de CLI e formato `PERGUNTA:`/`RESPOSTA:` (F04).
- Ingestão (F02). Histórico de conversa, streaming, threshold de score (non-goals do PRD).
- Alterar o `PROMPT_TEMPLATE`, o k, ou os modelos do enunciado.

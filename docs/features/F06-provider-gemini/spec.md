# Spec — F06 Suporte a Provider Gemini (alternativa à OpenAI)

## Objetivo

Permitir rodar todo o pipeline RAG (ingestão + busca) com **Gemini** em vez de OpenAI, selecionável por variável de ambiente, sem quebrar nenhuma restrição do enunciado nem as assinaturas dos stubs. Motivação: a conta OpenAI está sem quota (`429 insufficient_quota`); o enunciado permite Gemini como alternativa; a chave Google do usuário foi validada de ponta a ponta.

Cobre os critérios do PRD: **CA-06.1** (seleção por env), **CA-06.2** (restrições e assinaturas preservadas), **CA-06.3** (execução real com Gemini), **CA-06.4** (documentação e higiene).

## Fatos técnicos validados (com a chave do usuário)

| Componente | OpenAI (default) | Gemini |
|---|---|---|
| Embeddings | `text-embedding-3-small` (1536d) | `models/gemini-embedding-001` (3072d) ✅ |
| Chat/LLM | `OPENAI_MODEL` (ex. `gpt-4o-mini`) | `gemini-2.5-flash` ✅ |
| Classe embeddings | `langchain_openai.OpenAIEmbeddings` | `langchain_google_genai.GoogleGenerativeAIEmbeddings` |
| Classe chat | `langchain_openai.ChatOpenAI` | `langchain_google_genai.ChatGoogleGenerativeAI` |

> Nomes que **falham** com essa chave/API (não usar): `gemini-2.0-flash`, `gemini-1.5-flash`, `models/text-embedding-004`, `models/embedding-001` → todos retornam 404. A lib faz 5 retries com backoff em 404 (~60s desperdiçados) — usar apenas os nomes validados.

## Design técnico

### Novo módulo: `src/providers.py` (fábrica de provider — SRP)

Centraliza a seleção de provider para **garantir** que ingestão e busca usem o mesmo modelo de embedding (restrição do enunciado). Evita duplicar a lógica entre `ingest.py` e `search.py`.

```python
def obter_provider() -> str:
    """Lê LLM_PROVIDER (openai|gemini); default 'openai'. Valida valor."""

def validar_credencial_do_provider(provider: str) -> None:
    """Garante a chave do provider ativo (OPENAI_API_KEY ou GOOGLE_API_KEY),
    rejeitando ausência/placeholder. Levanta ValueError com msg PT."""

def criar_embeddings():
    """Retorna OpenAIEmbeddings(OPENAI_EMBEDDING_MODEL) ou
    GoogleGenerativeAIEmbeddings(GOOGLE_EMBEDDING_MODEL) conforme o provider."""

def criar_chat_llm():
    """Retorna ChatOpenAI(OPENAI_MODEL) ou
    ChatGoogleGenerativeAI(GOOGLE_MODEL) conforme o provider."""
```

Defaults de modelo (quando a env específica estiver ausente): embeddings Gemini → `models/gemini-embedding-001`; chat Gemini → `gemini-2.5-flash`. OpenAI mantém o comportamento atual (lê `OPENAI_EMBEDDING_MODEL`/`OPENAI_MODEL`).

### Integração

- **`src/ingest.py`**: em `criar_vector_store_para_ingestao`, trocar a instânciação direta de `OpenAIEmbeddings` por `providers.criar_embeddings()`; a validação de credencial passa a chamar `providers.validar_credencial_do_provider(...)` (mantendo as validações de `DATABASE_URL`/`PG_VECTOR_COLLECTION_NAME`).
- **`src/search.py`**: idem para embeddings em `criar_vector_store_para_busca`; em `criar_chain_rag`, trocar `ChatOpenAI(model=OPENAI_MODEL)` por `providers.criar_chat_llm()`.
- **Assinaturas públicas `ingest_pdf()` e `search_prompt(question=None)` NÃO mudam.** `k=10`, chunk `1000/150` e o `PROMPT_TEMPLATE` continuam intocados.

### Variáveis de ambiente (novas / re-documentadas)

| Var | Papel | Default |
|---|---|---|
| `LLM_PROVIDER` | `openai` \| `gemini` | `openai` |
| `GOOGLE_API_KEY` | chave Google (formato `AIza…`) | — (obrigatória se `gemini`) |
| `GOOGLE_EMBEDDING_MODEL` | modelo de embedding Gemini | `models/gemini-embedding-001` |
| `GOOGLE_MODEL` | chat model Gemini | `gemini-2.5-flash` |

### Testes unitários (mockados, sem rede)

`tests/test_providers.py`: com `LLM_PROVIDER=gemini` (via `patch.dict` do ambiente) e as classes de provider mockadas, `criar_embeddings()`/`criar_chat_llm()` instanciam as classes Google; com `openai`/ausente, instanciam as OpenAI. `validar_credencial_do_provider` rejeita chave ausente/placeholder do provider ativo. Nenhuma chamada de rede.

## Decisões e trade-offs

1. **Módulo `src/providers.py` compartilhado** (em vez de lógica inline em cada script): DRY e — crucial — força ingestão e busca a usarem o mesmo provider/modelo de embedding (restrição do enunciado). Custo: um arquivo a mais fora da "estrutura obrigatória" (permitido; a estrutura lista o mínimo, não proíbe helpers).
2. **Default `openai`**: retrocompatível — quem não setar `LLM_PROVIDER` mantém o comportamento atual.
3. **Sem auto-detecção de provider** por presença de chave: seleção explícita via `LLM_PROVIDER` evita ambiguidade (as duas chaves podem coexistir no `.env`).
4. **Troca de provider exige re-ingestão**: embeddings de 1536d (OpenAI) e 3072d (Gemini) são incompatíveis na mesma coleção; `pre_delete_collection=True` na ingestão recria a coleção. Documentado no README, não automatizado.

## Fora de escopo

- Auto-detecção de provider; mistura de providers na mesma coleção; migração de vetores entre dimensões.
- Outros providers (Anthropic, etc.); streaming de resposta.
- Qualquer alteração em `chunk_size/overlap`, `k=10`, no `PROMPT_TEMPLATE` ou na frase-padrão.
- Alterar `src/chat.py` (consome `search_prompt()`, cuja assinatura não muda).

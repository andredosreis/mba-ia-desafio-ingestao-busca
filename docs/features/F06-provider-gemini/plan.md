# Plan — F06 Suporte a Provider Gemini

## Stage 0 — Revalidar interfaces atuais
- **Fazer:** reler `src/ingest.py` e `src/search.py` e localizar os pontos exatos de instanciação (`OpenAIEmbeddings`, `ChatOpenAI`) e a validação de `OPENAI_API_KEY`. Confirmar que `ingest_pdf()` e `search_prompt(question=None)` são a interface pública consumida por `chat.py`.
- **Arquivos:** (leitura) `src/ingest.py`, `src/search.py`, `src/chat.py`.
- **Verificar:** lista dos pontos a alterar; confirmação de que nenhuma assinatura pública precisa mudar.

## Stage 1 — Criar `src/providers.py` + testes
- **Fazer:** implementar `obter_provider()`, `validar_credencial_do_provider()`, `criar_embeddings()`, `criar_chat_llm()` conforme o spec (defaults Gemini: `models/gemini-embedding-001`, `gemini-2.5-flash`). Criar `tests/test_providers.py` (mockado, sem rede).
- **Arquivos:** `src/providers.py` (novo), `tests/test_providers.py` (novo).
- **Verificar:** `python -m py_compile src/providers.py` exit 0; `pytest tests/test_providers.py -q` verde; testes cobrem seleção openai/gemini e rejeição de credencial ausente/placeholder.

## Stage 2 — Integrar em `src/ingest.py`
- **Fazer:** trocar a instanciação de embeddings por `providers.criar_embeddings()`; usar `providers.validar_credencial_do_provider()`. Manter validações de `DATABASE_URL`/`PG_VECTOR_COLLECTION_NAME`, `pre_delete_collection=True`, chunk `1000/150` e o tratamento de erros PT existente.
- **Arquivos:** `src/ingest.py`.
- **Verificar:** `py_compile` exit 0; `pytest tests/test_ingest.py -q` verde (ajustar mocks se necessário, sem afrouxar asserts); assinatura `ingest_pdf()` inalterada.

## Stage 3 — Integrar em `src/search.py`
- **Fazer:** trocar embeddings por `providers.criar_embeddings()` e o chat por `providers.criar_chat_llm()`; manter `similarity_search_with_score(pergunta, k=10)` e o `PROMPT_TEMPLATE` **byte-idêntico**. `search_prompt(question=None)` inalterada.
- **Arquivos:** `src/search.py`.
- **Verificar:** `py_compile` exit 0; `pytest tests/test_search.py -q` verde, incluindo a guarda de igualdade integral do `PROMPT_TEMPLATE` e o assert de `k=10`.

## Stage 4 — `.env.example` + `README.md`
- **Fazer:** re-adicionar ao `.env.example` `LLM_PROVIDER`, `GOOGLE_API_KEY`, `GOOGLE_EMBEDDING_MODEL` (`models/gemini-embedding-001`), `GOOGLE_MODEL` (`gemini-2.5-flash`), com comentários. No `README.md`: documentar a seleção de provider, as variáveis, os modelos Gemini validados e a necessidade de **re-ingestão** ao trocar de provider.
- **Arquivos:** `.env.example`, `README.md`.
- **Verificar:** `grep` confirma as 4 variáveis no `.env.example` e no README; nenhum valor de chave real.

## Stage 5 — Ajustar restrições em `CLAUDE.md`
- **Fazer:** atualizar a seção "Restrições Obrigatórias do Enunciado" do `CLAUDE.md` para refletir os dois providers permitidos (OpenAI padrão / Gemini alternativa), mantendo invioláveis chunk `1000/150`, `k=10`, `PROMPT_TEMPLATE`, mesmo modelo de embedding na ingestão e busca, e a frase-padrão.
- **Arquivos:** `CLAUDE.md`.
- **Verificar:** leitura confirma a nota de dois providers sem afrouxar as restrições estruturais.

## Stage 6 — Final Verification
- **Fazer:** rodar os quality gates do CLAUDE.md e conferir o `contract.md` (blocos unitários/mockados). Os blocos de execução real (CA-06.3) são do `evaluator` e dependem de Docker de pé + chave Gemini válida.
- **Verificar:**
  - `python -m py_compile src/*.py` → exit 0;
  - `python -m pytest tests/ -q` → todos verdes;
  - CA-06.1/06.2/06.4 verificáveis sem rede; CA-06.3 encaminhado ao evaluator.
- **Ao concluir:** marcar F06 como `implemented` no `PRDProgress.json`.

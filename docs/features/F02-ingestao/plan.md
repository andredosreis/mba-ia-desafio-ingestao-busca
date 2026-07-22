# Plan — F02 Ingestão do PDF

## Stage 1 — Helpers puros + testes (sem rede)
- **Fazer:** implementar `carregar_paginas_pdf` e `dividir_paginas_em_chunks` em
  `src/ingest.py`; criar `tests/test_ingest.py` com o teste do splitter
  (chunks ≤ 1000, overlap entre consecutivos) usando documentos sintéticos.
- **Arquivos:** `src/ingest.py`, `tests/test_ingest.py`.
- **Verificar:** `python -m pytest tests/test_ingest.py -q` verde.

## Stage 2 — Vector store + orquestração (mockado)
- **Fazer:** implementar `criar_vector_store_para_ingestao` e o corpo de
  `ingest_pdf()`; testes com mock de `OpenAIEmbeddings`/`PGVector` assertando
  `pre_delete_collection=True` e `add_documents(chunks)`.
- **Arquivos:** `src/ingest.py`, `tests/test_ingest.py`.
- **Verificar:** pytest verde; `python -m py_compile src/ingest.py`.

## Stage 3 — Tratamento de erros (CA-02.3)
- **Fazer:** capturar PDF ausente, conexão recusada e env vazia → mensagens PT
  + `sys.exit(1)`; teste do caminho de PDF ausente.
- **Arquivos:** `src/ingest.py`, `tests/test_ingest.py`.
- **Verificar:** `PDF_PATH=inexistente.pdf venv/bin/python src/ingest.py` →
  mensagem PT, exit 1, sem traceback; idem com `docker compose stop postgres`
  (religar depois com `docker compose start postgres`).

## Stage 4 — Execução real (CA-02.1 + CA-02.2)
- **Fazer:** com banco de pé e `OPENAI_API_KEY` real: `venv/bin/python src/ingest.py`.
- **Verificar:**
  - exit 0 + mensagem de sucesso com nº de chunks;
  - `SELECT count(*)` na collection `document_chunks` > 0 (query do contract);
  - `SELECT max(length(document)) <= 1000`;
  - rodar de novo → contagem idêntica (sem duplicação).
- **Pré-condição externa:** `OPENAI_API_KEY` real no `.env` (pendência registrada na F01).

## Stage 5 — Final Verification
- **Fazer:** gates do CLAUDE.md (`py_compile`, `pytest tests/ -q`) + percorrer o
  `contract.md` bloco a bloco.
- **Ao concluir:** preencher seção F02 do `docs/APRENDIZADO.md`; atualizar
  `docs/PRDProgress.json` (F02 → `implemented`).

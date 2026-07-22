# Plan — F03 Busca Semântica e Resposta

## Stage 1 — `montar_contexto` + guarda do prompt (testes puros)
- **Fazer:** implementar `montar_contexto`; testes: concatenação `'\n\n'`,
  scores ignorados; teste-guarda do `PROMPT_TEMPLATE` (placeholders `{contexto}`/
  `{pergunta}` e frase padrão exata presentes).
- **Arquivos:** `src/search.py`, `tests/test_search.py`.
- **Verificar:** `python -m pytest tests/test_search.py -q` verde.

## Stage 2 — Chain LCEL (mockada)
- **Fazer:** implementar `criar_chain_rag` (embeddings → PGVector → busca k=10 →
  prompt fixo → ChatOpenAI → StrOutputParser); testes com mocks assertando
  `similarity_search_with_score(pergunta, k=10)` literal.
- **Arquivos:** `src/search.py`, `tests/test_search.py`.
- **Verificar:** pytest verde; `python -m py_compile src/search.py`.

## Stage 3 — `search_prompt` + `verificar_colecao_populada`
- **Fazer:** implementar os dois modos de `search_prompt` (None → chain;
  pergunta → resposta str), caminho de erro (mensagem PT + `None`) e
  `verificar_colecao_populada()` via SQLAlchemy.
- **Arquivos:** `src/search.py`, `tests/test_search.py`.
- **Verificar:** pytest verde cobrindo os dois modos + caminho de erro.

## Stage 4 — Verificação real (CA-03.1 + CA-03.2)
- **Pré-condição:** F02 executada (banco populado) e `OPENAI_API_KEY` real.
- **Fazer:** via CLI real:
  ```bash
  venv/bin/python -c "import sys; sys.path.insert(0,'src'); from search import search_prompt; print(search_prompt('<pergunta presente no PDF>'))"
  venv/bin/python -c "import sys; sys.path.insert(0,'src'); from search import search_prompt; print(search_prompt('Qual é a capital da França?'))"
  ```
- **Verificar:** 1ª → resposta coerente com o PDF; 2ª → frase padrão EXATA.

## Stage 5 — Final Verification
- **Fazer:** gates do CLAUDE.md (`py_compile`, `pytest tests/ -q`) + percorrer o
  `contract.md` bloco a bloco (incluindo inspeção de código do CA-03.3/03.4).
- **Ao concluir:** preencher seção F03 do `docs/APRENDIZADO.md`; atualizar
  `docs/PRDProgress.json` (F03 → `implemented`).

# Plan — F04 CLI de Chat

## Stage 0 — Revalidação de interfaces (pré-requisito)
- **Fazer:** conferir que F02/F03 estão `implemented`/`evaluated` e que
  `search.py` expõe `search_prompt()` (chain com `.invoke` | `None`) e
  `verificar_colecao_populada()` como na spec da F03.
- **Verificar:** `docs/PRDProgress.json` + leitura de `src/search.py`. Divergiu?
  Atualizar esta spec antes de codar.

## Stage 1 — Loop e formatação (testes com chain falsa)
- **Fazer:** implementar `COMANDOS_SAIDA`, `processar_pergunta`,
  `executar_loop_chat`; testes 1–3 e 6 da spec (input mockado, chain falsa).
- **Arquivos:** `src/chat.py`, `tests/test_chat.py`.
- **Verificar:** `python -m pytest tests/test_chat.py -q` verde.

## Stage 2 — `main()` com validação de ambiente (CA-04.4)
- **Fazer:** integrar `search_prompt()` + `verificar_colecao_populada()`;
  mensagens de orientação em PT; testes 4–5 da spec.
- **Arquivos:** `src/chat.py`, `tests/test_chat.py`.
- **Verificar:** pytest verde; `python -m py_compile src/chat.py`.

## Stage 3 — Verificação real na CLI
- **Pré-condição:** banco populado (F02) e chave real.
- **Fazer/Verificar:**
  - `printf '<pergunta do PDF>\nQual é a capital da França?\nsair\n' | venv/bin/python src/chat.py`
    → `Faça sua pergunta:`, dois pares `PERGUNTA/RESPOSTA` (2ª = frase padrão), despedida, exit 0;
  - sessão interativa com Ctrl+C e outra com Ctrl+D → encerramento gracioso;
  - com collection recém-limpa → mensagem "Execute primeiro: python src/ingest.py";
  - com `OPENAI_API_KEY` ausente → orientação, sem traceback.
- **Restaurar:** re-rodar a ingestão se a collection foi limpa no teste.

## Stage 4 — Final Verification
- **Fazer:** gates do CLAUDE.md (`py_compile`, `pytest tests/ -q`) + contract
  bloco a bloco.
- **Ao concluir:** preencher seção F04 do `docs/APRENDIZADO.md`; atualizar
  `docs/PRDProgress.json` (F04 → `implemented`).

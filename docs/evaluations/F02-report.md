# Evaluation Report — F02 Ingestão do PDF

- Data: 2026-07-21 · **reavaliada em 2026-09-03**
- Avaliador: `evaluator` (independente)
- Veredito: **APPROVED** na reavaliação (ver seção final). A avaliação original ficou **BLOCKED** por falta de quota na conta OpenAI — bloqueio de ambiente removido ao rodar com o provider Gemini da F06.
- Gates: 2/2 verdes (`py_compile` exit 0; `pytest` 36/36 na reavaliação — eram 12/12 à época)
- Método: execução real (Docker + banco real + chave real); nenhum mock. Chave jamais impressa.

## Pré-requisitos de ambiente

| Pré-requisito | Estado | Evidência |
|---|---|---|
| Banco de pé + extensão `vector` | ✅ | `postgres_rag Up (healthy)`; `SELECT extname` → `vector` |
| venv com dependências | ✅ | pytest/py_compile executados no venv |
| `OPENAI_API_KEY` real (não placeholder) | ⚠️ **PARCIAL** | chave real presente (164 chars, validação de placeholder passa), mas conta **sem quota** — API retorna `429 insufficient_quota` |
| `document.pdf` na raiz | ✅ | 34 páginas, conteúdo tabular de empresas (faturamento/ano) |

## Resultado por item do contrato

| Item | GWT | Resultado | Evidência |
|---|---|---|---|
| CA-02.1 | Chunks 1000/150 + embeddings persistidos | 🚧 **BLOCKED** | `python src/ingest.py` → `Erro na ingestão: Error code: 429 ... insufficient_quota`, exit 1. A ingestão real não pôde completar por falta de crédito na conta OpenAI. Código chegou até a chamada de embeddings (PDF carregado, chunks gerados, store criado) |
| CA-02.2 | Reexecução não duplica | 🚧 **BLOCKED** | Depende do CA-02.1 (precisa de uma ingestão bem-sucedida como base) |
| CA-02.3a | PDF ausente → mensagem PT, sem traceback | ✅ **PASS** | `PDF_PATH=arquivo_inexistente.pdf python src/ingest.py` → `Erro: arquivo PDF não encontrado em 'arquivo_inexistente.pdf'. Verifique PDF_PATH no .env.`, EXIT=1, sem `Traceback` |
| CA-02.3b | Banco parado → mensagem PT + orientação, sem traceback | ✅ **PASS** | Com `docker compose stop postgres`: `Erro: não foi possível conectar ao banco. Suba-o com: docker compose up -d`, EXIT=1, sem `Traceback`. Banco religado após o teste |

## Testes armadilha

N/A nesta feature (pertencem à avaliação de F03/F04 — exigem pipeline de busca funcional).

## Problemas encontrados

1. **[BLOQUEIO — ambiente] Conta OpenAI sem quota.** `429 insufficient_quota` na geração de embeddings. Não é defeito do código: o erro foi tratado sem traceback e com exit 1. *Reproduzir:* `python src/ingest.py` com banco de pé. *Resolver:* adicionar créditos/billing na conta OpenAI e reavaliar.
2. **[BAIXA — cosmético] Ruído `Collection not found` no stdout.** Impresso pela biblioteca `langchain_postgres` na primeira execução (quando o `pre_delete_collection` não encontra collection prévia). Não viola o contrato, mas polui a saída.
3. **[INFO] Erros de API repassados em inglês.** O `429` aparece com texto do SDK em inglês, prefixado por `Erro na ingestão:`. O contrato só exige PT amigável para PDF ausente e banco fora (ambos PASS) — registrado como limitação conhecida (achado nº 4 da revisão de código), não como FAIL.

## Recomendações

- Adicionar créditos à conta OpenAI e **reexecutar esta avaliação** para CA-02.1/CA-02.2 (os únicos itens pendentes).
- Status permanece `implemented` (sem promoção a `evaluated` até os blocos bloqueados passarem).
- O comportamento correto dos handlers de erro (CA-02.3) já está comprovado em execução real — na reavaliação, apenas os dois blocos de ingestão precisam rodar.


---

## Reavaliação (2026-09-03)

Refeita com `LLM_PROVIDER=gemini` (F06), banco real e `document.pdf` real. Todos os blocos que estavam BLOCKED foram executados.

| Item | Resultado | Evidência |
|---|---|---|
| **CA-02.1** | ✅ **PASS** | `venv/bin/python src/ingest.py` → `Ingestão concluída: 67 chunks armazenados na collection 'document_chunks'.`, **EXIT=0**, stderr vazio, 0 traceback. SQL do contrato: `count(*)` = **67** (> 0); `max(length(document))` = **999** (≤ 1000); `count(*) FILTER (WHERE embedding IS NULL)` = **0** |
| **CA-02.2** | ✅ **PASS** | Segunda execução → EXIT=0 e a mesma query retorna **67** (não 134). A collection é recriada (`pre_delete_collection=True`), não acumulada |
| **CA-02.3a** | ✅ **PASS** | `PDF_PATH=arquivo_inexistente.pdf venv/bin/python src/ingest.py` → **EXIT=1**, stderr: `Erro: arquivo PDF não encontrado em 'arquivo_inexistente.pdf'. Verifique PDF_PATH no .env.`, **0 traceback** |
| **CA-02.3b** | ✅ **PASS** | Com `docker compose stop postgres` → **EXIT=1**, stderr: `Erro: não foi possível conectar ao banco. Suba-o com: docker compose up -d`, **0 traceback**, 0 vazamento de chave. Banco religado após o teste |

### Problemas da avaliação original

- **#1 (bloqueio de ambiente — quota OpenAI):** **RESOLVIDO**, não por correção de código, mas pela F06, que permite rodar o pipeline com Gemini.
- **#2 (`Collection not found` no stdout):** **PERSISTE**. Reapareceu na primeira ingestão contra um banco recém-criado. É uma linha em inglês impressa pela biblioteca `langchain_postgres`, não pelo projeto. Severidade BAIXA: o contrato exige que a saída informe sucesso e o número de chunks — o que ocorre — mas polui a primeira execução, que é justamente a que o avaliador do desafio vai ver.
- **#3 (erros de API repassados em inglês):** não reincidiu nesta rodada.

### Nota sobre o texto do contrato

Os pré-requisitos deste contrato exigem nominalmente `OPENAI_API_KEY` real e `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`. O contrato é anterior à F06. A substância — chave real do provider ativo e modelo de embedding definido por variável de ambiente — foi atendida com o provider Gemini. Recomenda-se ao `spec-writer` generalizar o texto para "chave do provider ativo".

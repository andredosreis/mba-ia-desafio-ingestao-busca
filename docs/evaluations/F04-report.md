# Evaluation Report — F04 CLI de Chat

- Data: 2026-07-22 · **reavaliada em 2026-09-03**
- Avaliador: `evaluator` (independente)
- Veredito: **APPROVED** na reavaliação (ver seção final). A avaliação original ficou **BLOCKED** por Docker parado e conta OpenAI sem quota.
- Gates: 2/2 verdes (`py_compile` exit 0; `pytest` 36/36 na reavaliação — eram 26/26 à época)
- Método: gates reais + execução real dos blocos possíveis (CLI real, sem mock); revisão de código independente por agente menor (Sonnet). Chave jamais impressa.

## Pré-requisitos de ambiente

| Pré-requisito | Estado | Evidência |
|---|---|---|
| Banco de pé + extensão `vector` | ❌ **NÃO ATENDIDO** | `docker compose up -d` → `failed to connect to the docker API ... docker.sock: no such file or directory`. O **daemon do Docker está parado** (não apenas os containers) — não é possível subir o banco neste ambiente sem o usuário iniciar o Docker Desktop |
| **Ingestão executada (collection `document_chunks` > 0)** | ❌ **NÃO ATENDIDO** | Depende do banco de pé + embeddings; ambos indisponíveis (sem DB e sem quota OpenAI) |
| venv com dependências | ✅ | `pytest`/`py_compile` executados no venv |
| `OPENAI_API_KEY` real com quota | ❌ **NÃO ATENDIDO** | Chave real presente (len 164, validação de placeholder passa), conta **sem crédito** (`429 insufficient_quota` — ver F02/F03-report) |
| Terminal interativo (Ctrl+C/Ctrl+D) | ⚠️ N/A | Loop nunca inicia sem base populada; testes de sinal não puderam ser exercidos via CLI real |

## Gates de qualidade

| Gate | Saída | Exit |
|---|---|---|
| `python -m py_compile src/*.py` | (sem saída) | **0** ✅ |
| `python -m pytest tests/ -q` | `26 passed in 2.52s` | **0** ✅ |

## Resultado por item do contrato

| Item | GWT | Resultado | Evidência |
|---|---|---|---|
| CA-04.1 | Prompt inicial + loop processa >1 pergunta | 🚧 **BLOCKED** | Loop real exige base populada + LLM ativo. Fonte correta (`src/chat.py:22` `while True` → processa+imprime a cada pergunta). Suporte: teste unitário **não-vacuoso** `tests/test_chat.py:31` dirige 2 perguntas e asserta `invoked_questions == [...]` (2 ciclos). Sem execução real da CLI in-context |
| CA-04.2 | Formato `PERGUNTA: ` / `RESPOSTA: ` + fora-de-contexto → frase padrão | 🚧 **BLOCKED** | Sessão real (pipe + LLM) indisponível. Fonte correta: `src/chat.py:24` `input("PERGUNTA: ")`, `:31` `print(f"RESPOSTA: {resposta}")`. **Achado nº 1:** nenhum teste asserta o literal `"PERGUNTA: "` (o monkeypatch de `input` descarta o argumento `prompt`) — regressão nessa string passaria silenciosa. A frase padrão exige LLM real |
| CA-04.3 | Encerramento gracioso (`sair`/Ctrl+C/Ctrl+D, sem traceback) | 🚧 **BLOCKED** (parcial) | Vias interativas não exercidas via CLI real (loop não inicia sem base). Suporte forte: handlers presentes (`src/chat.py:27-29` comandos de saída; `:32-34` `except (KeyboardInterrupt, EOFError)`); testes **não-vacuosos** `tests/test_chat.py:45/58/72`. **Comprovado em execução real:** falha de init (banco fora) encerrou **sem traceback**, EXIT 0 (ver CA-04.4) |
| CA-04.4 | Ambiente não pronto → orientação PT clara, sem traceback, sem imprimir chave | ✅ **PASS** (2 de 3 vias, execução real) | **Chave ausente:** `env OPENAI_API_KEY="" venv/bin/python src/chat.py </dev/null` → `Falha ao iniciar a busca: Erro: OPENAI_API_KEY não configurada no .env ...` + `Não foi possível iniciar o chat...` + `Passos: 1) docker compose up -d 2) configure o .env (OPENAI_API_KEY) 3) python src/ingest.py`; **EXIT=0**, `grep -c 'Traceback'` = **0**, valor da chave nunca impresso, loop não iniciou. **Banco fora:** `printf 'pergunta\nsair\n' | venv/bin/python src/chat.py` → `Erro: não foi possível conectar ao banco. Suba-o com: docker compose up -d` + orientação; **EXIT=0**, sem traceback. **BLOCKED:** a via "base vazia" (mensagem literal `A base está vazia. Execute primeiro: python src/ingest.py`, `src/chat.py:47`) exige banco de pé + init bem-sucedido — coberta por teste não-vacuoso (`tests/test_chat.py:98`), mas não exercida em execução real |

## Testes armadilha

| Pergunta | Resposta obtida | OK? |
|---|---|---|
| Qual é a capital da França? | 🚧 BLOCKED (sem DB + sem quota — loop não inicia) | — |
| Quantos clientes temos em 2024? | 🚧 BLOCKED | — |
| Você acha isso bom ou ruim? | 🚧 BLOCKED | — |

**Nota:** os testes armadilha exigem base populada + chamada LLM real; ambos indisponíveis. A frase-padrão é produzida pelo LLM via `PROMPT_TEMPLATE` (F03) — não há hardcode/swallow indevido dela em `src/chat.py` (confirmado na revisão de código).

## Problemas encontrados

1. **[MÉDIA — cobertura de teste] Literal `PERGUNTA: ` não testado.** O contrato (CA-04.2) exige a string exata `PERGUNTA: `. A fonte está correta (`src/chat.py:24`), mas todos os testes que dirigem o loop fazem `monkeypatch.setattr("builtins.input", lambda prompt="": ...)`, descartando o `prompt` — o literal nunca é asExpected. *Reproduzir:* alterar `"PERGUNTA: "` para outro texto → `pytest` continua verde. *Resolver:* asserar o argumento passado ao mock de `input`, ou um teste com `capsys` que verifique o prompt. **Não é defeito de código** (a fonte cumpre o formato), e sim lacuna de teste.
2. **[MÉDIA — silent failure] `except Exception` amplo em `processar_pergunta`.** `src/chat.py:15` captura qualquer exceção (inclusive `TypeError`/`AttributeError` de bug real) e devolve `"Erro ao consultar o modelo..."`, indistinguível de uma resposta normal na transcrição da CLI. Não ameaça a frase-padrão (que vem do LLM), mas pode mascarar regressões reais. *Resolver:* estreitar para exceções de rede/API do SDK OpenAI.
3. **[BAIXA — vazamento teórico] `src/search.py:159` imprime `{e}` cru no stderr.** Fora do escopo de `chat.py` (território F03). Improvável conter chave, mas registrado por causa do requisito "chave jamais impressa".
4. **[BAIXA — teste] Asserção de `RESPOSTA:` por substring, sem contagem.** `tests/test_chat.py:40` usa `in` em vez de contar ocorrências; fortalecer para `captured.count("RESPOSTA:") == 2` prova diretamente os "DOIS blocos" da CA-04.1.
5. **[BLOQUEIO — ambiente] Docker daemon parado + OpenAI sem quota.** Impede CA-04.1, CA-04.2, a via "base vazia" da CA-04.4, as vias interativas da CA-04.3 e os testes armadilha. *Resolver:* iniciar o Docker Desktop, `docker compose up -d`, resolver a quota OpenAI (ou chave Gemini válida), rodar a ingestão, reavaliar.

## Recomendações

- **Destravar o ambiente:** iniciar o Docker Desktop → `docker compose up -d` → adicionar crédito OpenAI (ou chave Google `AIza...` válida em `GOOGLE_API_KEY`) → `python src/ingest.py`. Só então os blocos bloqueados podem passar.
- **Na reavaliação, reexecutar apenas os blocos bloqueados:** CA-04.1, CA-04.2 (com pergunta in-context, ex.: "Qual o faturamento da Alfa Energia S.A.?" → R$ 722.875.391,46), CA-04.3 interativo (`sair`, Ctrl+C, Ctrl+D), CA-04.4 via base vazia, e ≥3 perguntas armadilha esperando exatamente `"Não tenho informações necessárias para responder sua pergunta."`. CA-04.4 (chave ausente / banco fora) já tem evidência real definitiva.
- **Antes do APPROVED final (opcional, melhora robustez):** endereçar os achados nº 1 (asserar `PERGUNTA: `) e nº 2 (estreitar o `except`). Não bloqueiam a aprovação por si sós, mas fecham lacunas.
- **Status permanece `implemented`** — sem promoção a `evaluated` até os blocos bloqueados passarem em execução real.


---

## Reavaliação (2026-09-03)

Banco de pé, base populada (67 chunks), provider Gemini. **Todos os quatro blocos foram exercidos na CLI real** — inclusive os dois que a avaliação original não conseguiu executar (Ctrl+C e base vazia).

| Item | Resultado | Evidência |
|---|---|---|
| **CA-04.1** | ✅ **PASS** | `printf 'P1\nP2\nsair\n' \| venv/bin/python src/chat.py` → saída contém `Faça sua pergunta:`; **2 blocos** `RESPOSTA: ` (uma por pergunta — o loop processa mais de uma); **EXIT=0** |
| **CA-04.2** | ✅ **PASS** | Prompt `PERGUNTA: ` visível 3× na saída piped; cada resposta prefixada por `RESPOSTA: `; P2 = `Qual é a capital da França?` → `RESPOSTA: Não tenho informações necessárias para responder sua pergunta.` (frase padrão exata). Resolve o **achado nº 1** da avaliação original, que apontava a ausência de verificação do literal `PERGUNTA: ` — agora comprovado em execução real |
| **CA-04.3** | ✅ **PASS** (3 vias) | **`sair`:** `Encerrando. Até logo!`, EXIT=0, 0 traceback. **Ctrl+C (SIGINT real):** processo iniciado com `start_new_session=True`, `os.kill(pid, SIGINT)` enviado enquanto bloqueado no `input()` → stdout `'Faça sua pergunta:\nPERGUNTA: \nEncerrando. Até logo!\n'`, **stderr vazio**, **EXIT=0**, 0 traceback. **Ctrl+D/EOF:** `venv/bin/python src/chat.py < /dev/null` → despedida, EXIT=0, 0 traceback |
| **CA-04.4** | ✅ **PASS** (3 vias) | **Base vazia:** após `DELETE FROM langchain_pg_embedding` (67 linhas removidas) → `A base está vazia. Execute primeiro: python src/ingest.py`, EXIT=0, stderr vazio, 0 traceback, **loop não iniciou**; base restaurada em seguida. **Chave do provider ativo ausente** (`GOOGLE_API_KEY=""`): `Falha ao iniciar a busca: Erro: GOOGLE_API_KEY não configurada no .env (...)` + orientação em PT, EXIT=0, 0 traceback, **0 vazamento de chave**, loop não iniciou. **Variante literal do contrato** (`LLM_PROVIDER=openai` sem `OPENAI_API_KEY`): mensagem equivalente para `OPENAI_API_KEY` |

### Problemas da avaliação original

- **#1 (nenhum teste asserta o literal `PERGUNTA: `):** o ponto cego no teste unitário **permanece**, mas o comportamento passou a ser verificado em execução real nesta reavaliação. Severidade rebaixada para BAIXA; sugestão ao implementador: capturar o argumento `prompt` no monkeypatch de `input`.
- **Bloqueios de ambiente:** **RESOLVIDOS** (Docker de pé; provider Gemini no lugar da conta OpenAI sem quota).

### Nota sobre o texto do contrato

O CA-04.4 fala em `.env` sem `OPENAI_API_KEY`. Após a F06 a mensagem correta é a do provider indicado por `LLM_PROVIDER`. Ambas as vias foram testadas e passam.

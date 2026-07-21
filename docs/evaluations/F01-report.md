# Evaluation Report — F01 Fundação e Infraestrutura

- Data: 2026-07-20
- Avaliador: `evaluator` (independente — não confia no relato do implementador)
- Veredito: **APPROVED** (com achados não-bloqueantes, ver seção "Problemas encontrados")
- Gates: 2/2 aplicáveis verdes (`py_compile` ✅; `pytest` N/A por contrato)
- Método: execução real (Docker + banco real + venv real); nenhum mock. Credenciais nunca impressas.

## Pré-requisitos de ambiente

| Pré-requisito | Estado | Evidência |
|---|---|---|
| Docker daemon em execução | ✅ | `docker info` OK |
| Python 3 disponível | ✅ | `Python 3.12.13` |
| `document.pdf` na raiz | ✅ | `175328 bytes`, presente |
| Porta host 5432 | ✅ | ocupada pelo próprio `com.docker` (Postgres do compose) |
| `.env` derivado do `.env.example` | ✅ | existe; 6 chaves obrigatórias presentes |
| venv | ⚠️ | existe, mas criado via `uv` (sem `pip` embutido) — ver Problema #1 |

## Gates de qualidade

| Gate | Resultado | Evidência |
|---|---|---|
| `python -m py_compile src/*.py` | ✅ exit 0 | sintaxe dos stubs sã |
| `pytest` | N/A | sem `tests/` nesta feature (previsto no contrato) |

## Resultado por item do contrato

| Item | GWT | Resultado | Evidência |
|---|---|---|---|
| **CA-01.1** | Postgres saudável + extensão `vector` criada | ✅ **PASS** | `docker compose ps` → `postgres_rag ... Up (healthy)`; `docker compose logs bootstrap_vector_ext` → `CREATE EXTENSION` (sem erro, exit 0); `SELECT extname,extversion FROM pg_extension WHERE extname='vector'` → `vector | 0.8.5` (1 row) |
| **CA-01.2** | Dependências instalam sem conflito + imports OK | ✅ **PASS** (com ressalva) | `python -c "import langchain, langchain_openai, langchain_postgres, langchain_text_splitters, pypdf"` → `ok` (exit 0); versões instaladas batem 1:1 com `requirements.txt` (langchain 0.3.27, langchain-openai 0.3.30, langchain-postgres 0.0.15, langchain-text-splitters 0.3.9, pypdf 6.0.0, psycopg 3.2.9). **Ressalva:** o comando literal `pip install -r requirements.txt` não roda no venv atual (`No module named pip`) — ver Problema #1 |
| **CA-01.3** | `.env` com chaves e defaults corretos | ✅ **PASS** (com ressalva) | 6 chaves presentes; via `dotenv_values`: `OPENAI_EMBEDDING_MODEL` resolve p/ `text-embedding-3-small`, `DATABASE_URL == postgresql+psycopg://postgres:postgres@localhost:5432/rag`, `PDF_PATH == document.pdf` (arquivo existe). Guardrail: `OPENAI_API_KEY` nunca impressa (mascarada em todos os passos). **Ressalva:** linha do embedding tem aspas literais e a API key ainda é placeholder — ver Problemas #2 e #3 |

## Testes armadilha (perguntas fora do contexto)

| Pergunta | Resposta obtida | OK? |
|---|---|---|
| — | **N/A nesta feature** | — |

**Justificativa:** os testes armadilha exigem o pipeline RAG funcional (ingestão + busca + chat). Em F01, `src/ingest.py`, `src/search.py` e `src/chat.py` ainda são **stubs** (`ingest_pdf()`/`search_prompt()` retornam `pass`; `chat.py` imprime "Não foi possível iniciar o chat" porque `search_prompt()` devolve `None`). Não há chat executável para interrogar. Forjar essas respostas seria falsear evidência. **Estes testes são OBRIGATÓRIOS e serão executados na avaliação de F03 (busca/resposta) e F04 (CLI).**

## Problemas encontrados

1. **[MÉDIA → rebaixada p/ BAIXA] venv sem `pip`, criado por `uv` — diverge do método documentado.**
   O venv no disco não possui `pip` (`python -m pip` → `No module named pip`); as dependências foram instaladas via `uv pip install`. O contrato define o *Given* como `python3 -m venv venv && source venv/bin/activate` + `pip install -r requirements.txt`, que **não é reproduzível** nesse venv.
   *Mitigação verificada:* recriei um venv com o comando documentado (`python3 -m venv`) e ele **produz `pip 25.0.1`** normalmente — ou seja, o caminho oficial funciona; só o venv entregue foi construído por outra ferramenta. As dependências, além disso, estão instaladas e com versões idênticas ao `requirements.txt`. Por isso é não-bloqueante.
   *Como reproduzir:* `source venv/bin/activate && python -m pip --version`.
   *Recomendação:* ou recriar o venv com `python3 -m venv venv` + `pip install -r requirements.txt`, ou adotar `uv` oficialmente e alinhar CLAUDE.md/contrato para refletir a ferramenta real de instalação.

2. **[BAIXA] `OPENAI_EMBEDDING_MODEL` com aspas literais inconsistentes no `.env`.**
   A linha é `OPENAI_EMBEDDING_MODEL='text-embedding-3-small'` (com aspas simples), enquanto `DATABASE_URL`, `PDF_PATH`, `PG_VECTOR_COLLECTION_NAME` e `OPENAI_MODEL` estão sem aspas. O `python-dotenv` remove as aspas casadas, então o valor efetivo é correto (`text-embedding-3-small`) e não quebra o fluxo Python. Porém é uma inconsistência que morderia qualquer consumidor que leia o `.env` sem passar pelo dotenv (script shell, `os.environ` sem `load_dotenv`).
   *Como reproduzir:* `grep OPENAI_EMBEDDING_MODEL .env`.
   *Recomendação:* normalizar para `OPENAI_EMBEDDING_MODEL=text-embedding-3-small` (sem aspas), igual às demais chaves.

3. **[MÉDIA] `OPENAI_API_KEY` ainda é o placeholder do template.**
   O valor começa com `sk-sua...` (mesmo texto do `.env.example`), não uma chave real. **Não bloqueia F01** — o CA-01.3 exige apenas a *presença* da chave e a feature é infra-only, sem chamada de API. Mas é **bloqueador rígido de F02 (ingestão/embeddings) e F03 (busca/resposta)**, que fazem chamadas reais à OpenAI. O implementador registrou isso como pendência no `APRENDIZADO.md` (transparência correta).
   *Recomendação:* preencher uma chave real antes de iniciar a Wave 2.

4. **[BAIXA] Container órfão de outro compose no ambiente.**
   `docker compose ps -a` lista `mba-rag-postgres` (`pgvector/pgvector:pg16`, serviço `db`), Exited, de ~3 semanas — resquício de uma configuração de compose anterior/alternativa. Está parado, mas pode causar confusão ou disputa de porta 5432 se subir por engano.
   *Como reproduzir:* `docker compose ps -a`.
   *Recomendação:* `docker rm mba-rag-postgres` e garantir que só o `docker-compose.yml` deste projeto define o Postgres.

5. **[INFO] `OPENAI_MODEL=gpt-4o-mini` diverge da sugestão do enunciado (`gpt-5-nano`).**
   Fora do escopo do contrato de F01 (CA-01.3 não valida o valor de `OPENAI_MODEL`). `gpt-4o-mini` é um modelo válido; o enunciado apenas *sugere* `gpt-5-nano`. Registrado para decisão consciente na avaliação de F03/F04.

## Verificação da correção do `docker-compose.yml` (contexto do bug de F01)

O serviço `bootstrap_vector_ext` foi corrigido de `command` string (que sofria shell-split do Compose e passava só `PGPASSWORD=postgres` para o `sh -c`) para `command` como **lista YAML de um elemento**. Confirmado em execução:
- `docker compose ps -a` mostra o `COMMAND` como `/bin/sh -c 'PGPASSW…'` (script inteiro num único argumento).
- Logs mostram `CREATE EXTENSION`; `pg_extension` confirma `vector 0.8.5`.
A análise de causa-raiz no `APRENDIZADO.md` está tecnicamente correta e a correção é idiomática.

## Recomendações (resumo priorizado)

- **Antes da Wave 2 (F02/F03):** resolver o Problema #3 (chave real da OpenAI) — é o único bloqueador funcional real do próximo passo.
- **Higiene (a qualquer momento):** Problemas #2 (aspas no `.env`) e #4 (container órfão) — correções de 1 minuto.
- **Alinhamento de processo:** decidir oficialmente entre `pip` e `uv` (Problema #1) e refletir no CLAUDE.md/contrato, para o ambiente reproduzível não divergir da doc.
- Nenhum desses achados invalida o objetivo de F01: **infra pronta para F02–F05** (banco + pgVector de pé, deps importáveis com versões corretas, `.env` válido). Por isso o veredito é **APPROVED**.

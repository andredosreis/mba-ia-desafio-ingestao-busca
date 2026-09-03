# Evaluation Report — F03 Busca Semântica e Resposta

- Data: 2026-07-21 · **reavaliada em 2026-09-03**
- Avaliador: `evaluator` (independente)
- Veredito: **APPROVED** na reavaliação (ver seção final). A avaliação original ficou **BLOCKED** por falta de quota na conta OpenAI e base vazia.
- Gates: 2/2 verdes (`py_compile` exit 0; `pytest` 36/36 na reavaliação — eram 12/12 à época)
- Método: inspeção de código com evidência executada + tentativa de execução real. Chave jamais impressa.

## Pré-requisitos de ambiente

| Pré-requisito | Estado | Evidência |
|---|---|---|
| Banco de pé + extensão `vector` | ✅ | `postgres_rag Up (healthy)`; `vector` presente |
| **Ingestão da F02 executada (collection > 0)** | ❌ **NÃO ATENDIDO** | Ingestão bloqueada por `429 insufficient_quota` (ver F02-report) — collection vazia |
| `OPENAI_API_KEY` real com quota | ❌ **NÃO ATENDIDO** | Chave real, conta sem crédito |

## Resultado por item do contrato

| Item | GWT | Resultado | Evidência |
|---|---|---|---|
| CA-03.1 | Resposta baseada só no conteúdo do PDF | 🚧 **BLOCKED** | Exige banco populado + chamada LLM real. Perguntas já preparadas a partir do PDF real (34 págs, tabela de empresas): "Qual o faturamento da Alfa Energia S.A.?" (esperado: R$ 722.875.391,46) |
| CA-03.2 | Fora do contexto → frase padrão exata | 🚧 **BLOCKED** | Exige chamada LLM real |
| CA-03.3 | `similarity_search_with_score(query, k=10)` literal + prompt intocado | ✅ **PASS** | `src/search.py:123` → `vector_store.similarity_search_with_score(pergunta, k=10)` (chamada direta, sem wrapper); teste unitário `tests/test_search.py:95` asserta k=10; comparação programática do bloco `PROMPT_TEMPLATE` atual vs stub original (`git show adfb91f:src/search.py`) → `IDENTICO ao stub: True`; teste de igualdade integral do template na suite |
| CA-03.4 | Mesmo modelo de embedding da ingestão | ✅ **PASS** | `src/ingest.py:51` e `src/search.py:88` leem a MESMA env var `OPENAI_EMBEDDING_MODEL` via `os.getenv`; nenhum modelo hardcoded (grep sem ocorrências de literais de modelo); `.env.example` define `text-embedding-3-small` |

## Testes armadilha

| Pergunta | Resposta obtida | OK? |
|---|---|---|
| Qual é a capital da França? | 🚧 BLOCKED (sem quota) | — |
| Quantos clientes temos em 2024? | 🚧 BLOCKED (sem quota) | — |
| Você acha isso bom ou ruim? | 🚧 BLOCKED (sem quota) | — |

**Nota:** o comportamento de falha do módulo foi verificado em execução real: com banco fora,
`search_prompt()` imprimiu `Erro: não foi possível conectar ao banco. Suba-o com: docker compose up -d`
e retornou `None` (contrato do stub do chat respeitado, sem traceback).

## Problemas encontrados

1. **[BLOQUEIO — ambiente] Sem quota OpenAI + collection vazia.** Impede CA-03.1, CA-03.2 e os testes armadilha. *Resolver:* adicionar créditos, rodar `python src/ingest.py`, reavaliar.

## Recomendações

- Após resolver a quota: reexecutar SOMENTE os blocos bloqueados (CA-03.1, CA-03.2 e as 3+ perguntas armadilha) — CA-03.3/CA-03.4 já têm evidência definitiva.
- Status permanece `implemented` até a reavaliação completa.
- Perguntas dentro-do-contexto sugeridas para a reavaliação (derivadas do PDF real): faturamento da Alfa Energia S.A.; ano de fundação da Alfa Agronegócio Indústria (1931).


---

## Reavaliação (2026-09-03)

Base populada (67 chunks, 3072 dimensões, provider Gemini). Executada com o comando literal do gate do contrato.

| Item | Resultado | Evidência |
|---|---|---|
| **CA-03.1** | ✅ **PASS** | `search_prompt('Qual o faturamento da Alfa Energia S.A.?')` → `O faturamento da Alfa Energia S.A. é R$ 722.875.391,46.` — string não vazia, sem exceção. **Verdade de referência conferida contra o documento por SQL**, não contra a palavra do LLM: `SELECT regexp_matches(document, ...)` sobre a collection devolve `Alfa Energia S.A. R$ 722.875.391,46 1972`. Nenhuma informação ausente do PDF na resposta |
| **CA-03.2** | ✅ **PASS** | Comparação byte a byte em Python (`resposta == FRASE`): `'Qual é a capital da França?'` → `True`; `'Você acha isso bom ou ruim?'` → `True`. Sem texto adicional |
| **CA-03.3** | ✅ **PASS** | `src/search.py:118` → `similarity_search_with_score(pergunta, k=10)`; `tests/test_search.py:97` afirma `k=10` na chamada; `PROMPT_TEMPLATE` comparado programaticamente com `git show adfb91f:src/search.py` → **byte-idêntico** |
| **CA-03.4** | ✅ **PASS** na substância | `src/ingest.py:65` e `src/search.py:102` chamam a **mesma** função `criar_embeddings()`; grep por literais de modelo em `ingest.py`/`search.py` → **nenhum** (nada hardcoded); o modelo vem de `OPENAI_EMBEDDING_MODEL` ou `GOOGLE_EMBEDDING_MODEL` em `src/providers.py`; `.env.example:16` define `text-embedding-3-small`. **Prova em runtime:** a busca recuperou corretamente vetores gravados na ingestão — se os modelos divergissem, haveria erro de dimensão ou resultados sem sentido |

### Nota sobre o texto do contrato (CA-03.4)

O contrato exige literalmente que "ambos criam `OpenAIEmbeddings` lendo a MESMA variável `OPENAI_EMBEDDING_MODEL`". Após a F06 isso deixou de ser literalmente verdadeiro: os dois chamam `providers.criar_embeddings()`, que decide a classe conforme `LLM_PROVIDER`.

Avaliado como PASS porque a **exigência substantiva** — mesmo modelo de embedding nas duas pontas, sem hardcode — não só é atendida como passou a ser garantida por construção, e não mais por coincidência entre dois trechos de código. Recomenda-se ao `spec-writer` atualizar a redação para refletir a fábrica de providers.

### Problemas da avaliação original

- **#1 (sem quota OpenAI + collection vazia):** **RESOLVIDO** pela F06 (provider Gemini) e pela ingestão bem-sucedida.

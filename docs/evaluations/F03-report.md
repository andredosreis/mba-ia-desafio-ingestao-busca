# Evaluation Report — F03 Busca Semântica e Resposta

- Data: 2026-07-21
- Avaliador: `evaluator` (independente)
- Veredito: **BLOCKED** (bloqueio de ambiente — sem quota OpenAI e sem base ingerida; itens de inspeção de código PASSARAM)
- Gates: 2/2 verdes (`py_compile` exit 0; `pytest` 12/12)
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

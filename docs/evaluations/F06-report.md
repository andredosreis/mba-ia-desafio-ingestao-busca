# Evaluation Report — F06 Suporte a Provider Gemini (alternativa à OpenAI)

- Data: 2026-09-03
- Avaliador: `evaluator`
- Veredito: **REJECTED** (1 cláusula bloqueante do CA-06.3; todo o resto verde)
- Gates: 2/2 verdes (`py_compile` exit 0; `pytest` 36/36)
- Método: execução real (Docker + banco real + chave Gemini real), verdade de referência extraída do banco por SQL, teste de mutação para provar não-vacuidade da suíte. Nenhum mock nos blocos de execução. Chave jamais impressa.

> ⚠️ **Ressalva de independência.** Esta avaliação foi conduzida na mesma sessão que implementou a F06 — o harness prevê um agente separado justamente para evitar isso. Compensei tratando o código como suspeito: toda afirmação abaixo tem evidência executada, a verdade de referência das respostas veio de `SELECT` no Postgres (não da palavra do LLM nem do relato do implementador), e a suíte foi submetida a mutação deliberada. Ainda assim, a limitação fica registrada: uma reavaliação por agente independente é recomendável antes da entrega.

## Pré-requisitos de ambiente

| Pré-requisito | Estado | Evidência |
|---|---|---|
| Banco de pé + extensão `vector` | ✅ | `postgres_rag Up (healthy)`; `SELECT extversion` → `vector 0.8.5` |
| Ingestão executada com Gemini (3072d) | ✅ | `SELECT count(*), vector_dims(embedding)` → `chunks=67, dims=3072` |
| `GOOGLE_API_KEY` real (formato `AIza…`) | ✅ | presente, `len=39`, prefixo `AIza` confirmado (valor nunca impresso) |
| `LLM_PROVIDER=gemini` no `.env` | ✅ | `dotenv_values` → `gemini` |
| `langchain-google-genai` pinado | ✅ | `requirements.txt:33` → `langchain-google-genai==2.1.9` |

## Gates de qualidade

| Gate | Saída | Exit |
|---|---|---|
| `python -m py_compile src/*.py` | (sem saída) | **0** ✅ |
| `python -m pytest tests/ -q` | `36 passed in 3.33s` | **0** ✅ |
| `pytest` sem chaves e com `DATABASE_URL` inválida | `36 passed in 2.67s` | **0** ✅ — prova que a suíte não depende de rede nem de API key |

## Teste de mutação (não-vacuidade da suíte)

Cada mutação foi aplicada, a suíte rodada, e o arquivo restaurado com `diff -q` confirmando byte-igualdade ao original.

| Mutação | Resultado | Veredito |
|---|---|---|
| `obter_provider` default `openai` → `gemini` | 2 failed | ✅ detectada |
| `GEMINI_EMBEDDING_MODEL_PADRAO` → `models/embedding-001` | **36 passed** | ❌ **SOBREVIVEU** (Problema #2) |
| `GEMINI_CHAT_MODEL_PADRAO` → `gemini-1.5-flash` | **36 passed** | ❌ **SOBREVIVEU** (Problema #2) |
| Validação de credencial desativada | 3 failed | ✅ detectada |
| `k=10` → `k=5` | 1 failed | ✅ detectada |
| `PROMPT_TEMPLATE` alterado em 1 caractere | 1 failed | ✅ detectada |

## Resultado por item do contrato

| Item | GWT | Resultado | Evidência |
|---|---|---|---|
| **CA-06.1** | Seleção de provider por `LLM_PROVIDER` | ✅ **PASS** (com achado) | Suíte cobre `gemini`, `openai`, ausente (default) e inválido; `pytest` verde sem rede e sem chaves. `gemini` → `GoogleGenerativeAIEmbeddings`/`ChatGoogleGenerativeAI`, provider inativo com `assert_not_called()`. `LLM_PROVIDER=foo` via CLI real → `Falha ao iniciar a busca: Erro: LLM_PROVIDER='foo' inválido. Use um destes: openai, gemini.`, sem traceback. Defaults corretos por inspeção (`src/providers.py:22-23` → `models/gemini-embedding-001`, `gemini-2.5-flash`) e comprovados em execução real (vetores 3072d). **Achado:** o assert dos defaults é tautológico — ver Problema #2 |
| **CA-06.2** | Restrições e assinaturas preservadas | ✅ **PASS** | `src/search.py:118` → `similarity_search_with_score(pergunta, k=10)` literal; `src/ingest.py:45-46` → `chunk_size=1000`/`chunk_overlap=150`; `PROMPT_TEMPLATE` comparado programaticamente com o stub original (`git show adfb91f:src/search.py`) → **byte-idêntico, 780 chars vs 780**; assinaturas `def ingest_pdf() -> None` (`src/ingest.py:76`) e `def search_prompt(question: str \| None = None)` (`src/search.py:135`) inalteradas; `criar_embeddings()` chamada nos DOIS lados (`src/ingest.py:65`, `src/search.py:102`); grep por instanciação direta de `OpenAIEmbeddings(`/`ChatOpenAI(`/`GoogleGenerativeAIEmbeddings(`/`ChatGoogleGenerativeAI(` em `ingest.py`/`search.py`/`chat.py` → **nenhuma ocorrência** |
| **CA-06.3** | Ingestão e busca reais com Gemini | ❌ **FAIL** (4 de 5 cláusulas passam; 1 falha) | **Ingestão:** `python src/ingest.py` → `Ingestão concluída: 67 chunks armazenados na collection 'document_chunks'.`, **EXIT=0**, stderr vazio, 0 traceback, 0 vazamento de chave. **Coleção:** SQL → `document_chunks \| 67 \| 3072` ✅; reexecução manteve 67 (não duplicou). **Dentro do contexto:** faturamento da Alfa Energia S.A. → `R$ 722.875.391,46` ✅ (verdade de referência por SQL: `Alfa Energia S.A. R$ 722.875.391,46 1972`); ano da Alfa Energia Holding → `1971` ✅ (SQL: `Alfa Energia Holding R$ 858.537,02 1971`). **Fora do contexto:** 4/4 byte-exatas. **Chave:** 0 ocorrências no output. ❌ **Cláusula "nenhum traceback cru" VIOLADA:** 2 tracebacks em stderr ao encerrar — ver Problema #1 |
| **CA-06.4** | Documentação e higiene | ✅ **PASS** | `.env.example` contém as 4 variáveis com placeholder na chave (`GOOGLE_API_KEY=AIza-sua-chave-aqui`); README documenta seleção de provider, `models/gemini-embedding-001`, `gemini-2.5-flash` e a re-ingestão obrigatória, e **todas as 10 variáveis** do `.env.example` estão documentadas (0 não-documentadas — CA-05.2 sem regressão); `CLAUDE.md:40` reflete dois providers mantendo `chunk_size=1000`/`chunk_overlap=150` (`:39`), `k=10` (`:41`), prompt fixo (`:42`) e frase-padrão (`:44`); `git grep -nE 'sk-(proj-)?[A-Za-z0-9]{24,}\|AIza[A-Za-z0-9_-]{30,}'` → **nenhuma** chave real versionada; `.env` não rastreado |

## Testes armadilha

Comparação **byte a byte** contra `"Não tenho informações necessárias para responder sua pergunta."`

| Pergunta | Resposta obtida | OK? |
|---|---|---|
| Qual é a capital da França? | `Não tenho informações necessárias para responder sua pergunta.` | ✅ byte-exata |
| Quantos clientes temos em 2024? | `Não tenho informações necessárias para responder sua pergunta.` | ✅ byte-exata |
| Você acha isso bom ou ruim? | `Não tenho informações necessárias para responder sua pergunta.` | ✅ byte-exata |
| Quem descobriu o Brasil? | `Não tenho informações necessárias para responder sua pergunta.` | ✅ byte-exata |

Mínimo exigido: 3. Executadas: 4. Nenhuma resposta usou conhecimento externo ao PDF.

### Transcrição da sessão real (evidência)

```text
Faça sua pergunta:
PERGUNTA: RESPOSTA: O faturamento da Alfa Energia S.A. é R$ 722.875.391,46.

PERGUNTA: RESPOSTA: A Alfa Energia Holding foi fundada em 1971.

PERGUNTA: RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

PERGUNTA: RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

PERGUNTA: RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

PERGUNTA: RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

PERGUNTA: Encerrando. Até logo!
```

## Problemas encontrados

### 1. [BLOQUEANTE — CA-06.3] Traceback cru do gRPC ao encerrar toda sessão real

O contrato exige, literalmente, "nenhum traceback cru". Ao encerrar, o usuário vê:

```text
Traceback (most recent call last):
  File "src/python/grpcio/grpc/_cython/_cygrpc/aio/grpc_aio.pyx.pxi", line 110, in grpc._cython.cygrpc.shutdown_grpc_aio
  ...
AttributeError: 'NoneType' object has no attribute 'POLLER'
Exception ignored in: 'grpc._cython.cygrpc.AioChannel.__dealloc__'
```

**Caracterização (todas as combinações testadas):**

| Cenário | Tracebacks |
|---|---|
| `sair` sem fazer pergunta (3 execuções) | 0, 0, 0 |
| 1 pergunta + `sair` (3 execuções) | **2, 2, 2** |
| 1 pergunta + EOF (Ctrl+D) | **2** |
| `python src/ingest.py` (mesma lib, via embeddings) | 0 |

O gatilho é a **chamada real ao LLM**: o canal assíncrono gRPC aberto por `ChatGoogleGenerativeAI` é destruído na finalização do interpretador, quando o módulo já foi parcialmente desmontado. É **100% determinístico** e atinge toda sessão de uso real — a única forma de não ver o traceback é não fazer nenhuma pergunta.

- **Severidade:** MÉDIA. Não é código do projeto (`grpcio==1.74.0`, dependência transitiva), sai **depois** de `Encerrando. Até logo!` e o **exit code permanece 0**. Nenhuma resposta é afetada. Mas é a última coisa que o avaliador do desafio vê na tela, e a cláusula do contrato é explícita.
- **Reproduzir:** `printf 'Qual o faturamento da Alfa Energia S.A.?\nsair\n' | python src/chat.py`
- **Não regride para OpenAI:** o caminho `LLM_PROVIDER=openai` não usa gRPC. Não pôde ser confirmado em execução por falta de quota na conta OpenAI.

### 2. [MÉDIA — CA-06.1] Assert tautológico dos modelos default: mutação sobrevive

`tests/test_providers.py:63,65,171-172` afirma o modelo default comparando com a **própria constante importada** do módulo sob teste:

```python
mock_embeddings_google.assert_called_once_with(model=GEMINI_EMBEDDING_MODEL_PADRAO)
```

Se alguém alterar `GEMINI_EMBEDDING_MODEL_PADRAO` para qualquer string, o teste continua verde — o esperado muda junto com o código. Comprovado: trocar o default para `models/embedding-001` e para `gemini-1.5-flash` manteve **36 passed** nas duas mutações.

Isso importa porque esses dois nomes são exatamente os que o spec marca como **404** — e o `.env` da máquina de fato continha `models/embedding-001` antes desta feature. A constante é a rede de segurança de todo o caminho Gemini, e hoje ela não tem guarda de regressão.

- **Severidade:** MÉDIA. O valor atual está correto (verificado por inspeção e por execução real com vetores 3072d), mas um typo futuro passaria pela suíte inteira e só apareceria como 404 + ~60s de retries em produção.
- **Reproduzir:** `sed -i '' 's|models/gemini-embedding-001|models/embedding-001|' src/providers.py && python -m pytest tests/ -q` → 36 passed.
- **Correção sugerida:** assertar o **literal** (`model="models/gemini-embedding-001"`) em vez da constante.

### 3. [INFO] Independência da avaliação comprometida

Implementador e avaliador foram a mesma sessão. Mitigado por evidência executada, verdade de referência via SQL e teste de mutação, mas não elimina o viés. Ver ressalva no topo.

## Recomendações

1. **Corrigir o Problema #1** para destravar a F06. A causa é a destruição do canal gRPC na saída do interpretador; a correção é localizada em `src/chat.py` (encerrar o processo antes de o gRPC desmontar, ou silenciar o ruído de shutdown dessa lib). Voltar para `implement-feature` — o avaliador não corrige código.
2. **Corrigir o Problema #2** trocando os asserts tautológicos por literais. Barato e elimina um ponto cego real.
3. **Reavaliar F02–F05.** Com o Gemini funcionando e a base populada, os critérios que estavam BLOCKED por falta de quota na OpenAI (CA-02.1, CA-02.2, CA-03.1, CA-03.2, CA-04.1/2/3, CA-05.1) agora rodam de verdade — esta avaliação já exerceu boa parte deles incidentalmente, todos com sucesso.
4. Status da F06 permanece **`implemented`** (sem promoção a `evaluated`).

---

## Atualização pós-correção (2026-09-03)

Os Problemas #1 e #2 foram corrigidos após este veredito. Registro factual das correções e da reverificação — **o veredito REJECTED acima permanece como o resultado da avaliação original**; a promoção a `evaluated` depende de nova rodada do `evaluator`.

### Problema #1 — causa-raiz e correção

Depuração por bisseção. Uma matriz de cenários mínimos (só construir embeddings; `+ embed_query`; `+ chat`; só chat), nos dois transportes, deu **0 traceback em 8 de 8** — derrubando a hipótese de que o `ChatGoogleGenerativeAI` sozinho bastava. A reprodução só ocorreu com o código real (`search_prompt()` + `invoke` → 2 tracebacks; sem `invoke` → 0), o que envolve também o `PGVector`: a conexão SQLAlchemy viva no fim do processo altera a ordem de desmontagem dos módulos na finalização do interpretador.

Causa-raiz: `GoogleGenerativeAIEmbeddings.validate_environment` (`langchain_google_genai/embeddings.py:110`) constrói **incondicionalmente** um `build_generative_async_service` com transporte `grpc_asyncio`, mesmo no caminho síncrono que nunca o utiliza. Esse `AioChannel` é destruído no shutdown, quando o módulo gRPC já foi desmontado → `AttributeError: 'NoneType' object has no attribute 'POLLER'`.

Correção: `transport="rest"` nas duas fábricas Gemini de `src/providers.py`, via a constante única `TRANSPORTE_GEMINI` (`src/providers.py:29`) — o valor não fica repetido nos dois construtores.

### Problema #2 — correção

`tests/test_providers.py` deixou de importar `GEMINI_EMBEDDING_MODEL_PADRAO`/`GEMINI_CHAT_MODEL_PADRAO` do módulo sob teste. Os valores esperados passaram a ser literais definidos uma única vez no próprio arquivo de teste (`MODELO_EMBEDDING_GEMINI_ESPERADO`, `MODELO_CHAT_GEMINI_ESPERADO`, `TRANSPORTE_GEMINI_ESPERADO`).

### Reverificação

| Verificação | Antes | Depois |
|---|---|---|
| Mutação `models/gemini-embedding-001` → `models/embedding-001` | 36 passed (sobreviveu) | **2 failed** ✅ |
| Mutação `gemini-2.5-flash` → `gemini-1.5-flash` | 36 passed (sobreviveu) | **1 failed** ✅ |
| Mutação `TRANSPORTE_GEMINI` `rest` → `grpc` | (não existia) | **2 failed** ✅ |
| `python src/chat.py`, 1 pergunta + `sair` | 2 tracebacks (3/3 execuções) | **0 tracebacks (5/5 execuções)** ✅ |
| `python src/chat.py`, 1 pergunta + EOF | 2 tracebacks | **0 tracebacks** ✅ |
| Bateria de 6 perguntas | 2 tracebacks | **stderr VAZIO**, exit 0 ✅ |
| `python src/ingest.py` com REST | — | exit 0, `67 chunks`, `dims=3072`, stderr vazio ✅ |
| Gates | 2/2 | **2/2** (`py_compile` exit 0; `pytest` 36/36) ✅ |
| Respostas dentro do contexto | corretas | corretas (`R$ 722.875.391,46`; `1971`) ✅ |
| Armadilhas fora do contexto | 4/4 byte-exatas | **4/4 byte-exatas** ✅ |

Restauração de todos os arquivos mutados confirmada por `diff -q` contra o backup original.

---

## Avaliação independente (2026-09-03) — veredito final

A ressalva de independência registrada no topo deste report foi sanada: um avaliador separado, sem participação na implementação, reavaliou a F06 do zero, formando juízo **antes** de ler este documento.

**Veredito: APPROVED.** F06 promovida a `evaluated`.

Ele não reaproveitou nenhuma evidência daqui. Entre o que produziu de forma independente:

- Escreveu o próprio script mockado contra `src.providers` em vez de confiar em `tests/test_providers.py` — 12/12 asserts, sem rede, cobrindo `gemini`, `openai`, `LLM_PROVIDER` ausente e valor inválido nas três funções públicas.
- Comparou o `PROMPT_TEMPLATE` com o stub original por **AST + SHA-256** (`fe7097c2…15eb73`, 780 chars nos dois) — método diferente do usado aqui, mesmo resultado.
- Rodou o próprio teste de mutação (modelo de embedding, transporte, `k=10`): todas detectadas.
- Varreu **todos os blobs de todo o histórico do git** (`git rev-list --objects --all`) atrás de chaves reais → zero. Escopo maior que o `git grep` sobre arquivos rastreados usado aqui.
- Confirmou stderr **completamente vazio** em execução real com 6 perguntas, validando de forma independente a correção do transporte REST.
- 9 perguntas fora do contexto no total, comparadas byte a byte contra os bytes UTF-8 esperados.

### Achado adicional dele, fora do texto do contrato

`src/chat.py`, em `processar_pergunta()`, retornava `"Erro ao consultar o modelo. Verifique sua conexão e a OPENAI_API_KEY."` mesmo com `LLM_PROVIDER=gemini` — mandando o usuário do Gemini conferir a variável errada. Ele não reprovou a F06 por isso (nenhum CA-06.x cobre essa string), mas registrou como inconsistente com o espírito do CA-06.4.

Correção aplicada: a mensagem passou a citar "a chave do provider ativo (OPENAI_API_KEY ou GOOGLE_API_KEY)". Reproduzido com `GOOGLE_API_KEY` inválida e confirmado em execução real.

### Limitação que permanece

O caminho `LLM_PROVIDER=openai` **nunca foi exercitado em execução real** — nem por este report, nem pelo avaliador independente — porque a conta OpenAI está sem quota (429). Está coberto por testes unitários mockados, verificados independentemente por ele. É a única parte da F06 sem evidência de execução real.

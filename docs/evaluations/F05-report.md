# Evaluation Report — F05 README e Entrega

- Data: 2026-07-22
- Avaliador: `evaluator` (independente)
- Veredito: **BLOCKED** (motivo único: bloqueio de ambiente impede o dry-run real da CA-05.1. O defeito de documentação da CA-05.2 foi **CORRIGIDO e re-verificado** nesta sessão — ver "Atualização pós-correção")
- Gates: 2/2 verdes (`py_compile` exit 0; `pytest` 26/26)
- Método: inspeção de conteúdo + verificações determinísticas reais (git index, `git grep`, `gh`, match byte-exato). Nenhuma chave impressa (valores mascarados).

## Pré-requisitos de ambiente

| Pré-requisito | Estado | Evidência |
|---|---|---|
| F01–F04 avaliadas + fluxo completo funcional | ⚠️ **PARCIAL** | F01 `evaluated`; F02/F03/F04 `implemented` com avaliação **BLOCKED** (sem quota/DB) — o fluxo ponta-a-ponta nunca rodou de verdade |
| Docker + Python 3 disponíveis | ❌ **NÃO ATENDIDO** | Docker **daemon parado** (`docker.sock` inexistente) — impossível subir o banco nesta sessão |
| `OPENAI_API_KEY` real para o dry-run | ❌ **NÃO ATENDIDO** | Conta OpenAI **sem quota** (`429 insufficient_quota`, ver F02–F04) |
| Repositório GitHub público acessível | ✅ | `gh repo view` → `andredosreis/mba-ia-desafio-ingestao-busca`, `visibility: PUBLIC` |

## Gates de qualidade

| Gate | Saída | Exit |
|---|---|---|
| `python -m py_compile src/*.py` | (sem saída) | **0** ✅ |
| `python -m pytest tests/ -q` | `26 passed in 2.49s` | **0** ✅ |

## Resultado por item do contrato

| Item | GWT | Resultado | Evidência |
|---|---|---|---|
| CA-05.1 | Execução completa guiada só pelo README (dry-run real) | 🚧 **BLOCKED** | Exige `docker compose up -d` → `ingest` → `chat` com LLM real. Docker daemon parado + sem quota → o dry-run ponta-a-ponta não pôde ser executado. **Suporte estático:** a sequência de comandos do README é autocontida e completa (clone → venv → `pip install -r requirements.txt` → `cp .env.example .env` + editar chave → `docker compose up -d` → `python src/ingest.py` → `python src/chat.py`); URL de clone confere com o repo público. Não substitui a execução real |
| CA-05.2 | Conteúdo obrigatório documentado | ✅ **PASS** (após correção) | ✅ pré-requisitos (Docker/Compose, Python, chave OpenAI — README:19-26); ✅ venv + `pip install` (39-50); ✅ `cp .env.example .env`, chave não exposta (placeholder `sk-sua-c…` no `.env.example`; tabela 62-69); ✅ ordem de execução (73-96); ✅ exemplo in-context + out-of-context com frase padrão **byte-exata** (`README` contém `"Não tenho informações necessárias para responder sua pergunta."` = `True`) no formato `PERGUNTA:`/`RESPOSTA:` (104-119). ✅ **"explicação de cada variável" agora cumprida:** removidas `GOOGLE_API_KEY`/`GOOGLE_EMBEDDING_MODEL` do `.env.example`; re-verificação → as 6 variáveis restantes constam do README (0 não-documentadas) |
| CA-05.3 | Repositório público higienizado | ✅ **PASS** | `git ls-files \| grep -E '(^\|/)\.env$\|^venv/\|^pgdata/'` → **vazio**; os 8 obrigatórios rastreados (`docker-compose.yml`, `requirements.txt`, `.env.example`, `src/ingest.py`, `src/search.py`, `src/chat.py`, `document.pdf`, `README.md`); `git grep -nE 'sk-(proj-)?[A-Za-z0-9]{24,}'` em **todos** os tracked (inclui `docs/`) → **nenhuma** chave real; `.env.example` usa placeholder; `gh repo view` → `PUBLIC` |

## Testes armadilha

| Pergunta | Resposta obtida | OK? |
|---|---|---|
| Qual é a capital da França? | 🚧 BLOCKED (sem DB + sem quota — chat não inicia) | — |
| Quantos clientes temos em 2024? | 🚧 BLOCKED | — |
| Você acha isso bom ou ruim? | 🚧 BLOCKED | — |

**Nota:** o README **documenta** um exemplo out-of-context com a frase-padrão byte-exata (CA-05.2), mas a verificação armadilha **em execução** exige a stack viva — bloqueada.

## Problemas encontrados

1. **[MÉDIA — documentação / CA-05.2] ✅ RESOLVIDO.** `GOOGLE_API_KEY`/`GOOGLE_EMBEDDING_MODEL` existiam no `.env.example` sem documentação no README (config morta — o código é OpenAI-only). **Corrigido nesta sessão pela via (b):** as duas variáveis foram removidas do `.env.example` (`grep -c GOOGLE_ .env.example` → 0), alinhando `.env.example` ↔ código ↔ README. Re-verificação: 0 variáveis não-documentadas; gates seguem verdes (26/26); `src/` não referencia `GOOGLE_`.
2. **[BLOQUEIO — ambiente] Dry-run real da CA-05.1 impossível.** Docker daemon parado + OpenAI sem quota impedem `up → ingest → chat` e os testes armadilha em execução. *Resolver:* iniciar Docker Desktop, resolver quota OpenAI (ou, se optar por Gemini no futuro, implementar o provider + chave Google `AIza…` válida), então seguir o README literalmente num clone limpo com `docker compose down -v` antes.

## Atualização pós-correção

Após o veredito, o usuário autorizou aplicar a correção aconselhada (Opção A). O `.env.example` foi realinhado para OpenAI-only (remoção do bloco Google). Resultado: **CA-05.2 → PASS**, **CA-05.3 → PASS**, gates 2/2 verdes. **Único item pendente: CA-05.1** (dry-run real), bloqueado exclusivamente pelo ambiente (Docker daemon parado + OpenAI sem quota). Assim que o ambiente for destravado, basta reexecutar a CA-05.1 e os testes armadilha para fechar F05 e promover a `evaluated`.

## Recomendações

- ~~Corrigir o achado nº 1 antes do APPROVED~~ ✅ **FEITO** — `.env.example` realinhado para OpenAI-only; `.env.example` ↔ código ↔ README agora coerentes.
- **Destravar o ambiente e reexecutar a CA-05.1** num clone limpo, seguindo o README ao pé da letra, com uma pergunta in-context (ex.: "Qual o faturamento da Alfa Energia S.A.?" → R$ 722.875.391,46) e ≥3 armadilhas esperando exatamente a frase-padrão.
- **CA-05.3 já tem evidência definitiva** (repo limpo, público, sem segredos) — não precisa reexecutar.
- **Status permanece `implemented`** — sem promoção a `evaluated` enquanto a CA-05.1 estiver bloqueada e o achado nº 1 não for corrigido.

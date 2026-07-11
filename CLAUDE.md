# CLAUDE.md — Harness do Projeto

Projeto: **Ingestão e Busca Semântica com LangChain e PostgreSQL (pgVector)**
Desafio da pós-graduação Full Cycle. PRD completo em `docs/PRD.md`.

## Fluxo de Trabalho (Harness)

Este projeto segue Harness Engineering. O ciclo de cada feature é:

1. `prd-writer` — gera/atualiza `docs/PRD.md` e `docs/PRDProgress.json`
2. `spec-writer` — gera `spec.md`, `plan.md` e `contract.md` (formato GWT) em `docs/features/FXX-nome/`
3. `implement-feature` — implementa seguindo o plan e cumprindo o contract
4. `evaluator` — agente separado avalia contra o contract e gera report

Regras do fluxo:

- `docs/PRDProgress.json` é a **fonte única de verdade** do estado do projeto. Leia-o antes de começar qualquer trabalho e atualize-o ao concluir.
- **Uma feature por vez.** Não comece outra feature antes de terminar a atual. Respeite as waves e dependências do tracking.
- O `contract.md` é derivado dos critérios de aceitação do PRD — não invente critérios novos.
- Quem implementa não avalia o próprio trabalho: a avaliação final é da skill `evaluator`.

## Ambiente

- Repositório: fork de `devfullcycle/mba-ia-desafio-ingestao-busca` → `andredosreis/mba-ia-desafio-ingestao-busca` (remote `origin`)
- Subir o banco: `docker compose up -d` (Postgres 17 + pgVector, porta host `5432`, db `rag`, user/senha `postgres/postgres`)
- A extensão `vector` é criada automaticamente pelo serviço `bootstrap_vector_ext` do compose — não criar manualmente
- Parar o banco: `docker compose down` (com `-v` para limpar dados)
- Ambiente virtual: `python3 -m venv venv && source venv/bin/activate`
- Dependências: `pip install -r requirements.txt` (já pinado pelo template — não repinar versões)
- Variáveis: `cp .env.example .env` e preencher `OPENAI_API_KEY` (convenção de nomes do template: `OPENAI_EMBEDDING_MODEL`, `OPENAI_MODEL`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, `PDF_PATH`)
- Ordem de execução do produto: `docker compose up -d` → `python src/ingest.py` → `python src/chat.py`

## Restrições Obrigatórias do Enunciado (NÃO ALTERAR)

Estas regras vêm do enunciado do desafio e são inegociáveis:

- Linguagem **Python** com framework **LangChain**; banco **PostgreSQL + pgVector** via Docker Compose.
- Split: `RecursiveCharacterTextSplitter` com `chunk_size=1000` e `chunk_overlap=150`.
- Embeddings: `text-embedding-3-small` (OpenAI). O MESMO modelo na ingestão e na busca.
- Busca: `similarity_search_with_score(query, k=10)`.
- LLM de resposta: modelo definido em `OPENAI_MODEL` no `.env` (enunciado sugere `gpt-5-nano`).
- O prompt de resposta é FIXO — já vem pronto no stub `src/search.py` como `PROMPT_TEMPLATE` (placeholders `{contexto}` e `{pergunta}`). Não reescrever, não "melhorar".
- Respeitar os contratos dos stubs do template: `src/search.py` expõe `search_prompt()` (consumido por `src/chat.py`), `src/ingest.py` expõe `ingest_pdf()` e lê `PDF_PATH` do `.env`.
- Perguntas fora do contexto devem responder exatamente: `"Não tenho informações necessárias para responder sua pergunta."`
- Estrutura obrigatória: `docker-compose.yml`, `requirements.txt`, `.env.example`, `src/ingest.py`, `src/search.py`, `src/chat.py`, `document.pdf`, `README.md`.

## Code Style

- Arquivos com menos de 400 linhas. Mais de uma responsabilidade num arquivo → criar outro.
- SOLID / Single Responsibility Principle.
- Nomes greppáveis: identificadores únicos e descritivos (evitar nomes genéricos como `data`, `util`, `helper`).
- PEP 8, type hints nas assinaturas públicas, docstrings curtas em português.
- Configuração via variáveis de ambiente (`python-dotenv`); nada hardcoded de credencial ou modelo.
- Toda saída de CLI em português, seguindo o formato do enunciado (`PERGUNTA:` / `RESPOSTA:`).

## Quality Gates

Rodar antes de marcar qualquer feature como implementada:

1. `python -m py_compile src/*.py` — sanidade de sintaxe
2. `python -m pytest tests/ -q` — suite de testes (quando existir)
3. Verificação funcional do contract da feature (via CLI real, não mock)

**Não criar linters ou gates de auto-validação próprios** além dos listados aqui. Se um gate novo parecer necessário, propor ao usuário primeiro.

## Testes

- Criar teste para cada nova função de lógica (split, montagem de prompt, formatação de contexto).
- **Mockar chamadas externas** (OpenAI, Postgres) nos testes unitários — testes não podem depender de API key nem de rede.
- Testes independentes, repetíveis, self-validating e rápidos.
- A verificação de ponta a ponta (banco real + API real) é papel do `evaluator` seguindo o `contract.md`, não da suite unitária.

## Guardrails

- **NUNCA** commitar `.env` ou expor a `OPENAI_API_KEY` (nem em logs, nem em output).
- Não alterar os parâmetros obrigatórios do enunciado (chunk, overlap, k, modelos, prompt).
- Não adicionar dependências fora do ecossistema LangChain/psycopg sem justificar no PRD.
- O sistema NUNCA deve responder com conhecimento externo ao PDF — esse é o critério central de aceitação do desafio.

# Contract — F06 Suporte a Provider Gemini (alternativa à OpenAI)

## Pré-requisitos de Ambiente
- venv com dependências instaladas (`langchain-google-genai` já pinado no `requirements.txt`).
- `.env` com bloco OpenAI e bloco Gemini. Para os blocos de execução real (CA-06.3): `GOOGLE_API_KEY` real (formato `AIza…`) e `LLM_PROVIDER=gemini`.
- Para CA-06.3 apenas: banco de pé (`docker compose up -d`, healthy, extensão `vector`) e **ingestão executada com o provider Gemini** (collection `document_chunks` populada com vetores 3072d).
- Os blocos unitários (CA-06.1, CA-06.2) e de inspeção (CA-06.4) **não** exigem banco, rede nem chave real.

## Gates de Qualidade
- `python -m py_compile src/*.py` → exit 0.
- `python -m pytest tests/ -q` → todos verdes (provider/chain/DB mockados; sem rede).

## Manifesto de Cobertura

### Surface: Módulo `src/providers.py`

#### CA-06.1 — Seleção de provider por `LLM_PROVIDER`
- **Given:** as classes de provider mockadas; ambiente com as envs mínimas de cada provider.
- **When:** com `LLM_PROVIDER=gemini`, chamo `criar_embeddings()` e `criar_chat_llm()`; depois com `LLM_PROVIDER=openai`; depois com `LLM_PROVIDER` ausente.
- **Then:**
  - `gemini` → instancia `GoogleGenerativeAIEmbeddings` (modelo `models/gemini-embedding-001` por default) e `ChatGoogleGenerativeAI` (`gemini-2.5-flash` por default);
  - `openai` → instancia `OpenAIEmbeddings` (`OPENAI_EMBEDDING_MODEL`) e `ChatOpenAI` (`OPENAI_MODEL`);
  - `LLM_PROVIDER` ausente → comporta-se como `openai` (default);
  - valor inválido (ex.: `LLM_PROVIDER=foo`) → `ValueError` com mensagem PT;
  - tudo verificado por teste unitário mockado, exit 0, sem rede.

#### CA-06.2 — Restrições e assinaturas preservadas em ambos os providers
- **Given:** o código-fonte de `src/ingest.py` e `src/search.py` após a integração.
- **When:** inspeção + suíte de testes.
- **Then:**
  - `src/search.py` chama literalmente `similarity_search_with_score(pergunta, k=10)` (`k=10` inalterado);
  - o `PROMPT_TEMPLATE` é **byte-idêntico** ao stub original (teste de igualdade integral verde);
  - `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)` inalterado em `ingest.py`;
  - ingestão e busca obtêm embeddings pela **mesma** função (`providers.criar_embeddings()`) — mesmo provider/modelo em ambos;
  - as assinaturas `def ingest_pdf()` e `def search_prompt(question=None)` permanecem idênticas (grep confirma);
  - `pytest tests/ -q` todo verde.

#### CA-06.3 — Ingestão e busca reais com Gemini (evaluator)
- **Given:** banco de pé, `.env` com `LLM_PROVIDER=gemini` e `GOOGLE_API_KEY` real.
- **When:** executo `python src/ingest.py` e depois `python src/chat.py` (via pipe), com uma pergunta presente no PDF e ≥3 perguntas fora do contexto.
- **Then:**
  - a ingestão conclui com exit 0 e imprime a contagem de chunks armazenados;
  - a coleção `document_chunks` fica populada com vetores de **3072** dimensões (verificável por SQL);
  - a pergunta dentro do contexto retorna resposta baseada no PDF (ex.: faturamento da Alfa Energia S.A. → R$ 722.875.391,46);
  - cada pergunta fora do contexto retorna exatamente `"Não tenho informações necessárias para responder sua pergunta."`;
  - nenhum traceback cru; chave nunca impressa.

#### CA-06.4 — Documentação e higiene
- **Given:** `.env.example`, `README.md`, `CLAUDE.md` e o índice git.
- **When:** inspeção.
- **Then:**
  - `.env.example` contém `LLM_PROVIDER`, `GOOGLE_API_KEY`, `GOOGLE_EMBEDDING_MODEL`, `GOOGLE_MODEL` (com placeholder na chave, não valor real);
  - `README.md` documenta a seleção de provider, os modelos Gemini validados e a necessidade de re-ingestão ao trocar de provider;
  - `CLAUDE.md` reflete os dois providers permitidos sem afrouxar chunk/`k`/prompt/frase-padrão;
  - `git grep -nE 'sk-(proj-)?[A-Za-z0-9]{24,}|AIza[A-Za-z0-9_-]{30,}'` sobre os arquivos versionados → **nenhuma** chave real.

## Critério de conclusão
CA-06.1, CA-06.2 e CA-06.4 verdes (unitário + inspeção); gates verdes; nenhuma chave versionada. CA-06.3 fica para o `evaluator` em execução real (Docker + chave Gemini). Só então F06 vai para `implemented` e é encaminhada ao `evaluator`.

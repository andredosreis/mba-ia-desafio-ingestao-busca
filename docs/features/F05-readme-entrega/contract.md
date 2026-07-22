# Contract — F05 README e Entrega

## Pré-requisitos de Ambiente
- F01–F04 implementadas e avaliadas; fluxo completo funcional (banco + ingestão + chat).
- Docker e Python 3 disponíveis; `OPENAI_API_KEY` real para o dry-run.
- Acesso ao repositório GitHub do projeto (fork público `andredosreis/mba-ia-desafio-ingestao-busca`).

## Gates de Qualidade
- `python -m py_compile src/*.py` → exit 0.
- `python -m pytest tests/ -q` → todos verdes.
- Dry-run funcional seguindo APENAS o README (bloco CA-05.1).

## Manifesto de Cobertura

### Surface: Documentação + Repositório

#### CA-05.1 — Execução completa guiada só pelo README
- **Given:** máquina com Docker e Python, sem contexto do projeto; clone limpo do repositório; banco zerado (`docker compose down -v`).
- **When:** executam-se, na ordem e literalmente, apenas os comandos do `README.md`.
- **Then:**
  - o banco sobe; a ingestão termina com exit 0;
  - `python src/chat.py` responde uma pergunta do PDF com conteúdo do documento;
  - pergunta fora do contexto retorna a frase padrão exata;
  - nenhum passo exige conhecimento que não esteja escrito no README.

#### CA-05.2 — Conteúdo obrigatório documentado
- **Given:** o arquivo `README.md`.
- **When:** inspeção do conteúdo.
- **Then:** o README contém, verificável por leitura:
  - pré-requisitos (Docker/Compose, Python, chave OpenAI);
  - criação/ativação do venv e `pip install -r requirements.txt`;
  - `cp .env.example .env` e explicação de cada variável (sem expor chave real);
  - ordem de execução: `docker compose up -d` → `python src/ingest.py` → `python src/chat.py`;
  - ao menos UM exemplo de pergunta dentro do contexto e UM fora (com a frase padrão exata), no formato `PERGUNTA:`/`RESPOSTA:`.

#### CA-05.3 — Repositório público higienizado
- **Given:** o repositório público no GitHub.
- **When:** inspeção do índice git e da plataforma.
- **Then:**
  - `git ls-files | grep -E '(^|/)\.env$|^venv/|^pgdata/'` → saída vazia;
  - `git ls-files` inclui: `docker-compose.yml`, `requirements.txt`, `.env.example`, `src/ingest.py`, `src/search.py`, `src/chat.py`, `document.pdf`, `README.md`;
  - nenhuma chave de API real em qualquer arquivo versionado;
  - o repositório está com visibilidade **pública** (`gh repo view --json visibility`).

## Critério de conclusão
Todos os blocos GWT passam, gates verdes, repositório público limpo. Só então
F05 pode ir para `implemented`, ser avaliada pelo `evaluator` — e o projeto está
pronto para entrega.

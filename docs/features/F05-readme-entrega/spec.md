# Spec — F05 README e Entrega

| Campo | Valor |
|---|---|
| Feature | F05 — README e Entrega |
| Wave | 4 |
| Depende de | F01–F04 (spec escrita antecipadamente; conteúdo final reflete o que foi implementado) |
| Critérios de aceitação | CA-05.1, CA-05.2, CA-05.3 |
| Entrega | `README.md` completo + repositório público higienizado |

## 1. Objetivo

Documentar o projeto de ponta a ponta para que **uma pessoa sem nenhum contexto**
consiga subir o banco, ingerir o PDF e conversar com a CLI só seguindo o README —
e garantir a higiene do repositório público (sem `.env`, `venv/`, dados locais).

- **CA-05.1** — README suficiente para execução completa por terceiros.
- **CA-05.2** — documenta pré-requisitos, venv, `.env`, ordem de execução e exemplos.
- **CA-05.3** — repositório público sem `.env`, `venv/` nem `pgdata/`.

## 2. Estrutura do README (em português)

1. **Título + descrição** — o que o sistema faz (RAG: ingestão de PDF + perguntas via CLI restritas ao documento).
2. **Tecnologias** — Python, LangChain, PostgreSQL + pgVector, Docker Compose, OpenAI.
3. **Pré-requisitos** — Docker/Compose, Python 3.10+, chave da OpenAI.
4. **Configuração**
   - clone do repositório;
   - `python3 -m venv venv && source venv/bin/activate`;
   - `pip install -r requirements.txt`;
   - `cp .env.example .env` + preencher `OPENAI_API_KEY` (tabela com cada variável e default).
5. **Ordem de execução** (comandos exatos do enunciado):
   1. `docker compose up -d`
   2. `python src/ingest.py`
   3. `python src/chat.py`
6. **Exemplos de uso** — sessão com pergunta dentro do contexto e outra fora
   (formato `PERGUNTA:`/`RESPOSTA:` do enunciado, incluindo a frase padrão).
7. **Estrutura do projeto** — árvore de arquivos obrigatória.
8. **Como funciona (resumo técnico)** — pipeline ingestão/busca em poucas linhas (chunks 1000/150, `text-embedding-3-small`, k=10, prompt fixo).
9. **Solução de problemas** — porta 5432 ocupada, chave inválida/placeholder, banco fora do ar, base vazia.

## 3. Higiene do repositório (CA-05.3)

- `git ls-files` NÃO pode listar `.env`, `venv/`, `pgdata/` (o `.gitignore` da F01 já cobre; aqui é verificação final).
- `document.pdf`, `docker-compose.yml`, `requirements.txt`, `.env.example`, `src/*`, `README.md` presentes e versionados.
- Repositório público no GitHub (entregável do desafio).

## 4. Decisões e trade-offs

- **README em português** — consistente com o CLI, o público (banca da pós) e o restante da documentação.
- **Instruções com `pip`** (caminho oficial do enunciado); nota curta mencionando `uv` como alternativa é opcional, sem trocar o padrão.
- **Sem badges/CI** — fora do escopo do desafio; foco em reprodutibilidade.
- **Docs do harness (`docs/`, `CLAUDE.md`)** permanecem no repo: documentam o processo (valor para a banca) e não conflitam com a estrutura obrigatória.

## 5. Fora do escopo

- Qualquer mudança de código em `src/` (F02–F04 encerradas).
- Deploy, CI/CD, publicação além do repositório público.

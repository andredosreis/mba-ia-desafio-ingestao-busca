# Contract — F04 CLI de Chat

## Pré-requisitos de Ambiente
- Banco de pé (`docker compose up -d`, healthy, extensão `vector`).
- F02 e F03 implementadas; **ingestão executada** (collection `document_chunks` com contagem > 0).
- venv com dependências; `.env` completo com `OPENAI_API_KEY` REAL.
- Terminal interativo disponível para os testes de Ctrl+C/Ctrl+D (os demais blocos aceitam entrada via pipe).

## Gates de Qualidade
- `python -m py_compile src/*.py` → exit 0.
- `python -m pytest tests/ -q` → todos verdes (chain/DB mockados).
- Verificação funcional real: `venv/bin/python src/chat.py` (interativo e via pipe).

## Manifesto de Cobertura

### Surface: CLI

#### CA-04.1 — Prompt inicial e loop de perguntas
- **Given:** banco populado, `.env` válido.
- **When:** executo `printf 'P1\nP2\nsair\n' | venv/bin/python src/chat.py` (P1/P2 = perguntas quaisquer).
- **Then:**
  - a saída contém `Faça sua pergunta:`;
  - contém DOIS blocos de resposta (um por pergunta) — o loop processa mais de uma pergunta;
  - exit code 0.

#### CA-04.2 — Formato PERGUNTA/RESPOSTA do enunciado
- **Given:** banco populado, `.env` válido.
- **When:** mesma execução do CA-04.1.
- **Then:**
  - o prompt de entrada é `PERGUNTA: ` (visível na saída piped);
  - cada resposta é prefixada por `RESPOSTA: `;
  - pergunta fora do contexto (ex.: P2 = `Qual é a capital da França?`) produz `RESPOSTA: Não tenho informações necessárias para responder sua pergunta.`.

#### CA-04.3 — Encerramento gracioso
- **Given:** chat em execução.
- **When:** digito `sair`.
- **Then:** mensagem de despedida em PT; exit code 0; sem traceback.
- **When:** pressiono Ctrl+C (SIGINT) durante o `input`.
- **Then:** encerramento sem `Traceback (most recent call last)` na saída.
- **When:** pressiono Ctrl+D (EOF) / a entrada piped termina.
- **Then:** idem — encerramento gracioso, exit 0.

#### CA-04.4 — Ambiente não pronto → orientação clara
- **Given:** collection vazia/inexistente (ingestão nunca rodou ou base limpa).
- **When:** executo `venv/bin/python src/chat.py`.
- **Then:**
  - mensagem em PT orientando executar `python src/ingest.py`;
  - programa encerra sem traceback; loop de perguntas não inicia.
- **Given:** `.env` sem `OPENAI_API_KEY` (ou variável obrigatória ausente).
- **When:** executo `venv/bin/python src/chat.py`.
- **Then:**
  - mensagem em PT indicando a configuração faltante (sem imprimir valores de chave);
  - sem `Traceback (most recent call last)`;
  - (pós-teste: restaurar `.env` e, se a base foi limpa, re-executar a ingestão).

## Critério de conclusão
Todos os blocos GWT passam na CLI real, gates verdes, chave jamais impressa.
Só então F04 pode ir para `implemented` e ser encaminhada ao `evaluator`.

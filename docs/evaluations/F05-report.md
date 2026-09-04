# Evaluation Report — F05 README e Entrega

- Data: 2026-07-22 · **reavaliada em 2026-09-03**
- Avaliador: `evaluator` (independente)
- Veredito: **REJECTED** na reavaliação. O dry-run da CA-05.1 finalmente pôde ser executado e **falhou**: seguindo o README literalmente, a instalação de dependências quebra. CA-05.2 e CA-05.3 passam. Ver seção final.
- Gates: 2/2 verdes (`py_compile` exit 0; `pytest` 36/36 na reavaliação — eram 26/26 à época)
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


---

## Reavaliação (2026-09-03)

O dry-run da CA-05.1, que nunca havia sido possível, foi executado de verdade: **clone limpo do GitHub, venv novo, banco zerado com `docker compose down -v`**, seguindo apenas os comandos do README.

> Nota de método: o clone foi feito da branch `feature/f06-provider-gemini`, porque a `main` ainda não contém a F06. Um avaliador que clone a `main` hoje recebe o código anterior à feature, que depende da conta OpenAI sem quota.

| Item | Resultado | Evidência |
|---|---|---|
| **CA-05.1** | ❌ **FAIL** | Ver Problema #4 abaixo. Os demais passos do README funcionam — comprovado na segunda tentativa |
| **CA-05.2** | ✅ **PASS** | Pré-requisitos (Docker/Compose, Python, chave OpenAI **ou** Google), venv + `pip install -r requirements.txt`, `cp .env.example .env`, **as 10 variáveis do `.env.example` explicadas** (0 não-documentadas), ordem de execução literal, e exemplos `PERGUNTA:`/`RESPOSTA:` dentro e fora do contexto com a frase padrão byte-exata. Nenhuma chave real no arquivo |
| **CA-05.3** | ✅ **PASS** | `git ls-files \| grep -E '(^\|/)\.env$\|^venv/\|^pgdata/'` → **vazio**; os 8 arquivos obrigatórios rastreados; `git grep -nE 'sk-(proj-)?[A-Za-z0-9]{24,}\|AIza[A-Za-z0-9_-]{30,}'` sobre todos os versionados → **nenhuma** chave real; `gh repo view` → **PUBLIC** |

### Problema #4 — [BLOQUEANTE — CA-05.1] O README promete Python 3.10+, mas as dependências exigem 3.11+

Seguindo o README literalmente numa máquina limpa:

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
ERROR: Could not find a version that satisfies the requirement numpy==2.3.2
ERROR: No matching distribution found for numpy==2.3.2

$ python src/ingest.py
ModuleNotFoundError: No module named 'dotenv'
```

- `numpy==2.3.2` (`requirements.txt:41`) declara `requires_python: >=3.11` (consultado na API do PyPI). O README anuncia **"Python 3.10+"** em dois lugares (linhas 9 e 29). Quem usar 3.10 — exatamente o mínimo prometido — **não consegue instalar**.
- Agravante nesta máquina: `python3` resolve para `/usr/bin/python3` = **Python 3.9.6**. O comando do README cria um venv 3.9, o `pip install` falha parcialmente (apenas 4 dos 78 pacotes) e a execução morre com `ModuleNotFoundError`. O `pip` do venv 3.9 é a versão 21.2.4, antiga.
- O venv do projeto funciona porque foi criado pelo **`uv`** com um CPython 3.12.13 em `~/.local/share/uv/python/...`, que **não está no PATH** como `python3.12`. Ou seja: o próprio ambiente de desenvolvimento não é reproduzível pelos comandos do README.
- **Severidade:** ALTA. É a primeira coisa que um avaliador executa, e falha antes de qualquer código do projeto rodar.
- **Reproduzir:** clone limpo → `python3 -m venv venv` com `python3` ≤ 3.10 → `pip install -r requirements.txt`.
- **Correção sugerida:** anunciar **Python 3.12** (versão em que o projeto é comprovadamente funcional) nas linhas 9 e 29 do README, e considerar instruir `python3.12 -m venv venv` com uma nota sobre como verificar a versão (`python3 --version`).

### O restante do fluxo do README funciona

Repetido o dry-run com Python 3.12.13 e o mesmo clone limpo:

| Passo | Resultado |
|---|---|
| `pip install -r requirements.txt` | exit 0, **78 pacotes**, 0 erros |
| `cp .env.example .env` + preencher chave | `.env.example` autoexplicativo; bastou `LLM_PROVIDER=gemini` e `GOOGLE_API_KEY` |
| `docker compose up -d` | `postgres_rag` healthy; extensão `vector 0.8.5` criada automaticamente em volume novo |
| `python src/ingest.py` | **EXIT=0**, `Ingestão concluída: 67 chunks armazenados na collection 'document_chunks'.` |
| `python src/chat.py` | Pergunta do PDF → `RESPOSTA: O faturamento da Alfa Energia S.A. é R$ 722.875.391,46.`; fora do contexto → frase padrão exata; **EXIT=0**, stderr vazio, 0 traceback |

Nenhum passo exigiu conhecimento fora do README — **exceto** a versão do Python, que é justamente o Problema #4.

Ambiente restaurado ao final: clone apagado (continha `.env` com chave real), volume do dry-run removido, projeto principal reingerido (67 chunks, 3072d).

### Recomendações

1. Corrigir o Problema #4 (uma linha em dois lugares do README). Depois disso, a F05 deve passar sem ressalvas.
2. **Fazer o merge da F06 na `main`** antes da entrega: hoje um avaliador que clone a `main` recebe código que depende de uma conta OpenAI sem quota.

---

## Correção do Problema #4 (2026-09-03, pós-reavaliação)

Aplicada após o veredito REJECTED acima. **O veredito permanece como resultado da reavaliação**; a promoção a `evaluated` depende de uma verificação independente.

A correção não se limitou a trocar o número da versão. Só isso não resolveria a falha: o leitor continuaria digitando `python3 -m venv venv`, e numa máquina onde `python3` é 3.9 o comando seguiria criando um venv quebrado, sem aviso.

Mudanças no `README.md`:

1. Linha 9 e 29: **"Python 3.10+" → "Python 3.12"**, com a razão explícita (`numpy==2.3.2` exige ≥3.11).
2. Passo 2 passou a começar por `python3 --version`, para o leitor descobrir o que o comando resolve na máquina dele **antes** de criar o venv.
3. Dois caminhos documentados: `python3 -m venv venv` se a versão for ≥3.11; `python3.12 -m venv venv` caso contrário, com a menção de que em muitos macOS o `python3` do sistema ainda é 3.9 e de que o sintoma da escolha errada é a falha em `numpy==2.3.2`.

Verificação: `grep "3\.10"` no README → **nenhuma ocorrência**. A configuração que o README agora anuncia (Python 3.12) é exatamente a que foi executada de ponta a ponta no dry-run desta reavaliação — clone limpo, banco zerado, 78 pacotes instalados sem erro, ingestão de 67 chunks e chat respondendo corretamente dentro e fora do contexto.

Limitação registrada: nesta máquina de desenvolvimento nem `python3.12` está no PATH (o interpretador é gerenciado pelo `uv`, fora dele). Numa instalação convencional de Python 3.12 — python.org ou Homebrew — o comando existe. O README está correto para a máquina de um avaliador; esta máquina é o caso atípico.

---

## Avaliação independente (2026-09-03) — achado que esta avaliação não encontrou

Um avaliador separado, sem participação na implementação, refez a F05 do zero. **Veredito: REJECTED**, por um motivo diferente e novo.

### Problema #5 — [BLOQUEANTE — CA-05.1] `pytest` documentado no README mas ausente de `requirements.txt`

O README (linha 225) instrui `python -m pytest tests/ -q`. Num clone limpo que seguiu o README ao pé da letra, esse comando morre:

```
$ python -m pytest tests/ -q
No module named pytest        (exit 1)
```

`pytest` não está em `requirements.txt` — nem na branch, nem em `origin/main`. Está instalado só no venv local do desenvolvedor (`9.1.1`), fora do arquivo de dependências. Isso viola a cláusula literal do contrato *"nenhum passo exige conhecimento que não esteja escrito no README"*: para rodar um comando que o próprio README manda rodar, é preciso saber, de fora dele, executar `pip install pytest`.

O avaliador confirmou pelo histórico (`git log -S pytest -- README.md`) que a seção de testes foi introduzida pelo commit `00a9c45` — o commit da própria F05 —, logo o achado está em escopo.

### Por que a avaliação anterior não pegou

Registro por honestidade metodológica, com as palavras do avaliador independente: o dry-run anterior *"só exercitou a cadeia do produto (compose → ingest → chat) e parou ali; não executou o último comando documentado do README"*. E mais: este report afirmava "gates 2/2 verdes (`pytest` 36/36)" — verdadeiro no venv do projeto, mas o gate **nunca foi testado a partir do clone limpo que a própria avaliação criou**, onde falhava.

É o tipo de ponto cego que aparece quando quem avalia já sabe o que espera confirmar — e é precisamente o motivo de o harness exigir um avaliador separado.

### O que ele confirmou como correto

- O dry-run do **produto** funciona de ponta a ponta a partir de clone limpo com banco zerado: `pip install` exit 0, extensão `vector` criada em volume novo, ingestão de 67 chunks a 3072 dimensões, e os **dois** exemplos in-context do README reproduzindo literalmente o que o README promete (`R$ 722.875.391,46` e `1971`), mais 4 armadilhas byte-exatas.
- CA-05.2 **PASS**: as 10 variáveis explicadas, ordem de execução correta, frase padrão byte-idêntica.
- CA-05.3 **PASS**: varredura de chaves em **todo o histórico do git** → nenhuma; 8 arquivos obrigatórios rastreados; repositório `PUBLIC`.
- A correção do Problema #4 (versão do Python) foi verificada e está correta.

### Correção do Problema #5

`pytest==9.1.1` adicionado ao `requirements.txt` (linha 59, em ordem alfabética após `pypdf==6.0.0`). Justificativa para o guardrail do `CLAUDE.md` sobre dependências: não é uma dependência nova do produto, e sim a formalização de uma ferramenta que o projeto já exige em dois lugares — o quality gate do `CLAUDE.md` e a seção de testes do README.

Revalidação do CA-05.1 solicitada ao mesmo avaliador independente.

---

## Revalidação independente (2026-09-03) — veredito final

**Veredito: APPROVED.** F05 promovida a `evaluated`.

O mesmo avaliador independente refez o dry-run do zero — `docker compose down -v`, clone limpo, venv 3.12 novo — e desta vez executou **todos** os comandos do README, sem parar na cadeia do produto.

### Nota de método dele

As correções estavam **não commitadas** na working tree, então um `git clone` puro teria revalidado o código antigo. Ele clonou a branch, aplicou o diff local por cima (90 linhas) e confirmou byte-igualdade em `requirements.txt`, `src/chat.py`, `src/ingest.py`, `src/search.py`, `src/providers.py`, `README.md` e `.env.example` antes de avaliar.

### Evidência do comando que havia reprovado

```
$ python -m pytest tests/ -q
....................................                                     [100%]
36 passed in 11.94s        (EXIT 0)
```

Executado no clone limpo, com o venv criado pelo README — e, como reforço da prova, **sem nenhum container Postgres de pé** e **antes de o `.env` existir**. A suíte é genuinamente hermética: não depende de banco nem de chave de API.

### Dry-run completo

| Passo do README | Resultado |
|---|---|
| `python3 --version` → `3.9.6`, então `python3.12 -m venv venv` | venv `Python 3.12.13` — o caminho alternativo documentado funcionou |
| `pip install -r requirements.txt` | exit 0, 28 s, **80 pacotes**, 0 erros (`pytest-9.1.1` no log) |
| `cp .env.example .env` + chave | OK |
| `docker compose up -d` | healthy; `\dt` → *"Did not find any relations"*; extensão `vector` criada |
| `python src/ingest.py` | exit 0; SQL → `document_chunks \| 67 \| 3072 \| 3072` |
| `python src/chat.py` | returncode 0, stderr vazio, chave não vazada; in-context ✅ e 4 armadilhas byte-exatas |
| `python -m pytest tests/ -q` | **36 passed, exit 0** |

O último bullet do CA-05.1 — *"nenhum passo exige conhecimento que não esteja escrito no README"* — passa a se sustentar.

### Observação registrada por ele (baixa severidade, não é defeito)

O fraseado da resposta in-context varia entre execuções: nesta rodada veio `R$ 722.875.391,46`, na anterior `O faturamento da Alfa Energia S.A. é R$ 722.875.391,46.` — que é a transcrição impressa no README. Variação normal de LLM, e o CA-05.1 pede apenas que a resposta traga conteúdo do documento. Fica o registro porque o README apresenta o bloco como transcrição literal, e um avaliador do desafio pode ver um texto ligeiramente diferente.

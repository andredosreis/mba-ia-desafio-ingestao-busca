# Guia de Aprendizado — Entenda Cada Passo

> **Doc vivo.** A Parte 1 (fundamentos) já está completa e pode ser estudada agora.
> A Parte 2 tem uma seção por feature, preenchida pela skill `implement-feature`
> ao final de cada implementação — com explicação do código real e perguntas de
> autoavaliação. Meta: ao final do projeto, você explica tudo sem ajuda.

**Como estudar:** leia a seção, feche o doc, explique em voz alta como se estivesse
apresentando ao professor. Depois responda as perguntas ANTES de abrir a resposta
(clique em "Resposta" para conferir).

---

## Parte 1 — Fundamentos do RAG

### 1.1 O problema que o RAG resolve

Uma LLM responde qualquer pergunta com o conhecimento dos dados de treino — e quando
não sabe, **inventa** (alucinação). Ela não conhece o seu PDF.

**RAG (Retrieval-Augmented Generation)** resolve isso em duas fases:

```
FASE 1 — INGESTÃO (offline, roda uma vez):
  PDF → texto → chunks → embeddings → banco vetorial

FASE 2 — CONSULTA (online, a cada pergunta):
  pergunta → embedding → busca dos chunks mais parecidos
           → chunks viram CONTEXTO no prompt → LLM responde SÓ com o contexto
```

A LLM não é re-treinada. Ela apenas recebe, junto com a pergunta, os trechos
do documento que têm mais chance de conter a resposta.

### 1.2 Embeddings — texto vira vetor

Um **embedding** é um vetor de números que representa o *significado* de um texto.
O modelo `text-embedding-3-small` da OpenAI transforma qualquer texto num vetor de
**1536 dimensões**. A propriedade mágica: textos com significados parecidos geram
vetores geometricamente próximos.

- "faturamento da empresa" e "receita anual" → vetores próximos
- "faturamento da empresa" e "receita de bolo" → vetores distantes

Por isso a busca é **semântica** e não por palavra-chave: encontra trechos que
*falam do mesmo assunto*, mesmo sem repetir as mesmas palavras.

**Regra de ouro do projeto:** o MESMO modelo de embedding usado na ingestão deve
ser usado na pergunta. Vetores de modelos diferentes vivem em "espaços" diferentes
e a comparação perde o sentido.

### 1.3 Chunking — por que dividir o PDF

Por que não gerar um embedding do PDF inteiro?

1. **Diluição** — um vetor só resume o documento todo; a informação específica ("o faturamento foi X") se perde na média.
2. **Granularidade da busca** — queremos recuperar o *trecho* que responde, não o documento inteiro.
3. **Limite de contexto** — o prompt da LLM tem tamanho finito; mandamos só os 10 melhores trechos.

O desafio exige `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)`:

- **chunk_size=1000** — cada pedaço tem até 1000 caracteres.
- **chunk_overlap=150** — cada chunk repete os últimos 150 caracteres do anterior. Isso evita que uma ideia cortada exatamente na fronteira entre dois chunks fique irrecuperável (metade num chunk, metade no outro, nenhum dos dois com a frase completa).
- **"Recursive"** — ele tenta quebrar primeiro em parágrafos (`\n\n`), depois linhas (`\n`), depois espaços, e só em último caso no meio de uma palavra. Ou seja: respeita a estrutura natural do texto o máximo possível.

### 1.4 pgVector — banco vetorial dentro do Postgres

**pgVector** é uma extensão do PostgreSQL que adiciona:

- um tipo de coluna `vector(N)` para armazenar embeddings;
- operadores de distância entre vetores (ex.: `<=>` para distância de cosseno);
- índices especializados para busca aproximada rápida.

Vantagem: você não precisa de um banco vetorial dedicado (Pinecone, Weaviate...) —
o Postgres que você já conhece guarda os chunks, os metadados e os vetores juntos.
No projeto, o LangChain gerencia as tabelas via classe `PGVector`, agrupando os
documentos numa **collection** (nome vem de `PG_VECTOR_COLLECTION_NAME`).

No nosso `docker-compose.yml`, o serviço `bootstrap_vector_ext` roda
`CREATE EXTENSION IF NOT EXISTS vector;` automaticamente após o banco subir.

### 1.5 Busca por similaridade

`similarity_search_with_score(query, k=10)` faz:

1. Gera o embedding da pergunta (mesmo modelo da ingestão).
2. Compara com todos os vetores da collection usando distância de cosseno.
3. Retorna os **10 chunks mais próximos**, cada um com seu *score*.

Sobre o score: no PGVector ele é uma **distância** — quanto MENOR, mais parecido.
Os 10 chunks retornados são concatenados e viram o `{contexto}` do prompt.

Por que k=10 e não k=1? A resposta pode estar espalhada em vários trechos, e o
melhor trecho nem sempre é o primeiro do ranking. 10 dá margem de segurança sem
estourar o prompt (10 × ~1000 chars ≈ 10k caracteres de contexto).

### 1.6 O prompt com guardrails

O prompt fixo do desafio tem três blocos: `CONTEXTO` (chunks concatenados),
`REGRAS` (responder só com base no contexto; se não estiver lá, responder a frase
padrão; nunca inventar; nunca opinar) e a `PERGUNTA DO USUÁRIO`.

As REGRAS são um **guardrail em linguagem natural**: transformam a LLM de "sabe-tudo"
em "leitora do contexto". Os exemplos de perguntas fora do contexto no próprio prompt
são *few-shot examples* — mostram ao modelo o comportamento esperado, o que é muito
mais eficaz do que só descrever a regra.

### 1.7 A chain (LangChain)

LangChain composta as etapas num pipeline declarativo (LCEL). Conceitualmente:

```
pergunta ─→ retriever (busca k=10) ─→ formata contexto ─┐
                                                        ├─→ prompt ─→ LLM ─→ resposta
pergunta ───────────────────────────────────────────────┘
```

Cada peça é substituível (trocar o LLM, trocar o banco) sem mudar o desenho —
essa é a proposta de valor do framework.

### 1.8 Perguntas de autoavaliação — Fundamentos

1. **Explique o fluxo completo do RAG deste projeto, da ingestão à resposta.**
   <details><summary>Resposta</summary>
   Ingestão: PyPDFLoader lê o PDF → RecursiveCharacterTextSplitter divide em chunks de 1000 chars com overlap de 150 → cada chunk vira um embedding de 1536 dims via text-embedding-3-small → chunks + vetores são salvos numa collection do PGVector no Postgres. Consulta: a pergunta vira embedding com o mesmo modelo → similarity_search_with_score retorna os 10 chunks mais próximos por distância de cosseno → chunks são concatenados no bloco CONTEXTO do prompt fixo → a LLM (gpt-5-nano) responde usando apenas o contexto → CLI imprime a resposta.
   </details>

2. **Por que o overlap de 150 caracteres existe? O que aconteceria sem ele?**
   <details><summary>Resposta</summary>
   Sem overlap, uma informação que caísse exatamente na fronteira entre dois chunks ficaria cortada ao meio — nenhum dos dois chunks teria a frase completa, e o embedding de nenhum deles representaria bem aquela informação. O overlap repete o final de um chunk no início do seguinte, garantindo que ideias na fronteira apareçam inteiras em pelo menos um chunk.
   </details>

3. **Por que é obrigatório usar o mesmo modelo de embedding na ingestão e na busca?**
   <details><summary>Resposta</summary>
   Cada modelo de embedding define seu próprio espaço vetorial. Comparar um vetor gerado por um modelo com vetores gerados por outro é comparar coordenadas de mapas diferentes — as distâncias deixam de ter significado, e a busca retorna resultados aleatórios.
   </details>

4. **O que o pgVector adiciona ao Postgres?**
   <details><summary>Resposta</summary>
   O tipo de coluna vector(N), operadores de distância entre vetores (cosseno, L2, produto interno) e índices para busca aproximada eficiente. Permite usar o Postgres como banco vetorial, guardando texto, metadados e embeddings no mesmo lugar.
   </details>

5. **Como o sistema garante que perguntas fora do contexto recebem a resposta padrão?**
   <details><summary>Resposta</summary>
   Pelo guardrail no prompt: as REGRAS instruem a responder somente com base no CONTEXTO e a devolver a frase padrão quando a informação não estiver explicitamente lá, reforçadas por exemplos few-shot de perguntas fora do contexto. Importante: a busca vetorial SEMPRE retorna 10 chunks (mesmo irrelevantes) — quem decide que o contexto não contém a resposta é a LLM seguindo as regras.
   </details>

6. **O que o score do `similarity_search_with_score` significa?**
   <details><summary>Resposta</summary>
   É a distância entre o vetor da pergunta e o vetor do chunk (cosseno, no PGVector). Quanto menor, mais semanticamente próximo. É útil para depurar a qualidade da busca — scores muito altos em todos os resultados indicam que o documento provavelmente não fala do assunto.
   </details>

---

## Parte 2 — Por Feature (preenchida durante a implementação)

> Cada seção é preenchida pela skill `implement-feature` no encerramento da feature:
> o que foi feito, o passo a passo do código real, decisões tomadas e perguntas
> de autoavaliação sobre A NOSSA implementação (não só teoria).

### F01 — Fundação e Infraestrutura

**O que foi feito e por quê**

F01 não escreveu código de produto — o objetivo era **validar** a infraestrutura
herdada do template (Docker Compose, `requirements.txt`, `.env.example`) e deixar
o ambiente pronto para F02–F05. Na prática isso significou: criar o venv, instalar
as dependências, subir o Postgres+pgVector via Docker Compose, confirmar que a
extensão `vector` existe no banco `rag`, e validar as variáveis do `.env`.

Durante a validação apareceram dois problemas reais que precisaram de correção:

1. **Bug no `docker-compose.yml`** — o serviço `bootstrap_vector_ext` "passava"
   (`exit code 0`, container "saudável" na aparência), mas **não criava a extensão
   `vector`**. Causa raiz: o serviço define `entrypoint: ["/bin/sh", "-c"]` (uma
   *lista*, "exec form") e `command` como uma **string simples**. Quando `command`
   é string, o Docker Compose faz *shell-split* nela antes de montar o argv final
   — ou seja, ele quebra a string em várias palavras e concatena com o entrypoint.
   O resultado real executado era `/bin/sh -c PGPASSWORD=postgres psql "..." -v ...`,
   onde a flag `-c` do `/bin/sh` consome **apenas o próximo argumento** como script.
   Esse argumento era `PGPASSWORD=postgres` — uma atribuição de variável sozinha, que
   em shell POSIX é uma instrução válida (não faz nada, mas não dá erro) e sai com
   código 0. Todo o resto (`psql`, a URL de conexão, o `-c "CREATE EXTENSION..."`)
   virava parâmetros posicionais (`$1`, `$2`...) do script, nunca usados.
   **Correção:** transformar `command` numa lista YAML com um único elemento
   (`command:\n  - '...'`). Uma lista não passa pelo *shell-split* do Compose —
   o conteúdo inteiro chega como um único argumento para `-c`, exatamente como
   pretendido. Depois da correção, `docker compose logs bootstrap_vector_ext`
   mostrou `CREATE EXTENSION` e a query em `pg_extension` confirmou `vector 0.8.5`.

2. **`OPENAI_API_KEY` ainda é o placeholder** — o `.env` tem `sk-sua-chave-aqui`
   (o mesmo texto do `.env.example`), não uma chave real. Isso não bloqueia a F01
   (o contrato exige só a *presença* da variável), mas vai impedir qualquer chamada
   real à API da OpenAI quando chegarmos em F02/F03. Fica registrado como pendência.

**Passo a passo do que foi executado**

```bash
python3 -m venv venv && source venv/bin/activate
# dependências já instaladas via `uv pip install -r requirements.txt` (mesmo efeito de pip)
docker compose up -d
docker compose exec postgres psql -U postgres -d rag -c \
  "SELECT extname FROM pg_extension WHERE extname='vector';"
```

- `docker compose ps` → `postgres_rag` com status `healthy`.
- `docker compose logs bootstrap_vector_ext` → `CREATE EXTENSION` (após a correção do YAML).
- `python -m py_compile src/*.py` → gate de sintaxe verde.
- Import de `langchain`, `langchain_openai`, `langchain_postgres`, `langchain_text_splitters`, `pypdf` → sem `ImportError`.

**Decisões tomadas**

- Nenhum arquivo novo em `src/`: F01 é só infraestrutura, código de produto é
  escopo de F02/F03/F04 (evita invadir a responsabilidade de outra feature).
- A correção do `docker-compose.yml` foi feita porque era **pré-requisito
  funcional** do CA-01.1 ("a extensão vector é criada") — sem ela, o critério de
  aceitação simplesmente não passa, independentemente de qualquer código Python.

**Perguntas de autoavaliação — F01**

1. **Por que `entrypoint: ["/bin/sh", "-c"]` + `command` como string quebra o script, mesmo o container saindo com exit code 0?**
   <details><summary>Resposta</summary>
   Porque quando `command` é uma string, o Docker Compose faz shell-split nela e a transforma numa lista de argumentos antes de concatenar com o `entrypoint`. A flag `-c` do `/bin/sh` só consome o argumento imediatamente seguinte como "script" — os demais viram parâmetros posicionais ignorados. Se esse primeiro argumento for uma sintaxe válida (mesmo que sem efeito, como uma atribuição de variável `VAR=valor`), o shell não gera erro e sai com código 0, mascarando a falha.
   </details>

2. **Por que transformar `command` numa lista YAML de um elemento resolve o problema?**
   <details><summary>Resposta</summary>
   Porque o Compose só aplica shell-split quando `command` é uma string escalar. Quando é uma lista, cada item da lista vira um argumento literal do processo, sem reprocessamento. Com um único item contendo o script inteiro, esse item chega intacto como o argumento do `-c`, e o `/bin/sh` o interpreta corretamente como um script completo (incluindo suas próprias aspas internas).
   </details>

3. **Por que um `exit code 0` não é prova suficiente de que a extensão `vector` foi criada?**
   <details><summary>Resposta</summary>
   Exit code 0 só significa que o processo não retornou erro — não que ele fez o que deveria. Um shell script vazio, ou uma atribuição de variável sem uso, também sai com 0. A validação real do CA-01.1 exige uma consulta direta (`SELECT extname FROM pg_extension WHERE extname='vector'`) que confirma o estado do banco, independentemente do que o container "disse" ter feito.
   </details>

4. **Por que a F01 não precisou (nem devia) escrever um script Python de verificação?**
   <details><summary>Resposta</summary>
   Porque a validação de infraestrutura pode ser feita inteiramente com as próprias ferramentas de infraestrutura (Docker Compose, psql, pip/uv) — não há lógica de negócio envolvida. Criar um `check_env.py` adicionaria código fora do previsto no PRD e antecipraria responsabilidades de conexão/embedding que pertencem à F02/F03, violando o princípio de uma feature por vez.
   </details>

5. **O que ainda falta antes de F02/F03 conseguirem rodar de ponta a ponta com a OpenAI real?**
   <details><summary>Resposta</summary>
   Substituir o valor placeholder `sk-sua-chave-aqui` em `OPENAI_API_KEY` por uma chave real da OpenAI. A F01 só valida que a variável existe no `.env`, não que ela é funcional — essa verificação fica para quando F02/F03 precisarem de fato chamar a API.
   </details>

### F02 — Ingestão do PDF
🔒 *A preencher após a implementação.*

### F03 — Busca Semântica e Resposta
🔒 *A preencher após a implementação.*

### F04 — CLI de Chat
🔒 *A preencher após a implementação.*

### F05 — README e Entrega
🔒 *A preencher após a implementação.*

---

## Parte 3 — Checklist final antes da entrega

- [ ] Consigo desenhar o fluxo completo (ingestão + consulta) de cabeça
- [ ] Sei explicar chunk_size, overlap e por que 1000/150
- [ ] Sei explicar o que é um embedding e o papel do text-embedding-3-small
- [ ] Sei explicar como o pgVector armazena e busca vetores
- [ ] Sei explicar a chain do search.py linha a linha
- [ ] Sei explicar por que o prompt fixo impede alucinação
- [ ] Respondi todas as perguntas de autoavaliação sem olhar as respostas
- [ ] (Opcional) Rodei o grill-me nas features F02 e F03

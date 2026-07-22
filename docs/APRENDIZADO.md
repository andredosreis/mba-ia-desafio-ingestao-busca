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

**O que foi feito e por quê**

Na F02 implementamos o pipeline completo de ingestão do documento PDF em `src/ingest.py`. O objetivo foi transformar o PDF bruto em vetores numéricos de 1536 dimensões e armazená-los no PostgreSQL com a extensão `pgvector`. 

Três decisões principais garantem o funcionamento correto:
1. **Idempotência com `pre_delete_collection=True`**: ao inicializar o `PGVector`, configuramos `pre_delete_collection=True`. Isso faz com que a coleção existente seja limpa antes da inserção, garantindo que re-execuções da ingestão não dupliquem os dados (atendendo ao CA-02.2).
2. **Chunking com `RecursiveCharacterTextSplitter`**: dividimos o texto em pedaços de no máximo 1000 caracteres com 150 caracteres de sobreposição (overlap). Isso preserva o contexto entre chunks adjacentes.
3. **Tratamento amigável de erros**: capturamos `FileNotFoundError` (PDF não encontrado) e erros de conexão com o banco de dados (banco parado), exibindo mensagens explicativas em português no `sys.stderr` e saindo com código 1 sem exibir tracebacks indecifráveis para o usuário.

**Passo a passo do código REAL (`src/ingest.py`)**

1. `carregar_paginas_pdf(caminho_pdf)`: verifica se o caminho do PDF existe (`os.path.exists`). Se não existir, lança `FileNotFoundError`. Caso exista, usa o `PyPDFLoader` para carregar o arquivo e retornar uma lista de `Document`.
2. `dividir_paginas_em_chunks(paginas)`: instancia `RecursiveCharacterTextSplitter` configurado com `chunk_size=1000` e `chunk_overlap=150`, retornando a lista de chunks.
3. `criar_vector_store_para_ingestao()`: valida as variáveis de ambiente (`DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, `OPENAI_EMBEDDING_MODEL`), instancia `OpenAIEmbeddings` com `text-embedding-3-small` e inicializa o `PGVector` com `pre_delete_collection=True`.
4. `ingest_pdf()`: orquestra todo o fluxo dentro de blocos `try/except`, chamando os helpers e invocando `vector_store.add_documents(chunks)`. Ao final, imprime no `stdout`: `Ingestão concluída: N chunks armazenados na collection 'document_chunks'.`

**Perguntas de autoavaliação — F02**

1. **Por que utilizamos `pre_delete_collection=True` na instanciação do PGVector?**
   <details><summary>Resposta</summary>
   Para garantir a idempotência do pipeline de ingestão. Ao recriar/limpar a coleção no PostgreSQL antes de adicionar os novos chunks, evitamos que a re-execução do script `src/ingest.py` acumule documentos duplicados na tabela do banco de dados.
   </details>

2. **Como o tratamento de erros do `ingest_pdf()` trata um arquivo PDF inexistente vs. falha na conexão do PostgreSQL?**
   <details><summary>Resposta</summary>
   O `carregar_paginas_pdf` lança `FileNotFoundError` com uma mensagem direcionando a checar a variável `PDF_PATH` no `.env`. Falhas de banco (como `OperationalError` ou recusa de conexão) são capturadas no `except Exception` principal e exibem uma mensagem orientando a subir o banco com `docker compose up -d`. Ambas as saídas são enviadas ao `sys.stderr` com `sys.exit(1)` e sem traceback cru.
   </details>

3. **Qual classe do LangChain foi utilizada para gerar os embeddings e qual modelo foi configurado?**
   <details><summary>Resposta</summary>
   Utilizamos a classe `OpenAIEmbeddings` da biblioteca `langchain_openai`, configurada com a variável de ambiente `OPENAI_EMBEDDING_MODEL` (cujo valor é `text-embedding-3-small`).
   </details>

---

### F03 — Busca Semântica e Resposta

**O que foi feito e por quê**

Na F03 implementamos a cadeia RAG de consulta em `src/search.py`. O componente recupera os 10 chunks mais relevantes do banco de dados PostgreSQL utilizando distância de cosseno, formata esses chunks dentro do prompt guardrail fixo do desafio e envia a requisição para a LLM (`ChatOpenAI`).

Decisões de destaque:
1. **Busca por similaridade `similarity_search_with_score(query, k=10)`**: conforme exigido pelo enunciado, realizamos a chamada literal de busca no `PGVector` fixando `k=10`.
2. **`PROMPT_TEMPLATE` Intocado**: preservamos o template original do desafio com os blocos `CONTEXTO`, `REGRAS`, `EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO` e `PERGUNTA DO USUÁRIO`, garantindo que a LLM responda estritamente com base nos dados recuperados e utilize a frase padrão exata para perguntas sem contexto.
3. **LCEL (LangChain Expression Language)**: a chain foi construída combinando `RunnableLambda(buscar_e_montar_contexto)`, `RunnablePassthrough()`, `PromptTemplate`, `ChatOpenAI` e `StrOutputParser()`.
4. **Interface dual em `search_prompt`**: quando chamada sem argumentos (`search_prompt()`), a função retorna o objeto chain pronto para ser invocado pelo chat (F04). Quando chamada com uma string (`search_prompt("pergunta")`), ela executa a busca e retorna diretamente a string de resposta.

**Passo a passo do código REAL (`src/search.py`)**

1. `montar_contexto(resultados)`: recebe a lista de tuplas `(Document, float)` retornada pelo `similarity_search_with_score`, extrai `page_content` de cada documento e os junta com `\n\n`.
2. `verificar_colecao_populada()`: executa uma consulta SQL via SQLAlchemy na tabela `langchain_pg_embedding` para verificar se a coleção possui registros (retornando `True` ou `False`), permitindo que a CLI (F04) alerte se o banco precisa de ingestão antes de aceitar perguntas.
3. `criar_vector_store_para_busca()`: inicializa a conexão com o `PGVector` sem `pre_delete_collection` (já que a busca é operação somente de leitura).
4. `criar_chain_rag()`: define a função interna `buscar_e_montar_contexto` (que executa `vector_store.similarity_search_with_score(pergunta, k=10)`), compõe o mapa LCEL e encadeia o `PromptTemplate`, `ChatOpenAI(model=OPENAI_MODEL)` e `StrOutputParser()`.
5. `search_prompt(question=None)`: gerencia a execução da chain e o tratamento de erros (exibindo mensagens claras em português e retornando `None` caso haja falha de conexão ou configuração).

**Perguntas de autoavaliação — F03**

1. **Por que o modelo de embedding usado na busca (`src/search.py`) precisa obrigatoriamente ser idêntico ao da ingestão (`src/ingest.py`)?**
   <details><summary>Resposta</summary>
   Cada modelo de embedding projeta o texto em um espaço vetorial distinto. Para que a distância de cosseno entre o vetor da pergunta e os vetores dos chunks armazenados seja matematicamente válida, ambos devem ser gerados pelo mesmo modelo (`text-embedding-3-small`).
   </details>

2. **Como a chain RAG lida com perguntas que não têm resposta no PDF (ex.: "Qual é a capital da França?")?**
   <details><summary>Resposta</summary>
   O `similarity_search_with_score` ainda trará os 10 chunks mais próximos no banco. No entanto, o `PROMPT_TEMPLATE` possui regras explícitas de guardrail e exemplos few-shot instruindo a LLM a responder exatamente `"Não tenho informações necessárias para responder sua pergunta."` quando a informação não estiver presente no contexto.
   </details>

3. **Qual é o comportamento da função `search_prompt()` quando invocada sem parâmetros versus com parâmetro?**
   <details><summary>Resposta</summary>
   Sem parâmetros (`search_prompt()`), ela constrói e retorna o objeto `Runnable` da chain LCEL. Com parâmetro (`search_prompt("pergunta")`), ela invoca a chain passando a pergunta e retorna diretamente a string com a resposta gerada pela LLM.
   </details>

### F04 — CLI de Chat

**O que foi feito e por quê**

Na F04 implementamos a interface de linha de comando (CLI) em `src/chat.py`, permitindo uma interação fluida em loop no terminal. A CLI se conecta com o componente de busca (F03) e com a base vetorial populada (F02).

Decisões de destaque:
1. **Validação de ambiente na inicialização (CA-04.4)**: antes de iniciar o loop de chat, `main()` verifica se a chain pôde ser criada (`search_prompt()`) e se a coleção do PGVector contém documentos (`verificar_colecao_populada()`). Se a base estiver vazia ou o ambiente com erro, a CLI imprime uma mensagem clara em português orientando os passos de correção e encerra graciosamente sem stack trace.
2. **Loop de chat resiliente (CA-04.1 e CA-04.2)**: a CLI exibe a mensagem inicial `"Faça sua pergunta:"` e entra em loop lendo `PERGUNTA: `. A resposta da LLM é impressa com o prefixo `RESPOSTA: `. Erros transitórios de modelo/rede na chamada do `.invoke()` são tratados por `processar_pergunta()`, exibindo aviso amigável sem encerrar a sessão de chat.
3. **Encerramento gracioso (CA-04.3)**: palavras-chave de saída (`sair`, `exit`, `quit` - case-insensitive) e atalhos de terminal (`Ctrl+C` / `KeyboardInterrupt` e `Ctrl+D` / `EOFError`) exibem a mensagem de despedida `"Encerrando. Até logo!"` e finalizam a aplicação com exit code 0 sem tracebacks.

**Passo a passo do código REAL (`src/chat.py`)**

1. `processar_pergunta(chain, pergunta: str)`: invoca `chain.invoke(pergunta)` dentro de um bloco `try/except`. Se ocorrer exceção na API, retorna a string `"Erro ao consultar o modelo. Verifique sua conexão e a OPENAI_API_KEY."`, mantendo o loop vivo.
2. `executar_loop_chat(chain)`: imprime `"Faça sua pergunta:"` e inicia um loop `while True`. Lê a entrada com `input("PERGUNTA: ").strip()`. Se vazia, ignora. Se corresponder a `COMANDOS_SAIDA` (`sair`, `exit`, `quit`), imprime despedida e encerra. Em caso de `KeyboardInterrupt` ou `EOFError`, imprime quebra de linha e despedida, encerrando graciosamente.
3. `main()`: invoca `search_prompt()`. Se retornar `None`, imprime instruções de solução (docker compose up -d, .env, ingest.py). Se `verificar_colecao_populada()` retornar `False`, imprime `"A base está vazia. Execute primeiro: python src/ingest.py"`. Se tudo estiver OK, chama `executar_loop_chat(chain)`.

**Perguntas de autoavaliação — F04**

1. **Como a CLI verifica se o banco de dados está populado antes de iniciar o loop de perguntas?**
   <details><summary>Resposta</summary>
   Invocando `verificar_colecao_populada()` exposta por `src/search.py`, que roda uma query SQL direta na tabela `langchain_pg_embedding` do Postgres sem fazer chamadas à API da OpenAI. Se retornar `False`, a CLI avisa para executar `python src/ingest.py` e encerra.
   </details>

2. **O que acontece se o usuário pressionar Ctrl+C (SIGINT) ou Ctrl+D (EOF) durante a leitura do prompt?**
   <details><summary>Resposta</summary>
   A exceção `KeyboardInterrupt` ou `EOFError` é capturada pelo bloco `try/except` de `executar_loop_chat()`, imprimindo a mensagem de despedida `"Encerrando. Até logo!"` e saindo graciosamente com exit code 0, sem exibir traceback de Python no terminal.
   </details>

3. **Por que erros ao invocar a chain RAG (`chain.invoke`) não encerram o loop de chat?**
   <details><summary>Resposta</summary>
   Porque `processar_pergunta()` envolve a chamada em um `try/except Exception`, capturando falhas pontuais de API ou rede e retornando uma mensagem de erro em português. Assim, o erro é exibido no campo `RESPOSTA: `, e a CLI continua pronta para aceitar novas perguntas do usuário.
   </details>

### F05 — README e Entrega

**O que foi feito e por quê**

Na F05 finalizamos a documentação principal no `README.md` e a validação de higiene do repositório público para a entrega do desafio.

Decisões de destaque:
1. **Documentação completa e autossuficiente (CA-05.1 e CA-05.2)**: o `README.md` foi elaborado em português claro, contendo pré-requisitos, instruções de criação/ativação do `venv`, instalação de dependências, tabela explicativa de variáveis de ambiente, ordem literal de execução (`docker compose up -d` -> `python src/ingest.py` -> `python src/chat.py`), exemplos de uso formatados em `PERGUNTA:` / `RESPOSTA:` (com pergunta no contexto e fora do contexto) e seção de solução de problemas.
2. **Higiene do repositório público (CA-05.3)**: confirmamos que nenhum arquivo sensível ou local (`.env`, `venv/`, `pgdata/`) está rastreado no git. Validamos a presença de todos os entregáveis do template e garantimos a ausência de chaves reais da OpenAI commitadas.

**Perguntas de autoavaliação — F05**

1. **Qual é a ordem exata de comandos necessária para subir e executar o sistema do zero em uma máquina limpa?**
   <details><summary>Resposta</summary>
   1) `python3 -m venv venv && source venv/bin/activate`  
   2) `pip install -r requirements.txt`  
   3) `cp .env.example .env` (e preencher `OPENAI_API_KEY`)  
   4) `docker compose up -d`  
   5) `python src/ingest.py`  
   6) `python src/chat.py`
   </details>

2. **Quais arquivos/diretórios NUNCA devem ser commitados no repositório público e por quê?**
   <details><summary>Resposta</summary>
   O arquivo `.env` (contém credenciais reais como a `OPENAI_API_KEY`), o diretório `venv/` (ambiente virtual Python local dependente de SO) e `pgdata/` (dados físicos do Postgres). Todos eles são ignorados pelo `.gitignore`.
   </details>

3. **Como o README documenta o comportamento do sistema diante de perguntas fora do contexto do PDF?**
   <details><summary>Resposta</summary>
   Exibindo um exemplo claro onde uma pergunta fora do documento (ex.: "Qual é a capital da França?") recebe obrigatoriamente a resposta padrão exata: `"Não tenho informações necessárias para responder sua pergunta."`.
   </details>

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

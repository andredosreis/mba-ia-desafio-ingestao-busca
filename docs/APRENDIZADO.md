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
🔒 *A preencher após a implementação.*

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

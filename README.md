# Ingestão e Busca Semântica com LangChain e PostgreSQL (pgVector)

Sistema RAG (*Retrieval-Augmented Generation*) desenvolvido como desafio prático da pós-graduação **Full Cycle**. O projeto realiza a ingestão de um documento PDF, calcula embeddings vetoriais (OpenAI ou Gemini, à sua escolha), armazena os chunks no PostgreSQL utilizando a extensão `pgVector` e disponibiliza uma interface CLI interativa de chat restrita estritamente ao conteúdo do documento.

---

## 🚀 Arquitetura e Tecnologias

- **Linguagem**: Python 3.10+
- **Framework de IA**: [LangChain](https://python.langchain.com/) (`langchain_openai`, `langchain_google_genai`, `langchain_postgres`, `langchain_text_splitters`)
- **Banco de Dados**: PostgreSQL 17 + extensão `pgVector`
- **Infraestrutura**: Docker & Docker Compose
- **Providers suportados** (selecionáveis por `LLM_PROVIDER`):

| | OpenAI (padrão) | Gemini |
|---|---|---|
| **Embeddings** | `text-embedding-3-small` (1536 dimensões) | `models/gemini-embedding-001` (3072 dimensões) |
| **LLM** | `OPENAI_MODEL` (ex.: `gpt-5-nano`, `gpt-4o-mini`) | `gemini-2.5-flash` |
| **Chave** | `OPENAI_API_KEY` | `GOOGLE_API_KEY` |

---

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/)
- [Python 3.10+](https://www.python.org/)
- Uma chave de API ativa de **um** destes providers:
  - [OpenAI](https://platform.openai.com/) → `OPENAI_API_KEY` (padrão), **ou**
  - [Google AI Studio](https://aistudio.google.com/apikey) → `GOOGLE_API_KEY` (alternativa)

---

## ⚙️ Configuração do Ambiente

### 1. Clonar o Repositório

```bash
git clone https://github.com/andredosreis/mba-ia-desafio-ingestao-busca.git
cd mba-ia-desafio-ingestao-busca
```

### 2. Criar e Ativar o Ambiente Virtual (venv)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente

Crie o arquivo `.env` a partir do modelo `.env.example`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e insira a chave do provider escolhido (`OPENAI_API_KEY` **ou** `GOOGLE_API_KEY`):

| Variável | Descrição | Valor Padrão / Exemplo |
|---|---|---|
| `LLM_PROVIDER` | Provider ativo: `openai` ou `gemini`. Se omitida, vale `openai` | `openai` |
| `DATABASE_URL` | URL de conexão do PostgreSQL (driver `psycopg 3`) | `postgresql+psycopg://postgres:postgres@localhost:5432/rag` |
| `PG_VECTOR_COLLECTION_NAME` | Nome da coleção no PGVector | `document_chunks` |
| `OPENAI_EMBEDDING_MODEL` | Modelo de embedding da OpenAI (usado se `LLM_PROVIDER=openai`) | `text-embedding-3-small` |
| `OPENAI_MODEL` | Modelo de linguagem (LLM) da OpenAI | `gpt-5-nano` ou `gpt-4o-mini` |
| `OPENAI_API_KEY` | Sua chave de API da OpenAI | `sk-proj-...` |
| `GOOGLE_EMBEDDING_MODEL` | Modelo de embedding do Gemini (usado se `LLM_PROVIDER=gemini`) | `models/gemini-embedding-001` |
| `GOOGLE_MODEL` | Modelo de linguagem (LLM) do Gemini | `gemini-2.5-flash` |
| `GOOGLE_API_KEY` | Sua chave de API do Google AI Studio | `AIza...` |
| `PDF_PATH` | Caminho do arquivo PDF a ingerir | `document.pdf` |

---

## 🔀 Escolhendo o Provider (OpenAI ou Gemini)

O pipeline roda inteiro com qualquer um dos dois. A escolha é **explícita**, pela variável `LLM_PROVIDER` — não há detecção automática, então as duas chaves podem conviver no mesmo `.env` sem ambiguidade.

**Para usar a OpenAI** (padrão — basta não mexer):
```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-sua-chave-real
```

**Para usar o Gemini:**
```dotenv
LLM_PROVIDER=gemini
GOOGLE_API_KEY=AIza-sua-chave-real
```

> ⚠️ **Trocar de provider exige re-executar a ingestão.** Os vetores da OpenAI têm 1536 dimensões e os do Gemini têm 3072 — são incompatíveis na mesma coleção. Depois de mudar o `LLM_PROVIDER`, rode `python src/ingest.py` novamente (ele recria a coleção do zero com `pre_delete_collection=True`).

Ingestão e busca obtêm o modelo pela **mesma** função (`src/providers.py`), o que garante por construção a restrição do desafio: o mesmo modelo de embedding nas duas pontas.

Modelos Gemini validados de ponta a ponta neste projeto: `models/gemini-embedding-001` (embeddings) e `gemini-2.5-flash` (chat). Outros nomes comuns — `gemini-1.5-flash`, `gemini-2.0-flash`, `models/text-embedding-004`, `models/embedding-001` — retornam **404** nesta API e fazem a biblioteca gastar ~60s em retries.

---

## 🏁 Ordem de Execução

Siga rigorosamente os 3 passos abaixo para rodar o produto:

### Passo 1: Subir o Banco de Dados (PostgreSQL + pgVector)

```bash
docker compose up -d
```
> O container `postgres_rag` subirá na porta `5432` e o serviço `bootstrap_vector_ext` habilitará a extensão `vector` automaticamente.

### Passo 2: Executar a Ingestão do PDF

```bash
python src/ingest.py
```
> Esse comando lê o arquivo `document.pdf`, divide o conteúdo em chunks com overlap, gera os embeddings e armazena os vetores no banco de dados.

### Passo 3: Iniciar a CLI de Chat

```bash
python src/chat.py
```
> Inicia a sessão interativa de chat no terminal.

---

## 💬 Exemplos de Uso (CLI de Chat)

Abaixo estão exemplos reais de interação via terminal, capturados com o provider Gemini.

> O `document.pdf` deste repositório é uma tabela com **nome, faturamento e ano de fundação** de empresas fictícias. As perguntas dentro do contexto refletem esse conteúdo — perguntas genéricas sobre "o objetivo do documento" caem, corretamente, na resposta padrão.

### Pergunta dentro do contexto do documento:
```text
Faça sua pergunta:
PERGUNTA: Qual o faturamento da Alfa Energia S.A.?
RESPOSTA: O faturamento da Alfa Energia S.A. é R$ 722.875.391,46.

PERGUNTA: Em que ano a Alfa Energia Holding foi fundada?
RESPOSTA: A Alfa Energia Holding foi fundada em 1971.

PERGUNTA:
```

### Pergunta fora do contexto do documento:
```text
PERGUNTA: Qual é a capital da França?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

PERGUNTA:
```

### Encerrando a sessão:
```text
PERGUNTA: sair
Encerrando. Até logo!
```
*(Você também pode encerrar a qualquer momento pressionando `Ctrl+C` ou `Ctrl+D`)*.

---

## 🧩 Como Funciona o Pipeline RAG

1. **Ingestão (`src/ingest.py`)**:
   - Carrega o arquivo configurado em `PDF_PATH` via `PyPDFLoader`.
   - Aplica `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)`.
   - Limpa a coleção anterior (`pre_delete_collection=True`) para garantir idempotência.
   - Converte os chunks em vetores via o provider ativo (`src/providers.py` → `OpenAIEmbeddings` ou `GoogleGenerativeAIEmbeddings`) e salva no `PGVector`.

2. **Busca e Resposta (`src/search.py`)**:
   - Executa busca por similaridade vetorial via `similarity_search_with_score(query, k=10)`.
   - Junta o texto dos 10 chunks no placeholder `{contexto}` do prompt fixo.
   - Aplica o guardrail estrito: se o contexto não contiver a resposta, a LLM responde obrigatoriamente `"Não tenho informações necessárias para responder sua pergunta."`.

3. **Interface CLI (`src/chat.py`)**:
   - Valida se o banco está acessível e a coleção populada antes de liberar o prompt.
   - Executa a chain RAG em loop com formatação `PERGUNTA: ` e `RESPOSTA: `.

---

## 🛠️ Solução de Problemas

- **Erro `não foi possível conectar ao banco`**:
  Verifique se o Docker está rodando e execute `docker compose up -d`.
- **Erro `Porta 5432 já está em uso`**:
  Verifique se você já possui uma instância local do PostgreSQL rodando na máquina (`sudo service postgresql stop` ou pare o container conflitante).
- **Mensagem `A base está vazia. Execute primeiro: python src/ingest.py`**:
  A CLI detectou que a ingestão não foi realizada. Execute `python src/ingest.py` antes de rodar o chat.
- **Erro `OPENAI_API_KEY não configurada`** (ou `GOOGLE_API_KEY não configurada`):
  Certifique-se de ter criado o arquivo `.env` a partir do `.env.example` e substituído o placeholder pela chave real **do provider indicado em `LLM_PROVIDER`**.
- **Erro `LLM_PROVIDER='...' inválido`**:
  Os únicos valores aceitos são `openai` e `gemini`. Deixar a variável em branco equivale a `openai`.
- **Erro de dimensão dos vetores após trocar de provider**:
  A coleção ainda guarda vetores do provider anterior. Rode `python src/ingest.py` de novo para recriá-la.

---

## 🧪 Executando os Testes Unitários

Para rodar a suíte automatizada de testes (com mocks de API e banco de dados):

```bash
python -m pytest tests/ -q
```
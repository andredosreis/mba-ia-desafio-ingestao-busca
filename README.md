# Ingestão e Busca Semântica com LangChain e PostgreSQL (pgVector)

Sistema RAG (*Retrieval-Augmented Generation*) desenvolvido como desafio prático da pós-graduação **Full Cycle**. O projeto realiza a ingestão de um documento PDF, calcula embeddings vetoriais com a OpenAI, armazena os chunks no PostgreSQL utilizando a extensão `pgVector` e disponibiliza uma interface CLI interativa de chat restrita estritamente ao conteúdo do documento.

---

## 🚀 Arquitetura e Tecnologias

- **Linguagem**: Python 3.10+
- **Framework de IA**: [LangChain](https://python.langchain.com/) (`langchain_openai`, `langchain_postgres`, `langchain_text_splitters`)
- **Banco de Dados**: PostgreSQL 17 + extensão `pgVector`
- **Infraestrutura**: Docker & Docker Compose
- **Modelos OpenAI**:
  - **Embeddings**: `text-embedding-3-small` (1536 dimensões)
  - **LLM**: Definido em `OPENAI_MODEL` no `.env` (ex.: `gpt-5-nano`, `gpt-4o-mini`)

---

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/)
- [Python 3.10+](https://www.python.org/)
- Uma chave de API ativa da [OpenAI](https://platform.openai.com/) (`OPENAI_API_KEY`)

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

Edite o arquivo `.env` e insira sua chave da OpenAI em `OPENAI_API_KEY`:

| Variável | Descrição | Valor Padrão / Exemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexão do PostgreSQL (driver `psycopg 3`) | `postgresql+psycopg://postgres:postgres@localhost:5432/rag` |
| `PG_VECTOR_COLLECTION_NAME` | Nome da coleção no PGVector | `document_chunks` |
| `OPENAI_EMBEDDING_MODEL` | Modelo de embedding da OpenAI | `text-embedding-3-small` |
| `OPENAI_MODEL` | Modelo de linguagem (LLM) | `gpt-5-nano` ou `gpt-4o-mini` |
| `OPENAI_API_KEY` | Sua chave de API da OpenAI | `sk-proj-...` |
| `PDF_PATH` | Caminho do arquivo PDF a ingerir | `document.pdf` |

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

Abaixo estão exemplos reais de interação via terminal:

### Pergunta dentro do contexto do documento:
```text
Faça sua pergunta:
PERGUNTA: Qual é o principal objetivo do documento?
RESPOSTA: O documento apresenta as diretrizes e regras para a implementação da busca semântica com LangChain e pgVector...

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
   - Converte os chunks em vetores via `OpenAIEmbeddings` (`text-embedding-3-small`) e salva no `PGVector`.

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
- **Erro `OPENAI_API_KEY não configurada`**:
  Certifique-se de ter criado o arquivo `.env` a partir do `.env.example` e substituído o valor de `OPENAI_API_KEY` por uma chave válida da OpenAI.

---

## 🧪 Executando os Testes Unitários

Para rodar a suíte automatizada de testes (com mocks de API e banco de dados):

```bash
python -m pytest tests/ -q
```
import os
import sys
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from psycopg import OperationalError as PsycopgOperationalError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError

load_dotenv()


def erro_causado_por_falha_de_conexao(excecao: BaseException) -> bool:
    """True se a cadeia de causas contém um OperationalError (banco inacessível)."""
    causa: BaseException | None = excecao
    while causa is not None:
        if isinstance(causa, (SQLAlchemyOperationalError, PsycopgOperationalError)):
            return True
        causa = causa.__cause__ or causa.__context__
    return False


PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def montar_contexto(resultados: list[tuple[Document, float]]) -> str:
    """Concatena o page_content dos documentos com '\n\n' (ignora scores)."""
    if not resultados:
        return ""
    docs = [doc for doc, _ in resultados]
    return "\n\n".join(doc.page_content for doc in docs)


def verificar_colecao_populada() -> bool:
    """True se a collection tem ao menos 1 documento (consulta SQL, sem API)."""
    connection = os.getenv("DATABASE_URL")
    collection_name = os.getenv("PG_VECTOR_COLLECTION_NAME", "document_chunks")
    if not connection:
        return False
    try:
        engine = create_engine(connection)
        query = text(
            "SELECT count(*) FROM langchain_pg_embedding e "
            "JOIN langchain_pg_collection c ON e.collection_id = c.uuid "
            "WHERE c.name = :col_name"
        )
        with engine.connect() as conn:
            res = conn.execute(query, {"col_name": collection_name}).scalar()
            return bool(res and res > 0)
    except Exception:
        return False


def criar_vector_store_para_busca() -> PGVector:
    """PGVector sem pre_delete_collection."""
    connection = os.getenv("DATABASE_URL")
    collection_name = os.getenv("PG_VECTOR_COLLECTION_NAME")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL")

    for var_name, var_val in [
        ("DATABASE_URL", connection),
        ("PG_VECTOR_COLLECTION_NAME", collection_name),
        ("OPENAI_EMBEDDING_MODEL", embedding_model),
    ]:
        if not var_val:
            raise ValueError(f"Erro: variável {var_name} não definida no .env.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-sua-chave-aqui":
        raise ValueError(
            "Erro: OPENAI_API_KEY não configurada no .env "
            "(substitua o placeholder por uma chave real)."
        )

    embeddings = OpenAIEmbeddings(model=embedding_model)
    return PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )


def criar_chain_rag() -> Runnable:
    """Monta a chain LCEL: busca k=10 -> prompt fixo -> LLM -> str."""
    model_name = os.getenv("OPENAI_MODEL")
    if not model_name:
        raise ValueError("Erro: variável OPENAI_MODEL não definida no .env.")

    vector_store = criar_vector_store_para_busca()

    def buscar_e_montar_contexto(pergunta: str) -> str:
        resultados = vector_store.similarity_search_with_score(pergunta, k=10)
        return montar_contexto(resultados)

    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
    llm = ChatOpenAI(model=model_name)

    chain = (
        {
            "contexto": RunnableLambda(buscar_e_montar_contexto),
            "pergunta": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def search_prompt(question: str | None = None) -> Runnable | str | None:
    """Sem argumento: retorna a chain (com .invoke(pergunta) -> str).
    Com argumento: retorna a resposta (str). Falha de inicialização:
    imprime orientação em PT no stderr e retorna None.
    """
    try:
        load_dotenv()
        chain = criar_chain_rag()
        if question is None:
            return chain
        return chain.invoke(question)
    except Exception as e:
        if erro_causado_por_falha_de_conexao(e):
            print(
                "Erro: não foi possível conectar ao banco. Suba-o com: docker compose up -d",
                file=sys.stderr,
            )
        else:
            print(f"Falha ao iniciar a busca: {e}", file=sys.stderr)
        return None
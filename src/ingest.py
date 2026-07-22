import os
import sys
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from psycopg import OperationalError as PsycopgOperationalError
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError

load_dotenv()

PDF_PATH = os.getenv("PDF_PATH")


def erro_causado_por_falha_de_conexao(excecao: BaseException) -> bool:
    """True se a cadeia de causas contém um OperationalError (banco inacessível)."""
    causa: BaseException | None = excecao
    while causa is not None:
        if isinstance(causa, (SQLAlchemyOperationalError, PsycopgOperationalError)):
            return True
        causa = causa.__cause__ or causa.__context__
    return False


def carregar_paginas_pdf(caminho_pdf: str) -> list[Document]:
    """Carrega o PDF via PyPDFLoader; FileNotFoundError se não existir."""
    if not caminho_pdf or not os.path.exists(caminho_pdf):
        raise FileNotFoundError(
            f"Erro: arquivo PDF não encontrado em '{caminho_pdf}'. Verifique PDF_PATH no .env."
        )
    loader = PyPDFLoader(caminho_pdf)
    return loader.load()


def dividir_paginas_em_chunks(paginas: list[Document]) -> list[Document]:
    """RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    return text_splitter.split_documents(paginas)


def criar_vector_store_para_ingestao() -> PGVector:
    """PGVector com pre_delete_collection=True (recria a collection)."""
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
        pre_delete_collection=True,
    )


def ingest_pdf() -> None:
    """Orquestra: carregar -> dividir -> embutir/persistir.
    Erros viram mensagens em português e sys.exit(1).
    """
    try:
        pdf_path = os.getenv("PDF_PATH")
        paginas = carregar_paginas_pdf(pdf_path)
        chunks = dividir_paginas_em_chunks(paginas)
        vector_store = criar_vector_store_para_ingestao()
        vector_store.add_documents(chunks)
        collection_name = os.getenv("PG_VECTOR_COLLECTION_NAME", "document_chunks")
        print(
            f"Ingestão concluída: {len(chunks)} chunks armazenados na collection '{collection_name}'."
        )
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except (SQLAlchemyOperationalError, PsycopgOperationalError):
        print(
            "Erro: não foi possível conectar ao banco. Suba-o com: docker compose up -d",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        if erro_causado_por_falha_de_conexao(e):
            print(
                "Erro: não foi possível conectar ao banco. Suba-o com: docker compose up -d",
                file=sys.stderr,
            )
        else:
            print(f"Erro na ingestão: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    ingest_pdf()
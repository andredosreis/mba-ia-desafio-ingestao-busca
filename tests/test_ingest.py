import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError

from src.ingest import (
    carregar_paginas_pdf,
    criar_vector_store_para_ingestao,
    dividir_paginas_em_chunks,
    ingest_pdf,
)


def test_dividir_paginas_em_chunks_limite_e_overlap():
    # Cria texto sintético longo (>1500 chars) com tokens DISTINTOS: com
    # palavras únicas, um trecho do fim do chunk 1 só reaparece no início
    # do chunk 2 se houver overlap>0 (com texto uniforme, um falso
    # positivo seria possível mesmo com overlap=0).
    texto_longo = " ".join(f"palavra{i:04d}" for i in range(400))
    doc_sintetico = Document(page_content=texto_longo, metadata={"source": "test.pdf"})

    chunks = dividir_paginas_em_chunks([doc_sintetico])

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.page_content) <= 1000

    # Verifica se há overlap entre o final do 1º chunk e o início do 2º chunk
    chunk1_end = chunks[0].page_content[-100:]
    assert chunk1_end in chunks[1].page_content


def test_carregar_paginas_pdf_arquivo_inexistente():
    with pytest.raises(FileNotFoundError) as exc_info:
        carregar_paginas_pdf("caminho_inexistente_12345.pdf")

    assert "arquivo PDF não encontrado" in str(exc_info.value)
    assert "caminho_inexistente_12345.pdf" in str(exc_info.value)


def test_criar_vector_store_para_ingestao():
    with patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+psycopg://postgres:postgres@localhost:5432/rag",
            "PG_VECTOR_COLLECTION_NAME": "test_collection",
            "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
            "OPENAI_API_KEY": "sk-fake-para-teste",
        },
    ), patch("src.ingest.PGVector") as mock_pgvector, patch(
        "src.ingest.OpenAIEmbeddings"
    ) as mock_embeddings:
        store = criar_vector_store_para_ingestao()

        mock_embeddings.assert_called_once_with(model="text-embedding-3-small")
        mock_pgvector.assert_called_once_with(
            embeddings=mock_embeddings.return_value,
            collection_name="test_collection",
            connection="postgresql+psycopg://postgres:postgres@localhost:5432/rag",
            use_jsonb=True,
            pre_delete_collection=True,
        )
        assert store == mock_pgvector.return_value


def test_ingest_pdf_sucesso_mockado(capsys):
    chunks_esperados = [Document(page_content="Texto de teste")]
    with patch(
        "src.ingest.carregar_paginas_pdf",
        return_value=[Document(page_content="Texto de teste")],
    ), patch(
        "src.ingest.dividir_paginas_em_chunks",
        return_value=chunks_esperados,
    ), patch(
        "src.ingest.criar_vector_store_para_ingestao"
    ) as mock_criar_store:
        mock_store = MagicMock()
        mock_criar_store.return_value = mock_store

        ingest_pdf()

        mock_store.add_documents.assert_called_once_with(chunks_esperados)
        captured = capsys.readouterr()
        assert "Ingestão concluída:" in captured.out


def test_ingest_pdf_trata_pdf_ausente(capsys):
    with patch.dict(os.environ, {"PDF_PATH": "nao_existe.pdf"}):
        with pytest.raises(SystemExit) as exc_info:
            ingest_pdf()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Erro: arquivo PDF não encontrado em 'nao_existe.pdf'" in captured.err


def test_ingest_pdf_trata_banco_fora_do_ar_via_cadeia_de_causas(capsys):
    """Regressão: o langchain_postgres embrulha o OperationalError original
    num Exception genérico ('Failed to create vector extension: ...') via
    `raise Exception(...) from e`. A detecção precisa seguir __cause__/
    __context__, não só o tipo direto da exceção capturada.
    """
    operational_error_original = SQLAlchemyOperationalError(
        "stmt", {}, Exception("refused")
    )

    def levantar_erro_embrulhado(*args, **kwargs):
        raise Exception(
            "Failed to create vector extension: connection refused"
        ) from operational_error_original

    with patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+psycopg://postgres:postgres@localhost:5432/rag",
            "PG_VECTOR_COLLECTION_NAME": "test_collection",
            "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
            "OPENAI_API_KEY": "sk-fake-para-teste",
        },
    ), patch(
        "src.ingest.carregar_paginas_pdf",
        return_value=[Document(page_content="Texto de teste")],
    ), patch(
        "src.ingest.dividir_paginas_em_chunks",
        return_value=[Document(page_content="Texto de teste")],
    ), patch(
        "src.ingest.PGVector", side_effect=levantar_erro_embrulhado
    ), patch("src.ingest.OpenAIEmbeddings"):
        with pytest.raises(SystemExit) as exc_info:
            ingest_pdf()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "docker compose up -d" in captured.err
        assert "Failed to create vector extension" not in captured.err

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from src.search import (
    PROMPT_TEMPLATE,
    criar_chain_rag,
    montar_contexto,
    search_prompt,
    verificar_colecao_populada,
)


def test_montar_contexto_concatenacao_e_ignora_scores():
    doc1 = Document(page_content="Primeiro parágrafo do PDF.")
    doc2 = Document(page_content="Segundo parágrafo do PDF.")

    resultados = [(doc1, 0.12), (doc2, 0.45)]
    contexto = montar_contexto(resultados)

    assert contexto == "Primeiro parágrafo do PDF.\n\nSegundo parágrafo do PDF."


PROMPT_TEMPLATE_ESPERADO = """
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


def test_guard_prompt_template_igual_ao_especificado():
    """Guarda de igualdade integral: PROMPT_TEMPLATE é FIXO (não reescrever,
    não "melhorar") — qualquer alteração de um único caractere deve quebrar
    este teste.
    """
    assert PROMPT_TEMPLATE == PROMPT_TEMPLATE_ESPERADO


def test_busca_k10_literal_e_chain_rag():
    with patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+psycopg://postgres:postgres@localhost:5432/rag",
            "PG_VECTOR_COLLECTION_NAME": "test_collection",
            "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
            "OPENAI_MODEL": "gpt-5-nano",
            "OPENAI_API_KEY": "sk-fake-para-teste",
        },
    ), patch("src.search.PGVector") as mock_pgvector, patch(
        "src.search.ChatOpenAI"
    ) as mock_chat:
        mock_store = MagicMock()
        mock_pgvector.return_value = mock_store
        mock_store.similarity_search_with_score.return_value = [
            (Document(page_content="Conteúdo de teste"), 0.1)
        ]

        fake_llm = RunnableLambda(
            lambda prompt_val: AIMessage(content="Resposta de teste")
        )
        mock_chat.return_value = fake_llm

        chain = criar_chain_rag()
        assert chain is not None

        res = chain.invoke("Qual é o faturamento?")
        assert res == "Resposta de teste"
        # Verifica se similarity_search_with_score foi chamado com k=10
        mock_store.similarity_search_with_score.assert_called_once_with(
            "Qual é o faturamento?", k=10
        )




def test_search_prompt_sem_e_com_argumento():
    with patch("src.search.criar_chain_rag") as mock_criar_chain:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Resposta gerada"
        mock_criar_chain.return_value = mock_chain

        # Sem argumento -> retorna a chain
        chain = search_prompt()
        assert chain == mock_chain

        # Com argumento -> invoca a chain e retorna string
        resposta = search_prompt("Pergunta de teste")
        assert resposta == "Resposta gerada"
        mock_chain.invoke.assert_called_once_with("Pergunta de teste")


def test_search_prompt_falha_inicializacao(capsys):
    with patch(
        "src.search.criar_chain_rag", side_effect=ValueError("Env ausente")
    ):
        res = search_prompt("Qualquer pergunta")

        assert res is None
        captured = capsys.readouterr()
        assert "Falha ao iniciar a busca: Env ausente" in captured.err


def test_verificar_colecao_populada_sem_env():
    with patch.dict(os.environ, {}, clear=True):
        assert verificar_colecao_populada() is False

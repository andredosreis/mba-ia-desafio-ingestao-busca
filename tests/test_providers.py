import os
from unittest.mock import patch

import pytest

from src.providers import (
    criar_chat_llm,
    criar_embeddings,
    obter_provider,
    validar_credencial_do_provider,
)

# Valores esperados escritos como literais e deliberadamente NÃO importados de
# `src.providers`: comparar o default com a própria constante do módulo torna o
# assert tautológico — trocar o default por um nome que retorna 404 (como
# `models/embedding-001`) passaria despercebido pela suíte inteira.
MODELO_EMBEDDING_GEMINI_ESPERADO = "models/gemini-embedding-001"
MODELO_CHAT_GEMINI_ESPERADO = "gemini-2.5-flash"
# REST, e não o gRPC padrão: o canal gRPC assíncrono que a biblioteca cria sem
# usar imprime um traceback cru ao encerrar o processo.
TRANSPORTE_GEMINI_ESPERADO = "rest"

# `clear=True` em todos os patch.dict: `load_dotenv()` roda no import dos
# módulos de src/ e injeta as chaves reais do .env em os.environ — sem limpar,
# os testes ficariam dependentes da máquina de quem roda.
AMBIENTE_OPENAI = {
    "OPENAI_API_KEY": "sk-fake-para-teste",
    "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
    "OPENAI_MODEL": "gpt-5-nano",
}
AMBIENTE_GEMINI = {
    "LLM_PROVIDER": "gemini",
    "GOOGLE_API_KEY": "AIza-fake-para-teste",
}


def test_obter_provider_default_e_valores_aceitos():
    with patch.dict(os.environ, {}, clear=True):
        assert obter_provider() == "openai"

    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini"}, clear=True):
        assert obter_provider() == "gemini"

    # Tolerante a caixa e espaços acidentais no .env
    with patch.dict(os.environ, {"LLM_PROVIDER": " GEMINI "}, clear=True):
        assert obter_provider() == "gemini"


def test_obter_provider_valor_invalido_levanta_erro_em_portugues():
    with patch.dict(os.environ, {"LLM_PROVIDER": "foo"}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            obter_provider()

    mensagem = str(exc_info.value)
    assert "LLM_PROVIDER='foo' inválido" in mensagem
    assert "openai" in mensagem and "gemini" in mensagem


def test_criar_embeddings_e_chat_com_gemini_usa_classes_google_e_defaults():
    with patch.dict(os.environ, AMBIENTE_GEMINI, clear=True), patch(
        "src.providers.GoogleGenerativeAIEmbeddings"
    ) as mock_embeddings_google, patch(
        "src.providers.ChatGoogleGenerativeAI"
    ) as mock_chat_google, patch(
        "src.providers.OpenAIEmbeddings"
    ) as mock_embeddings_openai, patch("src.providers.ChatOpenAI") as mock_chat_openai:
        embeddings = criar_embeddings()
        llm = criar_chat_llm()

        mock_embeddings_google.assert_called_once_with(
            model=MODELO_EMBEDDING_GEMINI_ESPERADO,
            transport=TRANSPORTE_GEMINI_ESPERADO,
        )
        mock_chat_google.assert_called_once_with(
            model=MODELO_CHAT_GEMINI_ESPERADO,
            transport=TRANSPORTE_GEMINI_ESPERADO,
        )
        assert embeddings == mock_embeddings_google.return_value
        assert llm == mock_chat_google.return_value
        # O provider inativo não pode ser tocado
        mock_embeddings_openai.assert_not_called()
        mock_chat_openai.assert_not_called()


def test_criar_embeddings_e_chat_com_gemini_respeita_modelos_do_env():
    ambiente = {
        **AMBIENTE_GEMINI,
        "GOOGLE_EMBEDDING_MODEL": "models/outro-embedding",
        "GOOGLE_MODEL": "gemini-outro-flash",
    }
    with patch.dict(os.environ, ambiente, clear=True), patch(
        "src.providers.GoogleGenerativeAIEmbeddings"
    ) as mock_embeddings_google, patch(
        "src.providers.ChatGoogleGenerativeAI"
    ) as mock_chat_google:
        criar_embeddings()
        criar_chat_llm()

        mock_embeddings_google.assert_called_once_with(
            model="models/outro-embedding", transport=TRANSPORTE_GEMINI_ESPERADO
        )
        mock_chat_google.assert_called_once_with(
            model="gemini-outro-flash", transport=TRANSPORTE_GEMINI_ESPERADO
        )


@pytest.mark.parametrize("llm_provider", ["openai", None])
def test_criar_embeddings_e_chat_com_openai_explicito_e_por_default(llm_provider):
    ambiente = dict(AMBIENTE_OPENAI)
    if llm_provider is not None:
        ambiente["LLM_PROVIDER"] = llm_provider

    with patch.dict(os.environ, ambiente, clear=True), patch(
        "src.providers.OpenAIEmbeddings"
    ) as mock_embeddings_openai, patch(
        "src.providers.ChatOpenAI"
    ) as mock_chat_openai, patch(
        "src.providers.GoogleGenerativeAIEmbeddings"
    ) as mock_embeddings_google, patch(
        "src.providers.ChatGoogleGenerativeAI"
    ) as mock_chat_google:
        criar_embeddings()
        criar_chat_llm()

        mock_embeddings_openai.assert_called_once_with(model="text-embedding-3-small")
        mock_chat_openai.assert_called_once_with(model="gpt-5-nano")
        mock_embeddings_google.assert_not_called()
        mock_chat_google.assert_not_called()


def test_validar_credencial_cobra_a_chave_do_provider_ativo():
    # Gemini ativo: a chave da OpenAI presente não supre a GOOGLE_API_KEY ausente
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-real"}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            validar_credencial_do_provider("gemini")
        assert "GOOGLE_API_KEY não configurada no .env" in str(exc_info.value)

    # OpenAI ativo: a chave do Google presente não supre a OPENAI_API_KEY ausente
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIza-real"}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            validar_credencial_do_provider("openai")
        assert "OPENAI_API_KEY não configurada no .env" in str(exc_info.value)


@pytest.mark.parametrize(
    ("provider", "nome_da_variavel", "placeholder"),
    [
        ("openai", "OPENAI_API_KEY", "sk-sua-chave-aqui"),
        ("gemini", "GOOGLE_API_KEY", "AIza-sua-chave-aqui"),
    ],
)
def test_validar_credencial_rejeita_placeholder_do_env_example(
    provider, nome_da_variavel, placeholder
):
    with patch.dict(os.environ, {nome_da_variavel: placeholder}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            validar_credencial_do_provider(provider)

    assert f"Erro: {nome_da_variavel} não configurada no .env" in str(exc_info.value)


def test_ingestao_e_busca_compartilham_a_mesma_fabrica_de_embeddings():
    """Restrição do enunciado: o MESMO modelo de embedding na ingestão e na busca.
    Com LLM_PROVIDER=gemini, ambos os módulos precisam chegar à classe Google
    com o mesmo nome de modelo — sem isso os vetores ficariam incompatíveis.
    """
    from src.ingest import criar_vector_store_para_ingestao
    from src.search import criar_vector_store_para_busca

    ambiente = {
        **AMBIENTE_GEMINI,
        "DATABASE_URL": "postgresql+psycopg://postgres:postgres@localhost:5432/rag",
        "PG_VECTOR_COLLECTION_NAME": "test_collection",
    }
    with patch.dict(os.environ, ambiente, clear=True), patch(
        "src.providers.GoogleGenerativeAIEmbeddings"
    ) as mock_embeddings_google, patch("src.ingest.PGVector"), patch(
        "src.search.PGVector"
    ):
        criar_vector_store_para_ingestao()
        criar_vector_store_para_busca()

    modelos_usados = [
        chamada.kwargs["model"] for chamada in mock_embeddings_google.call_args_list
    ]
    assert modelos_usados == [
        MODELO_EMBEDDING_GEMINI_ESPERADO,
        MODELO_EMBEDDING_GEMINI_ESPERADO,
    ]

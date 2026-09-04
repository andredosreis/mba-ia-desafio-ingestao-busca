"""Fábrica de provider de embeddings e LLM (OpenAI ou Gemini).

Centraliza a seleção do provider para garantir que a ingestão e a busca usem
SEMPRE o mesmo modelo de embedding — restrição obrigatória do enunciado.
A escolha é explícita, via a variável de ambiente `LLM_PROVIDER`.
"""

import os

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

PROVIDER_OPENAI = "openai"
PROVIDER_GEMINI = "gemini"
PROVIDERS_SUPORTADOS = (PROVIDER_OPENAI, PROVIDER_GEMINI)

# Modelos Gemini validados de ponta a ponta com a API atual. Nomes como
# `gemini-1.5-flash` ou `models/text-embedding-004` retornam 404 e fazem a
# biblioteca gastar ~60s em retries — não usar.
GEMINI_EMBEDDING_MODEL_PADRAO = "models/gemini-embedding-001"
GEMINI_CHAT_MODEL_PADRAO = "gemini-2.5-flash"

# Transporte HTTP/REST em vez do gRPC padrão. A biblioteca constrói um cliente
# gRPC assíncrono que o caminho síncrono nunca usa; esse canal é destruído na
# finalização do interpretador, quando o módulo gRPC já foi desmontado, e imprime
# um traceback cru no stderr ao fim de toda sessão que fez alguma pergunta.
TRANSPORTE_GEMINI = "rest"

# Valores de placeholder do `.env.example`: presentes, porém inválidos.
PLACEHOLDERS_DE_CHAVE = frozenset(
    {"sk-sua-chave-aqui", "AIza-sua-chave-aqui"}
)

VARIAVEL_DE_CHAVE_POR_PROVIDER = {
    PROVIDER_OPENAI: "OPENAI_API_KEY",
    PROVIDER_GEMINI: "GOOGLE_API_KEY",
}


def obter_provider() -> str:
    """Lê `LLM_PROVIDER` (openai|gemini); default 'openai'. ValueError se inválido."""
    provider = (os.getenv("LLM_PROVIDER") or PROVIDER_OPENAI).strip().lower()
    if provider not in PROVIDERS_SUPORTADOS:
        raise ValueError(
            f"Erro: LLM_PROVIDER='{provider}' inválido. "
            f"Use um destes: {', '.join(PROVIDERS_SUPORTADOS)}."
        )
    return provider


def validar_credencial_do_provider(provider: str) -> None:
    """Exige a chave do provider ativo (ausência ou placeholder → ValueError em PT)."""
    nome_da_variavel = VARIAVEL_DE_CHAVE_POR_PROVIDER[provider]
    chave = os.getenv(nome_da_variavel)
    if not chave or chave in PLACEHOLDERS_DE_CHAVE:
        raise ValueError(
            f"Erro: {nome_da_variavel} não configurada no .env "
            "(substitua o placeholder por uma chave real)."
        )


def _exigir_variavel(nome_da_variavel: str) -> str:
    """Retorna o valor da env obrigatória ou levanta ValueError em PT."""
    valor = os.getenv(nome_da_variavel)
    if not valor:
        raise ValueError(f"Erro: variável {nome_da_variavel} não definida no .env.")
    return valor


def criar_embeddings() -> Embeddings:
    """Instancia o modelo de embeddings do provider ativo."""
    provider = obter_provider()
    validar_credencial_do_provider(provider)

    if provider == PROVIDER_GEMINI:
        modelo = os.getenv("GOOGLE_EMBEDDING_MODEL") or GEMINI_EMBEDDING_MODEL_PADRAO
        return GoogleGenerativeAIEmbeddings(model=modelo, transport=TRANSPORTE_GEMINI)

    return OpenAIEmbeddings(model=_exigir_variavel("OPENAI_EMBEDDING_MODEL"))


def criar_chat_llm() -> BaseChatModel:
    """Instancia o LLM de resposta do provider ativo."""
    provider = obter_provider()
    validar_credencial_do_provider(provider)

    if provider == PROVIDER_GEMINI:
        modelo = os.getenv("GOOGLE_MODEL") or GEMINI_CHAT_MODEL_PADRAO
        return ChatGoogleGenerativeAI(model=modelo, transport=TRANSPORTE_GEMINI)

    return ChatOpenAI(model=_exigir_variavel("OPENAI_MODEL"))

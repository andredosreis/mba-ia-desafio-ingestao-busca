import sys
try:
    from search import search_prompt, verificar_colecao_populada
except ImportError:
    from src.search import search_prompt, verificar_colecao_populada

COMANDOS_SAIDA = {"sair", "exit", "quit"}


def processar_pergunta(chain, pergunta: str) -> str:
    """Invoca a chain RAG; se houver erro de API ou rede, retorna mensagem em PT sem derrubar o loop."""
    try:
        resultado = chain.invoke(pergunta)
        return str(resultado)
    except Exception:
        return "Erro ao consultar o modelo. Verifique sua conexão e a OPENAI_API_KEY."


def executar_loop_chat(chain) -> None:
    """Loop de chat: lê 'PERGUNTA: ', trata comandos de saída, imprime 'RESPOSTA: ...'."""
    print("Faça sua pergunta:")
    while True:
        try:
            pergunta = input("PERGUNTA: ").strip()
            if not pergunta:
                continue
            if pergunta.lower() in COMANDOS_SAIDA:
                print("Encerrando. Até logo!")
                break
            resposta = processar_pergunta(chain, pergunta)
            print(f"RESPOSTA: {resposta}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando. Até logo!")
            break


def main() -> None:
    """Valida ambiente (chain inicializada e coleção populada) e inicia o loop."""
    chain = search_prompt()

    if not chain:
        print("Não foi possível iniciar o chat. Verifique os erros de inicialização.")
        print("Passos: 1) docker compose up -d  2) configure o .env (OPENAI_API_KEY)  3) python src/ingest.py")
        return

    if not verificar_colecao_populada():
        print("A base está vazia. Execute primeiro: python src/ingest.py")
        return

    executar_loop_chat(chain)


if __name__ == "__main__":
    main()
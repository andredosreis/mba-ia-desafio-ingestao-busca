from unittest.mock import MagicMock
import pytest
import src.chat as chat_module


class DummyChain:
    def __init__(self, response="Resposta simulada"):
        self.response = response
        self.invoked_questions = []

    def invoke(self, question: str) -> str:
        self.invoked_questions.append(question)
        if question == "erro":
            raise RuntimeError("Erro de API simulado")
        return self.response


def test_processar_pergunta_sucesso():
    chain = DummyChain("Resposta OK")
    res = chat_module.processar_pergunta(chain, "Qual a regra?")
    assert res == "Resposta OK"
    assert chain.invoked_questions == ["Qual a regra?"]


def test_processar_pergunta_excecao():
    chain = DummyChain()
    res = chat_module.processar_pergunta(chain, "erro")
    assert "Erro ao consultar o modelo" in res


def test_loop_chat_multiplas_perguntas(capsys, monkeypatch):
    chain = DummyChain("Resultado RAG")
    inputs = iter(["  ", "Primeira pergunta?", "Segunda pergunta?", "sair"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    chat_module.executar_loop_chat(chain)

    captured = capsys.readouterr().out
    assert "Faça sua pergunta:" in captured
    assert "RESPOSTA: Resultado RAG" in captured
    assert "Encerrando. Até logo!" in captured
    assert chain.invoked_questions == ["Primeira pergunta?", "Segunda pergunta?"]


@pytest.mark.parametrize("comando", ["sair", "SAIR", "exit", "EXIT", "quit", "QUIT"])
def test_comandos_saida(capsys, monkeypatch, comando):
    chain = DummyChain()
    inputs = iter([comando])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    chat_module.executar_loop_chat(chain)

    captured = capsys.readouterr().out
    assert "Encerrando. Até logo!" in captured
    assert len(chain.invoked_questions) == 0


def test_encerramento_gracioso_keyboard_interrupt(capsys, monkeypatch):
    chain = DummyChain()

    def raise_interrupt(prompt=""):
        raise KeyboardInterrupt()

    monkeypatch.setattr("builtins.input", raise_interrupt)

    chat_module.executar_loop_chat(chain)

    captured = capsys.readouterr().out
    assert "Encerrando. Até logo!" in captured


def test_encerramento_gracioso_eof_error(capsys, monkeypatch):
    chain = DummyChain()

    def raise_eof(prompt=""):
        raise EOFError()

    monkeypatch.setattr("builtins.input", raise_eof)

    chat_module.executar_loop_chat(chain)

    captured = capsys.readouterr().out
    assert "Encerrando. Até logo!" in captured


def test_main_falha_inicializacao_search(capsys, monkeypatch):
    monkeypatch.setattr(chat_module, "search_prompt", lambda: None)
    mock_loop = MagicMock()
    monkeypatch.setattr(chat_module, "executar_loop_chat", mock_loop)

    chat_module.main()

    captured = capsys.readouterr().out
    assert "Não foi possível iniciar o chat" in captured
    mock_loop.assert_not_called()


def test_main_colecao_vazia(capsys, monkeypatch):
    chain = DummyChain()
    monkeypatch.setattr(chat_module, "search_prompt", lambda: chain)
    monkeypatch.setattr(chat_module, "verificar_colecao_populada", lambda: False)
    mock_loop = MagicMock()
    monkeypatch.setattr(chat_module, "executar_loop_chat", mock_loop)

    chat_module.main()

    captured = capsys.readouterr().out
    assert "A base está vazia. Execute primeiro: python src/ingest.py" in captured
    mock_loop.assert_not_called()


def test_main_sucesso(capsys, monkeypatch):
    chain = DummyChain()
    monkeypatch.setattr(chat_module, "search_prompt", lambda: chain)
    monkeypatch.setattr(chat_module, "verificar_colecao_populada", lambda: True)
    mock_loop = MagicMock()
    monkeypatch.setattr(chat_module, "executar_loop_chat", mock_loop)

    chat_module.main()

    mock_loop.assert_called_once_with(chain)

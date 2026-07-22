# Spec — F04 CLI de Chat

| Campo | Valor |
|---|---|
| Feature | F04 — CLI de Chat |
| Wave | 3 |
| Depende de | F02, F03 (spec escrita antecipadamente; revalidar interfaces antes de implementar) |
| Critérios de aceitação | CA-04.1, CA-04.2, CA-04.3, CA-04.4 |
| Entrega | `src/chat.py` + `tests/test_chat.py` |

> **Nota de dependência:** esta spec foi gerada antes da implementação de F02/F03,
> apoiada nos contratos já fixados pelo template (`search_prompt()` retorna chain
> com `.invoke(pergunta) -> str`, ou `None` em falha) e na função
> `verificar_colecao_populada()` definida na spec da F03. Antes de implementar,
> conferir que essas interfaces foram entregues como especificado.

## 1. Objetivo

Loop interativo de terminal no formato do enunciado: `Faça sua pergunta:`,
entrada `PERGUNTA:`, saída `RESPOSTA:`, encerramento gracioso e orientação clara
quando o ambiente não está pronto.

- **CA-04.1** — `python src/chat.py` exibe `Faça sua pergunta:` e aceita perguntas em loop.
- **CA-04.2** — saída no formato `PERGUNTA: ...` / `RESPOSTA: ...`.
- **CA-04.3** — `sair` (ou Ctrl+C/Ctrl+D) encerra graciosamente.
- **CA-04.4** — banco vazio ou `.env` incompleto → orientação em PT, sem stack trace.

## 2. Design técnico

Tudo em `src/chat.py` (mantém `from search import search_prompt` e o esqueleto do
stub: `chain = search_prompt()` + `if not chain`).

```python
COMANDOS_SAIDA = {"sair", "exit", "quit"}

def processar_pergunta(chain, pergunta: str) -> str:
    """Invoca a chain; erro de API/rede vira mensagem PT (loop não morre)."""

def executar_loop_chat(chain) -> None:
    """Loop: lê 'PERGUNTA: ', trata comandos de saída, imprime 'RESPOSTA: ...'."""

def main() -> None:
    """Valida ambiente (chain != None e coleção populada) e inicia o loop."""
```

### Fluxo do `main()`

1. `chain = search_prompt()` — se `None` (search já imprimiu a causa), imprime
   passos de correção e retorna:
   ```
   Não foi possível iniciar o chat. Verifique os erros de inicialização.
   Passos: 1) docker compose up -d  2) configure o .env (OPENAI_API_KEY)  3) python src/ingest.py
   ```
2. `verificar_colecao_populada()` — se `False`:
   `A base está vazia. Execute primeiro: python src/ingest.py` e retorna (CA-04.4).
3. Imprime `Faça sua pergunta:` e entra no loop.

### Loop (`executar_loop_chat`)

- `input("PERGUNTA: ")` → strip; vazio → continua.
- Comando em `COMANDOS_SAIDA` (case-insensitive) → `Encerrando. Até logo!` e sai.
- Caso normal → `print(f"RESPOSTA: {processar_pergunta(chain, pergunta)}\n")`.
- `KeyboardInterrupt`/`EOFError` no `input` → linha em branco + despedida, exit 0.

### `processar_pergunta`

- `chain.invoke(pergunta)` em try/except; exceção → retorna
  `Erro ao consultar o modelo. Verifique sua conexão e a OPENAI_API_KEY.`
  (o loop continua vivo; sem traceback).

## 3. Decisões e trade-offs

- **Verificação de base vazia na inicialização** (não a cada pergunta): custo zero
  de API, atende o CA-04.4 ("dado banco vazio, quando inicio o chat") literalmente.
- **Erro de invoke não derruba o loop**: falha transitória de rede não deve matar
  a sessão; usuário pode tentar de novo ou digitar `sair`.
- **`sair`/`exit`/`quit` case-insensitive**: o CA cita `sair`; sinônimos comuns são
  cortesia sem violar o enunciado.
- **Sem histórico/memória**: non-goal explícito do PRD.

## 4. Testes (unitários, sem rede)

`tests/test_chat.py` — chain falsa (objeto com `.invoke`) + `monkeypatch` de
`input`/`verificar_colecao_populada`:

1. Sequência `["pergunta", "sair"]` → imprime `RESPOSTA: ...` e a despedida.
2. `sair` imediato (e variantes `SAIR`, `exit`) → despedida, sem chamar a chain.
3. `EOFError`/`KeyboardInterrupt` no input → encerra gracioso, sem traceback.
4. `search_prompt` retornando `None` → mensagem de orientação, loop nunca inicia.
5. Coleção vazia → mensagem "Execute primeiro: python src/ingest.py", loop nunca inicia.
6. Chain que levanta exceção → `RESPOSTA:` com mensagem de erro PT e loop segue.

## 5. Fora do escopo

- Lógica de busca/prompt/LLM (F03). Ingestão (F02). README (F05).
- Histórico entre perguntas, streaming, cores/formatação além do enunciado.

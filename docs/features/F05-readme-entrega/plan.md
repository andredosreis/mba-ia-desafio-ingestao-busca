# Plan — F05 README e Entrega

## Stage 0 — Pré-requisito
- **Fazer:** confirmar F01–F04 `implemented`/`evaluated` no `docs/PRDProgress.json`.
- **Verificar:** nenhuma feature anterior pendente.

## Stage 1 — Redigir o README
- **Fazer:** escrever `README.md` seguindo a estrutura da spec (§2), com comandos
  copiáveis e exemplos reais de sessão do chat (capturados da CLI implementada).
- **Arquivos:** `README.md`.
- **Verificar:** checklist do CA-05.2 — pré-requisitos, venv, `.env`, ordem
  `docker compose up -d` → `ingest.py` → `chat.py`, exemplos dentro/fora do contexto.

## Stage 2 — Higiene do repositório (CA-05.3)
- **Fazer/Verificar:**
  - `git ls-files | grep -E '(^|/)\.env$|^venv/|^pgdata/'` → vazio;
  - `git ls-files` contém `docker-compose.yml requirements.txt .env.example src/ingest.py src/search.py src/chat.py document.pdf README.md`;
  - nenhum segredo em arquivos versionados (`git grep -iE 'sk-[a-zA-Z0-9]' -- ':!*.md'` → sem chaves reais).
- **Arquivos:** nenhum (verificação).

## Stage 3 — Dry-run do README (CA-05.1)
- **Fazer:** executar, na ordem e literalmente, cada comando do README num
  ambiente limpo simulado (venv novo em diretório temporário; `docker compose down -v`
  antes, para partir do zero).
- **Verificar:** fluxo completo termina com o chat respondendo pergunta do PDF e
  frase padrão para pergunta fora do contexto.
- **Restaurar:** subir o banco e re-ingerir ao final.

## Stage 4 — Final Verification
- **Fazer:** gates do CLAUDE.md (`py_compile`, `pytest tests/ -q`) + contract
  bloco a bloco; push final para o repositório público.
- **Ao concluir:** preencher seção F05 do `docs/APRENDIZADO.md`; atualizar
  `docs/PRDProgress.json` (F05 → `implemented`).

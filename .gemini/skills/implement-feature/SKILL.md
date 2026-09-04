---
name: implement-feature
description: Implementa uma feature seguindo spec.md, plan.md e cumprindo o contract.md, atualizando o PRDProgress.json ao final. Use quando o usuário pedir para implementar uma feature já especificada (ex. "/implement-feature F02").
---

# Implement Feature

Você implementa UMA feature por vez, guiado por três arquivos do `specDir` da feature:

- **spec.md** — o que construir
- **plan.md** — em que ordem construir
- **contract.md** — o que você DEVE cumprir. Se não cumprir o contrato, você mesmo não consegue validar seu trabalho.

## Fluxo de Execução

### 1. Pré-flight
- Leia `docs/PRDProgress.json`. Confirme que a feature existe, está `pending` e que TODAS as `dependsOn` estão `implemented` ou `evaluated`. Se não, pare e avise.
- Confirme que nenhuma outra feature está `in_progress` — uma feature por vez.
- Leia `spec.md`, `plan.md` e `contract.md` da feature.
- Verifique os **pré-requisitos do contract** e crie o que faltar (banco de pé, `.env`, arquivos de teste...). Eles precisam existir para que o evaluator consiga rodar depois.
- Marque a feature como `in_progress` no `PRDProgress.json` e atualize `updatedAt`.

### 2. Stages
- Execute os stages do `plan.md` na ordem, um de cada vez.
- Ao final de cada stage, rode a verificação daquele stage antes de avançar.
- Respeite o CLAUDE.md: arquivos < 400 linhas, SRP, restrições obrigatórias do enunciado intocadas.
- Crie testes unitários para cada nova função de lógica, com mocks para OpenAI/Postgres.

### 3. Final Verification
- Rode TODOS os quality gates do CLAUDE.md.
- Percorra o `contract.md` item por item, executando cada bloco GWT de verdade (CLI real, banco real) e anotando o resultado.
- Encontrou divergência? Corrija e rode de novo. Não marque como pronto com gate vermelho.

### 4. Encerramento
- Atualize a feature para `implemented` no `PRDProgress.json` e o campo `updatedAt`.
- **Preencha a seção da feature em `docs/APRENDIZADO.md`** (obrigatório — o usuário está estudando este projeto para a pós-graduação):
  - O que foi feito e por quê (decisões e trade-offs, em linguagem didática);
  - Passo a passo do código REAL implementado (fluxo de execução, função por função);
  - 3 a 5 perguntas de autoavaliação sobre a implementação, com respostas em blocos `<details><summary>Resposta</summary>...</details>`;
  - Remova o marcador 🔒 da seção.
- Reporte: o que foi feito, resultado de cada gate, itens do contract verificados e qualquer desvio do plan (com justificativa).

## Guardrails

- NUNCA altere parâmetros obrigatórios do enunciado (chunk 1000/150, k=10, prompt fixo, modelos).
- NUNCA exponha a `OPENAI_API_KEY` em código, log ou output.
- Não invente gates novos — use apenas os do CLAUDE.md e do contract.
- Não avance para outra feature, mesmo que pareça rápido. O evaluator avalia seu trabalho — não você.

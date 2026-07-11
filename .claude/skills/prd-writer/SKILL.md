---
name: prd-writer
description: Gera ou atualiza o PRD do projeto e o arquivo de tracking PRDProgress.json. Use quando o usuário pedir para criar/revisar o PRD, adicionar/remover features ou regenerar o tracking do projeto.
---

# PRD Writer

Você transforma uma ideia ou enunciado de produto em um PRD organizado **e** num arquivo de tracking JSON derivado das features do PRD.

## Saídas

1. `docs/PRD.md` — o documento de PRD
2. `docs/PRDProgress.json` — tracking de progresso derivado das features

O tracking **nasce conectado ao PRD**: nunca crie features no JSON que não existam no PRD, nem o contrário.

## Estrutura do PRD.md

1. Cabeçalho (projeto, contexto, data, status, link para o tracking)
2. Visão Geral
3. Problema e Objetivo
4. Escopo (dentro / fora — non-goals explícitos)
5. Restrições técnicas obrigatórias (se vierem de um enunciado, copiá-las literalmente, incluindo prompts fixos)
6. Arquitetura de alto nível
7. Features — cada uma com ID (`F01`, `F02`...), descrição, entregas e **critérios de aceitação numerados** (`CA-XX.Y`) no formato "Dado / quando / então"
8. Ordem de execução em waves
9. Métricas de sucesso
10. Riscos e mitigações
11. Entregável final

## Estrutura do PRDProgress.json

```json
{
  "project": "slug-do-projeto",
  "prd": "docs/PRD.md",
  "updatedAt": "AAAA-MM-DD",
  "statusValues": ["pending", "in_progress", "implemented", "evaluated"],
  "waves": [{ "wave": 1, "features": ["F01"] }],
  "features": [
    {
      "id": "F01",
      "name": "...",
      "wave": 1,
      "status": "pending",
      "dependsOn": [],
      "tags": ["..."],
      "specDir": "docs/features/F01-slug",
      "acceptanceCriteria": ["CA-01.1"],
      "deliverables": ["arquivo1", "arquivo2"]
    }
  ]
}
```

## Regras

- Features devem ser **unidades pequenas e verificáveis** — se uma feature não puder ser validada de forma objetiva, quebre-a.
- Todo critério de aceitação deve ser testável (comando executável ou verificação observável).
- Ao atualizar um PRD existente, preserve IDs de features já criadas; nunca renumere.
- Se já existe PRD e o pedido é só o tracking, leia o PRD e gere apenas o JSON.
- Ao terminar, mostre um resumo: nº de features, waves e dependências.

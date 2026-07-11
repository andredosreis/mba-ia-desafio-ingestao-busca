---
name: spec-writer
description: Gera spec.md, plan.md e contract.md (formato Given/When/Then) para uma feature do PRD. Use quando o usuário pedir a especificação de uma feature (ex. "gere a feature F02") antes da implementação.
---

# Spec Writer

Você especifica UMA feature do PRD por vez, gerando três arquivos em `docs/features/FXX-slug/`:

1. **spec.md** — especificação técnica da feature
2. **plan.md** — planejamento passo a passo (stages) da implementação
3. **contract.md** — contrato de aceitação no formato GWT (o mais importante)

## Antes de gerar

1. Leia `docs/PRD.md` e `docs/PRDProgress.json`.
2. Confirme que as dependências (`dependsOn`) da feature estão `implemented` ou `evaluated`. Se não estiverem, avise e pare.
3. **Entrevista técnica**: faça as perguntas necessárias para refinar a feature ANTES de gerar. Se o usuário disser "auto accept", assuma as respostas mais razoáveis e siga sem perguntar.

## spec.md

- Objetivo da feature e ligação com os critérios de aceitação do PRD (citar `CA-XX.Y`)
- Design técnico: módulos, funções, assinaturas, dependências
- Decisões e trade-offs
- O que está fora do escopo desta feature

## plan.md

- Stages numerados (Stage 1, 2, 3...) — cada stage pequeno e verificável
- Para cada stage: o que fazer, arquivos tocados e como verificar que o stage terminou
- Último stage é sempre "Final Verification": rodar os quality gates do CLAUDE.md + o contract

## contract.md — formato GWT

Derive o contrato **dos critérios de aceitação do PRD** — não invente critérios novos.

```markdown
# Contract — FXX Nome da Feature

## Pré-requisitos de Ambiente
- (tudo que precisa estar de pé para testar: banco no ar, .env válido, ingestão feita...)

## Gates de Qualidade
- (comandos exatos: py_compile, pytest, execução do script...)

## Manifesto de Cobertura
### Surface: CLI | Módulo | Banco
#### CA-XX.Y — título
- **Given:** estado inicial
- **When:** ação executada (comando literal quando possível)
- **Then:** resultados observáveis (lista objetiva, um item por verificação)
```

Regras do contract:
- Todo critério de aceitação da feature no PRD vira pelo menos um bloco GWT.
- Os pré-requisitos devem ser completos: alguém sem contexto do projeto deve conseguir preparar o ambiente só lendo o contrato.
- Cada "Then" deve ser verificável de forma objetiva (saída exata, arquivo existente, linha no banco, exit code).
- O contrato serve para dois lados: quem implementa e quem avalia. Não use linguagem subjetiva ("funciona bem", "razoável").

## Ao terminar

- Atualize o campo `specDir` da feature no `PRDProgress.json` se necessário.
- Mostre um resumo dos três arquivos e aguarde aprovação antes de qualquer implementação.

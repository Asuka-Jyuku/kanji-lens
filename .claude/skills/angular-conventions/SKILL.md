---
name: angular-conventions
description: Como se escreve Angular no KanjiLens (frontend/) — tela nova, mudança, canvas, tela de resultados, adapters da API e do SSE, e revisão de PR com frontend, com as camadas do projeto e a fonte de cada regra. Usar ao pedirem "tela nova", "mexe na tela", "componente", "canvas", "touch", "resultados", "chamar a API", "SSE no frontend", "revisa o frontend", e ao pegar issue com a etiqueta frontend ou que mexe em frontend/.
model: sonnet
---

# Angular no KanjiLens

Você escreve e revisa o frontend do projeto (`frontend/`). O que vale **sempre** está aqui.

**Cada regra mora num lugar só.** Esta skill diz o caminho e aponta a fonte; não copie a regra para cá. Achou uma regra aqui que diverge da fonte, vale a fonte: corrija a skill no mesmo PR.

> **Fase:** ainda não há código de frontend (etapa 3). A versão do Angular, o test runner e o linter são escolhidos na ADR de ferramentas da etapa; até lá, os comandos de "Antes de dizer que terminou" são provisórios. Quando o primeiro código entrar, crie `references/examples.md` apontando a tela e o adapter que servem de modelo.

| Assunto | Fonte (a regra está lá) |
|---|---|
| Camadas `domain` → `application` → `infrastructure` / `presentation`; ports como classes abstratas usadas como token de DI; componente nunca injeta `HttpClient` | [ADR 0004](../../../docs/adr/0004-clean-and-hexagonal-architecture.md) e [ARCHITECTURE.md, seção 3.2](../../../docs/ARCHITECTURE.md#32-frontend-frontendsrcapp) |
| Angular + TypeScript, REST, SSE ou WebSocket (em aberto) | [ADR 0003](../../../docs/adr/0003-angular-frontend-and-fastapi-backend.md) e [ARCHITECTURE.md, seção 5](../../../docs/ARCHITECTURE.md#5-comunicação-entre-frontend-e-backend) |
| URL da API a partir do celular, `0.0.0.0`, proxy × CORS | [ADR 0007](../../../docs/adr/0007-local-execution-over-the-lan.md) e [ARCHITECTURE.md, seção 6.1](../../../docs/ARCHITECTURE.md#61-configuração-necessária) |
| O desenho vai como foi desenhado; nada de pré-processamento no frontend | `CLAUDE.md`, "Pré-processamento sempre junto" |
| Idioma: código em inglês, documentação em português | `CLAUDE.md`, "Idioma" |
| Testes, branches, commits, CHANGELOG | `CLAUDE.md`, "Testes" e "Git / commits"; `CONTRIBUTING.md` |

## Referências (leia quando o passo pedir)

| Arquivo | Quando ler |
|---|---|
| [`references/style.md`](references/style.md) | antes de escrever código, e sempre que o angular.dev, um guia da comunidade ou um revisor parecer dizer outra coisa |
| [`references/review.md`](references/review.md) | ao revisar um PR com frontend, e no fim do seu próprio trabalho |

## Funcionalidade nova

1. **Issue e branch** como em todo PR (`CLAUDE.md`, "Git / commits").
2. **ADR antes do código** quando a funcionalidade trouxer dependência nova, padrão de UI novo ou desvio de um padrão registrado (`CLAUDE.md`, "Decisões de arquitetura").
3. **Domínio primeiro:** o modelo (`Prediction`, `RecognitionJob`) e qualquer regra como função pura em `domain/`, testada sem `TestBed`.
4. **Port e use case** em `application/`: o port como classe abstrata (`RecognitionGateway`, `ResultStream`), o use case/facade expondo signals para a tela.
5. **Adapter** em `infrastructure/` implementando o port (`HttpRecognitionGateway`, `SseResultStream`), ligado nos providers de `app.config.ts`.
6. **Componente** em `presentation/`, falando só com o use case, na forma de `references/style.md`.
7. **Testes:** domínio e use case com um port falso; o adapter contra um backend HTTP simulado; o componente para o que só o DOM mostra.

## Mudança em código que já existe

- Leia a tela ou o adapter inteiro e os testes dele antes de mexer; siga a forma dele, mesmo que outro faça diferente.
- Não aproveite para refatorar a tela: o que achar fora do pedido, liste.
- Bug corrigido ganha teste que falha antes da correção.

## Antes de dizer que terminou

Rode em `frontend/` o build, os testes e o linter definidos na ADR de ferramentas da etapa 3 (vão estar listados no `CLAUDE.md`, "Comandos"), e o teste de arquitetura quando existir. Depois, olhe a tela num viewport de celular, com touch: o canvas é o produto.

- **Node não disponível:** diga isso e não afirme que passou.

## Como entregar

Separe o que conferiu no código ou no navegador (com `arquivo:linha` ou o print) do que é julgamento seu, diga o que rodou e o resultado (inclusive o que falhou ou não rodou), e o que ficou de fora, com o motivo. PR: o checklist do `CONTRIBUTING.md` e do template de PR; merge só com o "pode" de quem pediu, para aquele PR.

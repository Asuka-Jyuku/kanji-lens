---
name: angular-conventions
description: Como se escreve Angular no KanjiLens (frontend/) — tela nova, mudança, canvas, tela de resultados, adapters da API e do SSE, avaliação de UI/UX e revisão de PR com frontend, com as camadas do projeto e a fonte de cada regra. Usar ao pedirem "tela nova", "mexe na tela", "componente", "canvas", "touch", "resultados", "chamar a API", "SSE no frontend", "UX", "acessibilidade", "avalia a tela", "revisa o frontend", e ao pegar issue com a etiqueta frontend ou que mexe em frontend/.
model: sonnet
---

# Angular no KanjiLens

Você escreve e revisa o frontend do projeto (`frontend/`). O que vale **sempre** está aqui.

**Cada regra mora num lugar só.** Esta skill diz o caminho e aponta a fonte; não copie a regra para cá. Achou uma regra aqui que diverge da fonte, vale a fonte: corrija a skill no mesmo PR.

> **Fase:** a estrutura de `frontend/` existe, com as ferramentas da [ADR 0017](../../../docs/adr/0017-frontend-tooling-angular-localize-vitest-eslint-boundaries.md): Angular 22 (zoneless, standalone), `@angular/localize` com `pt-BR` de origem, Vitest, ESLint com `eslint-plugin-boundaries` e Prettier. A área de desenho existe (#56): o domínio `Drawing`, o `DrawingSession` (signals) e o componente `DrawingPad`. A escolha do modo também (#57): `StrokeOrderMode`, `StrokeOrderModeSelection` e o componente `ModeSelector`. A exportação do desenho (#66), só no build de desenvolvimento, trouxe o primeiro port com adapter (`FileDownload` e `BrowserFileDownload`) e o lugar das ferramentas de desenvolvimento (`app.dev-tools.ts`; [ARCHITECTURE.md, 3.2](../../../docs/ARCHITECTURE.md#32-frontend-frontendsrcapp)). Os modelos a seguir estão em [`references/examples.md`](references/examples.md); os adapters HTTP e SSE entram na #58.

| Assunto | Fonte (a regra está lá) |
|---|---|
| UI/UX: as referências obrigatórias (Nielsen, NN/g, WCAG 2.2, WAI-ARIA, Shneiderman) e os padrões propostos | [`docs/UI-UX.md`](../../../docs/UI-UX.md): leia antes de propor, avaliar ou desenhar |
| Camadas `domain` → `application` → `infrastructure` / `presentation`; ports como classes abstratas usadas como token de DI; componente nunca injeta `HttpClient` | [ADR 0004](../../../docs/adr/0004-clean-and-hexagonal-architecture.md) e [ARCHITECTURE.md, seção 3.2](../../../docs/ARCHITECTURE.md#32-frontend-frontendsrcapp) |
| Angular + TypeScript, REST; o resultado por SSE (`EventSource` no `SseResultStream`, estado completo por evento), com polling de `GET /api/recognitions/{id}` como reserva | [ADR 0003](../../../docs/adr/0003-angular-frontend-and-fastapi-backend.md), [ADR 0020](../../../docs/adr/0020-result-notification-by-server-sent-events.md) e [ARCHITECTURE.md, seção 5](../../../docs/ARCHITECTURE.md#5-comunicação-entre-frontend-e-backend) |
| URL da API a partir do celular, `0.0.0.0`, proxy × CORS | [ADR 0007](../../../docs/adr/0007-local-execution-over-the-lan.md) e [ARCHITECTURE.md, seção 6.1](../../../docs/ARCHITECTURE.md#61-configuração-necessária) |
| O desenho vai como foi desenhado; nada de pré-processamento no frontend | `CLAUDE.md`, "Pré-processamento sempre junto" |
| Idioma: código em inglês, documentação em português | `CLAUDE.md`, "Idioma" |
| Textos da tela em português pelo i18n (japonês depois), `lang="ja"` nos kanjis, erro da API por código | [ADR 0009](../../../docs/adr/0009-portuguese-ui-first-then-japanese.md) e `references/style.md`, "Idioma da interface" |
| Testes, branches, commits, CHANGELOG | `CLAUDE.md`, "Testes" e "Git / commits"; `CONTRIBUTING.md` |

## Referências (leia quando o passo pedir)

| Arquivo | Quando ler |
|---|---|
| [`references/style.md`](references/style.md) | antes de escrever código, e sempre que o angular.dev, um guia da comunidade ou um revisor parecer dizer outra coisa |
| [`references/examples.md`](references/examples.md) | antes de escrever um tipo de domínio, um estado em signals ou um componente: o código que já serve de modelo |
| [`references/review.md`](references/review.md) | ao avaliar uma tela (UI/UX), ao revisar um PR com frontend, e no fim do seu próprio trabalho |

## Funcionalidade nova

1. **Issue e branch** como em todo PR (`CLAUDE.md`, "Git / commits").
2. **ADR antes do código** quando a funcionalidade trouxer dependência nova, padrão de UI novo ou desvio de um padrão registrado (`CLAUDE.md`, "Decisões de arquitetura").
3. **Domínio primeiro:** o modelo (`Drawing`, `StrokeOrderMode`, `Prediction`, `StrokeOrderEvaluation`, `RecognitionJob`) e qualquer regra como função pura em `domain/`, testada sem `TestBed`.
4. **Port e use case** em `application/`: o port como classe abstrata (`RecognitionGateway`, `ResultStream`), o use case/facade expondo signals para a tela.
5. **Adapter** em `infrastructure/` implementando o port (`HttpRecognitionGateway`, `SseResultStream`), ligado nos providers de `app.config.ts`.
6. **Componente** em `presentation/`, falando só com o use case, na forma de `references/style.md`.
7. **UI/UX:** cada decisão de desenho cita o princípio de `docs/UI-UX.md` que a sustenta, separando o que vem da fonte do que é julgamento seu; padrão novo de UI entra na lista de padrões de lá no mesmo PR.
8. **Testes:** domínio e use case com um port falso; o adapter contra um backend HTTP simulado; o componente para o que só o DOM mostra.

## Mudança em código que já existe

- Leia a tela ou o adapter inteiro e os testes dele antes de mexer; siga a forma dele, mesmo que outro faça diferente.
- Não aproveite para refatorar a tela: o que achar fora do pedido, liste.
- Bug corrigido ganha teste que falha antes da correção.

## Antes de dizer que terminou

**Documentos em dia:** atualize no mesmo PR o que a mudança afetou (`CLAUDE.md`, "Documentos nascem com o assunto").

Rode em `frontend/` os comandos do `CLAUDE.md`, "Comandos": `npm run lint` (que já roda o teste de arquitetura e a regra de i18n), `npm run test:ci`, `npm run build` e `npm run format:check`. Texto novo na tela? `npm run extract-i18n` tem de achá-lo. Depois, olhe a tela num viewport de celular, com touch: o canvas é o produto.

- **Node não disponível:** diga isso e não afirme que passou.

## Como entregar

Separe o que conferiu no código ou no navegador (com `arquivo:linha` ou o print) do que é julgamento seu, cite o princípio de UI/UX de cada decisão de desenho, diga o que rodou e o resultado (inclusive o que falhou ou não rodou), e o que ficou de fora, com o motivo. PR: o checklist do `CONTRIBUTING.md` e do template de PR; merge só com o "pode" de quem pediu, para aquele PR.

# Estilo do Angular no projeto

As regras de camada estão na ADR 0004 e não se repetem aqui.

## O que seguimos

| Ponto | Como fica aqui | Fonte |
|---|---|---|
| Componentes | Standalone, pequenos, uma responsabilidade; nomes do guia de 2025 (`canvas.ts`, classe `Canvas`, sem `.component`) | [Angular style guide](https://angular.dev/style-guide), ADR 0017 |
| Injeção | `inject()` nos campos. Port como classe abstrata só quando há duas implementações reais; senão, a classe concreta (`providedIn: 'root'`), trocada no teste por `useValue` | [Angular DI](https://angular.dev/guide/di), ADR 0004 |
| Estado | Signals (`signal`, `computed`) no serviço; o componente só lê. RxJS só dentro do adapter | [Angular signals](https://angular.dev/guide/signals) |
| Change detection | `OnPush` e zoneless | [Angular](https://angular.dev/best-practices/skipping-subtrees) |
| Templates | `@if`, `@for` com `track`, `@switch` | [Control flow](https://angular.dev/guide/templates/control-flow) |
| Limpeza | `DestroyRef` para assinaturas e `EventSource.close()` | [DestroyRef](https://angular.dev/api/core/DestroyRef) |
| Nomes | Em inglês, um arquivo por classe: `xxx.use-case.ts`, `xxx.gateway.ts` (port), `http-xxx.gateway.ts` (adapter) | ADR 0004 |

## Canvas e touch (o produto)

| Ponto | Por quê | Fonte |
|---|---|---|
| **Pointer Events**, não handlers de mouse e touch separados | um caminho só para mouse, dedo e caneta | [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events) |
| `touch-action: none` no canvas | senão desenhar rola ou dá zoom | [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action) |
| Bitmap do canvas × `devicePixelRatio` | senão o traço borra em tela de alta densidade | [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio) |
| `setPointerCapture` no `pointerdown` | o traço continua se o dedo sair do canvas | [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Element/setPointerCapture) |
| O desenho vai como **lista de traços** `[x, y, t]` (px CSS, ms desde o primeiro ponto), com o tamanho do canvas e o modo; `getCoalescedEvents()` quando existir; nada de PNG nem de normalização | a avaliação da ordem precisa da ordem e da direção; pré-processamento mora só no `kanjilens_ml` | [ADR 0012](../../../../docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md), [ADR 0016](../../../../docs/adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md) |
| Modo sempre à vista antes de desenhar, padrão "não importa" | o modo muda o resultado | ADR 0012; Nielsen 1 |
| `<button>` de verdade e estado anunciado (`role="status"`) | leitor de tela e teclado | [WAI-ARIA](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions) |

## Idioma da interface (ADR 0009)

- **Textos:** todos pelo `@angular/localize`, em português: `i18n="@@id"` no template e `$localize` no código. O lint falha com texto sem marcação.
- **Kanji na tela:** sempre com `lang="ja"` ([WCAG 3.1.2](https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts)).
- **Fonte japonesa:** a do sistema ou empacotada no build, nunca de CDN.
- **Erros da API:** a tela traduz o código (`queue_full`); a mensagem do backend nunca aparece.

## O que evitamos

- `HttpClient` ou `EventSource` fora de `infrastructure/`.
- Regra de negócio em template ou componente: vai para `domain/`.
- `localhost` fixo na URL da API: no celular, `localhost` é o celular.
- Port, use case ou camada nova "para o futuro".

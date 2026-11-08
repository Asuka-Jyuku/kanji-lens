# Estilo do Angular no projeto

O que se espera de Angular idiomático aqui, com a fonte de cada ponto. As regras de camada estão na ADR 0004 e não se repetem aqui.

## O que seguimos

| Ponto | Como fica aqui | Fonte |
|---|---|---|
| Componentes | Standalone, pequenos, uma responsabilidade; siga os padrões da versão do CLI escolhida na ADR de ferramentas, não brigue com eles | [Angular style guide](https://angular.dev/style-guide) |
| Injeção de dependência | `inject()` na inicialização dos campos; ports como classes abstratas usadas como token de DI, ligados com `{ provide: RecognitionGateway, useClass: HttpRecognitionGateway }` | [Angular DI](https://angular.dev/guide/di), ADR 0004 |
| Estado | Signals (`signal`, `computed`) no use case/facade; o componente só lê. RxJS só na borda do adapter (HTTP, `EventSource`), convertido em signal antes de chegar à tela | [Angular signals](https://angular.dev/guide/signals) |
| Change detection | `OnPush` (ou o padrão do CLI, se já for OnPush/zoneless); estado por signals, para a tela atualizar sem truque de zone | [Angular: change detection](https://angular.dev/best-practices/skipping-subtrees) |
| Templates | Control flow embutido (`@if`, `@for` com `track`) | [Angular control flow](https://angular.dev/guide/templates/control-flow) |
| Ciclo de vida e limpeza | `DestroyRef` / `takeUntilDestroyed` para assinaturas e `EventSource.close()` | [Angular: DestroyRef](https://angular.dev/api/core/DestroyRef) |
| Nomes | Em inglês; um arquivo por classe; `xxx.use-case.ts`, `xxx.gateway.ts` (port), `http-xxx.gateway.ts` (adapter), `xxx.component.ts` | ADR 0004, [Angular style guide](https://angular.dev/style-guide) |

## Canvas e touch (o produto)

| Ponto | Por quê | Fonte |
|---|---|---|
| **Pointer Events** (`pointerdown/move/up`), não handlers separados de mouse e touch | um caminho só para mouse, touch e caneta | [MDN: Pointer events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events) |
| `touch-action: none` no canvas | sem isso, desenhar no celular rola ou dá zoom na página | [MDN: touch-action](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action) |
| Tamanho interno do canvas × `devicePixelRatio` | senão o traço fica borrado em celular de alta densidade | [MDN: devicePixelRatio](https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio) |
| `setPointerCapture` no `pointerdown` | o traço continua se o dedo sair do canvas | [MDN: setPointerCapture](https://developer.mozilla.org/en-US/docs/Web/API/Element/setPointerCapture) |
| Guardar e enviar o desenho como **lista de traços** (cada traço, os pontos `[x, y, t]` na ordem do pointer: pixels CSS a partir do canto do canvas e milissegundos desde o primeiro ponto), junto com o tamanho do canvas e o `stroke_order_mode`; `getCoalescedEvents()` quando existir; nada de PNG nem de normalização | a avaliação da ordem do modo `ordered` precisa da ordem e da direção, que uma imagem perde; rasterizar, recortar, redimensionar e normalizar são pré-processamento de ML e moram só no `kanjilens_ml` | [ADR 0012](../../../../docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md) e [ADR 0016](../../../../docs/adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md); `CLAUDE.md`, "Pré-processamento sempre junto" |
| Seletor de modo (ordem importa / não importa) visível antes de reconhecer, com o modo atual sempre à vista | o modo muda o resultado; o padrão é "não importa" (ADR 0012) | ADR 0012; Nielsen 1 (visibilidade do estado) |
| Botões e estado acessíveis | "Reconhecer" e "Limpar" são `<button>` de verdade; o estado de processamento e os resultados são anunciados (`aria-live`) | [WAI-ARIA: live regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions) |

## Idioma da interface (ADR 0009)

| Ponto | Como fica aqui | Fonte |
|---|---|---|
| Textos | Todos pelo mecanismo de i18n escolhido na ADR de ferramentas da etapa 3, em português; nenhum texto direto no template ou no código, nem com um idioma só | ADR 0009 |
| Kanji na tela | `lang="ja"` em todo candidato e kanji mostrado, em qualquer idioma da interface | [WCAG 3.1.2](https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts), [W3C i18n](https://www.w3.org/International/questions/qa-lang-why) |
| Fonte japonesa | Do sistema (`"Hiragino Sans"`, `"Yu Gothic"`, `"Noto Sans JP"`, `sans-serif`) ou empacotada no build; nunca de CDN | ADRs 0007 e 0009 |
| Erros da API | O adapter recebe o código (`queue_full`) e a tela mostra o texto traduzido; a mensagem do backend nunca aparece para o usuário | ADR 0009 |

## O que evitamos

- `HttpClient` ou `EventSource` num componente ou num use case: só em `infrastructure/`.
- Regra de negócio em template ou componente: vai para `domain/`, como função pura.
- URL da API com `localhost` fixo: no celular, `localhost` é o celular (ADR 0007).

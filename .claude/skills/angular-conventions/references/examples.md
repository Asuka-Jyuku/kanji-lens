# Código que serve de modelo

Antes de escrever, abra o exemplo do mesmo tipo e siga a forma dele. Exemplo novo entra aqui no PR que cria o primeiro código daquele tipo.

| Tipo | Modelo | O que copiar |
|---|---|---|
| Domínio puro | `frontend/src/app/domain/drawing.ts` | `interface` e `type` com `readonly`, funções puras que devolvem um valor novo, limites como constante (os mesmos da API), o motivo de recusar como código (`DrawingLimit`) que a tela traduz |
| Teste do domínio | `frontend/src/app/domain/drawing.spec.ts` | sem `TestBed`; um teste por regra; um ajudante (`draw`) que repete o que o usuário faz |
| Estado em signals (application) | `frontend/src/app/application/drawing-session.ts` (`DrawingSession`) | `@Injectable({ providedIn: 'root' })`, `signal` privado e `computed`/`asReadonly` públicos, métodos que só chamam o domínio; só `@angular/core` |
| Componente com canvas | `frontend/src/app/presentation/drawing-pad/drawing-pad.ts` (`DrawingPad`) | `OnPush`, `inject()`, `viewChild.required`, `afterNextRender` para medir e `afterRenderEffect` para desenhar; Pointer Events com um ponteiro por vez, `setPointerCapture` e `getCoalescedEvents` protegidos por `?.`; nenhuma regra no componente |
| Texto e estado na tela | `frontend/src/app/presentation/drawing-pad/drawing-pad.html` | `i18n="@@id"` em todo texto, `i18n-aria-label` no nome acessível, `@switch` sobre o código do domínio, mensagem em `role="status"` |
| Teste de componente | `frontend/src/app/presentation/drawing-pad/drawing-pad.spec.ts` | `TestBed` com `whenStable()`; o jsdom não tem layout nem canvas 2D, então `getBoundingClientRect` e `getContext` são substituídos e o teste confere a captura, não o desenho na tela |
| Adapter HTTP e SSE, use case com port | *a criar* (#58) | — |

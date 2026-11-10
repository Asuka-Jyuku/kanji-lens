# Código que serve de modelo

Antes de escrever, abra o exemplo do mesmo tipo e siga a forma dele. Exemplo novo entra aqui no PR que cria o primeiro código daquele tipo.

| Tipo | Modelo | O que copiar |
|---|---|---|
| Domínio puro | `frontend/src/app/domain/drawing.ts` | `interface` e `type` com `readonly`, funções puras que devolvem um valor novo, limites como constante (os mesmos da API), o motivo de recusar como código (`DrawingLimit`) que a tela traduz |
| Teste do domínio | `frontend/src/app/domain/drawing.spec.ts` | sem `TestBed`; um teste por regra; um ajudante (`draw`) que repete o que o usuário faz |
| Estado em signals (application) | `frontend/src/app/application/drawing-session.ts` (`DrawingSession`) | `@Injectable({ providedIn: 'root' })`, `signal` privado e `computed`/`asReadonly` públicos, métodos que só chamam o domínio; só `@angular/core` |
| Componente com canvas | `frontend/src/app/presentation/drawing-pad/drawing-pad.ts` (`DrawingPad`) | `OnPush`, `inject()`, `viewChild.required`, `afterNextRender` para medir e `afterRenderEffect` para desenhar; Pointer Events com um ponteiro por vez, `setPointerCapture` e `getCoalescedEvents` protegidos por `?.`; nenhuma regra no componente |
| Grupo de opções (formulário nativo) | `frontend/src/app/presentation/mode-selector/` (`ModeSelector`) | `<fieldset>` com `<legend>` e `<input type="radio">` nativos com o mesmo `name` (o teclado vem do navegador), o `<label>` inteiro como alvo de toque de 3rem, o estado lido de um signal e o valor conferido por uma função do domínio (`isStrokeOrderMode`) antes de chegar ao use case; destaque da opção marcada e do foco com `:has()` |
| Texto e estado na tela | `frontend/src/app/presentation/drawing-pad/drawing-pad.html` | `i18n="@@id"` em todo texto, `i18n-aria-label` no nome acessível, `@switch` sobre o código do domínio, mensagem em `role="status"` |
| Teste de componente | `frontend/src/app/presentation/drawing-pad/drawing-pad.spec.ts` | `TestBed` com `whenStable()`; o jsdom não tem layout nem canvas 2D, então `getBoundingClientRect` e `getContext` são substituídos e o teste confere a captura, não o desenho na tela |
| Port, use case e adapter | `application/file-download.ts` (`FileDownload`), `application/export-drawing.use-case.ts` (`ExportDrawing`) e `infrastructure/browser-file-download.ts` (`BrowserFileDownload`) | o port como `abstract class`; o use case com `inject()` dos estados e do port, montando o valor com funções do domínio; o adapter com `@Injectable()`, `extends` do port e a API do navegador só nele (`DOCUMENT`, `Blob`); a ligação port → adapter num array de providers do shell |
| Teste de use case e de adapter | `application/export-drawing.use-case.spec.ts` e `infrastructure/browser-file-download.spec.ts` | o use case com um port falso (`class FakeFileDownload extends FileDownload`) em `providers`; o adapter com a API do navegador substituída e restaurada no `afterEach` |
| Ferramenta só de desenvolvimento | `src/app/app.dev-tools.ts` e `app.dev-tools.development.ts` | o componente e os providers listados no arquivo de desenvolvimento, que o `fileReplacements` do `angular.json` só põe no build de desenvolvimento; o `App` os mostra com `NgComponentOutlet`; o CI confere o bundle de produção (`npm run check:production-bundle`) |
| Adapter HTTP e SSE | *a criar* (#58) | — |

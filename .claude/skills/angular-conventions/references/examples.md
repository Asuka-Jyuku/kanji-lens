# Código que serve de modelo

Antes de escrever, abra o exemplo do mesmo tipo e siga a forma dele. Os caminhos são de `frontend/src/app/`.

| Tipo | Modelo | O que copiar |
|---|---|---|
| Domínio puro | `domain/drawing.ts` | `interface` e `type` com `readonly`; funções puras que devolvem um valor novo; limites como constante (os mesmos da API); o motivo de recusar como código (`DrawingLimit`) |
| Teste do domínio | `domain/drawing.spec.ts` | sem `TestBed`; um teste por regra; um ajudante (`draw`) que imita o usuário |
| Estado em signals | `application/drawing-session.ts` (`DrawingSession`, com o desenho e o `mode`) | `providedIn: 'root'`; `signal` privado e `computed`/`asReadonly` públicos; métodos que só chamam o domínio (`chooseMode()`, `undo()`) |
| Use case que junta peças | `application/recognize-drawing.use-case.ts` (`RecognizeDrawing`) | `inject()` do estado e dos ports; estado do tipo do domínio num `signal`; `computed` para o que a tela decide (`canRecognize`); limpeza no `DestroyRef` |
| Teste de use case | `application/recognize-drawing.use-case.spec.ts` | fakes escritos à mão; `vi.useFakeTimers()` para o tempo; um teste por transição e por erro |
| Port (classe abstrata) | `application/recognition.gateway.ts` | a classe é o token de DI; só tipos do domínio; `Promise` para pedido e resposta; erro como código do domínio |
| Adapter HTTP | `infrastructure/http-recognition.gateway.ts` | `HttpClient` + `firstValueFrom`, URL relativa `/api`, `HttpErrorResponse` virando código do domínio; o JSON lido por uma função que recusa o que não reconhece (`recognition-api.ts`) |
| Adapter SSE | `infrastructure/sse-result-stream.ts` | `EventSource` nativo, fecha no estado final e no `close()` |
| Teste de adapter | `http-recognition.gateway.spec.ts`, `sse-result-stream.spec.ts` | `HttpTestingController`; um `EventSource` falso com `vi.stubGlobal` |
| Componente com canvas | `presentation/drawing-pad/drawing-pad.ts` | `OnPush`, `viewChild.required`, `afterNextRender` para medir, `afterRenderEffect` para desenhar; Pointer Events com um ponteiro por vez; nenhuma regra no componente |
| Grupo de opções | `presentation/mode-selector/` | `<fieldset>` com `<legend>` e rádios nativos; o `<label>` inteiro como alvo de 3rem; o valor conferido no domínio antes de chegar ao estado |
| Texto e estado na tela | `presentation/drawing-pad/drawing-pad.html` | `i18n="@@id"` em todo texto, `i18n-aria-label`, `@switch` sobre o código do domínio, `role="status"` |
| Teste de componente | `presentation/drawing-pad/drawing-pad.spec.ts` | `TestBed` com `whenStable()`; `getBoundingClientRect` e `getContext` substituídos, porque o jsdom não tem layout nem canvas |
| Ferramenta só de desenvolvimento | `presentation/drawing-export/` e `app.dev-tools*.ts` | tudo numa pasta, sem port nem use case: o componente monta o arquivo (`drawing-sample.ts`) e baixa direto; o `fileReplacements` do `angular.json` põe o `DEV_TOOL` só no build de desenvolvimento, e o CI confere o bundle de produção |

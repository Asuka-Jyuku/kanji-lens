---
name: angular-conventions
description: Como se escreve Angular no KanjiLens (frontend/) — tela nova, mudança, canvas, tela de resultados, adapters da API e do SSE, avaliação de UI/UX e revisão de PR com frontend, com as camadas do projeto e a fonte de cada regra. Usar ao pedirem "tela nova", "mexe na tela", "componente", "canvas", "touch", "resultados", "chamar a API", "SSE no frontend", "UX", "acessibilidade", "avalia a tela", "revisa o frontend", e ao pegar issue com a etiqueta frontend ou que mexe em frontend/.
model: sonnet
---

# Angular no KanjiLens

Para escrever e revisar o `frontend/`. Cada regra mora num lugar só: aqui fica o caminho e a fonte. Se a skill divergir da fonte, vale a fonte, e a skill se corrige no mesmo PR.

| Assunto | Fonte |
|---|---|
| UI/UX: referências e padrões da tela | [`docs/UI-UX.md`](../../../docs/UI-UX.md) (leia antes de desenhar ou avaliar) |
| Camadas, ports como classes abstratas, componente sem `HttpClient` | [ADR 0004](../../../docs/adr/0004-clean-and-hexagonal-architecture.md) e [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md) |
| Resultado por SSE, com polling de reserva | [ADR 0020](../../../docs/adr/0020-result-notification-by-server-sent-events.md) |
| API pelo proxy de `/api`, celular na rede local | [ADR 0007](../../../docs/adr/0007-local-execution-over-the-lan.md) e [`docs/RUNNING.md`](../../../docs/RUNNING.md) |
| O desenho vai como foi desenhado | `CLAUDE.md`, "Arquitetura" |
| Textos pelo i18n, `lang="ja"` nos kanjis, erro da API por código | [ADR 0009](../../../docs/adr/0009-portuguese-ui-first-then-japanese.md) e `references/style.md` |
| Testes, commits, CHANGELOG | `CLAUDE.md` e `CONTRIBUTING.md` |

## Referências

| Arquivo | Quando ler |
|---|---|
| [`references/style.md`](references/style.md) | antes de escrever código |
| [`references/examples.md`](references/examples.md) | antes de escrever um tipo novo: o código que serve de modelo |
| [`references/review.md`](references/review.md) | ao avaliar uma tela, revisar um PR e no fim do seu trabalho |

## Funcionalidade nova

1. **Issue e branch** como em todo PR.
2. **Domínio primeiro:** tipos e regras como funções puras em `domain/`, testadas sem `TestBed`.
3. **Estado** num serviço com signals em `application/` (como o `DrawingSession`). Use case só quando junta várias peças, como o `RecognizeDrawing`.
4. **Port só com uma segunda implementação real.** Uma classe concreta basta; o teste a troca por `useValue`. Os ports que existem (`RecognitionGateway`, `ResultStream`) ficam, sem ganhar irmãos.
5. **Componente** em `presentation/`, falando só com `application/`. Uma tela nova, como a lista de candidatos (#59), costuma ser **um componente só**.
6. **UI/UX:** cada decisão de desenho cita o princípio do `docs/UI-UX.md`; diga o que é fonte e o que é julgamento seu.
7. **Testes** de comportamento: o domínio direto, o use case com fakes, o componente pelo que a tela mostra.

## Mudança em código que já existe

- Leia o arquivo e os testes antes; siga a forma dele.
- Não refatore de carona: liste o que achar fora do pedido.
- Bug corrigido ganha teste que falhava antes.

## Antes de dizer que terminou

- **Comandos** do `CLAUDE.md`: `npm run lint`, `npm run test:ci`, `npm run build`, `npm run check:production-bundle` e `npm run format:check`. Texto novo na tela? O `npm run extract-i18n` tem de achá-lo.
- **Olhe a tela** num viewport de celular, com touch: o canvas é o produto. Sem Node disponível, diga isso e não afirme que passou.
- **Documentos:** atualize só o que ficou falso.

## Como entregar

- Separe o que você conferiu (`arquivo:linha` ou print) do que é julgamento seu.
- Diga o que rodou e o resultado, inclusive o que falhou, e o que ficou de fora.
- Merge é decisão de quem pediu.

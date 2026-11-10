# UI/UX: referências e padrões

As fontes de UI/UX do projeto e os padrões que saem delas. Vale para quem propõe, avalia, revisa ou implementa qualquer parte da tela. O jeito de escrever o Angular está na skill `angular-conventions`.

**Estado:** a tela de reconhecimento existe: escolha do modo, canvas, "Reconhecer" e a lista de candidatos com a avaliação da ordem. Os padrões marcados como *no código* foram conferidos no navegador, em vários tamanhos de tela, e num celular de verdade, com o dedo, em 2026-11-10 (#59). **Ainda falta testar com leitor de tela** (TalkBack ou VoiceOver). Os textos citados aqui são os de português, que passam pelo i18n ([ADR 0009](adr/0009-portuguese-ui-first-then-japanese.md)).

## Referências

Toda recomendação de UI/UX cita o princípio que a sustenta.

| Fonte | Para quê |
|---|---|
| [Nielsen, 10 heurísticas](https://www.nngroup.com/articles/ten-usability-heuristics/) | Avaliação geral. As mais usadas: 1 estado do sistema visível, 2 sem jargão, 3 controle e liberdade (desfazer, limpar), 4 consistência, 5 prevenir erro, 8 design minimalista, 9 ajudar a sair do erro |
| [Nielsen, *Progressive Disclosure*](https://www.nngroup.com/articles/progressive-disclosure/) | O essencial primeiro (canvas, botões, candidatos); o resto atrás de um controle secundário |
| [Harley, *Touch Targets*](https://www.nngroup.com/articles/touch-target-size/) | Alvo de toque de pelo menos 1 cm no celular |
| [Shneiderman, *The Eyes Have It*](https://doi.org/10.1109/VL.1996.545307) | Se houver histórico ou estatística: resumo primeiro, detalhe depois |
| [Kendrick, *Toggle-Switch Guidelines*](https://www.nngroup.com/articles/toggle-switch-guidelines/) | Interruptor só para efeito imediato |
| [WAI-ARIA, *Disclosure*](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) e [*Switch*](https://www.w3.org/WAI/ARIA/apg/patterns/switch/) | Mostrar/esconder um bloco (`aria-expanded`); interruptor com rótulo que não muda |
| [W3C i18n, atributo `lang`](https://www.w3.org/International/questions/qa-lang-why) | `lang="ja"` também escolhe a fonte: sem ele, o navegador pode mostrar a forma chinesa do kanji |

**WCAG 2.2** ([Understanding](https://www.w3.org/WAI/WCAG22/Understanding/)):

| Critério | Aqui quer dizer |
|---|---|
| 2.1.1 Keyboard | Tudo funciona pelo teclado, menos o traço à mão livre (a própria WCAG o exclui) |
| 2.5.1 Pointer Gestures e 2.5.7 Dragging | Gesto e arrasto só no canvas; o resto é botão |
| 2.5.2 Pointer Cancellation | Botões agem ao soltar (`click`), não no `pointerdown` |
| 2.5.8 Target Size | Mínimo de 24×24 px; aqui vale o 1 cm da NN/g |
| 4.1.3 Status Messages | "Na fila", "Reconhecendo…" e os erros são anunciados (`role="status"`) sem tirar o foco |
| 1.1.1 Non-text Content | O canvas tem nome ("Área de desenho do kanji"); candidatos são texto, não imagem |
| 1.4.3 e 1.4.11 Contrast | Texto com 4,5:1; borda do canvas, traço e foco com 3:1 |
| 1.4.10 Reflow e 1.3.4 Orientation | Funciona a partir de 320 px, em pé e deitado |
| 1.4.13 Content on Hover | Balão dispensável e persistente; no toque não há hover |
| 3.3.1 Error Identification | O erro diz em texto o que houve e o que fazer |
| 3.3.2 Labels | Todo controle tem rótulo visível |
| 3.1.1 e 3.1.2 Language | `lang="pt-BR"` na página e `lang="ja"` em todo kanji |

## Padrões

Desviar de um padrão pede motivo escrito, e ADR se mudar uma decisão. *Julgamento próprio* marca o que não vem direto de uma fonte.

**No código:**
- **Canvas primeiro:** o canvas é o maior elemento e cabe na tela sem rolar, com os botões logo abaixo, ao alcance do polegar (Nielsen 8; Harley). "Reconhecer" é o único botão preenchido. Num celular baixo em pé (320×568), o canvas encolhe para cerca de 190 px. *Julgamento próprio* sobre o arranjo; conferido em 360×800, 360×640, 320×568, 800×360 e 640×320 (#56, #58).
- **Escolha do modo antes de desenhar:** "Ordem dos traços: importa / não importa", com `<fieldset>`, `<legend>` e dois rádios, acima do canvas, começando em "não importa" (ADR 0012). Não é interruptor, porque o efeito só aparece no próximo reconhecimento (Kendrick). A opção inteira é alvo de toque de 3rem. Trocar o modo não apaga o desenho (Nielsen 1 e 3; WCAG 3.3.2) (#57).
- **Estado do job sempre visível:** "Enviando…", "Na fila", "Reconhecendo…", e no fim o resultado, numa linha `role="status"` com altura reservada (Nielsen 1; WCAG 4.1.3). Cada erro diz o que fazer: fila cheia, falha do reconhecimento, desenho recusado ou grande demais, resultado expirado, sem conexão e servidor que demorou (WCAG 3.3.1) (#58).
- **"Reconhecer" desligado** com o canvas vazio, enquanto o job anterior não termina e, depois de fila cheia, pelos segundos do `Retry-After` (Nielsen 5). *Julgamento próprio* (#58).
- **Desfazer o último traço**, além de limpar tudo (Nielsen 3) (#56).
- **Desenho no limite diz o porquê:** ao chegar no limite de traços ou pontos, o desenho para e uma mensagem anunciada diz o que fazer (Nielsen 9; WCAG 3.3.1) (#56).
- **Um dedo por vez:** um segundo dedo é ignorado enquanto o primeiro desenha (Nielsen 5). *Julgamento próprio* (#56).
- **Girar o celular não apaga o desenho:** os traços acompanham o novo tamanho do canvas (Nielsen 3; WCAG 1.3.4). *Julgamento próprio* (#56).
- **Celular deitado:** os botões e a escolha do modo vão para o lado do canvas, para nada sair da tela (WCAG 1.3.4). *Julgamento próprio* (#56, #57).
- **Nenhum comando por gesto além do desenho** (WCAG 2.5.1 e 2.5.7).
- **Nenhum texto fora do i18n.** Erro da API chega como código e vira texto no frontend (ADR 0009).
- **Kanji marcado como japonês** (`lang="ja"`), com fonte do sistema, nunca de CDN (WCAG 3.1.2; ADRs 0007 e 0009).
- **Candidatos como lista,** do mais provável ao menos, com o kanji grande (`lang="ja"`) e a confiança em porcentagem ("81%", nunca "softmax 0.81"; Nielsen 2). No modo `ordered`, cada um é um botão (`aria-pressed`) de 3rem: o aluno toca no kanji que quis escrever, e a avaliação da ordem é a daquele kanji. O mais provável já começa escolhido. No `unordered`, ainda não há ação ao tocar (vem na #35), então os candidatos são só texto, sem botão que não faz nada (Nielsen 4; WCAG 2.1.1 e 2.5.8). *Julgamento próprio* sobre o toque escolher o kanji (#59).
- **Avaliação da ordem em texto:** "Ordem dos traços certa para 日." ou a lista do que corrigir ("3º traço: deveria ser o 4º.", "2º traço: direção invertida."), numa região `role="status"` que sempre existe na página, para ser anunciada (WCAG 3.3.1 e 4.1.3). Traço juntado ou dividido e número de traços diferente aparecem como observação, não como erro. Sem avaliação, a tela diz o porquê (#59).
- **Atribuição do KanjiVG** no rodapé, como pede a licença (CC BY-SA 3.0; ADR 0016) (#59).
- **Celular deitado ou pequeno em pé (320×568):** o resultado fica abaixo da dobra e a página rola para mostrá-lo; a linha "Mais provável" continua à vista. *Julgamento próprio*, aprovado no teste no celular (#59).

**A fazer:**
- **Destaque no desenho** dos traços fora de ordem, como complemento do texto, nunca no lugar dele (#70).

## Ao propor ou revisar

Separe o que vem das fontes do que é julgamento próprio, e diga quando algo não foi testado num celular de verdade, com o dedo. Fonte nova entra na tabela com link conferido. Padrão novo entra na lista no mesmo PR da tela.

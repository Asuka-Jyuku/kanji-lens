# UI/UX: referências e padrões

As fontes de UI/UX do projeto e os padrões que saem delas. Vale para quem propõe, avalia, revisa ou implementa tela, canvas, resultado, navegação ou controle, seja pessoa ou o Claude. O roteiro do código Angular (camadas, componentes, testes, revisão) está na skill `angular-conventions` (`.claude/skills/`), que aponta para este documento em vez de copiá-lo.

> **Fase:** ainda não há frontend (etapa 3). As referências já valem; os padrões abaixo são **propostos** e passam a "adotados" quando a primeira tela entrar e for validada com uso real num celular. A interface é em português, com o japonês depois, e todo texto passa pelo i18n desde a primeira tela ([ADR 0009](adr/0009-portuguese-ui-first-then-japanese.md)); os textos citados aqui ("Na fila", "Desenhe um kanji") são os de português.

## Referências obrigatórias

Ao propor, avaliar, revisar ou implementar qualquer coisa de UI/UX, basear a recomendação nestas fontes e **citar qual princípio sustenta cada decisão**:

### Usabilidade

| Fonte | Usar para | Link |
|---|---|---|
| Nielsen — 10 heurísticas de usabilidade (NN/g) | Avaliação geral de tela; as mais usadas aqui: 1 *Visibility of System Status* (o job está na fila, processando, pronto), 2 *Match Between the System and the Real World* (sem jargão de ML na tela), 3 *User Control and Freedom* (limpar, desfazer o traço), 4 *Consistency and Standards*, 5 *Error Prevention*, 8 *Aesthetic and Minimalist Design*, 9 *Help Users Recognize, Diagnose, and Recover from Errors* | [nngroup.com/articles/ten-usability-heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) |
| Nielsen — *Progressive Disclosure* (NN/g, 2006) | Mostrar primeiro o essencial (canvas, botões, top-K); o especializado (espessura do traço, mais candidatos, detalhes do modelo) atrás de um controle secundário | [nngroup.com/articles/progressive-disclosure](https://www.nngroup.com/articles/progressive-disclosure/) |
| Harley — *Touch Targets on Touchscreens* (NN/g, 2019) | Alvo de toque com pelo menos 1 cm × 1 cm no celular; mais folga que o mínimo da WCAG 2.5.8 | [nngroup.com/articles/touch-target-size](https://www.nngroup.com/articles/touch-target-size/) |
| Shneiderman — *"Overview first, zoom and filter, then details-on-demand"* (*The Eyes Have It*, IEEE Symposium on Visual Languages, 1996) | Se houver histórico ou estatística de reconhecimentos: resumo primeiro, detalhe sob demanda | [doi:10.1109/VL.1996.545307](https://doi.org/10.1109/VL.1996.545307) |

### Acessibilidade (WCAG 2.2)

| Critério | Usar para | Link |
|---|---|---|
| 2.1.1 *Keyboard* (A) | Tudo funciona por teclado **menos o traço à mão livre**, que a própria WCAG exclui ("Free hand drawing [...] require path dependent input"). Limpar, reconhecer, escolher um candidato e qualquer configuração precisam de `<button>`/`<a>` | [w3.org/WAI/WCAG22/Understanding/keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard) |
| 2.5.1 *Pointer Gestures* (A) | Gesto de caminho só onde ele é essencial (o desenho do kanji); nenhum outro comando por gesto (ex.: "chacoalhar para limpar", "deslizar para enviar") sem um botão equivalente | [w3.org/WAI/WCAG22/Understanding/pointer-gestures](https://www.w3.org/WAI/WCAG22/Understanding/pointer-gestures) |
| 2.5.2 *Pointer Cancellation* (A) | Botões agem no soltar (`click`), não no `pointerdown`: dá para desistir arrastando o dedo para fora | [w3.org/WAI/WCAG22/Understanding/pointer-cancellation](https://www.w3.org/WAI/WCAG22/Understanding/pointer-cancellation) |
| 2.5.7 *Dragging Movements* (AA) | Arrastar só no canvas, onde é essencial; reordenar, ajustar ou escolher nunca exige arrastar | [w3.org/WAI/WCAG22/Understanding/dragging-movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements) |
| 2.5.8 *Target Size (Minimum)* (AA) | Alvo de clique/toque ≥ 24×24 CSS px (o mínimo legal; aqui vale o 1 cm da NN/g, acima) | [w3.org/WAI/WCAG22/Understanding/target-size-minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum) |
| 4.1.3 *Status Messages* (AA) | "Na fila", "Reconhecendo…", "Pronto: 5 candidatos", "Fila cheia, tente de novo" anunciados por leitor de tela (`aria-live`/`role="status"`) sem tirar o foco | [w3.org/WAI/WCAG22/Understanding/status-messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages) |
| 1.1.1 *Non-text Content* (A) | O `<canvas>` tem nome acessível ("Área de desenho do kanji"); os candidatos são texto de verdade, não imagem | [w3.org/WAI/WCAG22/Understanding/non-text-content](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content) |
| 1.4.3 *Contrast (Minimum)* (AA) | Texto ≥ 4,5:1 sobre o fundo (3:1 se grande: 18 pt, ou 14 pt em negrito), inclusive a porcentagem de confiança | [w3.org/WAI/WCAG22/Understanding/contrast-minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum) |
| 1.4.11 *Non-text Contrast* (AA) | Borda do canvas, traço sobre o fundo, borda e foco dos controles com contraste ≥ 3:1 com o que está ao lado | [w3.org/WAI/WCAG22/Understanding/non-text-contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast) |
| 1.4.10 *Reflow* (AA) | Funciona em 320 CSS px de largura sem rolar para o lado: o canvas encolhe junto com a tela | [w3.org/WAI/WCAG22/Understanding/reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow) |
| 1.3.4 *Orientation* (AA) | Funciona com o celular em pé e deitado; não travar a orientação | [w3.org/WAI/WCAG22/Understanding/orientation](https://www.w3.org/WAI/WCAG22/Understanding/orientation) |
| 1.4.13 *Content on Hover or Focus* (AA) | Dica ou balão: dispensável (Esc), alcançável e persistente; em toque não existe hover | [w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus) |
| 3.3.1 *Error Identification* (A) | Erro (desenho vazio, fila cheia, servidor fora do ar, falha do reconhecimento) dito em texto: o que deu errado e o que fazer | [w3.org/WAI/WCAG22/Understanding/error-identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification) |
| 3.1.1 *Language of Page* (A) | `<html lang="pt-BR">`, e `lang="ja"` quando a interface estiver em japonês | [w3.org/WAI/WCAG22/Understanding/language-of-page](https://www.w3.org/WAI/WCAG22/Understanding/language-of-page) |
| 3.1.2 *Language of Parts* (AA) | Todo kanji na tela (candidatos, o kanji escolhido) com `lang="ja"`, em qualquer idioma da interface: o leitor de tela pronuncia em japonês | [w3.org/WAI/WCAG22/Understanding/language-of-parts](https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts) |
| 3.3.2 *Labels or Instructions* (A) | Todo controle com rótulo visível; uma instrução curta perto do canvas ("Desenhe um kanji") | [w3.org/WAI/WCAG22/Understanding/labels-or-instructions](https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions) |

### Idioma e escrita japonesa

| Fonte | Usar para | Link |
|---|---|---|
| W3C Internationalization — *Why use the language attribute?* | O `lang="ja"` também escolhe a fonte: chinês e japonês usam muitas vezes o mesmo código Unicode para um kanji, com pequenas diferenças no desenho, e sem `lang` o navegador pode mostrar a forma chinesa | [w3.org/International/questions/qa-lang-why](https://www.w3.org/International/questions/qa-lang-why) |

### Padrões de componente (WAI-ARIA APG e NN/g)

| Fonte | Usar para | Link |
|---|---|---|
| WAI-ARIA APG — *Disclosure (Show/Hide) Pattern* | Mostrar e esconder um bloco (opções do traço, mais candidatos): o controle é `<button>`, Enter e Espaço alternam, `aria-expanded` diz o estado e `aria-controls` aponta para o conteúdo | [w3.org/WAI/ARIA/apg/patterns/disclosure](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) |
| WAI-ARIA APG — *Switch Pattern* | Interruptor: `role="switch"` (no checkbox nativo usa o `checked`), Espaço alterna, o rótulo **não muda** com o estado | [w3.org/WAI/ARIA/apg/patterns/switch](https://www.w3.org/WAI/ARIA/apg/patterns/switch/) |
| Kendrick — *Toggle-Switch Guidelines* (NN/g, 2018) | Interruptor só para efeito **imediato**; o que depende de "Salvar" fica caixa de marcar; rótulo curto, palavra-chave primeiro | [nngroup.com/articles/toggle-switch-guidelines](https://www.nngroup.com/articles/toggle-switch-guidelines/) |

## Padrões propostos

A partir das referências acima. Passam a "adotados" com a primeira tela validada; desviar de um adotado pede motivo registrado (e ADR, se mudar a decisão).

- **Canvas primeiro:** na tela de reconhecimento, o canvas é o maior elemento e cabe inteiro na tela do celular sem rolar, com "Limpar" e "Reconhecer" logo abaixo, ao alcance do polegar (Nielsen 8; Harley, NN/g).
- **O estado do job sempre visível:** `queued` → "Na fila", `processing` → "Reconhecendo…", `completed` → os candidatos, `failed`/`503`/sem rede → a mensagem do que fazer, todos anunciados (Nielsen 1; WCAG 4.1.3 e 3.3.1).
- **"Reconhecer" desabilitado com o canvas vazio**, em vez de mandar e receber um erro (Nielsen 5).
- **Desfazer o último traço**, além de limpar tudo: errar um traço não obriga a redesenhar o kanji inteiro (Nielsen 3).
- **Candidatos como lista de botões**, do mais provável ao menos, com o kanji grande e a confiança em porcentagem ao lado; cada um é alvo de toque e de teclado (WCAG 2.1.1 e 2.5.8; Nielsen 6).
- **Kanji sempre marcado como japonês** (`lang="ja"`) e com fonte japonesa do sistema ou empacotada, nunca de CDN (WCAG 3.1.2; W3C i18n; ADRs 0007 e 0009).
- **Nenhum texto de interface fora do i18n**, nem com um idioma só; erro vindo da API chega como código e vira texto no frontend (ADR 0009).
- **Confiança sem jargão:** "81%" em vez de "softmax 0.81"; se precisar explicar, um balão que abre por toque e por teclado, nunca só `title=` (Nielsen 2; WCAG 1.4.13).
- **Seletor de modo visível antes de desenhar:** "Ordem dos traços: importa / não importa" é um grupo de duas opções com rótulo visível (por exemplo, `<fieldset>` com `<legend>` e dois `<input type="radio">`), com o modo atual sempre à vista. Não é interruptor: o efeito só aparece no próximo reconhecimento, e o switch é para efeito imediato. O padrão é "não importa" (ADR 0012) (Nielsen 1; WCAG 3.3.2; Kendrick, NN/g). Fica acima do canvas, da mesma largura dele; a opção inteira é o alvo de toque, de 3rem, e a marcada ganha borda na cor do foco além do ponto do rádio. Trocar o modo não apaga o desenho (Nielsen 3) (#57).
- **Resultado da avaliação da ordem em texto, além do destaque visual:** no modo `ordered`, dizer em palavras se a ordem está certa e qual traço está fora de ordem ou na direção errada (por exemplo, "3º traço: deveria ser o 4º"). O destaque no desenho, como cor ou número sobre o traço, complementa o texto e não o substitui. A mensagem é anunciada como as outras de estado. *Julgamento próprio* sobre o formato; a resposta da API ainda não está fechada (ARCHITECTURE.md, seção 2.2) (Nielsen 1 e 9; WCAG 3.3.1 e 4.1.3).
- **Nenhum comando por gesto além do desenho:** limpar e reconhecer são botões (WCAG 2.5.1 e 2.5.7).
- **Funciona em pé, deitado e a partir de 320 px** (WCAG 1.3.4 e 1.4.10).
- **Celular deitado: botões ao lado do canvas.** Na tela baixa, o canvas usa a altura que sobra embaixo do título, e "Desfazer" e "Limpar" vão para o lado, para nada sair da tela sem rolar ("Canvas primeiro"; WCAG 1.3.4). *Julgamento próprio* sobre o arranjo; conferido em 800×360 e 640×320 no navegador, não num celular de verdade (#56). O seletor de modo vai para a esquerda do canvas, com as opções uma embaixo da outra, e a mensagem de limite fica embaixo dos botões, ao lado do canvas, em vez de abaixo dele, que fazia a página rolar 30 px (#57).
- **Girar o celular não apaga o desenho:** os traços acompanham o novo tamanho do canvas, mantendo a forma (Nielsen 3 e 5; WCAG 1.3.4). *Julgamento próprio*, a alternativa era limpar (#56).
- **Um dedo por vez no canvas:** um segundo dedo é ignorado enquanto o primeiro desenha, para um toque acidental da mão não virar traço (Nielsen 5). *Julgamento próprio* (#56).
- **Desenho no limite diz o porquê:** ao chegar no limite de traços ou de pontos da API, o desenho para de crescer e uma mensagem anunciada diz o que fazer ("Desfaça ou limpe para continuar") (Nielsen 9; WCAG 3.3.1 e 4.1.3) (#56).

## Ao propor ou revisar

Separar explicitamente o que vem dessas fontes do que é **julgamento próprio** (trade-off sem fonte direta), e dizer quando algo não foi validado com uso real, principalmente num celular de verdade, com o dedo. Fonte nova entra nesta tabela com link verificado, não citada de memória. Padrão novo de UI entra na lista acima no mesmo PR da tela.

# Avaliação de tela e revisão de código Angular

Use ao avaliar uma tela, ao revisar um PR com frontend e no fim do seu próprio trabalho. Cada achado sai com `arquivo:linha` (ou o print), o que dá errado (quem usa faz X → acontece Y) e a fonte: o princípio de `docs/UI-UX.md`, a ADR ou a regra. O que for gosto, sem fonte, diga que é julgamento.

## O que a CI já pega (não gaste a revisão nisso)

Build, checagem de tipos, testes, linter, a regra de i18n e o teste de arquitetura (`eslint-plugin-boundaries`; ADR 0017). Se um deles falhou na CI, a revisão aponta o job; não reexplica a regra.

## Avaliar uma tela (UI/UX)

Abra a tela num viewport de celular (360×800, com touch) e num de computador **e** leia o código. Prints automatizados entram quando a ferramenta de teste no navegador for escolhida na ADR de ferramentas da etapa 3; até lá, diga como olhou. Do mais grave ao menos:

1. **O canvas é o centro:** é o maior elemento, cabe inteiro no celular sem rolar, e "Limpar" e "Reconhecer" ficam logo abaixo, ao alcance do polegar (Nielsen 8; Harley, NN/g).
2. **Desenhar funciona no celular:** o traço não rola nem dá zoom na página, não sai borrado e continua se o dedo sair do canvas (`style.md`, "Canvas e touch").
3. **Estado do job visível e anunciado:** na fila, reconhecendo, pronto, falhou, fila cheia e sem rede, cada um com texto e anunciado sem tirar o foco (Nielsen 1; WCAG 4.1.3 e 3.3.1).
4. **Teclado:** tudo menos o traço funciona por teclado: limpar, reconhecer, escolher um candidato, abrir opções; foco visível (WCAG 2.1.1 e 1.4.11).
5. **Gestos:** nenhum comando só por gesto ou arrasto fora do desenho; botões agem no soltar (WCAG 2.5.1, 2.5.2 e 2.5.7).
6. **Alvo** de toque ≥ 1 cm (Harley, NN/g), nunca abaixo de 24×24 px (WCAG 2.5.8); **contraste** de texto ≥ 4,5:1 e de borda, traço e foco ≥ 3:1 (WCAG 1.4.3 e 1.4.11).
7. **Candidatos:** texto de verdade com `lang="ja"`, do mais provável ao menos, confiança em porcentagem e sem jargão de ML (WCAG 1.1.1 e 3.1.2; Nielsen 2 e 6).
8. **Controle e erro:** dá para desfazer o último traço e limpar tudo; "Reconhecer" não manda canvas vazio (Nielsen 3 e 5).
9. **Dica e balão:** nada só em `title=`; o balão some com Esc e funciona no toque (WCAG 1.4.13).
10. **Celular:** nada rola para o lado em 320 px, funciona em pé e deitado (WCAG 1.4.10 e 1.3.4).

Separe o que viu na tela do que leu no código, e diga o que não deu para ver (backend falso, celular de verdade, leitor de tela de verdade, rede local).

## O que só a revisão pega

**Camadas (ADR 0004)**
- [ ] `domain/` não importa nada do Angular; `application/` só importa `domain/` e os próprios ports.
- [ ] Nenhum `HttpClient`, `EventSource` ou `fetch` fora de `infrastructure/`.
- [ ] Adapter novo ligado ao port em `app.config.ts`, não instanciado à mão.
- [ ] Nenhuma regra de negócio escondida num componente ou template.

**Regras e testes**
- [ ] Cada regra nova tem teste; use cases testados com port falso, não com `HttpClient` simulado.
- [ ] Bug corrigido com teste que falhava antes.

**Canvas e touch**
- [ ] Pointer Events, `touch-action: none`, `devicePixelRatio` e pointer capture no lugar (`style.md`).
- [ ] O desenho vai como foi desenhado: nada de recortar, redimensionar, inverter ou normalizar no frontend.
- [ ] Limpar o canvas também limpa os resultados e qualquer job pendente.
- [ ] O canvas guarda o desenho como lista de traços (pontos na ordem do pointer) e envia isso com o `stroke_order_mode`; nada de PNG nem de normalização no frontend (ADR 0012).
- [ ] O seletor de modo é um grupo de opções com rótulo visível, e o resultado da avaliação da ordem aparece em texto, não só em cor (`docs/UI-UX.md`, padrões propostos).

**Fluxo assíncrono (ADR 0005)**
- [ ] Todo estado do job aparece na tela: `queued`, `processing`, `completed`, `failed`, mais o `503` (fila cheia) e erro de rede.
- [ ] A conexão SSE é fechada no destroy; o polling de `GET /api/recognitions/{id}` assume quando o SSE cai.
- [ ] Um segundo "Recognize" com um job pendente não deixa dois streams abertos.

**Rede local (ADR 0007)**
- [ ] Nenhuma URL com `localhost` fixo; a base da API vem da configuração ou do proxy do servidor de desenvolvimento.

**UI/UX (`docs/UI-UX.md`)**
- [ ] Cada decisão de desenho no PR cita o princípio de UI/UX, separando fonte de julgamento, e diz o que não foi validado com uso real.
- [ ] Padrão novo de UI: na lista de padrões de `docs/UI-UX.md` e, se mudar decisão, ADR.

**Idioma (`CLAUDE.md`, "Idioma")**
- [ ] Código, nomes de arquivos e comentários em inglês.
- [ ] Nenhum texto de interface escrito direto no template ou no código: tudo pelo i18n, em português (ADR 0009).
- [ ] Todo kanji na tela com `lang="ja"`; `<html lang>` certo; fonte japonesa do sistema ou empacotada, nunca de CDN (ADR 0009, WCAG 3.1.1 e 3.1.2).
- [ ] Erro da API mostrado a partir do código (`queue_full`), não da mensagem do backend.

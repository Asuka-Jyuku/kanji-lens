# Avaliação de tela e revisão do frontend

Cada achado sai com `arquivo:linha` (ou print), o que dá errado (faz X → acontece Y) e a fonte: o princípio do `docs/UI-UX.md`, a ADR ou a regra. Sem fonte, diga que é julgamento.

**O CI já pega** build, tipos, testes, lint, i18n e camadas. Não gaste a revisão nisso.

## Avaliar uma tela (UI/UX)

Olhe num viewport de celular (360×800, com touch) e num de computador, **e** leia o código. Do mais grave ao menos:

1. **O canvas é o centro:** o maior elemento, inteiro no celular sem rolar, com os botões ao alcance do polegar (Nielsen 8).
2. **Desenhar funciona no celular:** sem rolar nem dar zoom, sem borrar, e o traço continua se o dedo sair do canvas.
3. **Estado do job visível e anunciado:** na fila, reconhecendo, pronto, falhou, fila cheia e sem rede (Nielsen 1; WCAG 4.1.3 e 3.3.1).
4. **Teclado:** tudo menos o traço funciona pelo teclado, com foco visível (WCAG 2.1.1 e 1.4.11).
5. **Gestos:** nenhum comando só por gesto (WCAG 2.5.1, 2.5.2 e 2.5.7).
6. **Alvo** de toque de pelo menos 1 cm, nunca abaixo de 24×24 px (WCAG 2.5.8). **Contraste** de 4,5:1 no texto e 3:1 em borda, traço e foco.
7. **Candidatos:** texto com `lang="ja"`, do mais provável ao menos, confiança em porcentagem e sem jargão (Nielsen 2).
8. **Controle:** desfazer e limpar; "Reconhecer" não manda canvas vazio (Nielsen 3 e 5).
9. **Celular:** nada rola para o lado em 320 px; funciona em pé e deitado (WCAG 1.4.10 e 1.3.4).

Diga o que você viu na tela, o que leu no código e o que não deu para ver (celular de verdade, leitor de tela, rede local).

## O que só a revisão pega

- [ ] `domain/` não importa Angular; nada de `HttpClient`, `EventSource` ou `fetch` fora de `infrastructure/`.
- [ ] Nenhum port, use case ou camada nova sem uma segunda implementação real.
- [ ] Nenhuma regra de negócio no componente ou no template.
- [ ] Regra nova com teste; bug corrigido com teste que falhava antes.
- [ ] O desenho vai como foi desenhado: nada de recortar, redimensionar ou normalizar no frontend.
- [ ] Limpar o canvas também limpa os resultados e o job pendente.
- [ ] O SSE fecha no destroy, e o polling assume quando ele cai; um segundo "Reconhecer" não deixa dois streams abertos.
- [ ] Nenhuma URL com `localhost` fixo.
- [ ] Decisão de desenho cita o princípio do `docs/UI-UX.md` e diz o que não foi testado num celular.
- [ ] Nenhum texto de interface direto no template; todo kanji com `lang="ja"`; erro da API mostrado pelo código.

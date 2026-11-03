# 0009. Interface em português primeiro, japonês depois, com i18n desde a primeira tela

- **Status:** Aceita
- **Data:** 2026-11-03
- **Relacionadas:** [0003](0003-angular-frontend-and-fastapi-backend.md), [0004](0004-clean-and-hexagonal-architecture.md), [0007](0007-local-execution-over-the-lan.md)

## Contexto

O idioma dos textos da tela estava em aberto: o esboço do ARCHITECTURE.md estava em inglês ("Clear", "Recognize"), e o `docs/UI-UX.md` usava exemplos em português. Quem vai usar o app primeiro fala português; o japonês vem depois, para quem estuda ou fala japonês. O app mostra kanji o tempo todo, então o texto japonês já aparece na tela desde o começo, mesmo com a interface em português. A regra de idioma do código (inglês) não muda: ela vale para identificadores, não para o que o usuário lê.

## Alternativas consideradas

- **Só português, texto direto no template; i18n quando o japonês chegar** — o mínimo de trabalho agora; o japonês vira uma refatoração de todas as telas (achar cada texto, extrair, revisar), feita quando já houver muitas telas.
- **Português e japonês juntos desde o começo** — nenhuma refatoração depois; dobra o trabalho de texto de cada tela agora, antes de a interface se estabilizar.
- **Português primeiro, mas todo texto passando pelo mecanismo de i18n desde a primeira tela** — custa um pouco de cerimônia por texto agora; o japonês depois vira só um arquivo de tradução, sem mexer nas telas.

## Decisão

A interface nasce em **português do Brasil (`pt-BR`)**, e o **japonês (`ja`)** entra depois. Desde a primeira tela, **todo texto visível passa pelo mecanismo de i18n**, mesmo com um idioma só: nenhum texto de interface fica escrito direto no template ou no código. O mecanismo (o `@angular/localize`, oficial e resolvido no build, uma versão do app por idioma; ou uma biblioteca de tradução em tempo de execução, como o Transloco, que troca de idioma sem recarregar) é escolhido na ADR de ferramentas da etapa 3.

## Consequências

- **Positivas:** o japonês é tradução, não refatoração; os textos ficam todos num lugar, fáceis de revisar; a forma certa do kanji e a pronúncia do leitor de tela ficam garantidas pelo `lang` (abaixo).
- **Negativas:** cada texto novo custa uma chave e uma entrada no arquivo de tradução, mesmo com um idioma só; o japonês da interface precisa de alguém que o revise de verdade (tradução automática na tela de um app para quem estuda japonês é um risco); a escolha do mecanismo fica para a etapa 3, e as duas opções têm custos diferentes (um build por idioma × uma biblioteca a mais).
- **Na prática:**
  - `<html lang="pt-BR">` (e `lang="ja"` quando a interface estiver em japonês) (WCAG 3.1.1).
  - **Os candidatos do reconhecimento e qualquer kanji na tela levam `lang="ja"`, em qualquer idioma da interface** (WCAG 3.1.2). Sem isso, o leitor de tela lê o kanji com a voz do português e o navegador pode desenhar a forma chinesa do caractere, já que chinês e japonês usam muitas vezes o mesmo código Unicode ([W3C, *Why use the language attribute?*](https://www.w3.org/International/questions/qa-lang-why)).
  - Fonte japonesa: as do sistema (`"Hiragino Sans"`, `"Yu Gothic"`, `"Noto Sans JP"`, `sans-serif`) ou uma empacotada no build; **nunca de CDN**, porque o app pode rodar numa rede local sem internet (ADR 0007).
  - **O backend não devolve texto para a tela.** Erros e estados saem como códigos estáveis (`queue_full`, `invalid_drawing`, `job_not_found`), e o frontend os transforma em texto no idioma da interface. As mensagens do backend são em inglês e servem para log (`CLAUDE.md`, "Idioma").
  - Os textos de exemplo do `docs/UI-UX.md` e do ARCHITECTURE.md ficam em português.

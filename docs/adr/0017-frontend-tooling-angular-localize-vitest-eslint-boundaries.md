# 0017. Ferramentas do frontend: Angular 22, @angular/localize, Vitest, ESLint com boundaries

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0003](0003-angular-frontend-and-fastapi-backend.md), [0004](0004-clean-and-hexagonal-architecture.md), [0009](0009-portuguese-ui-first-then-japanese.md), [0011](0011-school-notebook-as-server-with-cpu-first-inference.md), [0013](0013-run-directly-on-the-school-notebook-without-docker.md)

## Contexto

Nenhum código do frontend entra antes das ferramentas da etapa ([#21](https://github.com/Asuka-Jyuku/kanji-lens/issues/21)). O framework é o Angular ([ADR 0003](0003-angular-frontend-and-fastapi-backend.md)), e as camadas são `domain`, `application`, `infrastructure` e `presentation` ([ADR 0004](0004-clean-and-hexagonal-architecture.md)).

A [ADR 0009](0009-portuguese-ui-first-then-japanese.md) exige i18n desde a primeira tela, em português, com o japonês depois. Ela deixou para esta ADR a escolha entre o `@angular/localize` (oficial, um build por idioma) e uma biblioteca em tempo de execução, como o Transloco.

O frontend vai para o notebook da escola como build estático ([ADR 0013](0013-run-directly-on-the-school-notebook-without-docker.md)), então o Node só é necessário para desenvolver e gerar o build.

Versões conferidas no npm e no nodejs.org em 2026-11-08:

| Ferramenta | Versão | Observação |
|---|---|---|
| Node | 26.13 (LTS ativo desde 2026-10-28) | O Angular 22 aceita `^22.22.3 \|\| ^24.15.0 \|\| >=26` |
| Angular (core, CLI, `@angular/build`) | 22.2 | Exige **TypeScript 6.0**: o TypeScript 7 já saiu, mas ainda não é suportado |
| Vitest | 5.x | Executor de testes padrão do CLI (`@angular/build:unit-test`), com jsdom |
| ESLint, angular-eslint, typescript-eslint | 10.14, 22.6, 8.72 | — |
| Prettier | 3.x | Já vem configurado pelo CLI |
| eslint-plugin-boundaries | 7.4 | — |
| npm | 11.20 | Bloqueia scripts de instalação por padrão |

## Alternativas consideradas

- **i18n:**
  - **`@angular/localize`:** oficial, sem biblioteca extra e sem custo em execução. A extração de textos (`ng extract-i18n`) é nativa, e o angular-eslint tem uma regra que obriga marcar todo texto. Em compensação, gera um build por idioma, e trocar de idioma recarrega a página.
  - **Transloco:** troca de idioma sem recarregar e guarda os textos em JSON. É uma dependência de terceiros, e chave faltando só aparece em execução.
- **Gerenciador de pacotes:**
  - **pnpm ou Yarn:** mais rápidos e mais estritos, mas mais uma ferramenta para instalar (o corepack saiu do Node);
  - **npm:** vem com o Node.
- **Executor de testes:**
  - **Karma:** ainda suportado, mas fora do padrão do CLI;
  - **Vitest:** o padrão do CLI 22.
- **Teste de arquitetura:**
  - **dependency-cruiser:** poderoso, mas é mais uma ferramenta e mais um comando;
  - **eslint-plugin-boundaries:** roda dentro do lint e entende tanto camadas quanto pacotes externos (por exemplo, proibir `@angular/common/http` nos componentes).
- **Versão do Node:**
  - **24 LTS:** em manutenção;
  - **26 LTS:** a mais recente, ativa até 2027 e suportada pelo Angular 22.

## Decisão

- **Node 26 LTS** (`.nvmrc` e `engines` no `package.json`) e **npm**, com o `package-lock.json` versionado. Os scripts de instalação seguem bloqueados, como é o padrão do npm 11. O único bloqueado hoje é o do `msgpackr-extract`, um acelerador opcional com alternativa em JavaScript, e ele fica sem aprovar.
- **Angular 22.2**, gerado pelo CLI:
  - componentes standalone, **sem `zone.js`** (zoneless), `OnPush`, modo `strict`, CSS puro e rotas, sem SSR;
  - **guia de nomes de 2025** do CLI (`app.ts`, classe `App`, sem o sufixo `.component`). Os sufixos próprios do projeto (`.use-case.ts`, `.gateway.ts`) continuam valendo.
- **TypeScript 6.0**, a versão que o Angular 22 suporta.
- **i18n: `@angular/localize`.**
  - O idioma de origem é **`pt-BR`** (`i18n.sourceLocale`), com `<html lang="pt-BR">`.
  - Todo texto de template leva `i18n="@@id"`, com id estável, e a regra `@angular-eslint/template/i18n` falha quando um texto ou atributo visível não está marcado.
  - `npm run extract-i18n` gera o `src/locale/messages.xlf` (XLIFF 2).
  - O japonês entra como `messages.ja.xlf` e um segundo build (`/ja/`). Trocar de idioma navega para o outro build.
  - O Angular não tem dados de idioma próprios para `pt-BR`: no CLDR, o `pt` já é o português do Brasil, e o build avisa que usa o `pt`. O aviso é esperado.
- **Testes:** Vitest pelo `ng test`, com jsdom. Domínio e use cases são testados sem `TestBed`; componentes, com ele.
- **Lint e formatação:** ESLint (angular-eslint, typescript-eslint, regras de acessibilidade dos templates) e Prettier.
- **Teste de arquitetura:** `eslint-plugin-boundaries` no `eslint.config.js`, que faz o `npm run lint` falhar quando um import quebra a regra. Também olha os imports de pacotes (`checkAllOrigins`):
  - **`domain`:** importa só `domain`, e nenhum pacote (nem o Angular);
  - **`application`:** importa `domain` e `application`, e só o `@angular/core` (signals e DI); nada de RxJS;
  - **`infrastructure`:** importa as camadas de dentro e qualquer pacote (é onde moram o `HttpClient`, o `EventSource` e o RxJS);
  - **`presentation`:** importa `domain`, `application` e `presentation`, e pacotes `@angular/*`, **menos o `@angular/common/http`**;
  - **shell** (`main.ts` e `app*.ts`, o composition root): importa tudo.

## Consequências

- **Positivas:**
  - nenhum texto de interface escapa do i18n sem o lint reclamar;
  - o japonês vira um arquivo de tradução e uma configuração de build;
  - as regras da ADR 0004 viram erro de lint no editor e no CI, inclusive "componente nunca usa `HttpClient`";
  - zero dependência de i18n em execução;
  - o build é estático, então o notebook não precisa de Node.
- **Negativas:**
  - **trocar de idioma recarrega a página**, e o servidor precisa servir dois builds (`/` ou `/pt-BR/` e `/ja/`) quando o japonês chegar;
  - **o servidor de desenvolvimento serve um idioma por vez**;
  - **a `application` depende do `@angular/core`** por causa dos signals: a camada não é TypeScript puro como o `domain`, e isso vale como exceção registrada;
  - **o TypeScript fica preso no 6.0** até o Angular suportar o 7;
  - **o lint dá um falso negativo** se alguém desligar a regra num arquivo (`eslint-disable`): a revisão do PR precisa olhar isso;
  - **quem desenvolve precisa do Node 26:** com o 22 o projeto roda, mas o npm avisa pelo `engines`.
- **Na prática:**
  - os comandos estão no `CLAUDE.md`, "Comandos";
  - a skill `angular-conventions` segue o guia de nomes de 2025;
  - o ARCHITECTURE.md (seção 3.2) registra que a `application` pode usar o `@angular/core`;
  - o CI ([#32](https://github.com/Asuka-Jyuku/kanji-lens/issues/32)) roda `lint`, `test:ci`, `build` e `format:check`.

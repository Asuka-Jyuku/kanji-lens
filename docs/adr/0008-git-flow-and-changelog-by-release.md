# 0008. Branches `main` + `develop` e CHANGELOG por release

- **Status:** Aceita
- **Data:** 2026-11-03
- **Relacionadas:** [0002](0002-monorepo-for-frontend-backend-and-ml.md)

## Contexto

Vários desenvolvedores vão trabalhar em paralelo, e agentes do Claude Code também vão abrir PRs. O time não quer trabalhar direto na `main`: ela só deve ter versões já integradas e conferidas. O projeto segue o fluxo de um projeto irmão (Finanças Local): `main` + `develop`, Conventional Commits, Keep a Changelog. Aquele projeto sobe a versão em **todo PR** para o `develop`, o que gerou conflitos constantes de merge no arquivo de versão e no CHANGELOG entre PRs paralelos, e exigiu um script só para resolvê-los. Ele faz isso porque publica instaladores cujas notas de atualização saem de cada versão; o KanjiLens não tem instalador nem canal de atualização.

## Alternativas consideradas

- **Trunk-based** (só a `main`, branches curtas) — o mínimo de cerimônia; o time não quer trabalho entrando direto na `main`.
- **`main` + `develop`, versão subindo a cada PR** (como no Finanças Local) — cada PR mergeado é uma versão; conflito em `VERSION` e `CHANGELOG.md` em todo PR paralelo, sem um canal de release que precise disso.
- **`main` + `develop`, seção `[Não publicado]`, versão subindo no release** — cada PR põe a sua entrada em `[Não publicado]`, que só dá conflito quando dois PRs mexem nas mesmas linhas; a versão e a seção com data são definidas uma vez, quando o `develop` vai para a `main`.

## Decisão

Usamos `main` (protegida, estável) e `develop` (protegida, integração, branch padrão do GitHub), com `feature/*` e `fix/*` saindo do `develop`, e `hotfix/*` saindo da `main`. A versão fica só no `VERSION` e sobe **no release**, pelo maior tipo de Conventional Commit em `[Não publicado]`. Todo PR para o `develop` põe a sua entrada em `## [Não publicado]` no `CHANGELOG.md`.

O tipo de merge segue o destino: **squash** nos PRs para o `develop` (um commit por PR, com o título do PR como mensagem) e **merge commit** no release, no hotfix e na volta `main` → `develop`, para as duas branches continuarem com o mesmo histórico. *Rebase and merge* fica desligado.

## Consequências

- **Positivas:** nada chega à `main` sem passar pelo `develop`; PRs paralelos raramente dão conflito no CHANGELOG e nunca na versão; um release é um PR do `develop` para a `main` e uma tag.
- **Negativas:** difere do Finanças Local num ponto (a versão por PR), então quem trabalha nos dois precisa lembrar disso; o GitHub não deixa escolher o tipo de merge por branch de destino, então squash × merge commit vale pelo combinado, e um squash no release faz a `main` divergir da `develop` (a volta passa a dar conflito); o `develop` não tem versão própria entre um release e outro; alguém precisa fazer os releases, ou o `[Não publicado]` cresce sem fim; o `Closes #N` só vale em PR para o branch padrão, então o padrão tem de ser o `develop`.
- **Na prática:** as regras de branch, os passos do release e o formato do CHANGELOG estão no [CONTRIBUTING.md](../../CONTRIBUTING.md) e no `CLAUDE.md`, "Git / commits". Depois de cada release, faça o merge da `main` de volta no `develop`, com merge commit. As opções de merge do repositório (squash com o título do PR, merge commit com o título do PR, sem rebase, apagar a branch depois do merge) estão no CONTRIBUTING.md, "Tipo de merge". Quando houver CI, ela confere se todo PR para o `develop` mexeu em `[Não publicado]`.
- **Atualização de 2026-11-10 ([#82](https://github.com/Asuka-Jyuku/kanji-lens/issues/82)):** cada PR põe **uma linha** no `CHANGELOG.md`, não uma lista; o detalhe fica no PR. O git flow (develop, release e hotfix) continua de propósito: o repositório também é portfólio.

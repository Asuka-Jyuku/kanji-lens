# Como contribuir

Como trabalhamos no KanjiLens: branches, issues, épicos, commits, releases e pull requests. O porquê de cada regra está nas ADRs ([docs/adr/](docs/adr/README.md)); as regras que o Claude Code segue em toda tarefa estão no [CLAUDE.md](CLAUDE.md).

**Idioma:** documentação, issues e corpo dos PRs em português; commits, título do PR, nomes de branch, código e nomes de arquivos em inglês (tabela completa no `CLAUDE.md`, "Idioma").

## Branches

| Branch | Para quê | Regras |
|---|---|---|
| `main` | Estável: a última versão publicada | Protegida: só recebe PR vindo de `develop`, `release/*` ou `hotfix/*` |
| `develop` | Integração do que está pronto para a próxima versão | Protegida, **branch padrão do GitHub**: recebe PR das branches de trabalho |
| `feature/<topic>` | Funcionalidade ou melhoria (ex.: `feature/canvas-touch`) | Sai de `develop`, volta para `develop` |
| `fix/<topic>` | Correção sem urgência | Sai de `develop`, volta para `develop` |
| `hotfix/<topic>` | Correção urgente do que está publicado | Sai de `main`, volta para `main` **e** `develop` |
| `release/<version>` | (opcional) Ajustes finais antes de publicar | Sai de `develop`, volta para `main` e `develop` |

Por que o `develop` é o branch padrão ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)):
- **PR novo:** já sugere o `develop` como destino.
- **`Closes #N` na descrição:** vincula o PR à issue (painel *Development* e o workflow "Pull request linked to issue" do Project) e fecha a issue quando o PR entra no `develop`.
- **Fora do branch padrão, o `Closes #N` não vale.** No PR de `develop` para `main`, ele não faz nada, mas as issues já foram fechadas antes.

Fluxo do dia a dia, com a branch criada pela issue:

```bash
git switch develop
git pull
gh issue develop <número> --base develop --name feature/my-topic --checkout   # ou fix/<topic>
# ... trabalho e commits; ponha a sua entrada em [Não publicado] no CHANGELOG.md ...
git push
gh pr create --base develop --fill    # na descrição: Closes #<número>
```

Issue feita em vários PRs: crie a branch com `git switch -c feature/<topic>-part-1`. A branch criada pelo `gh issue develop` fica ligada à issue, e o merge da primeira parte a fecharia. Só a última parte leva `Closes #N`.

### Tipo de merge

O tipo de merge depende do destino do PR ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)). O GitHub não deixa escolher por branch, então a regra vale pelo combinado: **confira o botão antes de clicar**.

| PR | Merge | Por quê |
|---|---|---|
| `feature/*` ou `fix/*` → `develop` | **Squash and merge** | Um commit por PR na `develop`, com o título do PR (Conventional Commits, em inglês) como mensagem |
| `release/*` → `main` | **Create a merge commit** | A `main` passa a conter os commits da `develop`; com squash, a `main` teria um commit que a `develop` não tem, e a volta daria conflito em todo release |
| `main` → `develop` (a volta depois do release ou do hotfix) | **Create a merge commit** | Pelo mesmo motivo: as duas branches continuam com o mesmo histórico |
| `hotfix/*` → `main` | **Create a merge commit**, e depois a volta `main` → `develop` | A correção chega à `develop` pela volta, sem um segundo PR com o mesmo conteúdo |

**Rebase and merge** fica desligado. O título do PR de release e o da volta também seguem Conventional Commits, porque viram a mensagem do merge commit: `chore(release): v0.1.0` e `chore(release): merge v0.1.0 back into develop`.

**Configuração do repositório** (Settings → General → Pull Requests), que faz o título do PR virar a mensagem nos dois tipos e mantém o corpo em português fora do histórico:
- *Allow squash merging*: ligado, com a mensagem padrão **"Pull request title and commit details"**;
- *Allow merge commits*: ligado, com a mensagem padrão **"Pull request title"**;
- *Allow rebase merging*: desligado;
- *Automatically delete head branches*: ligado.

## Issues

Não há issue? Crie uma antes, já no nome de quem pediu (`gh issue create --assignee @me`): todo PR fecha a issue dele. Ao começar a trabalhar numa issue, atribua-a a você e ponha a etiqueta `in progress` (`gh issue edit <número> --add-assignee @me --add-label "in progress"`); tire a etiqueta ao fechar.

Templates de issue (`.github/ISSUE_TEMPLATE/`):

| Template | Etiqueta | Para quê |
|---|---|---|
| Problema | `bug` | Algo não funciona como deveria |
| Melhoria | `enhancement` | Funcionalidade ou ajuste que o usuário vê |
| Manutenção (chore) | `chore` | Tarefa interna que o usuário não vê: dependência, CI, script, documentação, limpeza |
| Investigação (spike) | `spike` | Pergunta a responder antes de decidir ou estimar; termina numa resposta, numa ADR ou em issues novas, não em código de produção |
| Épico | `epic` | Um grupo de issues (veja abaixo) |

### Dependências entre issues

Dependência vai no GitHub (painel **Relationships**), além do "Depende de: #N" no texto, para ninguém pegar uma issue ainda bloqueada. O `<id>` é o id numérico da issue, não o número dela:

```bash
gh api repos/Asuka-Jyuku/kanji-lens/issues/<N> -q .id                                   # o id de uma issue
gh api -X POST repos/Asuka-Jyuku/kanji-lens/issues/<bloqueada>/dependencies/blocked_by -F issue_id=<id da que bloqueia>
gh api -X POST repos/Asuka-Jyuku/kanji-lens/issues/<épico>/sub_issues -F sub_issue_id=<id da história>   # ligar ao épico
```

Ligar uma história ao épico (sub-issue) é outra coisa e não substitui o *blocked by*. Só dependência real bloqueia: "de preferência antes" não.

## Épicos

Um épico agrupa issues. Há dois tipos:

| Tipo | O que é | Ciclo de vida |
|---|---|---|
| **Épico de entrega** | Um objetivo com fim, dividido em histórias em ordem (ex.: "Machine Learning", a etapa 1 do [ARCHITECTURE.md, "Escopo do MVP"](docs/ARCHITECTURE.md#9-escopo-do-mvp)) | Fica com o Status `Epic` no Project e é fechado à mão quando a definição de pronto é atingida |
| **Épico de tema** | Uma área permanente, que continua recebendo issues (ex.: "Segurança", "Testes e CI", "Documentação") | **Nunca fecha**: fica com o Status `Epic` no Project |

Regras:
- **Título:** `Épico · <nome>`. **Etiquetas:** `epic` e `epic: <name>`; toda história do épico também leva `epic: <name>`.
- **Um pai por issue** (o GitHub aceita um só): o objetivo principal decide. Bug vai para o épico da área que quebrou (não há épico de bugs). A área secundária fica numa etiqueta de área (`frontend`, `backend`, `ml`, `infra`).
- **As histórias são sub-issues** do épico (comando acima), listadas na seção "Etapas" do épico na ordem de trabalho, com *blocked by* só para dependência real.
- **Ninguém é atribuído ao épico nem às histórias dele.** Só a história que alguém pega para fazer vai para o nome dessa pessoa, com `in progress`; o épico continua sem dono.
- **O texto do épico fica em dia:** marque as histórias conforme fecham e ponha uma nota "Revisão de AAAA-MM-DD" no topo de "Etapas" quando o plano mudar (histórias novas, ordem nova, issue reaberta).
- **Todo épico tem o Status `Epic` no Project**, do começo ao fim, e nunca passa por Backlog, In progress ou Done. O workflow "Auto-close issue" fecha a issue cujo Status vai para **Done**, então arrastar um épico para lá o fecharia. O andamento do épico aparece no campo "Sub-issues progress", não no Status. O "Auto-add to project" põe o épico recém-criado em `Backlog`: troque para `Epic` logo depois de criar (comando em "Backlog no Project").

A estrutura do texto de um épico está no template de Épico (`.github/ISSUE_TEMPLATE/epic.md`).

### Backlog no Project

As issues e o andamento ficam no GitHub Project do repositório, o [CNN de Kanjis](https://github.com/orgs/Asuka-Jyuku/projects/6) (número 6). Issue nova (e sub-issue) entra sozinha, pelo workflow "Auto-add to project", com o Status `Backlog`.
- **Campos:** **Status** (Backlog, Ready, In progress, In review, Done e Epic, este só para épicos), **Priority** (P0–P2) e **Size** (XS–XL). Na prática, a prioridade vai na etiqueta `priority: high|medium|low`.
- **Pelo `gh`** (a conta precisa do escopo `project`): `gh project item-list 6 --owner Asuka-Jyuku`, `gh project field-list 6 --owner Asuka-Jyuku` e `gh project item-edit`.
- **Pôr um épico no Status `Epic`:**

  ```bash
  item=$(gh project item-add 6 --owner Asuka-Jyuku --url <url do épico> --format json -q .id)   # devolve o item que já existe
  gh project item-edit --project-id PVT_kwDOEOSoQM4BqAo9 --id "$item" \
    --field-id PVTSSF_lADOEOSoQM4BqAo9zhoZnfE --single-select-option-id ddf6b0a8
  ```

### Etiquetas

Os nomes das etiquetas ficam em inglês, como os outros identificadores; a descrição de cada uma, em português.

| Grupo | Etiquetas |
|---|---|
| Tipo | `bug`, `enhancement`, `chore`, `spike`, `epic` |
| Área | `frontend`, `backend`, `ml`, `infra` |
| Prioridade | `priority: high` (algo quebrado ou que bloqueia outra issue), `priority: medium` (próxima da fila), `priority: low` (quando houver tempo) |
| Épico | `epic: <name>`, uma por épico |
| Andamento | `in progress` |

## Mensagens de commit

[Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/), **em inglês**:

```
<type>(<optional scope>): <imperative summary, up to ~70 characters>

<optional body explaining why>
```

Tipos: `feat` (funcionalidade), `fix` (correção), `refactor`, `perf`, `docs`, `style`, `test`, `build`, `ci`, `chore`.
Escopos: `frontend`, `backend`, `ml`, `infra`, `repo`.

Exemplos:
- `feat(frontend): draw on the canvas with touch`
- `fix(backend): answer 503 when the job queue is full`
- `feat(ml)!: change input size to 64x64` (o `!` marca uma quebra: aqui, os pesos antigos deixam de carregar)

O título do PR segue o mesmo formato, em inglês, porque vira o commit do squash. O corpo do PR é em português, pelo template.

## CHANGELOG e releases

A versão fica só no [`VERSION`](VERSION); a tag `vX.Y.Z` tem de ser igual ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)).

**Todo PR para o `develop` põe a sua entrada em `## [Não publicado]`** no [`CHANGELOG.md`](CHANGELOG.md), dentro do título que já existe ali: `### Funcionalidades`, `### Correções` ou `### Publicação e documentação` (nunca outro título de mesmo tipo). Escreva para quem usa ou roda o projeto, em português: o que muda para essa pessoa, com o número da issue.

Para publicar uma versão:
1. Numa branch `release/<version>` saindo do `develop`, escolha a versão pelo maior tipo em `[Não publicado]`:

   | Maior tipo em `[Não publicado]` | Sobe | Exemplo |
   |---|---|---|
   | `feat` | o número do meio | 0.2.0 → 0.3.0 |
   | `fix`, `docs`, `build`, `ci`, `refactor`, `perf`, `test`, `chore`, `style` | o último | 0.2.0 → 0.2.1 |
   | Quebra (`!`) | o primeiro (o do meio enquanto estiver em `0.x`) | 1.2.0 → 2.0.0 |

2. Atualize o `VERSION` (e `pyproject.toml`/`package.json`, quando existirem); troque `## [Não publicado]` por `## [X.Y.Z] — AAAA-MM-DD` e crie um `## [Não publicado]` vazio acima.
3. PR de `release/<version>` para `main`, com o título `chore(release): vX.Y.Z`, e merge com **merge commit** (nunca squash).
4. Tag na `main`: `git tag vX.Y.Z && git push --tags`.
5. **Faça o merge da `main` de volta no `develop`**, por um PR `main` → `develop` com **merge commit**, para o CHANGELOG do `develop` ficar igual ao publicado.

## Checklist do pull request

O template em `.github/pull_request_template.md` tem a lista completa. Os pontos que mais escapam:
- `Closes #N` na descrição.
- Entrada em `[Não publicado]` no `CHANGELOG.md`.
- Regra sem teste não está pronta; bug corrigido ganha teste que falhava antes.
- Mudou pré-processamento, tamanho da entrada ou lista de classes? Treino, inferência e versão do modelo no mesmo PR, com Top-1/Top-5 antes e depois.
- Mudou tela, canvas ou controle? As decisões de desenho citam o princípio de [docs/UI-UX.md](docs/UI-UX.md).
- Mudou o `README.md`? O `README.pt-BR.md` também, e vice-versa.
- Decisão de arquitetura? ADR no mesmo PR, ou o motivo de não precisar.

## Claude Code no projeto

Quem usa o Claude Code no repositório recebe, pelo `.claude/`:
- **as skills de `.claude/skills/`**: `angular-conventions` (frontend), `fastapi-conventions` (backend) e `ml-conventions` (ML), cada uma o roteiro da sua parte, apontando a ADR ou o documento onde cada regra mora;
- **os agentes de `.claude/agents/`**: `dev-angular`, `dev-backend` e `dev-ml`, que carregam a skill da sua parte e podem trabalhar em paralelo (um agente por tela, use case ou experimento);
- **o hook dos agentes** (`.claude/hooks/block-merge-in-agent.sh`), que barra `gh pr merge` e `git push` forçado vindos de um agente. Merge é sempre decisão de uma pessoa.

## Convenções de código

- Nomes em inglês, no vocabulário das camadas (`XxxUseCase`, `XxxPort` ou um nome de papel, `XxxAdapter`, `XxxRequest`/`XxxResponse`); comentários no código também em inglês.
- Clean Architecture com ports and adapters, em camadas ([ADR 0004](docs/adr/0004-clean-and-hexagonal-architecture.md)): as dependências apontam para dentro; framework só nos adapters.
- Formatação e lint: definidos por stack na ADR de ferramentas do começo de cada etapa, com um `.editorconfig` na raiz.

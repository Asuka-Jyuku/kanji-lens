# Como contribuir

Branches, issues, Project, commits e releases do KanjiLens. O porquê de cada regra está nas [ADRs](docs/adr/README.md); as regras do dia a dia estão no [CLAUDE.md](CLAUDE.md).

**Idioma:** documentação, issues e corpo dos PRs em português; commits, título do PR, branches e código em inglês.

## Branches (git flow)

| Branch | Para quê | Sai de → volta para |
|---|---|---|
| `main` | A última versão publicada (protegida) | só recebe `develop`, `release/*` ou `hotfix/*` |
| `develop` | O que vai para a próxima versão (protegida, branch padrão) | recebe os PRs de trabalho |
| `feature/<topic>` | Funcionalidade ou melhoria | `develop` → `develop` |
| `fix/<topic>` | Correção sem pressa | `develop` → `develop` |
| `release/<version>` | Preparar uma versão | `develop` → `main` e `develop` |
| `hotfix/<topic>` | Correção urgente do que está publicado | `main` → `main` e `develop` |

Como a `develop` é a branch padrão, o `Closes #N` do PR fecha a issue quando o PR entra nela ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)).

```bash
git switch develop && git pull
gh issue develop <número> --base develop --name feature/my-topic --checkout
# ... commits, e uma linha em [Não publicado] no CHANGELOG.md ...
git push
gh pr create --base develop --fill    # na descrição: Closes #<número>
```

**Issue feita em vários PRs:** crie a branch com `git switch -c`, porque a branch do `gh issue develop` fecha a issue no primeiro merge. Só o último PR leva `Closes #N`; os outros, "Parte de #N".

### Tipo de merge

O GitHub não deixa escolher o tipo por branch, então **confira o botão antes de clicar**:

| PR | Merge |
|---|---|
| `feature/*` ou `fix/*` → `develop` | **Squash and merge**: um commit por PR, com o título do PR |
| `release/*` → `main` | **Create a merge commit** |
| `hotfix/*` → `main` | **Create a merge commit**, e depois a volta `main` → `develop` |
| `main` → `develop` (a volta) | **Create a merge commit** |

Com squash no release, a `main` teria um commit que a `develop` não tem, e toda volta daria conflito. *Rebase and merge* fica desligado.

O PR precisa do check `CI` verde e de estar atualizado com a base. Se outro PR entrou antes, use "Update branch" e espere o CI de novo.

## Issues

| Template | Etiqueta | Para quê |
|---|---|---|
| Melhoria | `enhancement` | O que o usuário vê |
| Problema | `bug` | Algo que não funciona |
| Manutenção | `chore` | Tarefa interna: dependência, CI, script, documentação |
| Investigação | `spike` | Uma pergunta a responder; termina numa resposta, numa ADR ou em issues, não em código de produção |
| Épico | `epic` | Um grupo de issues |

**Etiquetas** (nomes em inglês): tipo (`bug`, `enhancement`, `chore`, `spike`, `epic`), área (`frontend`, `backend`, `ml`, `infra`), épico (`epic: <name>`) e `in progress`.

### Dependências entre issues

O `<id>` é o id numérico da issue, não o número:

```bash
gh api repos/Asuka-Jyuku/kanji-lens/issues/<N> -q .id                       # o id de uma issue
gh api -X POST repos/Asuka-Jyuku/kanji-lens/issues/<bloqueada>/dependencies/blocked_by -F issue_id=<id da que bloqueia>
gh api -X POST repos/Asuka-Jyuku/kanji-lens/issues/<épico>/sub_issues -F sub_issue_id=<id da história>
```

Só dependência real bloqueia; "de preferência antes", não. Ser sub-issue de um épico não substitui o *blocked by*. Um PR não pode bloquear uma issue.

## Épicos

- **Dois tipos:**
  - **de entrega**, com fim (ex.: "Machine Learning"), fechado à mão quando fica pronto;
  - **de tema**, que nunca fecha (ex.: "Documentação e processo").
- **Título** `Épico · <nome>`, com as etiquetas `epic` e `epic: <name>`; as histórias também levam `epic: <name>`.
- **Um pai por issue.** Bug vai para o épico da área que quebrou.
- **As histórias são sub-issues do épico.** O andamento aparece em "Sub-issues progress"; não precisa marcar caixas no texto do épico.
- **Ninguém é atribuído ao épico nem às histórias.** Só a história que alguém pega vai para o nome dessa pessoa.
- **O épico fica sempre com o Status `Epic`.** Se for para `Done`, o Project fecha o épico sozinho. Ao criar, troque de `Backlog` para `Epic`.

### Backlog no Project

O andamento fica no [Project "CNN de Kanjis"](https://github.com/orgs/Asuka-Jyuku/projects/6) (número 6). Issue nova entra sozinha, em `Backlog`. Campos: **Status**, **Priority** (0–4) e **Size** (XS–XL).

### Status no Project

| Quando | Status | Etiqueta `in progress` |
|---|---|---|
| Ninguém pegou, sem bloqueio | `Ready` | — |
| Pegou a issue (e se atribuiu) | `In progress` | põe |
| Abriu o PR, mesmo parcial | `In review` | mantém |
| O PR fechou a issue | `Done` (automático) | tira |
| PR parcial entrou e a issue espera outra | `Backlog` | tira |

#### Priority

**0** caminho crítico ou algo quebrado; **1** a próxima; **2** depois; **3** quando der; **4** ideia ou fora do MVP. Toda issue tem uma, inclusive épicos.

#### Comandos

```bash
item=$(gh project item-add 6 --owner Asuka-Jyuku --url <url da issue> --format json -q .id)   # devolve o item, mesmo se já existir
gh project item-edit --project-id PVT_kwDOEOSoQM4BqAo9 --id "$item" \
  --field-id <campo> --single-select-option-id <opção>
# Status   PVTSSF_lADOEOSoQM4BqAo9zhoZnfE: Backlog f75ad846, Ready 61e4505c, In progress 47fc9ee4,
#          In review df73e18b, Done 98236657, Epic ddf6b0a8
# Priority PVTSSF_lADOEOSoQM4BqAo9zhpC3vg: 0 3310041b, 1 645b2e32, 2 705be3b7, 3 7e5e438c, 4 5969c008
```

A conta do `gh` precisa do escopo `project`.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/), em inglês: `<type>(<scope>): <resumo no imperativo>`.

- **Tipos:** `feat`, `fix`, `refactor`, `perf`, `docs`, `style`, `test`, `build`, `ci`, `chore`.
- **Escopos:** `frontend`, `backend`, `ml`, `infra`, `repo`.
- **Exemplos:**
  - `feat(frontend): draw on the canvas with touch`;
  - `fix(backend): answer 503 when the job queue is full`;
  - `feat(ml)!: change input size to 64x64` (o `!` marca uma quebra).
- **Título do PR:** o mesmo formato, porque vira o commit do squash.

## CHANGELOG e releases

Todo PR para a `develop` põe **uma linha** em `## [Não publicado]` no [`CHANGELOG.md`](CHANGELOG.md), dentro do título que já existe (`Funcionalidades`, `Correções` ou `Publicação e documentação`). A linha diz o que muda para quem usa ou roda o projeto, com o número da issue.

Para publicar uma versão:
1. Crie `release/<version>` a partir da `develop`. A versão vem do maior tipo em `[Não publicado]`: `feat` sobe o número do meio (0.2.0 → 0.3.0); o resto sobe o último (0.2.0 → 0.2.1); quebra sobe o primeiro (o do meio enquanto for `0.x`).
2. Atualize o [`VERSION`](VERSION) (e `pyproject.toml`/`package.json`). Troque `[Não publicado]` por `## [X.Y.Z] — AAAA-MM-DD` e crie um `[Não publicado]` vazio acima.
3. Abra o PR `release/<version>` → `main`, com o título `chore(release): vX.Y.Z`, e faça o merge com merge commit.
4. Crie a tag na `main`: `git tag vX.Y.Z && git push --tags`.
5. Faça a volta `main` → `develop` por PR, com merge commit (título `chore(release): merge vX.Y.Z back into develop`).

## CI

O workflow `CI` roda em todo PR e push na `develop` e na `main` ([ADR 0018](docs/adr/0018-ci-with-github-actions-and-a-single-required-check.md)). Cada parte só roda quando muda:
- **Python**, no Linux e no Windows: Ruff, mypy, pytest e os contratos de arquitetura.
- **Frontend:** lint, Prettier, testes, build e a checagem do bundle de produção.
- **Docs links:** links e âncoras dos `.md`.
- **`CI`:** passa quando os outros passaram ou foram pulados. É o único check obrigatório.

Os comandos são os do `CLAUDE.md`, "Comandos".

## Checklist do PR

O template de PR traz a lista. O que mais escapa:
- `Closes #N` e a linha no `CHANGELOG.md`;
- teste para a regra nova, e para o bug corrigido;
- modelo, pré-processamento ou avaliação da ordem mudaram: números antes e depois, no mesmo conjunto;
- mudou o `README.md`: o `README.en.md` também.

## Claude Code

As skills de `.claude/skills/` guiam o trabalho em cada parte: `angular-conventions`, `fastapi-conventions` e `ml-conventions`. Merge é sempre decisão de uma pessoa.

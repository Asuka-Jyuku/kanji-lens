# CLAUDE.md

Regras que valem em qualquer tarefa neste repositório. O que é de um assunto só fica no lugar dele (skill, `CONTRIBUTING.md` ou `docs/`).

## Idioma

| Em português do Brasil | Em inglês |
|---|---|
| Documentação (`docs/`, ADRs, `CHANGELOG.md`, `CONTRIBUTING.md`, este arquivo, skills) | Código, nomes de arquivos e pastas, comentários, logs e mensagens de erro |
| Issues e corpo dos PRs | Commits, título do PR (vira o commit do squash) e nomes de branch |
| Respostas e resumos | Etiquetas do GitHub e nomes de skills |
| Textos da tela, sempre pelo i18n ([ADR 0009](docs/adr/0009-portuguese-ui-first-then-japanese.md)) | Códigos de erro da API (`queue_full`), que o frontend traduz |

Termo técnico fica em inglês (use case, port, adapter, job, Top-5). O `README.md` tem a tradução `README.pt-BR.md`: **mudou um, muda o outro no mesmo PR**.

## O que é

O KanjiLens reconhece kanjis desenhados à mão. O aluno escolhe se a ordem dos traços importa, desenha num canvas e recebe os candidatos mais prováveis. Uma CNN em PyTorch reconhece o kanji; no modo `ordered`, os traços também são comparados com o KanjiVG ([ADR 0012](docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md)).

É um monorepo: `frontend/` (Angular), `backend/` (FastAPI) e `ml/` (dataset, treino e o pré-processamento compartilhado). Tudo roda no notebook da escola (i7, 16 GB, sem GPU), acessado pela rede local, sem nuvem. Por isso a inferência é só na CPU, e número de desempenho só vale medido lá ([ADR 0011](docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md)).

**Andamento:** fica no [GitHub Project](https://github.com/orgs/Asuka-Jyuku/projects/6) e nos épicos, não aqui. Hoje o fluxo completo funciona com um reconhecedor falso; o modelo de verdade vai treinar com desenhos sintéticos do KanjiVG enquanto o ETL estiver fora ([ADR 0022](docs/adr/0022-synthetic-training-data-from-kanjivg-while-etl-is-down.md)).

Visão geral no [README.pt-BR.md](README.pt-BR.md), desenho no [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) e o porquê das decisões em [docs/adr/](docs/adr/README.md).

## Comandos

Para pôr o app de pé (instalação, celular na rede local, problemas comuns), siga o [docs/RUNNING.md](docs/RUNNING.md). O CI roda estes mesmos comandos, e o Python também no Windows. Links dos `.md`: `python3 .github/scripts/check_doc_links.py`.

**Python** (ML e backend, da raiz):

```bash
uv sync --all-packages                                  # dependências (PyTorch só-CPU)
uv run ruff check . && uv run ruff format --check .     # lint e formatação
uv run --directory ml mypy                              # tipos; idem --directory backend
uv run --directory ml pytest                            # testes, inclusive o de arquitetura; idem backend
uv run --directory ml lint-imports                      # só os contratos de arquitetura; idem backend
uv add --package kanjilens-ml <pacote>                  # dependência nova (backend: --package kanjilens)
uv run --directory ml python scripts/prepare_kanjivg.py         # baixa o KanjiVG e gera as referências
uv run --directory ml python scripts/benchmark_stroke_order.py  # mede a avaliação da ordem
uv run --directory backend uvicorn kanjilens.bootstrap.app:create_app --factory --reload   # API em 127.0.0.1:8000
```

A API fica em `127.0.0.1` e roda com **um processo só** (sem `--workers`), porque a fila é em memória ([ADR 0019](docs/adr/0019-in-memory-job-queue-with-one-inference-process.md)). O celular chega a ela pelo proxy do frontend.

**Frontend** (dentro de `frontend/`, Node 26: `fnm use 26`):

```bash
npm ci
npm start                          # http://localhost:4200, com /api encaminhado para 127.0.0.1:8000
npm start -- --host 0.0.0.0        # aberto para o celular (libere só a porta 4200)
KANJILENS_API_URL=http://127.0.0.1:8100 npm start   # API em outra porta
npm run lint                       # ESLint, com arquitetura e i18n
npm run test:ci                    # testes, uma vez
npm run build                      # build de produção
npm run check:production-bundle    # depois do build: nada de ferramenta de desenvolvimento no dist/
npm run format:check               # Prettier
npm run extract-i18n               # textos marcados com i18n
```

## Arquitetura

Camadas com ports and adapters ([ADR 0004](docs/adr/0004-clean-and-hexagonal-architecture.md)). **As dependências apontam para dentro:** o domínio não conhece framework, e só os adapters tocam em FastAPI, PyTorch, `HttpClient` ou APIs do navegador. Detalhes no [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

- **Backend:** `domain/` → `application/` → `adapters/` → `bootstrap/` (o único lugar que liga as peças).
- **Frontend:** `domain/` → `application/` → `infrastructure/` e `presentation/`. **Componente nunca injeta `HttpClient`.**
- **ML:** uma biblioteca. O backend só a usa no processo de inferência, e o PyTorch nunca entra no processo da API.
- **Pré-processamento sempre junto:** um lugar só (`ml/src/kanjilens_ml/preprocessing/`), usado pelo treino e pela inferência. O frontend manda os traços como desenhados. Mudou o pré-processamento, o tamanho da entrada ou a lista de classes? Treino, inferência e versão do modelo mudam no mesmo PR. Duas cópias que divergem fazem o modelo errar sem dar erro.
- **Sem cerimônia:** nada de port ou use case novo sem uma segunda implementação real (o fake do teste não conta). Uma classe concreta basta. Exemplo: a lista de candidatos (#59) é um componente só, lendo o `RecognizeDrawing.result`.

As decisões em aberto estão no `docs/ARCHITECTURE.md`. Não implemente uma delas como se estivesse fechada: feche com uma ADR antes.

## Testes

- **Regra nova nasce com teste.** Bug corrigido ganha um teste que falhava antes.
- Teste o comportamento, não a montagem: nada de teste que só confere uma constante ou o framework.
- **Qualidade do modelo se mede:** Top-1 e Top-5 no mesmo split de teste fixo, antes e depois, em todo PR que muda modelo, pré-processamento ou dados. Na avaliação da ordem, erros detectados × falsos alarmes no mesmo conjunto fixo de desenhos. Queda precisa de um "aceito porque...".
- **Teste de arquitetura:** Import Linter no ML e no backend (`pyproject.toml`) e `eslint-plugin-boundaries` no frontend. Falha quando um import quebra as camadas.

## Decisões de arquitetura (ADRs)

Escreva uma ADR para **decisão difícil de desfazer**: dataset, modelo, contrato da API, exposição na rede, a stack de cada parte, ou uma decisão em aberto que se fecha. Dependência ou ferramenta pequena, refatoração, tela ou endpoint que segue o padrão não precisam. Critérios e índice em [docs/adr/README.md](docs/adr/README.md).

- Mudança que contraria uma ADR aceita: avise o usuário antes, não contorne.
- A decisão mudou? ADR nova, e a antiga vira `Substituída por NNNN`. Nunca apague ADR.
- A ADR vai no mesmo PR da mudança. Marque como *inferido* o que o usuário não confirmou.

## Convenções de código e dados

- **Nunca suba dataset, pesos nem binário grande.** `ml/datasets/` e `ml/artifacts/` ficam fora do git.
- **ETL9G** ([ADR 0021](docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md)): só pelo site oficial. Nenhuma imagem do ETL entra no repositório, nem em teste.
- **KanjiVG** (CC BY-SA 3.0): versão fixada com checksum, gerado por script, fora do git, com a atribuição mantida, inclusive na interface ([ADR 0016](docs/adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)).

## Segurança

O app fica aberto a **qualquer um na rede local, sem login**. Portas, CORS, limites e dados dos alunos estão no [docs/SECURITY.md](docs/SECURITY.md): leia antes de mexer em rota, porta, limite, fila, proxy ou rede.
- Todo dado que chega pela rede tem formato e tamanho máximos, conferidos antes da fila.
- **Nenhuma saída de rede** do app rodando. Chamada nova para fora precisa de ADR.
- Os desenhos somem quando o resultado expira, salvo ADR.

## Documentos nascem com o assunto

**Atualize só o que ficou falso** com a sua mudança, no mesmo PR. Não repita o estado atual em vários lugares: o andamento fica no Project.

| Documento | Muda quando muda |
|---|---|
| `docs/ARCHITECTURE.md` | camadas, contrato da API, decisões em aberto |
| `docs/MODEL.md` | dataset, pré-processamento, treino, modelo ou avaliação da ordem |
| `docs/SECURITY.md` | portas, CORS, limites, fronteira de rede |
| `docs/RUNNING.md` | portas, variáveis de ambiente, forma de subir |
| `docs/architecture/domain.md` | termo ou estado novo do domínio |
| `CHANGELOG.md` | todo PR: uma linha |

Documento novo só nasce quando há assunto para ele. Pesquisa longa de um spike fica em `docs/spikes/`.

**Tela, canvas ou controle:** leia o [docs/UI-UX.md](docs/UI-UX.md) antes e cite o princípio que sustenta cada decisão. Diga quando algo não foi testado num celular de verdade.

## Skills (`.claude/skills/`)

- `angular-conventions`: todo trabalho no frontend.
- `fastapi-conventions`: todo trabalho no backend.
- `ml-conventions`: dataset, pré-processamento, treino, avaliação e inferência.

## Git / commits

- **Conventional Commits em inglês.** Escopos: `frontend`, `backend`, `ml`, `infra`, `repo`.
- **Git flow** ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)): trabalho sai de `develop` em `feature/<topic>` ou `fix/<topic>` e volta por PR. A `main` só recebe `develop`, `release/*` ou `hotfix/*`. Nunca commite direto na `main` nem na `develop`.
- **Merge:** **squash** para a `develop`; **merge commit** no release, no hotfix e na volta `main` → `develop`. Diga qual dos dois ao abrir o PR. **Merge é decisão de uma pessoa.**
- **Sem coautoria do Claude:** nada de `Co-Authored-By: Claude` nem linha parecida.
- **Versão** só no `VERSION`, e sobe no release, pelo maior tipo em `[Não publicado]`: `feat` sobe o do meio, o resto sobe o último. Quebra: pergunte antes.
- **`CHANGELOG.md`:** uma linha por PR em `[Não publicado]`, dentro do título que já existe, dizendo o que muda para quem usa ou roda.

## Issues e Project

Detalhes e comandos no [CONTRIBUTING.md](CONTRIBUTING.md).
- Todo PR para a `develop` leva `Closes #N`. Sem issue? Crie uma (`gh issue create --assignee @me`). Sem saber o número? Pergunte.
- **Pegou uma issue:** atribua a quem pediu, ponha a etiqueta `in progress` e o Status `In progress`. **Abriu o PR:** `In review`. **Fechou:** tire a etiqueta (o `Done` é automático). PR parcial entrou e a issue espera outra: volta para `Backlog`, sem a etiqueta.
- **Dependência real** vai como *blocked by* no GitHub, além do texto. Issue bloqueada não começa: diga o que falta e pare.
- **Épicos e as histórias deles não têm dono.** Só a história que alguém pega vai para o nome dessa pessoa.

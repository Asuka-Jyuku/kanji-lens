# 0018. CI no GitHub Actions, com um check obrigatório só

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0002](0002-monorepo-for-frontend-backend-and-ml.md), [0008](0008-git-flow-and-changelog-by-release.md), [0013](0013-run-directly-on-the-school-notebook-without-docker.md), [0014](0014-ml-tooling-python-uv-ruff-pytest-import-linter.md), [0015](0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md), [0017](0017-frontend-tooling-angular-localize-vitest-eslint-boundaries.md)

## Contexto

Os documentos já contam com uma CI ("o que a CI já pega", nas skills; filtro por caminho, na [ADR 0002](0002-monorepo-for-frontend-backend-and-ml.md)), mas ela não existia ([#32](https://github.com/Asuka-Jyuku/kanji-lens/issues/32)). As três partes já têm comandos de lint, tipos, testes e teste de arquitetura (ADRs [0014](0014-ml-tooling-python-uv-ruff-pytest-import-linter.md), [0015](0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md) e [0017](0017-frontend-tooling-angular-localize-vitest-eslint-boundaries.md)).

O notebook da escola roda Windows ([ADR 0013](0013-run-directly-on-the-school-notebook-without-docker.md)), e o desenvolvimento acontece no Linux. O repositório é público, então os minutos do GitHub Actions são gratuitos.

Num monorepo, rodar tudo em todo PR é lento. Para isso há o filtro por caminho. Mas um workflow filtrado por caminho que seja **check obrigatório** fica "pendente" para sempre nos PRs que não tocam aquela parte, e o merge trava.

## Alternativas consideradas

- **Um workflow por parte, cada um com filtro por caminho e obrigatório:** simples de ler, mas trava o merge dos PRs que não tocam a parte.
- **Um workflow por parte, nenhum obrigatório:** não trava, mas deixa fazer merge com o CI vermelho.
- **Um workflow só, que roda tudo em todo PR:** sem armadilha, mas um PR só de documentação instala o PyTorch duas vezes (Linux e Windows) e o Angular.
- **Um workflow só, com um job que detecta as partes alteradas e um job final de agregação obrigatório:** cada parte roda só quando muda, e o check obrigatório (`CI`) sempre termina. Custa um job a mais e uma action de terceiros para detectar as mudanças.
- **Serviço de CI fora do GitHub:** sem ganho para um repositório público no GitHub.

## Decisão

Um workflow, `.github/workflows/ci.yml`, roda em todo PR e em todo push para o `develop` e para a `main`, e também à mão (`workflow_dispatch`). Os jobs:

| Job | Quando roda | O que faz |
|---|---|---|
| `changes` | sempre | detecta, nos PRs, que partes mudaram (`dorny/paths-filter`); em push e na execução manual, marca todas |
| `python` | mudou `ml/`, `backend/`, `pyproject.toml`, `uv.lock` ou `.python-version` | em **Linux e Windows**: `uv sync --all-packages --locked`, `ruff check` e `ruff format --check` (só no Linux), `mypy` e `pytest` (testes e contratos de arquitetura) do ML e do backend |
| `frontend` | mudou `frontend/` | no Linux: `npm ci`, `lint` (com arquitetura e i18n), `format:check`, `test:ci` e `build` |
| `docs` | mudou algum `.md` | links relativos e âncoras dos Markdown (`.github/scripts/check_doc_links.py`) |
| `CI` | sempre (`if: always()`) | falha se algum job falhou ou foi cancelado; passa se todos passaram ou foram pulados |

- **Uma mudança no próprio `ci.yml`** roda tudo.
- **O único check obrigatório** na proteção do `develop` e da `main` é o **`CI`**.
- **Segurança:**
  - permissões mínimas (`contents: read`, e `pull-requests: read` só no `changes`);
  - `persist-credentials: false` no checkout;
  - **actions fixadas por SHA de commit**, com a versão em comentário: `actions/checkout` v7.0.1, `astral-sh/setup-uv` v10.3.3 (uv 0.13.7), `actions/setup-node` v7.1.0 e `dorny/paths-filter` v4.0.3.
- **Cache:** o uv guarda o cache pelo `uv.lock`, e o npm pelo `package-lock.json`. Um PR novo na mesma branch cancela a execução anterior.
- **O CI não usa dataset, pesos nem GPU:** os testes geram dados minúsculos. A avaliação do modelo e o benchmark ficam fora do CI.

## Consequências

- **Positivas:**
  - nenhuma regra (lint, tipos, testes, contratos de arquitetura, i18n, links) depende de alguém lembrar de rodar;
  - o Windows do notebook é testado em todo PR que mexe em Python;
  - PR só de documentação termina em segundos;
  - o check obrigatório nunca fica pendente por causa do filtro;
  - o CI chama os mesmos comandos do `CLAUDE.md`.
- **Negativas:**
  - **o job `python` baixa o PyTorch só-CPU** em Linux e Windows quando o cache não serve, e leva alguns minutos;
  - **uma action de terceiros** (`dorny/paths-filter`) participa da decisão do que roda. Fica fixada por SHA, mas atualizar exige conferir o código;
  - **atualizar uma action** é trocar o SHA à mão (Dependabot ou Renovate podem entrar depois, com ADR);
  - **o filtro só olha os caminhos:** uma mudança que afete outra parte sem tocar os arquivos dela, como uma variável de ambiente nova, não roda aquela parte no PR. Ela roda no push para o `develop`;
  - **a proteção de branch** precisa ser configurada no GitHub depois do primeiro run do workflow, porque o check `CI` precisa existir antes.
- **Na prática:**
  - os comandos locais são os do `CLAUDE.md`, "Comandos": se passam localmente, passam no CI (a menos de diferenças do Windows);
  - etapa nova numa parte entra no job dela, no mesmo PR que cria o comando;
  - a `main` e o `develop` exigem o check `CI` para o merge (configuração do repositório, descrita no `CONTRIBUTING.md`).

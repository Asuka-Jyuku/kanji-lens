# Registros de decisão de arquitetura (ADRs)

Cada ADR registra **uma** decisão: o problema, as alternativas, o que foi escolhido e o custo. Serve para quem chega depois entender **por que** o código é assim antes de mudar.

## Quando escrever

Para **decisão difícil de desfazer**:
- o dataset, o modelo ou o pré-processamento (tamanho da entrada, normalização, lista de classes);
- o contrato da API;
- exposição na rede ou segurança (portas, CORS, limites, autenticação, saída de rede nova);
- a stack de cada parte, ou como o app roda e é instalado;
- uma decisão em aberto do [ARCHITECTURE.md](../ARCHITECTURE.md) que se fecha;
- um padrão de código que vale para o projeto todo.

Não precisa: dependência ou ferramenta pequena, correção, refatoração, ajuste visual, tela ou endpoint que segue o padrão.

## Como escrever

1. Copie [0000-template.md](0000-template.md) para `NNNN-title-in-kebab-case.md`, com o próximo número. Nome do arquivo em inglês, texto em português.
2. Preencha contexto, alternativas, decisão e consequências. **As negativas são obrigatórias.**
3. Ponha a linha no índice abaixo e a ADR no mesmo PR da mudança.

## Status

| Status | Significado |
|---|---|
| Proposta | Em discussão (PR aberto) |
| Aceita | Vale para o código atual |
| Substituída por NNNN | Trocada por outra. A antiga **não é apagada**: muda o status e aponta para a nova |
| Descontinuada | Deixou de valer, sem substituta |

ADR aceita só se edita com uma nota de atualização: correção, detalhe da mesma decisão ou consequência nova. Se a decisão mudou, é ADR nova.

As ADRs 0002, 0003 e 0005 a 0007 foram escritas depois das decisões; o que não estava registrado está marcado como *inferido*.

## Índice

| ADR | Título | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions-in-adrs.md) | Registrar decisões de arquitetura em ADRs | Aceita |
| [0002](0002-monorepo-for-frontend-backend-and-ml.md) | Monorepo para frontend, backend e ML | Aceita |
| [0003](0003-angular-frontend-and-fastapi-backend.md) | Frontend em Angular e backend em FastAPI, conversando por REST | Aceita |
| [0004](0004-clean-and-hexagonal-architecture.md) | Clean Architecture com ports and adapters, em camadas | Aceita |
| [0005](0005-asynchronous-recognition-with-queue-and-workers.md) | Reconhecimento assíncrono com fila de jobs e workers | Aceita |
| [0006](0006-cnn-with-pytorch.md) | CNN em PyTorch para o reconhecimento | Aceita |
| [0007](0007-local-execution-over-the-lan.md) | Execução local, acessada pela rede local, sem nuvem | Aceita |
| [0008](0008-git-flow-and-changelog-by-release.md) | Branches `main` + `develop` e CHANGELOG por release | Aceita |
| [0009](0009-portuguese-ui-first-then-japanese.md) | Interface em português primeiro, japonês depois, com i18n desde a primeira tela | Aceita |
| [0010](0010-two-recognition-modes-with-specialized-models.md) | Dois modos de reconhecimento com modelos especializados (Opção C) | Substituída por 0012 |
| [0011](0011-school-notebook-as-server-with-cpu-first-inference.md) | Notebook da escola como servidor, com inferência CPU-first | Aceita |
| [0012](0012-ordered-mode-as-stroke-order-evaluation.md) | Modo `ordered` como avaliação da ordem dos traços contra uma referência | Aceita |
| [0013](0013-run-directly-on-the-school-notebook-without-docker.md) | Execução direta no notebook da escola, sem Docker | Aceita |
| [0014](0014-ml-tooling-python-uv-ruff-pytest-import-linter.md) | Ferramentas do ML: Python 3.15, uv, Ruff, mypy, pytest e Import Linter | Aceita |
| [0015](0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md) | Ferramentas do backend: FastAPI e Uvicorn no workspace do uv | Aceita |
| [0016](0016-stroke-order-check-by-bipartite-matching-and-capture-format.md) | Avaliação da ordem por correspondência bipartite, formato dos traços e uso do KanjiVG | Aceita |
| [0017](0017-frontend-tooling-angular-localize-vitest-eslint-boundaries.md) | Ferramentas do frontend: Angular 22, @angular/localize, Vitest, ESLint com boundaries | Aceita |
| [0018](0018-ci-with-github-actions-and-a-single-required-check.md) | CI no GitHub Actions, com um check obrigatório só | Aceita |
| [0019](0019-in-memory-job-queue-with-one-inference-process.md) | Fila em memória (`asyncio.Queue`) com um processo de inferência | Aceita |
| [0020](0020-result-notification-by-server-sent-events.md) | Notificação do resultado por SSE, com polling como reserva | Aceita |
| [0021](0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md) | ETL9G como dataset do reconhecimento e os 1.026 kanji escolares como primeiras classes | Aceita |
| [0022](0022-synthetic-training-data-from-kanjivg-while-etl-is-down.md) | Treino com desenhos sintéticos do KanjiVG enquanto o ETL estiver fora | Aceita |

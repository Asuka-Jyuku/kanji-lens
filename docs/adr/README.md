# Registros de decisão de arquitetura (ADRs)

Cada ADR registra **uma** decisão técnica que afeta a forma do sistema: o problema, as alternativas consideradas, o que foi escolhido e o custo dessa escolha. O objetivo é que quem chegar depois (inclusive o Claude Code) entenda **por que** o código é como é antes de mudar.

## Quando escrever uma ADR

Escreva (ou atualize) uma ADR quando a mudança:

- adiciona ou troca uma **dependência, biblioteca, ferramenta ou integração externa** (inclusive uma saída de rede nova);
- muda o **modelo, o dataset ou o pré-processamento** além de um ajuste de rotina (arquitetura, tamanho da entrada, normalização, lista de classes, fonte dos dados);
- muda **segurança** ou exposição na rede: portas, CORS, limites de entrada, autenticação;
- muda **infraestrutura** ou entrega: como roda, contêineres, scripts, CI;
- **fecha uma decisão em aberto** listada em [ARCHITECTURE.md, "Decisões em resumo"](../ARCHITECTURE.md#10-decisões-em-resumo);
- estabelece ou quebra um **padrão de código** que vale para o projeto todo (camadas, nomes, como uma camada fala com outra).

Não precisa de ADR: correção de bug, refatoração local, ajuste visual, tela ou endpoint novo que só segue padrões já registrados.

## Como escrever

1. Copie [0000-template.md](0000-template.md) para `NNNN-title-in-kebab-case.md`, com o próximo número livre. O nome do arquivo fica em inglês; o texto, em português.
2. Preencha contexto, alternativas, decisão e consequências — **as consequências negativas são obrigatórias**.
3. Adicione a linha no índice abaixo.
4. Inclua a ADR no mesmo pull request da mudança que ela justifica.

## Ciclo de vida

| Status | Significado |
|---|---|
| Proposta | Em discussão (pull request aberto). |
| Aceita | Vale para o código atual. |
| Substituída por NNNN | Trocada por outra decisão. A ADR antiga **não é apagada**: muda o status e aponta para a nova. |
| Descontinuada | Deixou de valer sem substituta (ex.: a funcionalidade foi removida). |

Uma ADR aceita só é **editada** para correções, novos detalhes da mesma decisão ou atualização de consequências. Se a decisão em si mudou, crie uma ADR nova e marque a antiga como substituída.

As ADRs 0002, 0003 e 0005 a 0007 foram escritas depois das decisões, a partir do desenho em [ARCHITECTURE.md](../ARCHITECTURE.md) (commit `d72a4d4`). O contexto delas é reconstruído; o que não estava registrado está marcado como *inferido*.

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
| [0010](0010-two-recognition-modes-with-specialized-models.md) | Dois modos de reconhecimento com modelos especializados (Opção C) | Aceita |
| [0011](0011-school-notebook-as-server-with-cpu-first-inference.md) | Notebook da escola como servidor, com inferência CPU-first | Aceita |

# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e [versionamento semântico](https://semver.org/lang/pt-BR/). Todo PR para o `develop` põe a sua entrada em `[Não publicado]`; a versão é definida no release ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)).

## [Não publicado]

### Funcionalidades
- **A API recebe o desenho** em `POST /api/recognitions` e responde na hora com o `job_id` (#45):
  - **limites:** corpo de até 1 MiB e os limites de traços e pontos;
  - **erros:** desenho inválido ou modo desconhecido → `400`, desenho grande demais → `413`, sempre com um código estável no corpo (`{"error": "..."}`) para o frontend traduzir;
  - **fila:** até 16 jobs esperando; cheia, `503` com `Retry-After` e `queue_full`;
  - **expiração:** o job e o desenho somem 5 minutos depois de terminados;
  - ainda não há quem processe a fila: isso entra na #46.
- **O domínio do reconhecimento existe no backend** (#44):
  - **regras:** o desenho, o modo, o job com os estados, os candidatos e a avaliação da ordem, cada um com as próprias regras;
  - **desenho fora dos limites:** é recusado com um código estável, `drawing_too_large` (muito grande) ou `invalid_drawing` (formato errado), que o frontend vai traduzir;
  - **job:** só passa por `queued` → `processing` → `completed` ou `failed`, e o resultado expira 5 minutos depois do fim;
  - **documentação:** glossário e diagrama de estados em [docs/architecture/domain.md](docs/architecture/domain.md).

### Publicação e documentação
- **Documentação alinhada com a fila, o SSE e as ferramentas**:
  - as ADRs 0003 e 0004, as skills e o `CLAUDE.md` deixam de tratar a fila e a notificação como decisões em aberto e descrevem o processo de inferência no lugar dos "workers";
  - as skills do backend e do ML ganham as regras da fronteira entre processos (só dados serializáveis, falha do processo vira `failed`) e do SSE;
  - o README mostra o endpoint `/events` e aponta os comandos de desenvolvimento;
  - o escopo do MVP marca o que já foi feito e liga as etapas do backend às histórias #44–#48;
  - o `CONTRIBUTING.md` explica que o PR precisa estar atualizado com o `develop` antes do merge.
- **Todo desenvolvimento termina com os documentos em dia:** a regra está no `CLAUDE.md`, nas skills e no checklist do PR.
- **Fila e notificação decididas** (spike em [docs/spikes/queue-and-notification.md](docs/spikes/queue-and-notification.md), #19, #20):
  - **fila** ([ADR 0019](docs/adr/0019-in-memory-job-queue-with-one-inference-process.md)): `asyncio.Queue` limitada; os jobs rodam um por vez num processo de inferência separado, e a API segue respondendo enquanto o modelo trabalha. Sem Redis, que não roda nativo no Windows;
  - **notificação** ([ADR 0020](docs/adr/0020-result-notification-by-server-sent-events.md)): o resultado chega por SSE, com consulta periódica (polling) de reserva.
- **A prioridade fica num campo só, o `Priority` do Project, de 0 a 4**, com o significado de cada valor no [CONTRIBUTING.md](CONTRIBUTING.md#backlog-no-project) e nas próprias opções do campo. As etiquetas `priority:` foram apagadas (#41).
- **CI no GitHub Actions** ([ADR 0018](docs/adr/0018-ci-with-github-actions-and-a-single-required-check.md)), em todo PR para o `develop` ou a `main`:
  - **Python:** lint, tipos, testes e arquitetura do ML e do backend, no Linux e no Windows;
  - **frontend:** lint, formatação, testes e build;
  - **documentação:** links dos `.md`;
  - **filtro por parte:** cada uma roda só quando muda;
  - **merge:** um único check, `CI`, decide (#32).
- **A estrutura do frontend existe** ([ADR 0017](docs/adr/0017-frontend-tooling-angular-localize-vitest-eslint-boundaries.md)):
  - **plataforma:** Angular 22 com Node 26 LTS;
  - **textos:** pelo `@angular/localize`, em português; o lint falha com texto sem marcação, e o japonês vai virar um segundo build;
  - **testes e lint:** Vitest, ESLint e Prettier;
  - **teste de arquitetura:** falha quando um componente usa `HttpClient` ou quando o domínio importa o Angular;
  - **comandos:** no `CLAUDE.md` (#21).
- **Como a ordem dos traços é avaliada** ([ADR 0016](docs/adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md); spike em [docs/spikes/stroke-order-evaluation.md](docs/spikes/stroke-order-evaluation.md), #28):
  - **algoritmo:** correspondência bipartite contra o KanjiVG, que também trata traços unidos ou quebrados;
  - **candidatos:** a avaliação vale para todos os candidatos e não muda o ranking;
  - **requisição:** o canvas manda os pontos como desenhados (`[x, y, t]`), com limites de tamanho;
  - **resposta:** diz, por candidato, que traço está fora de ordem ou na direção errada;
  - **KanjiVG:** licença confirmada (CC BY-SA 3.0) e versão fixada.
- **A estrutura do backend existe** ([ADR 0015](docs/adr/0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md)): API FastAPI com Uvicorn, no mesmo workspace do ML. O backend usa o `kanjilens_ml` com as mesmas versões do treino. Por enquanto, a API só responde a `GET /api/health`. Seis contratos de arquitetura falham quando um import quebra as camadas. Os comandos, inclusive o de subir a API, estão no `CLAUDE.md` (#18).
- **A estrutura de `ml/` existe, com as ferramentas do ML** ([ADR 0014](docs/adr/0014-ml-tooling-python-uv-ruff-pytest-import-linter.md)): Python 3.15 instalado pelo uv, um lock só para as partes Python e o PyTorch só-CPU. Ruff, mypy e pytest cuidam de lint, tipos e testes, e um teste de arquitetura (Import Linter) falha quando um import quebra as regras de dependência. Os comandos estão no `CLAUDE.md` (#12).
- **O KanjiLens roda direto no notebook da escola, sem Docker** ([ADR 0013](docs/adr/0013-run-directly-on-the-school-notebook-without-docker.md)): ambiente Python isolado, frontend como build estático e os processos como serviço do sistema. Sobra mais memória para o modelo. A instalação passo a passo vai para o `docs/RUNNING.md` (#33).
- **O notebook da escola roda Windows**, e a instalação passo a passo no `docs/RUNNING.md` vai ser para ele (#33).
- **O modo padrão é "ordem dos traços não importa".** Quem quer treinar a ordem troca a opção antes de desenhar ([ADR 0012](docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md)).
- **O verbete do kanji escolhido abre num dicionário externo, em nova aba.** O padrão é o Takoboto, e o aluno pode escolher outro numa configuração guardada no aparelho (#35). O dicionário próprio fica para depois (#33).
- **Documentação revisada depois das ADRs 0010–0012** (#30):
  - **Avaliação da ordem nas regras de qualidade:** erros detectados × falsos alarmes passam a ser medidos como o Top-1/Top-5, com item próprio no checklist do PR.
  - **Padrões de tela para o seletor de modo e para o resultado da avaliação da ordem**, este em texto, e não só em cor ([docs/UI-UX.md](docs/UI-UX.md)).
  - **Produção separada do desenvolvimento na execução local:** o build estático na mesma origem da API dispensa CORS; a proposta de QR Code na parede foi registrada.
  - **Licença do KanjiVG nos READMEs.**
  - **O verbete do kanji escolhido** entra como decisão em aberto.
- **Dois modos de reconhecimento: a ordem dos traços importa ou não** ([ADR 0012](docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md), que substitui a [ADR 0010](docs/adr/0010-two-recognition-modes-with-specialized-models.md)). O aluno escolhe o modo a cada reconhecimento, e o canvas envia a lista de traços, não uma imagem.
  - Os dois modos reconhecem o kanji com a mesma CNN 2D compacta, que não depende da ordem.
  - Quando a ordem importa, o KanjiLens também confere a ordem e a direção dos traços contra a referência do KanjiVG e diz quais traços estão fora de ordem, como se faz em sistemas de ensino de kanji. Não há modelo temporal, nem dataset de escrita *online* para treinar.
  - A investigação está em [docs/spikes/model-and-runtime-evaluation.md](docs/spikes/model-and-runtime-evaluation.md) (#23, #26). Ela traz candidatos, runtimes, plano de benchmark, projetos do GitHub para estudo e, na seção 5.3, como o modo com ordem costuma ser feito.
- **O notebook da escola é o servidor** ([ADR 0011](docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md)): Dell Inspiron 3501 (i7-1165G7, 16 GB).
  - A inferência roda só na CPU, e o frontend é servido como build estático.
  - O dimensionamento é para 3–5 alunos enviando desenhos ao mesmo tempo, com 10 clientes como teste de estresse.
  - O treino roda noutra máquina. Os números de desempenho valem só quando medidos no notebook (#24).
- **Referências de UI/UX para o frontend** ([docs/UI-UX.md](docs/UI-UX.md)): as fontes obrigatórias (heurísticas de Nielsen, NN/g, WCAG 2.2, WAI-ARIA) aplicadas ao canvas e ao toque, e os padrões propostos para a tela de reconhecimento. O agente `dev-angular` ganha o modo de avaliação de tela, com o checklist na skill `angular-conventions`.
- **A interface vai ser em português, com o japonês depois** ([ADR 0009](docs/adr/0009-portuguese-ui-first-then-japanese.md)). Todo texto da tela passa pelo i18n desde a primeira tela, para o japonês ser só uma tradução, e os kanjis aparecem sempre marcados como japonês, para o leitor de tela pronunciar certo e o navegador usar a forma japonesa do caractere.
- **Fluxo de trabalho e documentação do projeto organizados.** O documento de design passa a ser o [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), com as camadas de Clean Architecture / ports and adapters do backend, do frontend e do ML. As decisões já tomadas estão registradas nas ADRs 0001 a 0008, em [docs/adr/](docs/adr/README.md). O [CONTRIBUTING.md](CONTRIBUTING.md) descreve as branches `main` + `develop`, as issues, os épicos, o Project, as etiquetas, os commits e os releases. Os templates de issue e de PR estão em `.github/`. A configuração do Claude Code está em `.claude/`: uma skill e um agente por stack.
- **Código sob a licença MIT** ([LICENSE](LICENSE)). A licença cobre só o código; datasets e pesos treinados ficam de fora e seguem os termos de cada dataset.
- **README bilíngue** (`README.md` em inglês e `README.pt-BR.md`), com visão geral, fluxo, stack, API planejada, estrutura do repositório, roadmap e decisões em aberto.
- **Regra do tipo de merge** ([CONTRIBUTING.md, "Tipo de merge"](CONTRIBUTING.md#tipo-de-merge); ADR 0008): squash nos PRs para o `develop` e merge commit no release, no hotfix e na volta `main` → `develop`, para o histórico das duas branches não divergir.
- **Épicos têm um Status próprio no Project** ([CONTRIBUTING.md, "Épicos"](CONTRIBUTING.md#épicos)): todo épico fica em `Epic`, fora do fluxo Backlog → Done, para o workflow de fechamento automático não fechar um épico por engano. O link do [Project](https://github.com/orgs/Asuka-Jyuku/projects/6) entra no CONTRIBUTING (#10).

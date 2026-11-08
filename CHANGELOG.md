# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e [versionamento semântico](https://semver.org/lang/pt-BR/). Todo PR para o `develop` põe a sua entrada em `[Não publicado]`; a versão é definida no release ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)).

## [Não publicado]

### Publicação e documentação
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

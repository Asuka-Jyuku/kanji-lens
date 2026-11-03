# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e [versionamento semântico](https://semver.org/lang/pt-BR/). Todo PR para o `develop` põe a sua entrada em `[Não publicado]`; a versão é definida no release ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)).

## [Não publicado]

### Publicação e documentação
- **Referências de UI/UX para o frontend** ([docs/UI-UX.md](docs/UI-UX.md)): as fontes obrigatórias (heurísticas de Nielsen, NN/g, WCAG 2.2, WAI-ARIA) aplicadas ao canvas e ao toque, e os padrões propostos para a tela de reconhecimento. O agente `dev-angular` ganha o modo de avaliação de tela, com o checklist na skill `angular-conventions`. O idioma da interface entra na lista de decisões em aberto.
- **Fluxo de trabalho e documentação do projeto organizados.** O documento de design passa a ser o [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), com as camadas de Clean Architecture / ports and adapters do backend, do frontend e do ML. As decisões já tomadas estão registradas nas ADRs 0001 a 0008, em [docs/adr/](docs/adr/README.md). O [CONTRIBUTING.md](CONTRIBUTING.md) descreve as branches `main` + `develop`, as issues, os épicos, o Project, as etiquetas, os commits e os releases. Os templates de issue e de PR estão em `.github/`. A configuração do Claude Code está em `.claude/`: uma skill e um agente por stack.
- **Código sob a licença MIT** ([LICENSE](LICENSE)). A licença cobre só o código; datasets e pesos treinados ficam de fora e seguem os termos de cada dataset.
- **README bilíngue** (`README.md` em inglês e `README.pt-BR.md`), com visão geral, fluxo, stack, API planejada, estrutura do repositório, roadmap e decisões em aberto.

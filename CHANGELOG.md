# Changelog

Formato do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e [versionamento semântico](https://semver.org/lang/pt-BR/). Cada PR para a `develop` põe uma linha em `[Não publicado]`; a versão sai no release ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)).

## [Não publicado]

### Funcionalidades
- "Reconhecer" envia o desenho, mostra o estado do job ("Na fila", "Reconhecendo…") e o candidato mais provável; cada erro diz o que fazer (#58).
- Num celular pequeno em pé, o canvas encolhe para tudo caber sem rolar (#58).
- No build de desenvolvimento, dá para salvar o desenho como JSON, com o kanji e a ordem usada, para montar os conjuntos de teste (#66).
- A ordem e a direção dos traços são comparadas com o KanjiVG, sem acusar erro por traço unido ou quebrado (parte da #29).
- Antes de desenhar, o aluno escolhe se a ordem dos traços importa; o padrão é "não importa" (#57).
- Com o celular deitado, a mensagem de limite do desenho não faz mais a página rolar (#57).
- A tela tem a área de desenho, com mouse, dedo ou caneta, "Desfazer traço" e "Limpar" (#56).
- Os traços desenhados são normalizados para a avaliação da ordem (parte da #14).
- O resultado sai pelo SSE em `/api/recognitions/{id}/events` e pelo `GET /api/recognitions/{id}`, no mesmo formato (#47).
- A API processa os jobs um por vez num processo separado, ainda com um reconhecedor provisório (#46).
- A API recebe o desenho em `POST /api/recognitions`, com limites de tamanho e fila de até 16 jobs (#45).
- O domínio do reconhecimento existe no backend: desenho, modo, job, candidatos e avaliação da ordem (#44).

### Publicação e documentação
- O frontend ficou mais simples por dentro, sem mudar a tela: a exportação de desenho numa pasta só, sem router e sem `@angular/forms`, e o modo junto do desenho (#80).
- O backend e o ML perderam peças que não se pagavam, sem mudar a API: o port `Clock`, testes que só conferiam constantes e os pacotes vazios do ML (#81).
- Documentação de processo mais curta e simples (`CLAUDE.md`, `CONTRIBUTING.md`, skills, templates). Regras novas: atualizar só o que ficou falso, andamento só no Project, nada de port novo sem uma segunda implementação e ADR só para decisão difícil de desfazer. Os agentes dev foram removidos; as skills continuam (#82).
- Spike sobre treinar sem o ETL: desenhos sintéticos do KanjiVG e do Kanji alive, validados só em escrita humana ([docs/spikes/training-without-etl.md](docs/spikes/training-without-etl.md), #78).
- O `docs/SECURITY.md` reúne portas, CORS, limites e o que acontece com os desenhos dos alunos (#58).
- O `docs/RUNNING.md` explica como rodar o KanjiLens e abrir pelo celular na rede local (#61).
- O andamento das issues aparece no Status do Project (#61).
- O dataset escolhido é o ETL9G, com os 1.026 kanji escolares como classes, começando pelos 240 da 1ª e 2ª série; o download espera o site oficial voltar ([ADR 0021](docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md), #11).
- Fila em memória com um processo de inferência, e o resultado por SSE com polling de reserva ([ADR 0019](docs/adr/0019-in-memory-job-queue-with-one-inference-process.md), [ADR 0020](docs/adr/0020-result-notification-by-server-sent-events.md), #19, #20).
- A prioridade fica só no campo `Priority` do Project, de 0 a 4 (#41).
- CI no GitHub Actions, com Python no Linux e no Windows, frontend e links das docs, e um único check obrigatório ([ADR 0018](docs/adr/0018-ci-with-github-actions-and-a-single-required-check.md), #32).
- Estrutura do frontend: Angular 22, i18n, Vitest, ESLint e Prettier ([ADR 0017](docs/adr/0017-frontend-tooling-angular-localize-vitest-eslint-boundaries.md), #21).
- A ordem dos traços é avaliada por correspondência bipartite contra o KanjiVG ([ADR 0016](docs/adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md), #28).
- Estrutura do backend: FastAPI com Uvicorn, no mesmo workspace do ML ([ADR 0015](docs/adr/0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md), #18).
- Estrutura do ML: Python 3.15, uv, Ruff, mypy, pytest e PyTorch só-CPU ([ADR 0014](docs/adr/0014-ml-tooling-python-uv-ruff-pytest-import-linter.md), #12).
- O KanjiLens roda direto no notebook da escola (Windows), sem Docker ([ADR 0013](docs/adr/0013-run-directly-on-the-school-notebook-without-docker.md), #33).
- O verbete do kanji escolhido abre num dicionário externo, o Takoboto por padrão (#35).
- Dois modos: a ordem dos traços importa ou não, e a mesma CNN reconhece nos dois ([ADR 0012](docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md), que substitui a 0010; #23, #26, #30).
- O notebook da escola é o servidor, com inferência só na CPU, para 3–5 alunos ao mesmo tempo ([ADR 0011](docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md), #24).
- Referências de UI/UX para o frontend ([docs/UI-UX.md](docs/UI-UX.md)).
- A interface é em português, com o japonês depois, e todo texto passa pelo i18n ([ADR 0009](docs/adr/0009-portuguese-ui-first-then-japanese.md)).
- Fluxo de trabalho organizado: ADRs, branches `main` e `develop`, issues, épicos, Project e templates (#10).
- Código sob a licença MIT; datasets e pesos ficam de fora ([LICENSE](LICENSE)).
- README em inglês e em português.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**O que fica aqui:** o que vale em qualquer tarefa ou dispara de lado, no meio de outra. O que é de um assunto só está no lugar dele (skill, `CONTRIBUTING.md` ou `docs/`), com uma linha aqui dizendo quando ler. Regra nova segue o mesmo critério.

## Idioma

| Em português do Brasil | Em inglês |
|---|---|
| Documentação: `docs/`, ADRs, `CHANGELOG.md`, `CONTRIBUTING.md`, este arquivo, skills e agentes de `.claude/` | Código: classes, funções, variáveis, **nomes de arquivos e pastas**, comentários no código, mensagens de log e de erro |
| Issues (título e corpo) e o corpo dos PRs, seguindo os templates de `.github/` | Mensagens de commit, **título do PR** (vira o commit do squash) e nomes de branch |
| Respostas, perguntas e resumos de fim de tarefa | Etiquetas do GitHub e nomes de skills e agentes |
| **Textos da tela:** português primeiro, japonês depois, sempre pelo i18n e nunca escritos direto no template ([ADR 0009](docs/adr/0009-portuguese-ui-first-then-japanese.md)) | Códigos de erro e de estado que a API devolve (`queue_full`), que o frontend transforma em texto |

Vale também quando o conteúdo técnico (log, erro, documentação de biblioteca) vier em inglês e depois de a conversa ser resumida. Termo técnico fica em inglês, sem tradução forçada (use case, port, adapter, worker, job, Top-5). O `README.md` é em inglês e tem a tradução `README.pt-BR.md`: **mudou um, muda o outro no mesmo PR**.

## O que é o projeto

O KanjiLens reconhece kanjis manuscritos: a pessoa escolhe se a ordem dos traços importa, desenha num canvas e recebe os top-K candidatos, ordenados por confiança. O reconhecimento é uma CNN 2D compacta, treinada em PyTorch, que não depende da ordem; no modo `ordered`, os traços também são comparados com a ordem e a direção do KanjiVG, e a resposta diz quais estão fora de ordem ([ADR 0012](docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md)). É um **monorepo** ([ADR 0002](docs/adr/0002-monorepo-for-frontend-backend-and-ml.md)) com três partes: `frontend/` (Angular), `backend/` (Python, FastAPI, fila de jobs e workers) e `ml/` (dataset, treino, avaliação e o pré-processamento compartilhado). Tudo roda numa máquina só e é acessado pela rede local, sem nuvem ([ADR 0007](docs/adr/0007-local-execution-over-the-lan.md)). Essa máquina é o notebook da escola (Dell Inspiron 3501, i7-1165G7, 16 GB, sem GPU dedicada), então a inferência é **CPU-first** e todo número de desempenho é medido nele ([ADR 0011](docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md)). Veja o [README.pt-BR.md](README.pt-BR.md) para a visão geral e o [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para o desenho. O porquê das decisões está nas ADRs em [docs/adr/](docs/adr/README.md).

**Fase:** só desenho, ainda sem código. O roteiro do MVP está em [docs/ARCHITECTURE.md, "Escopo do MVP"](docs/ARCHITECTURE.md#9-escopo-do-mvp).

## Comandos

Ainda não há. Cada etapa acrescenta os seus aqui (build, testes, lint, rodar) no PR em que o primeiro código dela entra. As ferramentas (gerenciador de pacotes, linter, test runner) são escolhidas numa ADR no começo de cada etapa, não aqui.

## Arquitetura (detalhes em docs/ARCHITECTURE.md)

**Clean Architecture com ports and adapters (hexagonal), em camadas** ([ADR 0004](docs/adr/0004-clean-and-hexagonal-architecture.md)). A regra de dependência é a única que nunca se dobra: **as dependências apontam para dentro**. O domínio não conhece framework nenhum, a camada de aplicação só conhece o domínio e os próprios ports, e só os adapters tocam em FastAPI, PyTorch, `HttpClient` do Angular, fila ou APIs do navegador.

- **Backend** (`backend/src/kanjilens/`): `domain/` → `application/` (use cases + ports) → `adapters/inbound` (HTTP, SSE, consumidor da fila) e `adapters/outbound` (recognizer, avaliador da ordem, fila, armazenamento dos jobs, notifier) → `bootstrap/` (composition root, o único lugar que liga adapters a ports). Os schemas do Pydantic ficam no adapter HTTP, nunca no domínio.
- **Frontend** (`frontend/src/app/`): `domain/` → `application/` (use cases, ports como classes abstratas usadas como token de DI) → `infrastructure/` (adapters HTTP e SSE) e `presentation/` (componentes, páginas, rotas). **Componente nunca injeta `HttpClient`**: só fala com a camada de aplicação.
- **ML** (`ml/src/kanjilens_ml/`): é uma biblioteca, não uma camada do backend. O backend a usa **só dentro dos adapters outbound do recognizer e do avaliador da ordem**; o PyTorch, só no do recognizer.
- **Pré-processamento sempre junto:** existe **um** módulo de pré-processamento (`ml/src/kanjilens_ml/preprocessing/`), importado pelo treino e pelos adapters do backend. Ele gera, a partir da mesma lista de traços, a imagem da CNN e os traços normalizados da avaliação da ordem; o frontend envia os traços como foram desenhados. Mudou o pré-processamento, o tamanho da entrada, a normalização ou a lista de classes? Treino, inferência e versão do modelo mudam **no mesmo PR**. Duas cópias que divergem fazem o modelo errar calado em produção (*train/serve skew*): nenhum erro, só previsão errada.

As decisões em aberto (fila, SSE × WebSocket, dataset, quantidade de classes, algoritmo de avaliação da ordem, modo padrão da interface, runtime de inferência) estão em [docs/ARCHITECTURE.md, "Decisões em resumo"](docs/ARCHITECTURE.md#10-decisões-em-resumo). **Não implemente uma decisão em aberto como se estivesse fechada:** feche-a com uma ADR antes.

## Testes

- **Toda regra nasce com teste.** Domínio e use cases são testados sem framework, com adapters falsos implementando os ports: é para isso que serve o desenho hexagonal. Bug corrigido ganha teste que falha antes da correção.
- **Adapters ganham teste de integração** contra a coisa real quando for barato (test client do FastAPI, fila real no mesmo processo, o modelo real num conjunto fixo de desenhos).
- **Qualidade do modelo se mede, não se afirma:** Top-1 e Top-5 no **mesmo split de teste fixo**, antes e depois, em todo PR que muda modelo, pré-processamento ou dados de treino. O mesmo vale para a avaliação da ordem: erros detectados × falsos alarmes no mesmo conjunto fixo de desenhos com ordem certa e errada, em todo PR que muda o algoritmo, a normalização dos traços ou os dados do KanjiVG. Queda precisa de um "aceito porque..." explícito no PR.
- **Teste de arquitetura** (quando cada parte tiver código): um teste que falha quando um import quebra a regra de dependência. Entra com o primeiro código de cada parte, e a ferramenta é escolhida na ADR de ferramentas da etapa.

## Decisões de arquitetura (ADRs) — obrigatório

As decisões ficam em `docs/adr/` (índice, critérios e ciclo de vida em [docs/adr/README.md](docs/adr/README.md); modelo em `docs/adr/0000-template.md`). **Antes de implementar** qualquer mudança que adicione ou troque dependência ou ferramenta, mude modelo, dataset ou pré-processamento além de um ajuste de rotina, mexa em segurança ou exposição na rede, infraestrutura ou CI, feche uma decisão em aberto, ou crie/quebre um padrão de código do projeto:

1. Leia o índice de `docs/adr/README.md` e as ADRs do assunto. Se a mudança contraria uma ADR **Aceita**, avise o usuário antes de seguir — não contorne a decisão em silêncio.
2. **Já existe ADR do assunto:** atualize-a se a mudança só detalha ou ajusta a mesma decisão. Se a decisão em si mudou, crie uma ADR nova e marque a antiga como `Substituída por NNNN` — nunca apague ADR.
3. **Não existe:** crie `docs/adr/NNNN-title-in-kebab-case.md` (nome do arquivo em inglês, texto em português) a partir do modelo, com o próximo número livre, alternativas consideradas e consequências negativas; marque como *inferido* o que não foi confirmado pelo usuário.
4. Atualize o índice em `docs/adr/README.md` e, se mudar o estado atual descrito, `docs/ARCHITECTURE.md`.
5. A ADR vai no mesmo PR da mudança. Ao final, diga ao usuário qual ADR foi criada ou atualizada (ou por que a mudança não precisou de uma).

Não precisa de ADR: bugfix, refatoração local, ajuste visual, tela ou endpoint que só segue padrões já registrados.

## Convenções de código

- Nomes em inglês, no vocabulário das camadas: `XxxUseCase`, `XxxPort` (ou um nome de papel, como `KanjiRecognizer`, `JobQueue`), `XxxAdapter`, `XxxRequest`/`XxxResponse` (só nos schemas HTTP).
- As regras de cada stack estão nas skills (`angular-conventions`, `fastapi-conventions`, `ml-conventions`), não aqui.
- **Nunca suba dataset, pesos do modelo nem binário grande.** `ml/datasets/` e `ml/artifacts/` estão no `.gitignore`; como obter cada um fica documentado junto do código que usa. Confira a licença do dataset antes de usar ou descrever: alguns datasets de kanji manuscrito (o ETL, por exemplo) exigem cadastro e podem proibir redistribuição (*a confirmar* quando o dataset for escolhido). Os dados de referência do KanjiVG (CC BY-SA 3.0, *a confirmar*) seguem a mesma regra até a escolha de como empacotá-los (#28): versão e licença registradas, atribuição mantida.

## Segurança (específico deste projeto — não genérico)

Diferente de um app só em `localhost`, o KanjiLens fica **acessível a qualquer um na rede local, sem login**. Pontos que afetam como escrever código aqui:
- **Entrada limitada:** o desenho enviado (traços e modo) tem formato e tamanho máximos, em quantidade de traços e de pontos, conferidos no adapter HTTP antes de qualquer coisa chegar à fila. Um `POST` sem limite pode esgotar a memória ou travar os workers.
- **Fila limitada:** a fila tem tamanho máximo; cheia, a API responde `503` com `Retry-After` em vez de aceitar mais trabalho.
- **CORS** só libera a origem do frontend, nunca `*`. Se o frontend fizer proxy de `/api`, o CORS fica desligado.
- **Nenhuma saída de rede** do app em execução. Chamada nova para fora (telemetria, download de modelo em tempo de execução, CDN) precisa de ADR.
- Os desenhos não são guardados depois que o resultado do job expira, a menos que uma ADR diga o contrário (coletar desenhos de alunos para testar a avaliação da ordem é um desses casos: precisa de ADR antes).
- O `docs/SECURITY.md` nasce no primeiro PR que expõe a API na rede local (veja "Documentos nascem com o assunto").

## Documentos nascem com o assunto

Não crie documento vazio. Cada um nasce no primeiro PR que precisa dele e, daí em diante, muda junto com o código:

| Documento | Nasce quando | Muda junto com |
|---|---|---|
| `docs/MODEL.md` | etapa 1 (ML): dataset, pré-processamento, treino, métricas, versões do modelo | qualquer mudança em dataset, pré-processamento, treino ou modelo |
| `docs/SECURITY.md` | a API é exposta na rede local pela primeira vez | portas, CORS, limites de entrada, fronteira de rede nova |
| `docs/architecture/domain.md` | o primeiro código de domínio: glossário e diagrama de estados do job | termo novo do domínio ou estado novo |
| `docs/RUNNING.md` | a primeira parte que roda: como rodar localmente e na rede local | qualquer mudança em portas, variáveis de ambiente ou partida |

A pesquisa de um spike com resposta longa fica em `docs/spikes/`, linkada na issue e na ADR que ela gerou (ex.: [docs/spikes/model-and-runtime-evaluation.md](docs/spikes/model-and-runtime-evaluation.md)). Os projetos do GitHub citados ali são referência de estudo: copiar código, pesos ou dados deles passa pela licença de cada um e por uma ADR.

## UI/UX

**Mexeu em tela, canvas, resultado, navegação ou controle? Leia [docs/UI-UX.md](docs/UI-UX.md) antes de propor, avaliar, revisar ou implementar:** as referências obrigatórias (Nielsen, NN/g, WCAG 2.2, WAI-ARIA, Shneiderman) e os padrões propostos. Cite o princípio que sustenta cada decisão, separe o que vem das fontes do que é julgamento próprio e diga quando algo não foi validado com uso real num celular.

## Skills e agentes do projeto (`.claude/`)

- **Angular:** a skill `angular-conventions` é o roteiro de todo trabalho no frontend (tela nova, mudança, avaliação de UI/UX, revisão). O agente `dev-angular` a carrega, para avaliar telas em paralelo (um agente por tela), implementar ou revisar.
- **FastAPI:** a skill `fastapi-conventions` é o roteiro de todo trabalho no backend (use case, adapter, endpoint, worker, revisão). O agente `dev-backend` a carrega.
- **ML:** a skill `ml-conventions` é o roteiro de dataset, pré-processamento, treino, avaliação e do adapter do recognizer. O agente `dev-ml` a carrega.
- Os agentes compartilham um hook (`.claude/hooks/block-merge-in-agent.sh`) que barra `gh pr merge` e `git push` forçado.

## Git / commits

Conventional Commits **em inglês** (fluxo de branches, comandos e o Project em [CONTRIBUTING.md](CONTRIBUTING.md)). Escopos: `frontend`, `backend`, `ml`, `infra`, `repo`. **A `main` é protegida** (só recebe merge de `develop`, `release/*` ou `hotfix/*`); trabalho novo parte de `develop` em `feature/<topic>` ou `fix/<topic>` e volta para `develop` por PR ([ADR 0008](docs/adr/0008-git-flow-and-changelog-by-release.md)). Nunca faça commit direto na `main` nem na `develop`.

**Tipo de merge** (tabela em [CONTRIBUTING.md, "Tipo de merge"](CONTRIBUTING.md#tipo-de-merge)): PR para a `develop` entra por **squash**; release (`release/*` → `main`), hotfix (`hotfix/*` → `main`) e a volta `main` → `develop` entram por **merge commit**. Ao abrir ou revisar um PR, diga qual dos dois ele leva. Merge continua sendo decisão de uma pessoa.

**Versão: só no arquivo `VERSION`**, na raiz; a tag `vX.Y.Z` tem de ser igual, e `pyproject.toml`/`package.json` seguem o mesmo número quando existirem. A versão **sobe no release, não a cada PR** (ADR 0008):
- `feat` → o número do meio (0.2.0 → 0.3.0); `fix`, `docs`, `build`, `ci`, `refactor`, `perf`, `test`, `chore`, `style` → o último; quebra de verdade → o primeiro (pergunte ao usuário antes). Enquanto estiver em `0.x`, quebra sobe o número do meio.
- No release, vale o maior tipo entre as entradas de `[Não publicado]`.

**`CHANGELOG.md`:** todo PR para o `develop` põe a sua entrada em `## [Não publicado]`, no topo, **dentro** do `### Funcionalidades` / `### Correções` / `### Publicação e documentação` que já existe ali (nunca outro título de mesmo tipo). No release, `[Não publicado]` vira `## [X.Y.Z] — AAAA-MM-DD` e um `[Não publicado]` vazio é criado acima. Escreva a entrada para quem usa ou roda o projeto: o que muda para essa pessoa, não quais arquivos mudaram.

**Issues** (o branch padrão do GitHub é o `develop`):
- Todo PR para o `develop` leva `Closes #N` na descrição: o GitHub vincula o PR à issue e a fecha no merge.
- **Branch nova:** de preferência criada pela issue, com `gh issue develop <N> --base develop --name feature/<topic> --checkout`. Issue feita em vários PRs: crie a branch com `git switch -c`, porque a branch criada pela issue a fecha no primeiro merge; só o último PR fecha a issue.
- **Issue nova já nasce no nome de quem pediu** (`gh issue create --assignee @me`, ou o login de quem pediu). **Exceção, os épicos:** o épico e as histórias dele não são atribuídos a ninguém — nem ao criar, nem depois, nem ao ligar uma história ao épico. Só a história que uma pessoa **pega**, pedindo aqui, vai para o nome dela, com a etiqueta `in progress`. Se o usuário pedir para não atribuir uma issue a ele, não atribua.
- **Antes de trabalhar numa issue:** atribuir a quem pediu e pôr a etiqueta `in progress` (`gh issue edit <N> --add-assignee @me --add-label "in progress"`). Ao fechar, tirar a etiqueta.
- **Dependência entre issues vai no GitHub, não só no texto:** issue que só pode começar depois de outra pronta ganha *blocked by* (comando em [CONTRIBUTING.md](CONTRIBUTING.md#dependências-entre-issues)), além do "Depende de: #N" no texto. Só dependência real: "de preferência antes" não bloqueia, e ligar ao épico (sub-issue) não substitui o *blocked by*. **Issue bloqueada não começa:** diga o que falta e pare.
- **Épicos:** como se organizam (épico de entrega × épico de tema, um pai por issue, etiqueta `epic: <name>`) está em [CONTRIBUTING.md, "Épicos"](CONTRIBUTING.md#épicos).
- **Não sabe o número da issue:** pergunte ao usuário. Se não houver issue, ofereça criar uma.
- **Backlog e andamento** ficam no GitHub Project do repositório (link e campos em [CONTRIBUTING.md](CONTRIBUTING.md#backlog-no-project)): consulte quando a conversa for sobre backlog, andamento ou o que falta.

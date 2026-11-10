---
name: fastapi-conventions
description: Como se escreve o backend do KanjiLens (backend/, Python + FastAPI) — use case, port, adapter inbound (rota HTTP, SSE, consumidor da fila), adapter outbound (recognizer, avaliador da ordem, fila, armazenamento dos jobs, notifier), composition root, e revisão de PR com backend, seguindo Clean Architecture / ports and adapters, com a fonte de cada regra. Usar ao pedirem "endpoint novo", "use case", "port", "adapter", "worker", "fila", "SSE", "status do job", "revisa o backend", e ao pegar issue com a etiqueta backend ou que mexe em backend/.
model: sonnet
---

# FastAPI no KanjiLens

Você escreve e revisa o backend do projeto (`backend/`). O que vale **sempre** está aqui.

**Cada regra mora num lugar só.** Esta skill diz o caminho e aponta a fonte; não copie a regra para cá. Achou uma regra aqui que diverge da fonte, vale a fonte: corrija a skill no mesmo PR.

> **Fase:** a estrutura de `backend/` existe, com as ferramentas da [ADR 0015](../../../docs/adr/0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md): FastAPI, Uvicorn, uv, Ruff, mypy, pytest com `httpx2` e Import Linter. O domínio do reconhecimento existe ([docs/architecture/domain.md](../../../docs/architecture/domain.md)); a aplicação é criada por `create_app()` em `bootstrap/app.py`, com o `GET /api/health` e o `POST /api/recognitions` (use case `SubmitRecognition`, fila e repositório em memória). O `lifespan` sobe o processo de inferência e o consumidor da fila, que roda o use case `ProcessRecognition` com o reconhecedor e a avaliação da ordem falsos até a #48. O resultado sai pelo `GET /api/recognitions/{id}` e pelo SSE (`/events`), os dois pelo use case `GetRecognition` e no mesmo schema. Os modelos a seguir estão em [`references/examples.md`](references/examples.md).

| Assunto | Fonte (a regra está lá) |
|---|---|
| Camadas `domain` → `application` (`use_cases`, `ports`) → `adapters` (`inbound`, `outbound`) → `bootstrap`; o que cada uma pode importar | [ADR 0004](../../../docs/adr/0004-clean-and-hexagonal-architecture.md) e [ARCHITECTURE.md, seção 3.1](../../../docs/ARCHITECTURE.md#31-backend-backendsrckanjilens) |
| Fluxo do job, `job_id`, estados, o modelo e as referências do KanjiVG carregados uma vez no processo de inferência, uma inferência ativa por vez no início, um processo do Uvicorn só com `asyncio.Queue`, inferência fora do event loop | [ADR 0005](../../../docs/adr/0005-asynchronous-recognition-with-queue-and-workers.md), [ADR 0011](../../../docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md) e [ARCHITECTURE.md, seção 4](../../../docs/ARCHITECTURE.md#4-processamento-assíncrono-e-concorrência) |
| Endpoints, o SSE nativo do FastAPI (`EventSourceResponse`, estado completo por evento) e o polling de reserva | [ADR 0020](../../../docs/adr/0020-result-notification-by-server-sent-events.md) e [ARCHITECTURE.md, seção 5](../../../docs/ARCHITECTURE.md#5-comunicação-entre-frontend-e-backend) |
| Fila `asyncio.Queue` limitada (16, `503` cheia), um processo de inferência (`ProcessPoolExecutor`, `spawn`, modelo carregado no `initializer`), jobs em memória com expiração | [ADR 0019](../../../docs/adr/0019-in-memory-job-queue-with-one-inference-process.md) |
| Limite de entrada, fila limitada, CORS, nenhuma saída de rede | [`docs/SECURITY.md`](../../../docs/SECURITY.md) e [ADR 0007](../../../docs/adr/0007-local-execution-over-the-lan.md) |
| O adapter do recognizer, o do avaliador da ordem e o `kanjilens_ml` | skill `ml-conventions`, "Inferência"; [ADR 0012](../../../docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md) |
| Idioma: código em inglês, documentação em português | `CLAUDE.md`, "Idioma" |
| Testes, branches, commits, CHANGELOG | `CLAUDE.md`, "Testes" e "Git / commits"; `CONTRIBUTING.md` |

## Referências (leia quando o passo pedir)

| Arquivo | Quando ler |
|---|---|
| [`references/style.md`](references/style.md) | antes de escrever código, e sempre que um tutorial de FastAPI ou um revisor parecer dizer outra coisa |
| [`references/review.md`](references/review.md) | ao revisar um PR com backend, e no fim do seu próprio trabalho |
| [`references/examples.md`](references/examples.md) | antes de escrever um tipo de domínio, um use case ou um adapter: o código que já serve de modelo |

## Funcionalidade nova

1. **Issue e branch** como em todo PR (`CLAUDE.md`, "Git / commits").
2. **ADR antes do código** quando a funcionalidade trouxer dependência, fechar uma decisão em aberto (ARCHITECTURE.md, seção 10; ex.: o runtime de inferência) ou criar um padrão novo (`CLAUDE.md`, "Decisões de arquitetura").
3. **Domínio:** entidade ou value object em `domain/`, com as regras dele (ex.: as transições permitidas de `JobStatus`) em Python puro, testado sozinho.
4. **Port** em `application/ports/` como `typing.Protocol`, com nome de papel (`KanjiRecognizer`, `JobQueue`), usando só tipos do domínio.
5. **Use case** em `application/use_cases/`: uma classe, dependências (ports) pelo construtor, um método público. Testado com adapters falsos.
6. **Adapters:** inbound em `adapters/inbound/` (rota + Pydantic `XxxRequest`/`XxxResponse` + mapeamento de e para o domínio; erros de domínio viram status HTTP aqui); outbound em `adapters/outbound/`, implementando o port.
7. **Ligação** só em `bootstrap/`: monta os adapters, injeta nos use cases e expõe os use cases às rotas.
8. **Testes:** unitários do domínio e do use case; integração dos adapters (test client do FastAPI, fila real no mesmo processo, o SSE lido até o estado final, o pool de verdade com um modelo falso); os casos de erro do endpoint (`400`/`413`/`404`/`503`).

## Mudança em código que já existe

- Leia o módulo inteiro e os testes dele antes de mexer; siga a forma dele.
- Não aproveite para refatorar: o que achar fora do pedido, liste.
- Bug corrigido ganha teste que falha antes da correção.

## Antes de dizer que terminou

**Documentos em dia:** atualize no mesmo PR o que a mudança afetou (`CLAUDE.md`, "Documentos nascem com o assunto").

Rode os comandos do `CLAUDE.md`, "Comandos": `ruff check` e `ruff format --check` na raiz, e `mypy`, `pytest` e `lint-imports` com `--directory backend`. O `pytest` já roda o teste de arquitetura (os seis contratos do `backend/pyproject.toml`). Mudou o `kanjilens_ml`? Rode também com `--directory ml`.

- **Python ou dependências não disponíveis:** diga isso e não afirme que passou.

## Como entregar

Separe o que conferiu no código (com `arquivo:linha`) do que é julgamento seu, diga o que rodou e o resultado (inclusive o que falhou ou não rodou), e o que ficou de fora, com o motivo. PR: o checklist do `CONTRIBUTING.md` e do template de PR; merge só com o "pode" de quem pediu, para aquele PR.

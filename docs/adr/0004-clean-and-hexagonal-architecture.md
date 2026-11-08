# 0004. Clean Architecture com ports and adapters, em camadas

- **Status:** Aceita
- **Data:** 2026-11-03
- **Relacionadas:** [0002](0002-monorepo-for-frontend-backend-and-ml.md), [0005](0005-asynchronous-recognition-with-queue-and-workers.md), [0019](0019-in-memory-job-queue-with-one-inference-process.md), [0020](0020-result-notification-by-server-sent-events.md)

## Contexto

Duas das decisões em aberto são de infraestrutura que fica logo atrás do fluxo principal: a fila de jobs (`asyncio.Queue` agora, talvez Redis + Celery/RQ depois) e a notificação do resultado (SSE ou WebSocket). O próprio modelo vai ser retreinado e trocado muitas vezes. Vários desenvolvedores e agentes vão trabalhar em paralelo, então o código precisa de fronteiras que digam a cada um onde cada lógica mora. O time prefere trabalhar por camadas.

## Alternativas consideradas

- **Organização pelo framework** (`api/`, `services/`, `workers/`, `models/`, como no primeiro esboço do README) — simples e conhecida; mas FastAPI, Pydantic e PyTorch vazam para o código de negócio, e trocar a fila ou o notifier obriga a editar os services.
- **Vertical slices** (uma pasta por funcionalidade, com tudo dentro) — pouca cerimônia; com três use cases quase não há o que fatiar, e as decisões de infraestrutura continuariam espalhadas.
- **Clean Architecture com ports and adapters** — domínio e use cases sem import de framework; fila, notifier, armazenamento dos jobs e recognizer atrás de ports; adapters trocados num lugar só; custa mais arquivos e código de mapeamento.

## Decisão

Usamos Clean Architecture com ports and adapters (hexagonal) no backend e no frontend, organizada em camadas, com as dependências apontando para dentro. O motivo principal é que as decisões em aberto e o modelo viram adapters substituíveis, e os use cases ficam testáveis com fakes.

**Backend** (`backend/src/kanjilens/`): `domain/` → `application/` (`use_cases/`, `ports/`) → `adapters/inbound/` e `adapters/outbound/` → `bootstrap/` (composition root).
**Frontend** (`frontend/src/app/`): `domain/` → `application/` (use cases, ports como classes abstratas usadas como token de DI) → `infrastructure/` e `presentation/`.
**ML** (`ml/src/kanjilens_ml/`) é uma biblioteca, usada pelo backend só dentro do adapter outbound do recognizer.

A tabela completa do que cada camada pode importar está em [ARCHITECTURE.md, seção 3](../ARCHITECTURE.md#3-camadas-clean-architecture-e-ports-and-adapters).

## Consequências

- **Positivas:** `asyncio.Queue` → Redis e SSE → WebSocket trocam, cada um, um adapter e a ligação em `bootstrap/`, sem mexer nos use cases; use cases e regras de domínio têm teste unitário com adapters falsos, sem FastAPI, PyTorch nem navegador; cada camada responde com clareza "onde isso vai".
- **Negativas:** mais arquivos e indireção do que uma API de 3 endpoints precisa; schemas do Pydantic e objetos do domínio ficam duplicados, com código de mapeamento no adapter HTTP; a regra de dependência se quebra com um import só, então precisa de um teste de arquitetura para se manter.
- **Na prática:**
  - O domínio só importa a biblioteca padrão (backend) ou nada do Angular (frontend).
  - Pydantic só em `adapters/inbound/http`; PyTorch e `kanjilens_ml` só em `adapters/outbound/recognizer`.
  - **Atualização de 2026-11-08 ([ADR 0012](0012-ordered-mode-as-stroke-order-evaluation.md)):** o `kanjilens_ml` também entra no adapter outbound do avaliador da ordem (port proposto `StrokeOrderEvaluator`), que não usa PyTorch. O PyTorch continua só no recognizer.
  - Componente nunca injeta `HttpClient`; os adapters são ligados aos ports em `app.config.ts`.
  - `bootstrap/` é o único módulo do backend que conhece adapters concretos.
  - Cada parte ganha um teste de arquitetura (uma regra de import que falha) junto com o primeiro código; a ferramenta é escolhida na ADR de ferramentas da etapa.
- **Atualização de 2026-11-08 ([ADR 0019](0019-in-memory-job-queue-with-one-inference-process.md) e [ADR 0020](0020-result-notification-by-server-sent-events.md)):** as duas decisões em aberto do contexto foram fechadas. A fila é `asyncio.Queue` limitada, com um processo de inferência, e o resultado volta por SSE. Os ports continuam os mesmos, e trocar a fila ou o canal segue sendo trocar um adapter. O teste de arquitetura existe nas três partes: Import Linter no ML e no backend (ADRs [0014](0014-ml-tooling-python-uv-ruff-pytest-import-linter.md) e [0015](0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md)) e `eslint-plugin-boundaries` no frontend ([ADR 0017](0017-frontend-tooling-angular-localize-vitest-eslint-boundaries.md)).

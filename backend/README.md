# kanjilens (backend)

Backend do KanjiLens: a API FastAPI, os jobs de reconhecimento, a fila e o processo de inferência ([ADR 0019](../docs/adr/0019-in-memory-job-queue-with-one-inference-process.md)), a notificação por SSE ([ADR 0020](../docs/adr/0020-result-notification-by-server-sent-events.md)), em Clean Architecture com ports and adapters ([ADR 0004](../docs/adr/0004-clean-and-hexagonal-architecture.md)).

As ferramentas estão na [ADR 0015](../docs/adr/0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md); os comandos, no [`CLAUDE.md`](../CLAUDE.md#comandos); as regras do backend, na skill `fastapi-conventions`.

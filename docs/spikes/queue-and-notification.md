# Spike: fila de jobs e notificação do resultado

> **Issues:** [#20](https://github.com/Asuka-Jyuku/kanji-lens/issues/20) (fila) e [#19](https://github.com/Asuka-Jyuku/kanji-lens/issues/19) (SSE × WebSocket)  
> **Tipo:** spike técnico (pesquisa e protótipo)  
> **Status:** decidido nas ADRs [0019](../adr/0019-in-memory-job-queue-with-one-inference-process.md) (fila) e [0020](../adr/0020-result-notification-by-server-sent-events.md) (notificação)  
> **Data:** 2026-11-08

---

## 1. Perguntas

- **#20:** a primeira versão usa `asyncio.Queue` no mesmo processo ou Redis com Celery/RQ? E como o job chega ao processo de inferência sem travar o event loop do FastAPI ([ADR 0011](../adr/0011-school-notebook-as-server-with-cpu-first-inference.md))?
- **#19:** o resultado volta ao navegador por SSE ou por WebSocket?

## 2. O que pesou

**Ambiente:** o notebook da escola roda **Windows**, sem Docker ([ADR 0013](../adr/0013-run-directly-on-the-school-notebook-without-docker.md)). A carga é de 3–5 alunos numa janela curta, com 10 clientes como estresse, e uma inferência ativa por vez ([ADR 0011](../adr/0011-school-notebook-as-server-with-cpu-first-inference.md)).

**Fila**, conferido nas fontes em 2026-11-08:

| Opção | No Windows | Observação |
|---|---|---|
| Redis | **sem versão nativa oficial**: o redis.io indica o Memurai (parceiro comercial) ou o WSL | o WSL é uma VM Linux, a mesma camada que a ADR 0013 evitou |
| RQ | **o worker padrão depende de `fork()`**, que o Windows não tem; a própria documentação manda usar `SimpleWorker` com outro mecanismo de timeout | o pacote `rq-win` existe, mas se declara só para desenvolvimento |
| Celery | **a documentação diz que não suporta Windows** | funciona com `--pool=solo` ou `threads`, sem garantia |
| `asyncio.Queue` + `ProcessPoolExecutor` | biblioteca padrão; no Windows o processo filho nasce por `spawn` | um processo só para a API, e os jobs somem se ele reiniciar |

**Notificação:**

| Opção | Observação |
|---|---|
| **SSE** | O FastAPI tem suporte nativo desde a 0.135 (`fastapi.sse.EventSourceResponse`), e o projeto está na 0.162.2. Ele já manda um `ping` a cada 15 s, `Cache-Control: no-cache` e `X-Accel-Buffering: no`. No navegador, o `EventSource` é nativo e reconecta sozinho. É HTTP comum, sem upgrade de protocolo |
| WebSocket | Bidirecional. Precisa de reconexão manual no navegador e de outro protocolo. O caso do KanjiLens é de uma via só, "o job terminou", uma vez por job |
| Polling | O mais simples, mas atrasa o resultado e gasta requisições. Fica como **reserva** (`GET /api/recognitions/{id}`), se o SSE cair |

## 3. Protótipo

Descartável, fora do repositório, com Python 3.13, FastAPI 0.162.2, Uvicorn 0.54 e `httpx2` 2.16.

- **API:** FastAPI num processo só.
- **Fila:** `asyncio.Queue(maxsize=8)`. Cheia, o `POST` responde `503` com `Retry-After`.
- **Consumidor:** uma tarefa que pega um job por vez e roda a inferência por `run_in_executor` num `ProcessPoolExecutor(max_workers=1)`, criado com o contexto **`spawn`**, como acontece no Windows. O `initializer` "carrega o modelo" uma vez (2 s de CPU).
- **Inferência:** 0,3 s de CPU por job, imitando a CNN mais a avaliação da ordem.
- **SSE:** `GET /api/recognitions/{id}/events` com `EventSourceResponse`. Cada mudança de estado manda o estado completo do job (`queued`, `processing`, `completed`), e o stream termina no estado final.
- **Carga:** N clientes enviam ao mesmo tempo e escutam o próprio SSE. Em paralelo, um cliente chama `/api/health` a cada 50 ms.

| Clientes | Aceitos | Recusados (`503`) | Envio → resultado (p50 / máx.) | `/api/health` durante a carga (p95) |
|---:|---:|---:|---:|---:|
| 1 | 1 | 0 | 0,31 s / 0,31 s | 2,8 ms |
| 3 | 3 | 0 | 0,61 s / 0,91 s | 2,3 ms |
| 5 | 5 | 0 | 0,91 s / 1,51 s | 2,4 ms |
| 10 | 8 | 2 | 1,36 s / 2,42 s | 2,7 ms |
| 20 | 8 | 12 | 1,38 s / 2,43 s | 3,0 ms |

**Leitura:**
- **A API e o SSE continuam respondendo durante a inferência** (`/api/health` em cerca de 3 ms no p95), porque o trabalho de CPU roda em outro processo. É o que a ADR 0011 pede.
- **Com uma inferência por vez, o tempo cresce de forma linear com a fila:** o quinto aluno de uma rajada espera os quatro anteriores (cerca de 1,5 s com 0,3 s por job).
- **A fila limitada protege o processo:** passou do limite, `503`. Com limite 8, o estresse de 10 clientes já teve 2 recusas. O limite inicial proposto é **16** (cerca de 5 s de espera no pior caso com 0,3 s por job), a revisar com o tempo real do modelo.
- **Reconexão sem cabeçalho extra:** um evento com o estado completo é idempotente. Quem reconecta recebe o estado atual, sem precisar do `Last-Event-ID`.

**Limitações:**
- O protótipo rodou no Linux, com `spawn` forçado, e a inferência foi um laço de CPU. O tempo real do modelo e o comportamento no notebook Windows ficam para o benchmark e o teste de carga.
- O protótipo não entra no repositório. A implementação sai nas histórias do backend.

## 4. Recomendação

- **#20:** `asyncio.Queue` limitada, com **um processo de inferência** (`ProcessPoolExecutor` de 1 processo, `spawn`, modelo e KanjiVG carregados uma vez no `initializer`). Jobs e resultados em memória, com expiração. O Uvicorn roda com um processo só. Redis, RQ e Celery ficam de fora enquanto o servidor for o notebook Windows.
- **#19:** **SSE** nativo do FastAPI, com eventos de estado completo, e polling como reserva. WebSocket fica de fora.

Fontes:
- [redis.io: Install Redis on Windows](https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/install-redis-on-windows/)
- [RQ: Testing (Windows e `SimpleWorker`)](https://python-rq.org/docs/testing)
- [rq-win](https://pypi.org/project/rq-win/)
- [Celery: Introduction (Windows)](https://sources.debian.org/src/celery/5.5.3-4/docs/getting-started/introduction.rst)
- [FastAPI: Server-Sent Events](https://fastapi.tiangolo.com/pt/tutorial/server-sent-events/)
- [HTML: Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html)

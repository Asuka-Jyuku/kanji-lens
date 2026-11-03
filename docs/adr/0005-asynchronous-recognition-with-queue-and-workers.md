# 0005. Reconhecimento assíncrono com fila de jobs e workers

- **Status:** Aceita
- **Data:** 2026-11-03
- **Relacionadas:** [0004](0004-clean-and-hexagonal-architecture.md), [0006](0006-cnn-with-pytorch.md)

## Contexto

A inferência da CNN é CPU/GPU-bound, e a duração cresce com a quantidade de classes e com o hardware do servidor. O app precisa atender cerca de 10 usuários simultâneos numa máquina só. Se a requisição HTTP esperasse a inferência, requisições lentas se acumulariam e prenderiam conexões. Decisão registrada depois do fato, a partir do [ARCHITECTURE.md](../ARCHITECTURE.md) (seções 2.2 e 3 do commit `d72a4d4`).

## Alternativas consideradas

- **Inferência síncrona na requisição** — a mais simples; a requisição fica aberta durante toda a inferência e, no event loop do FastAPI, bloqueia todas as outras, inclusive o SSE.
- **Inferência síncrona num thread pool** (`run_in_threadpool`) — libera o loop; ainda prende a conexão à inferência, sem fila para limitar a carga e sem job para consultar. *Inferido:* não discutido explicitamente.
- **Fila de jobs com workers** — a API responde na hora com um `job_id`; os workers consomem a fila, cada um com o modelo carregado uma vez; o resultado é notificado ou consultado; custa um armazenamento de jobs, um canal de notificação e estados de job.

## Decisão

Processamos o reconhecimento de forma assíncrona: `POST /api/recognitions` cria um job, coloca na fila e responde `queued` com um `job_id`; os workers rodam a inferência com o modelo carregado uma vez por worker; o resultado é enviado ao cliente (SSE ou WebSocket, em aberto), com `GET /api/recognitions/{id}` como fallback por polling. **Qual fila** (`asyncio.Queue` ou Redis + Celery/RQ) continua em aberto, atrás do port `JobQueue`.

## Consequências

- **Positivas:** as requisições HTTP ficam curtas, qualquer que seja o tempo de inferência; a quantidade de workers limita o uso de CPU/GPU; o modelo de job deixa espaço para progresso e cancelamento depois.
- **Negativas:** mais peças que uma chamada síncrona (estados do job, armazenamento, notificação, expiração); com `asyncio.Queue`, fila e resultados vivem num processo só, então o Uvicorn precisa rodar **um processo só** (`--workers 1`) até o Redis; a inferência ainda tem de rodar fora do event loop (`run_in_executor`), e `torch.set_num_threads` precisa de ajuste quando vários workers dividem um processo.
- **Na prática:** use cases `SubmitRecognition`, `GetRecognition` e `ProcessRecognition` atrás dos ports `JobQueue`, `JobRepository`, `KanjiRecognizer` e `ResultNotifier` (ADR 0004); a fila tem tamanho máximo e responde `503` quando cheia (`CLAUDE.md`, "Segurança"); os resultados dos jobs expiram.

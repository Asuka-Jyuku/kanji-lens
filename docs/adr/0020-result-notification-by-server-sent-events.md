# 0020. Notificação do resultado por SSE, com polling como reserva

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0003](0003-angular-frontend-and-fastapi-backend.md), [0004](0004-clean-and-hexagonal-architecture.md), [0005](0005-asynchronous-recognition-with-queue-and-workers.md), [0015](0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md), [0019](0019-in-memory-job-queue-with-one-inference-process.md)

## Contexto

O `POST /api/recognitions` responde na hora com o `job_id` ([ADR 0005](0005-asynchronous-recognition-with-queue-and-workers.md)), e o resultado sai depois, do processo de inferência ([ADR 0019](0019-in-memory-job-queue-with-one-inference-process.md)). Como avisar o navegador estava em aberto: SSE ou WebSocket ([#19](https://github.com/Asuka-Jyuku/kanji-lens/issues/19)).

O caso é de **uma via só, uma vez por job**: o servidor avisa que o job foi para `processing` e depois para `completed` ou `failed`. O frontend roda no celular, na rede local, e pode perder a conexão.

O [spike](../spikes/queue-and-notification.md) conferiu duas coisas:
- **O FastAPI tem SSE nativo desde a 0.135** (`fastapi.sse.EventSourceResponse`), e o projeto está na 0.162.2. Ele já manda um `ping` de keep-alive a cada 15 s, além de `Cache-Control: no-cache` e `X-Accel-Buffering: no`.
- **O protótipo funcionou:** entregou `queued`, `processing` e `completed` a 5 clientes simultâneos, sem atrasar a API.

## Alternativas consideradas

- **WebSocket:** bidirecional, o que o KanjiLens não precisa. Usa outro protocolo (upgrade), a reconexão é feita à mão no navegador, e precisaria de uma dependência ou de mais código no Angular.
- **Só polling** (`GET /api/recognitions/{id}` a cada N segundos): o mais simples, mas o resultado chega atrasado, há requisições desnecessárias, e mais carga com vários alunos.
- **SSE (`EventSource`) com polling como reserva:** nativo dos dois lados, HTTP comum, com reconexão automática no navegador. Mantém uma conexão aberta por job enquanto ele não termina.

## Decisão

- **Endpoint:** `GET /api/recognitions/{id}/events`, com `EventSourceResponse` do FastAPI.
  - O stream manda **um evento por mudança de estado**, com o nome do estado (`event: queued | processing | completed | failed`) e o **estado completo do job** em `data`, no mesmo formato do `GET /api/recognitions/{id}`.
  - O stream termina no estado final.
  - Job inexistente ou expirado responde `404` com `job_not_found`.
- **Reconexão:** como cada evento traz o estado completo, quem reconecta recebe o estado atual, sem `Last-Event-ID`.
- **Polling como reserva:** `GET /api/recognitions/{id}` devolve o estado atual. O frontend usa o polling quando o `EventSource` falha repetidamente.
- **No frontend:** o adapter `SseResultStream` (infrastructure) implementa o port `ResultStream` com o `EventSource` nativo. Ele fecha a conexão no estado final ou quando a tela é destruída, e entrega o estado como signal para a camada de aplicação ([ADR 0004](0004-clean-and-hexagonal-architecture.md)).
- **WebSocket fica de fora.** Volta só se surgir comunicação bidirecional, como cancelar um job ou mostrar progresso fino, com uma ADR nova.

## Consequências

- **Positivas:**
  - nenhuma dependência nova, nem no backend nem no frontend;
  - HTTP comum, então passa pelo mesmo caminho da API (mesma origem em produção, sem CORS);
  - a reconexão é automática e sem estado no servidor;
  - o resultado chega assim que o job termina;
  - o polling garante o resultado mesmo se o SSE não funcionar em algum aparelho.
- **Negativas:**
  - **Uma conexão aberta por job até o fim.** Em HTTP/1.1, o navegador limita as conexões por origem (cerca de 6), então várias abas do mesmo aparelho com jobs abertos podem esbarrar nesse limite. Com um job por vez por aluno, isso não deve ocorrer (*a verificar* no teste com celulares).
  - **Proxy na frente da API**, se houver, precisa não fazer buffering da resposta. O FastAPI já manda o cabeçalho para o Nginx, e outro proxy precisa ser conferido.
  - **Dois caminhos para o mesmo dado** (SSE e polling): o formato do estado precisa ser um só e testado nos dois.
- **Na prática:**
  - o contrato (endpoint, nomes dos eventos, formato do estado) fica no ARCHITECTURE.md, seção 5;
  - o use case `GetRecognition` serve aos dois caminhos;
  - o notifier (`ResultNotifier`) avisa as conexões abertas quando o estado muda;
  - os testes do backend usam o test client do FastAPI lendo o stream até o estado final.
- *Atualização de 2026-11-08 (#47), detalhes da implementação:*
  - **Inscrever antes de ler.** O stream se inscreve no notifier (`InMemoryResultNotifier`, uma fila por conexão) e só então lê o estado atual pelo `GetRecognition`. Assim nenhuma mudança cai entre a leitura e a espera. Uma mudança lida e também avisada não sai duas vezes: o stream só manda um evento quando o estado muda.
  - **O `ProcessRecognition` grava e depois avisa.** Quem é avisado nunca lê um estado mais antigo do que o do aviso.
  - **O `404` sai antes de o stream abrir.** O job é conferido numa dependência da rota. O cliente recebe `404` com `job_not_found`, e não um stream vazio.
  - **Cliente que desconecta** fecha o gerador, e a inscrição sai junto. Nada fica pendurado.
  - **Campo que não se aplica não vem**, nem como `null` (ARCHITECTURE.md, seção 2.2). O `GET` e o SSE usam o mesmo schema (`RecognitionStateResponse`).
  - **O lado do stream lê o notifier por um `Protocol` local** (`JobUpdates`). O port `ResultNotifier` é o que o use case precisa, e ele só avisa.

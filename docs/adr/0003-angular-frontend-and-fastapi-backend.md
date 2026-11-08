# 0003. Frontend em Angular e backend em FastAPI, conversando por REST

- **Status:** Aceita
- **Data:** 2026-11-03
- **Relacionadas:** [0005](0005-asynchronous-recognition-with-queue-and-workers.md), [0006](0006-cnn-with-pytorch.md), [0020](0020-result-notification-by-server-sent-events.md)

## Contexto

O app precisa de uma interface web com um canvas de desenho que funcione com mouse e com touch no celular, e de um servidor que rode um modelo PyTorch. O modelo é em Python, então o código de inferência é em Python, qualquer que seja o framework web. Decisão registrada depois do fato, a partir do [ARCHITECTURE.md](../ARCHITECTURE.md) (seções 2 e 4 do commit `d72a4d4`).

## Alternativas consideradas

- **Frontend: Angular** — estrutura opinativa (DI, rotas, cliente HTTP tipado), que se encaixa no desenho em camadas da ADR 0004; mais pesado que as alternativas para uma tela só. *Inferido:* escolhido também porque o time já conhece.
- **Frontend: React ou TypeScript puro** — mais leve para uma tela; sem DI embutida, então ports e adapters precisariam de ligação feita à mão. *Inferido:* não avaliado a fundo.
- **Backend: FastAPI** — assíncrono por padrão, o que combina com a fila de jobs e com SSE; validação com Pydantic e especificação OpenAPI de graça; a mesma linguagem do modelo.
- **Backend: Flask ou Django** — maduros; o Flask é síncrono por padrão, e o Django traz ORM e admin de que o projeto não precisa. *Inferido.*
- **Protocolo: REST × SOAP** — o SOAP foi descartado por adicionar complexidade sem benefício aqui. O **gRPC** é *inferido* como não considerado: o navegador não o chama sem um proxy.

## Decisão

Usamos Angular com TypeScript no frontend e Python com FastAPI no backend, conversando por REST (mais SSE ou WebSocket para notificar o resultado, ainda em aberto). Python no servidor deixa a inferência na mesma linguagem do modelo.

## Consequências

- **Positivas:** uma linguagem só entre treino e inferência; endpoints assíncronos e SSE são nativos do FastAPI; a DI do Angular corresponde direto a ports e adapters.
- **Negativas:** dois ecossistemas para manter (Node e Python), com ferramentas e atualizações próprias; o Angular é mais framework do que um app de uma tela precisa; o servidor de desenvolvimento do frontend e a API são origens diferentes, então é preciso CORS ou proxy (ADR 0007).
- **Na prática:** o contrato da API é a especificação OpenAPI gerada pelo FastAPI; o frontend só chega a ela pelos adapters de `infrastructure/`; as ferramentas de cada stack são escolhidas numa ADR no começo da etapa.
- **Atualização de 2026-11-08 ([ADR 0020](0020-result-notification-by-server-sent-events.md)):** a notificação do resultado é por **SSE**, com o `GET /api/recognitions/{id}` como reserva. O WebSocket ficou de fora. As ferramentas de cada stack estão nas ADRs [0014](0014-ml-tooling-python-uv-ruff-pytest-import-linter.md), [0015](0015-backend-tooling-fastapi-uvicorn-on-the-uv-workspace.md) e [0017](0017-frontend-tooling-angular-localize-vitest-eslint-boundaries.md).

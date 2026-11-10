# Estilo do backend no projeto

O que se espera de Python e FastAPI idiomáticos aqui, com a fonte de cada ponto. As regras de camada estão na ADR 0004 e não se repetem aqui.

## O que seguimos

| Ponto | Como fica aqui | Fonte |
|---|---|---|
| Ports | `typing.Protocol`, pequenos, declarados em `application/ports/`, com duas implementações de verdade (o adapter e o fake do teste) | [PEP 544](https://peps.python.org/pep-0544/), ADR 0004 |
| Tipos do domínio | `@dataclass(frozen=True)` para value objects, `enum.Enum` (`StrEnum`) para `JobStatus`; nada de Pydantic no domínio | [dataclasses](https://docs.python.org/3/library/dataclasses.html), ADR 0004 |
| Use cases | Uma classe por ação, ports injetados pelo `__init__`, um método público (`execute` ou `__call__`) | ADR 0004 |
| Ligação das rotas | O adapter inbound expõe uma fábrica de router que recebe os use cases já montados (`recognitions_router(submit_recognition)`), e o `bootstrap/` a chama; a rota nunca monta adapter. `Depends` fica para dados da própria requisição | ADR 0004; [FastAPI: bigger applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) |
| Schemas | Pydantic `XxxRequest`/`XxxResponse` em `adapters/inbound/http/`, mapeados explicitamente de e para os tipos do domínio | [FastAPI: response model](https://fastapi.tiangolo.com/tutorial/response-model/) |
| Erros | O domínio lança exceções de domínio (`JobNotFound`, `QueueFull`); o adapter HTTP as converte em status com os exception handlers de `adapters/inbound/http/errors.py`, e o corpo é sempre `{"error": "<código>"}`, com um **código estável** (`job_not_found`, `queue_full`, `invalid_drawing`). Erro de validação do schema vira `400` ou `413` com código, nunca o `422` padrão do FastAPI (ARCHITECTURE.md, seção 5.3). Texto para o usuário nunca sai do backend: o frontend traduz o código (ADR 0009) | [FastAPI: handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/), ADR 0009 |
| Assíncrono | Rotas `async def`; **inferência CPU-bound nunca no event loop**: o consumidor da fila a manda por `run_in_executor` para o **processo de inferência**, um `ProcessPoolExecutor(max_workers=1)` com contexto `spawn` explícito | [asyncio: run_in_executor](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor), ADR 0019 |
| Fronteira entre processos | O que vai para o processo de inferência e o que volta passa por pickle: traços como listas, resultados como tipos simples ou dataclasses do domínio, nunca tensores nem objetos do PyTorch. A função chamada no pool é de nível de módulo (o `spawn` a importa pelo nome). `BrokenProcessPool` vira `failed` no job e recria o pool | [concurrent.futures: ProcessPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor), ADR 0019 |
| Ciclo de vida | No `lifespan` do FastAPI, ligado em `bootstrap/`: criar o processo de inferência (o `initializer` carrega o modelo e as referências do KanjiVG uma vez), iniciar a tarefa consumidora da fila e, no fim, cancelá-la e fechar o pool | [FastAPI: lifespan events](https://fastapi.tiangolo.com/advanced/events/), ADR 0019 |
| SSE | `EventSourceResponse` do FastAPI com um gerador `async`: um `ServerSentEvent` por mudança de estado, `event` com o estado e `data` com o estado completo do job (o mesmo schema do `GET`), terminando no estado final | [FastAPI: Server-Sent Events](https://fastapi.tiangolo.com/tutorial/server-sent-events/), ADR 0020 |
| Configuração | Lida de variáveis de ambiente só em `bootstrap/` e passada adiante como valores simples | ADR 0004 |
| Tipos | Type hints em toda função pública; o type checker da ADR de ferramentas roda limpo | [PEP 484](https://peps.python.org/pep-0484/) |
| Schema da entrada | Números com `StrictFloat`/`StrictInt` (texto ou booleano não vira coordenada), `extra="forbid"` e `max_length` com os limites do domínio; o modelo inteiro fica no modo normal, porque o FastAPI valida o JSON já convertido (modo Python), em que o estrito recusa lista no lugar de tupla e texto no lugar de enum | [Pydantic: strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) |
| Fakes | Os fakes dos ports ficam em `backend/tests/fakes.py` (`from fakes import ...`), compartilhados pelos testes | `CLAUDE.md`, "Testes" |
| Log | `logging`, com o `job_id` em toda mensagem sobre um job, em inglês; nunca logar os bytes do desenho | — (julgamento) |

## O que evitamos

- Import de FastAPI, Pydantic, PyTorch ou `kanjilens_ml` em `domain/` ou `application/`.
- Singletons globais para o modelo ou a fila: são montados uma vez em `bootstrap/` e injetados.
- `uvicorn --workers > 1` enquanto a fila for `asyncio.Queue` (ADR 0019).
- Thread pool para a inferência: o PyTorch e a avaliação da ordem disputariam o GIL e a CPU com a API (ADR 0019).
- WebSocket para o resultado: o canal é o SSE (ADR 0020).
- Aceitar um desenho antes de conferir tamanho e formato ([`docs/SECURITY.md`](../../../../docs/SECURITY.md), "Limites de entrada").

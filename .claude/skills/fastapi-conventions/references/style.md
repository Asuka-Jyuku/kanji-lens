# Estilo do backend no projeto

O que se espera de Python e FastAPI idiomáticos aqui, com a fonte de cada ponto. As regras de camada estão na ADR 0004 e não se repetem aqui.

## O que seguimos

| Ponto | Como fica aqui | Fonte |
|---|---|---|
| Ports | `typing.Protocol`, pequenos, declarados em `application/ports/`, com duas implementações de verdade (o adapter e o fake do teste) | [PEP 544](https://peps.python.org/pep-0544/), ADR 0004 |
| Tipos do domínio | `@dataclass(frozen=True)` para value objects, `enum.Enum` (`StrEnum`) para `JobStatus`; nada de Pydantic no domínio | [dataclasses](https://docs.python.org/3/library/dataclasses.html), ADR 0004 |
| Use cases | Uma classe por ação, ports injetados pelo `__init__`, um método público (`execute` ou `__call__`) | ADR 0004 |
| DI do FastAPI | `Depends` só nos adapters inbound, para pegar um use case já montado no container de `bootstrap/`; nunca para montar adapter dentro da rota | [FastAPI: dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) |
| Schemas | Pydantic `XxxRequest`/`XxxResponse` em `adapters/inbound/http/`, mapeados explicitamente de e para os tipos do domínio | [FastAPI: response model](https://fastapi.tiangolo.com/tutorial/response-model/) |
| Erros | O domínio lança exceções de domínio (`JobNotFound`, `QueueFull`); o adapter HTTP as converte em status com exception handlers, e o corpo leva um **código estável** (`job_not_found`, `queue_full`, `invalid_drawing`). Texto para o usuário nunca sai do backend: o frontend traduz o código (ADR 0009) | [FastAPI: handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/), ADR 0009 |
| Assíncrono | Rotas `async def`; **inferência CPU-bound nunca no event loop**: `run_in_executor` (thread ou process pool) no adapter do worker | [asyncio: run_in_executor](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor), ADR 0005 |
| Ciclo de vida | Carregar o modelo e as referências do KanjiVG e iniciar/parar os workers no `lifespan` do FastAPI, ligado em `bootstrap/` | [FastAPI: lifespan events](https://fastapi.tiangolo.com/advanced/events/) |
| Configuração | Lida de variáveis de ambiente só em `bootstrap/` e passada adiante como valores simples | ADR 0004 |
| Tipos | Type hints em toda função pública; o type checker da ADR de ferramentas roda limpo | [PEP 484](https://peps.python.org/pep-0484/) |
| Log | `logging`, com o `job_id` em toda mensagem sobre um job, em inglês; nunca logar os bytes do desenho | — (julgamento) |

## O que evitamos

- Import de FastAPI, Pydantic, PyTorch ou `kanjilens_ml` em `domain/` ou `application/`.
- Singletons globais para o modelo ou a fila: são montados uma vez em `bootstrap/` e injetados.
- `uvicorn --workers > 1` enquanto a fila for `asyncio.Queue` (ADR 0005).
- Aceitar um desenho antes de conferir tamanho e formato (`CLAUDE.md`, "Segurança").

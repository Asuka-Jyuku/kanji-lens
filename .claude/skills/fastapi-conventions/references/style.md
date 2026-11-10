# Estilo do backend no projeto

As regras de camada estão na ADR 0004 e não se repetem aqui.

## O que seguimos

| Ponto | Como fica aqui | Fonte |
|---|---|---|
| Ports | `typing.Protocol` pequeno, em `application/ports/`, só quando há uma segunda implementação real; valor simples (o horário) entra como parâmetro | [PEP 544](https://peps.python.org/pep-0544/), ADR 0004 |
| Domínio | `@dataclass(frozen=True)` e `StrEnum`; nada de Pydantic | ADR 0004 |
| Use cases | Uma classe por ação, dependências pelo `__init__`, um método público | ADR 0004 |
| Rotas | Uma fábrica de router recebe os use cases montados em `bootstrap/`; `Depends` só para dados da requisição | [FastAPI](https://fastapi.tiangolo.com/tutorial/bigger-applications/) |
| Schemas | Pydantic `XxxRequest`/`XxxResponse` em `adapters/inbound/http/`, mapeados para o domínio | [FastAPI](https://fastapi.tiangolo.com/tutorial/response-model/) |
| Erros | O domínio lança erro com **código estável** (`job_not_found`, `queue_full`); o adapter HTTP vira status com corpo `{"error": "<código>"}`. Validação vira `400` ou `413`, nunca o `422` padrão. O texto para o usuário sai do frontend | ADR 0009 |
| Assíncrono | Rotas `async def`; **inferência nunca no event loop**: vai para o processo de inferência (`ProcessPoolExecutor(max_workers=1)`, `spawn`) | ADR 0019 |
| Fronteira entre processos | Só o que o pickle leva: listas e tipos simples, nunca tensores. Função do pool de nível de módulo. `BrokenProcessPool` vira `failed` e recria o pool | ADR 0019 |
| Ciclo de vida | No `lifespan`: subir o processo de inferência (o `initializer` carrega o modelo uma vez) e o consumidor da fila; no fim, parar os dois | [FastAPI](https://fastapi.tiangolo.com/advanced/events/) |
| SSE | `EventSourceResponse`: um evento por estado, com o estado completo (o mesmo schema do `GET`), até o estado final | ADR 0020 |
| Entrada | `StrictFloat`/`StrictInt`, `extra="forbid"` e `max_length` com os limites do domínio | [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) |
| Configuração | Variáveis de ambiente lidas só em `bootstrap/` | ADR 0004 |
| Fakes | Em `backend/tests/fakes.py`, compartilhados | `CLAUDE.md`, "Testes" |
| Log | `logging`, em inglês, com o `job_id`; nunca os bytes do desenho | julgamento |

## O que evitamos

- FastAPI, Pydantic, PyTorch ou `kanjilens_ml` em `domain/` ou `application/`.
- Singleton global para o modelo ou a fila: monte em `bootstrap/` e injete.
- `uvicorn --workers` maior que 1 com a fila em memória.
- Thread pool para a inferência: disputaria a CPU com a API.
- WebSocket para o resultado: o canal é o SSE.
- Aceitar um desenho antes de conferir tamanho e formato ([`docs/SECURITY.md`](../../../../docs/SECURITY.md)).
- Port, camada ou teste "para o futuro".

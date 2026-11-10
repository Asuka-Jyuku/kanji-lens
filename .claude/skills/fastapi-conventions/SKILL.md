---
name: fastapi-conventions
description: Como se escreve o backend do KanjiLens (backend/, Python + FastAPI) — use case, port, adapter inbound (rota HTTP, SSE, consumidor da fila), adapter outbound (recognizer, avaliador da ordem, fila, armazenamento dos jobs, notifier), composition root, e revisão de PR com backend, seguindo Clean Architecture / ports and adapters, com a fonte de cada regra. Usar ao pedirem "endpoint novo", "use case", "port", "adapter", "worker", "fila", "SSE", "status do job", "revisa o backend", e ao pegar issue com a etiqueta backend ou que mexe em backend/.
model: sonnet
---

# FastAPI no KanjiLens

Para escrever e revisar o `backend/`. Cada regra mora num lugar só: aqui fica o caminho e a fonte. Se a skill divergir da fonte, vale a fonte, e a skill se corrige no mesmo PR.

| Assunto | Fonte |
|---|---|
| Camadas e o que cada uma importa | [ADR 0004](../../../docs/adr/0004-clean-and-hexagonal-architecture.md) e [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md) |
| Job, estados, fila de 16, um processo de inferência (`spawn`), modelo carregado uma vez | [ADR 0005](../../../docs/adr/0005-asynchronous-recognition-with-queue-and-workers.md) e [ADR 0019](../../../docs/adr/0019-in-memory-job-queue-with-one-inference-process.md) |
| Endpoints, SSE nativo do FastAPI, polling de reserva | [ADR 0020](../../../docs/adr/0020-result-notification-by-server-sent-events.md) |
| Limites de entrada, CORS, nenhuma saída de rede | [`docs/SECURITY.md`](../../../docs/SECURITY.md) |
| O recognizer, o avaliador da ordem e o `kanjilens_ml` | skill `ml-conventions`, "Inferência" |
| Testes, commits, CHANGELOG | `CLAUDE.md` e `CONTRIBUTING.md` |

## Referências

| Arquivo | Quando ler |
|---|---|
| [`references/style.md`](references/style.md) | antes de escrever código |
| [`references/examples.md`](references/examples.md) | antes de escrever um tipo novo: o código que serve de modelo |
| [`references/review.md`](references/review.md) | ao revisar um PR e no fim do seu trabalho |

## Funcionalidade nova

1. **Issue e branch** como em todo PR.
2. **Domínio:** a regra em Python puro em `domain/`, testada sozinha.
3. **Use case** em `application/use_cases/` quando há regra para orquestrar; uma leitura simples não precisa de um.
4. **Port só com uma segunda implementação real** (o fake do teste não conta). Os ports que existem ficam, sem ganhar irmãos. Valor simples, como o horário, entra como parâmetro (`now`), não como port.
5. **Adapters:** a rota com os schemas Pydantic e o mapeamento para o domínio; o erro do domínio vira status HTTP aqui.
6. **Ligação** só em `bootstrap/`.
7. **Testes** de comportamento: o domínio direto, o use case com fakes, o endpoint pelo `TestClient`, os erros (`400`, `413`, `404`, `503`). Nada de teste que só confere uma constante ou a montagem do app.

## Mudança em código que já existe

- Leia o módulo e os testes antes; siga a forma dele.
- Não refatore de carona: liste o que achar fora do pedido.
- Bug corrigido ganha teste que falhava antes.

## Antes de dizer que terminou

- **Comandos** do `CLAUDE.md`: `ruff check` e `ruff format --check` na raiz; `mypy`, `pytest` e `lint-imports` com `--directory backend`. Mudou o `kanjilens_ml`? Rode também com `--directory ml`. Sem Python disponível, diga isso e não afirme que passou.
- **Documentos:** atualize só o que ficou falso.

## Como entregar

- Separe o que você conferiu (`arquivo:linha`) do que é julgamento seu.
- Diga o que rodou e o resultado, inclusive o que falhou, e o que ficou de fora.
- Merge é decisão de quem pediu.

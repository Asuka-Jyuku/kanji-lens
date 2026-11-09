# Código que serve de modelo

Antes de escrever, abra o exemplo do mesmo tipo e siga a forma dele. Exemplo novo entra aqui no PR que cria o primeiro código daquele tipo.

| Tipo | Modelo | O que copiar |
|---|---|---|
| Value object que se valida ao nascer | `backend/src/kanjilens/domain/drawing.py` (`Drawing`) | `@dataclass(frozen=True, slots=True)`, regras no `__post_init__`, erro do domínio com código estável; limites como constante do domínio, reaproveitados pelo adapter |
| Entidade com estados | `backend/src/kanjilens/domain/job.py` (`RecognitionJob`) | transições como métodos que devolvem um objeto novo (`dataclasses.replace`), `InvalidJobTransition` para o resto, horário recebido de fora (sem relógio no domínio) |
| União de variantes | `backend/src/kanjilens/domain/stroke_order.py` (`StrokeOrderEvaluation`, `StrokeOrderIssue`) | `type X = A \| B` com dataclasses, `match` por classe, valor derivado como `property` (`correct`) em vez de campo |
| Erros do domínio | `backend/src/kanjilens/domain/errors.py` | uma classe por caso, herdando de `DomainError`, com `code` estável |
| Teste do domínio | `backend/tests/domain/test_job.py` | um teste por regra, `parametrize` com `id` legível para as transições proibidas, pickle de ida e volta do que cruza para o processo de inferência |
| Port | `backend/src/kanjilens/application/ports/job_repository.py` | `typing.Protocol` pequeno, só tipos do domínio, docstring dizendo o contrato (o que devolve quando não acha) |
| Use case | `backend/src/kanjilens/application/use_cases/submit_recognition.py` (`SubmitRecognition`) | ports pelo `__init__`, um método `execute`, horário vindo do `Clock`, desfazer o que fez quando um port falha (`QueueFull`) |
| Adapter inbound HTTP | `backend/src/kanjilens/adapters/inbound/http/recognitions.py` | schema Pydantic com `to_drawing()` para o domínio, fábrica de router recebendo o use case, `responses` com os códigos de erro |
| Erros na borda HTTP | `backend/src/kanjilens/adapters/inbound/http/errors.py` | erro do domínio → status, validação → `400`/`413` com código, corpo `{"error": "<código>"}` |
| Adapter outbound em memória | `backend/src/kanjilens/adapters/outbound/jobs/in_memory_job_repository.py` | implementa o port sem herdar dele, recebe o `Clock`, aplica a regra do domínio (`is_expired`) |
| Fakes dos ports | `backend/tests/fakes.py` | uma classe simples por port, com o estado à mostra para o teste conferir |
| Teste do use case | `backend/tests/application/test_submit_recognition.py` | só fakes, sem FastAPI |
| Teste do endpoint | `backend/tests/adapters/test_recognitions_endpoint.py` | `TestClient(create_app())`, um caso por status, `pytest.param(..., id=...)` dizendo de onde vem o erro (schema ou domínio) |
| Consumidor da fila, SSE | *a criar* (#46, #47) | — |

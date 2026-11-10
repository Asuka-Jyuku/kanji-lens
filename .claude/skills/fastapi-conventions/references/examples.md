# Código que serve de modelo

Antes de escrever, abra o exemplo do mesmo tipo e siga a forma dele. Os caminhos são de `backend/src/kanjilens/`, e os testes, de `backend/tests/`.

| Tipo | Modelo | O que copiar |
|---|---|---|
| Value object que se valida | `domain/drawing.py` (`Drawing`) | `@dataclass(frozen=True, slots=True)`, regras no `__post_init__`, erro com código estável; limites como constante, reaproveitados pelo schema |
| Entidade com estados | `domain/job.py` (`RecognitionJob`) | transições que devolvem um objeto novo, `InvalidJobTransition` para o resto, o horário vindo de fora |
| União de variantes | `domain/stroke_order.py` | `type X = A \| B` com dataclasses, `match` por classe, valor derivado como `property` |
| Erros do domínio | `domain/errors.py` | uma classe por caso, com `code` estável |
| Use case | `application/use_cases/submit_recognition.py` | dependências pelo `__init__`, um método `execute`, o horário de um `now` recebido, desfazer o que fez quando algo falha (`QueueFull`) |
| Use case que espera outro processo | `application/use_cases/process_recognition.py` | toda falha vira `failed` (nenhum job fica `processing` para sempre), o `job_id` no log |
| Rota HTTP | `adapters/inbound/http/recognitions.py` | schema com `to_drawing()`, fábrica de router que recebe o use case, `responses` com os erros |
| Erros na borda HTTP | `adapters/inbound/http/errors.py` | erro do domínio → status; validação → `400`/`413` com código; corpo `{"error": "<código>"}` |
| Schema de saída | `adapters/inbound/http/recognition_state.py` | `from_job()`, sem os `None`; o mesmo schema no `GET` e no SSE |
| SSE | `adapters/inbound/http/recognition_events.py` | `404` antes do stream; inscrever antes de ler; gerador testável sem HTTP |
| Processo de inferência | `adapters/outbound/inference/process.py` | `spawn` explícito, o `initializer` rodado no `start()`, `BrokenProcessPool` recria o pool |
| O que cruza processos | `adapters/outbound/recognizer/process_pool_recognizer.py` e `stroke_order/process_pool_evaluator.py` | a função do worker recebe o `Drawing` e devolve as classes do domínio, que passam pelo pickle; a conversão do resultado do ML para o domínio fica na própria função, dentro do worker |
| Ligação | `bootstrap/app.py` | `create_app(inference)` recebe as funções do worker; o teste passa as dele; o `/api/health` mora aqui |
| Fakes | `tests/fakes.py` | uma classe simples por port, com o estado à mostra |
| Teste do endpoint | `tests/adapters/test_recognitions_endpoint.py` | `TestClient(create_app())` sem subir o processo de inferência; um caso por status |
| Teste com o processo de verdade | `tests/adapters/test_app_lifespan.py` | as funções do worker em `tests/worker_functions.py`; derrubar o worker com `os._exit` |
| Teste do SSE | `tests/adapters/test_result_endpoints.py` | ler o stream numa thread com prazo, para não travar o CI |

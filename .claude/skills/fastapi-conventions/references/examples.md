# Código que serve de modelo

Antes de escrever, abra o exemplo do mesmo tipo e siga a forma dele. Exemplo novo entra aqui no PR que cria o primeiro código daquele tipo.

| Tipo | Modelo | O que copiar |
|---|---|---|
| Value object que se valida ao nascer | `backend/src/kanjilens/domain/drawing.py` (`Drawing`) | `@dataclass(frozen=True, slots=True)`, regras no `__post_init__`, erro do domínio com código estável; limites como constante do domínio, reaproveitados pelo adapter |
| Entidade com estados | `backend/src/kanjilens/domain/job.py` (`RecognitionJob`) | transições como métodos que devolvem um objeto novo (`dataclasses.replace`), `InvalidJobTransition` para o resto, horário recebido de fora (sem relógio no domínio) |
| União de variantes | `backend/src/kanjilens/domain/stroke_order.py` (`StrokeOrderEvaluation`, `StrokeOrderIssue`) | `type X = A \| B` com dataclasses, `match` por classe, valor derivado como `property` (`correct`) em vez de campo |
| Erros do domínio | `backend/src/kanjilens/domain/errors.py` | uma classe por caso, herdando de `DomainError`, com `code` estável |
| Teste do domínio | `backend/tests/domain/test_job.py` | um teste por regra, `parametrize` com `id` legível para as transições proibidas, pickle de ida e volta do que cruza para o processo de inferência |
| Use case, port, adapter | *a criar* (#45, #46, #47) | — |

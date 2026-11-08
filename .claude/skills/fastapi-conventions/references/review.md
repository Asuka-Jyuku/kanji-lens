# Revisão de código do backend

Use ao revisar um PR com backend e no fim do seu próprio trabalho. Cada achado sai com `arquivo:linha`, o que acontece de errado (entrada → resultado) e a fonte da regra; o que for gosto, sem fonte, diga que é julgamento.

## O que a CI já pega (não gaste a revisão nisso)

Ruff (lint e formatação), mypy strict, pytest e o teste de arquitetura (os seis contratos do Import Linter; ADRs 0015 e 0018), no Linux e no Windows. Se um deles falhou na CI, a revisão aponta o job; não reexplica a regra.

## O que só a revisão pega

**Camadas (ADR 0004)**
- [ ] `domain/` só importa a biblioteca padrão; `application/` só importa `domain/` e os próprios ports.
- [ ] Pydantic só em `adapters/inbound/http/`; PyTorch só em `adapters/outbound/recognizer/`; `kanjilens_ml` só nesse adapter e no do avaliador da ordem (ADRs 0004 e 0012).
- [ ] Adapters concretos só são citados em `bootstrap/`.
- [ ] Port novo tem um fake usado nos testes do use case.

**Regras e testes**
- [ ] Cada regra nova tem teste; use cases testados com fakes, não com patch de módulo.
- [ ] As transições de `JobStatus` são garantidas no domínio, com um teste para cada transição proibida.
- [ ] Bug corrigido com teste que falhava antes.

**Assíncrono e concorrência (ADRs 0005 e 0019)**
- [ ] A inferência roda no processo de inferência (`ProcessPoolExecutor` de 1 processo, `spawn`); nada CPU-bound num caminho `async def`, nem num thread pool.
- [ ] O que cruza para o processo de inferência é serializável por pickle (listas e tipos simples, nunca tensores); `BrokenProcessPool` deixa o job `failed` e recria o pool.
- [ ] O modelo e as referências do KanjiVG são carregados uma vez no processo de inferência, não por requisição; o job `ordered` também passa pela avaliação da ordem (ADRs 0011 e 0012).
- [ ] Threads do runtime configuradas explicitamente (`torch.set_num_threads` ou equivalente); mais de uma inferência simultânea só com medição no notebook da escola (ADR 0011).
- [ ] Nada supõe mais de um processo do Uvicorn enquanto a fila estiver em memória.
- [ ] O stream SSE manda o estado completo a cada mudança, termina no estado final e não deixa tarefa nem espera pendurada quando o cliente desconecta (ADR 0020).

**Segurança na rede local (`CLAUDE.md`, "Segurança")**
- [ ] Tamanho e formato do desenho (quantidade de traços e de pontos) e o `stroke_order_mode` conferidos antes de ir para a fila (`413` / `400`); o corpo continua limitado pelo `BodySizeLimitMiddleware` (1 MiB).
- [ ] A fila é limitada; fila cheia → `503` com `Retry-After`.
- [ ] O CORS só lista a origem do frontend, nunca `*`.
- [ ] Nenhuma saída de rede nova; resultados dos jobs e desenhos expiram.

**Contrato**
- [ ] O formato da resposta bate com o ARCHITECTURE.md, seções 2.2 e 5 (`job_id`, `status`, `predictions[].kanji`, `predictions[].confidence`, `stroke_order`, nomes dos eventos SSE); o SSE e o `GET` usam o mesmo schema; uma mudança atualiza o documento e o frontend no mesmo PR.
- [ ] Erro devolve `{"error": "<código>"}` com código estável (`queue_full`), nunca texto para o usuário nem o `422` do FastAPI; código novo entra no frontend, com a tradução, no mesmo PR (ADR 0009).

**Idioma (`CLAUDE.md`, "Idioma")**
- [ ] Código, nomes de arquivos, comentários e mensagens de log e de erro em inglês.

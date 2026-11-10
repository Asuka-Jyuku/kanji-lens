# Revisão do backend

Cada achado sai com `arquivo:linha`, o que dá errado (entrada → resultado) e a fonte. Sem fonte, diga que é julgamento.

**O CI já pega** Ruff, mypy strict, pytest e os contratos do Import Linter, no Linux e no Windows. Não gaste a revisão nisso.

## O que só a revisão pega

**Camadas (ADR 0004)**
- [ ] `domain/` só importa a biblioteca padrão; Pydantic só em `adapters/inbound/http/`; PyTorch e `kanjilens_ml` só no processo de inferência.
- [ ] Adapters concretos só aparecem em `bootstrap/`.
- [ ] Nenhum port, use case ou camada nova sem uma segunda implementação real.

**Testes**
- [ ] Regra nova com teste; use case testado com fakes, não com patch de módulo.
- [ ] Testes de comportamento, não de constante nem de montagem.
- [ ] Bug corrigido com teste que falhava antes.

**Processo de inferência (ADR 0019)**
- [ ] Nada CPU-bound num `async def` nem num thread pool.
- [ ] O que cruza processos passa pelo pickle (nada de tensores); `BrokenProcessPool` deixa o job `failed`.
- [ ] O modelo e o KanjiVG são carregados uma vez, no `initializer`.
- [ ] Nada supõe mais de um processo do Uvicorn.
- [ ] O SSE manda o estado completo, termina no estado final e não deixa tarefa pendurada quando o cliente sai.

**Segurança ([`docs/SECURITY.md`](../../../../docs/SECURITY.md))**
- [ ] Tamanho e formato do desenho conferidos antes da fila (`413`/`400`); corpo limitado a 1 MiB.
- [ ] Fila cheia → `503` com `Retry-After`.
- [ ] Nenhuma saída de rede nova; jobs e desenhos expiram.

**Contrato**
- [ ] A resposta bate com o `docs/ARCHITECTURE.md`; o `GET` e o SSE usam o mesmo schema; mudou o contrato, o frontend muda no mesmo PR.
- [ ] Erro devolve `{"error": "<código>"}` com código estável; código novo ganha tradução no frontend.
- [ ] Código, comentários e logs em inglês.

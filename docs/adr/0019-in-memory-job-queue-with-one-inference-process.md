# 0019. Fila em memória (`asyncio.Queue`) com um processo de inferência

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0004](0004-clean-and-hexagonal-architecture.md), [0005](0005-asynchronous-recognition-with-queue-and-workers.md), [0011](0011-school-notebook-as-server-with-cpu-first-inference.md), [0013](0013-run-directly-on-the-school-notebook-without-docker.md), [0020](0020-result-notification-by-server-sent-events.md)

## Contexto

A [ADR 0005](0005-asynchronous-recognition-with-queue-and-workers.md) decidiu o processamento assíncrono por fila e workers, mas deixou em aberto qual fila. A [ADR 0011](0011-school-notebook-as-server-with-cpu-first-inference.md) pede:
- um processo de inferência separado do event loop do FastAPI;
- o modelo e as referências do KanjiVG carregados uma vez;
- uma inferência ativa por vez no início;
- carga de 3–5 alunos numa janela curta, com 10 clientes como estresse.

O servidor é o notebook **Windows**, sem Docker ([ADR 0013](0013-run-directly-on-the-school-notebook-without-docker.md)).

O [spike da fila e da notificação](../spikes/queue-and-notification.md) ([#20](https://github.com/Asuka-Jyuku/kanji-lens/issues/20)) achou dois fatos que decidem a questão:
- **Redis, RQ e Celery ficam mal no Windows.** O Redis não tem versão nativa oficial (Memurai ou WSL). O worker padrão do RQ depende de `fork()`. O Celery não suporta Windows.
- **O protótipo com `asyncio.Queue` e um `ProcessPoolExecutor` de 1 processo (`spawn`) funcionou.** A API respondeu em cerca de 3 ms (p95) durante a inferência, a fila limitada recusou o excesso com `503`, e 5 clientes simultâneos tiveram o resultado em até 1,5 s, com 0,3 s por job.

## Alternativas consideradas

- **Redis + Celery ou RQ:** jobs persistentes e workers em processos independentes. No Windows, porém, exigem Memurai ou WSL, e o worker não tem suporte oficial ou precisa de modo alternativo. São mais serviços para instalar e manter no notebook, e mais memória disputando com o modelo.
- **Fila em SQLite (persistente, no mesmo processo):** sobrevive a reinícios, mas exige controlar concorrência e fazer polling do banco. Para jobs de segundos, o ganho é pequeno.
- **`asyncio.Queue` no processo da API e `ProcessPoolExecutor` para a inferência:** só biblioteca padrão, funciona igual no Linux e no Windows, e o modelo fica isolado num processo. Em compensação, jobs e resultados somem se a API reiniciar, e a API precisa rodar com um processo só.

## Decisão

- **Fila:** `asyncio.Queue` **limitada**, com tamanho inicial **16**, no processo da API. Cheia, o `POST /api/recognitions` responde **`503`** com `Retry-After` e o código `queue_full`.
- **Execução:** uma tarefa consumidora pega **um job por vez** e o executa por `run_in_executor` num **`ProcessPoolExecutor(max_workers=1)`**, criado explicitamente com o contexto `spawn` (o padrão do Windows, igual em todas as plataformas). Esse processo é **o processo de inferência** da ADR 0011:
  - o `initializer` carrega o modelo e as referências do KanjiVG uma vez;
  - o job leva os traços e o `stroke_order_mode`, e volta com os candidatos e a avaliação da ordem.
- **Estado dos jobs:** fica em memória (`JobRepository` em memória). Os resultados expiram **5 minutos** depois de terminados (valor inicial), e os traços são descartados junto, como pede o `CLAUDE.md`, "Segurança".
- **Uvicorn com um processo só** (sem `--workers`), porque a fila e os jobs vivem na memória dele.
- **Falha do processo de inferência:** se o processo morrer (`BrokenProcessPool`), o job vira `failed`, e o pool é recriado, o que recarrega o modelo.
- **Ports:** `JobQueue` e `JobRepository` com adapters em memória, e o recognizer chamando o processo de inferência ([ADR 0004](0004-clean-and-hexagonal-architecture.md)). Trocar por outra fila continua sendo trocar um adapter.

## Consequências

- **Positivas:**
  - nenhum serviço novo para instalar no notebook;
  - mesmo comportamento no Linux de desenvolvimento e no Windows da escola;
  - o event loop nunca roda a inferência, então a API e o SSE seguem respondendo;
  - a fila limitada protege a memória e dá um erro claro ao usuário;
  - a CPU fica com uma inferência por vez, sem oversubscription.
- **Negativas:**
  - **Reiniciar a API perde os jobs na fila e os resultados ainda não lidos.** O aluno precisa reenviar o desenho. É aceitável para jobs de segundos, sem login.
  - **Um processo só para a API:** não dá para escalar com `--workers`. Para a carga da escola, um processo basta (*a medir* no teste de carga).
  - **Com uma inferência por vez, o tempo de espera cresce com a fila.** O limite 16 e a eventual segunda execução simultânea se ajustam com o tempo real do modelo, no benchmark.
  - **`spawn` recarrega o modelo** a cada processo novo, inclusive quando o pool é recriado depois de uma falha. A partida e a recuperação levam o tempo de carga do modelo.
  - **Os dados do job cruzam processos por pickle:** o que vai e o que volta precisa ser serializável (listas de traços e resultados simples, nunca tensores ou objetos do PyTorch).
- **Na prática:**
  - o adapter da fila mora em `adapters/outbound/`, e o consumidor em `adapters/inbound/` (o consumidor da fila que chama `ProcessRecognition`);
  - o processo de inferência é montado no `lifespan`, em `bootstrap/`;
  - testes de use case usam fila e recognizer falsos; um teste de integração sobe o pool de verdade com um modelo falso;
  - voltar ao Redis ou a outra fila persistente pede uma ADR nova, com motivo medido (por exemplo, a necessidade de mais de um processo de API).
- *Atualização de 2026-11-08 (#46), detalhes da implementação:*
  - **O reconhecimento e a avaliação da ordem cruzam separados.** Cada um tem o seu port (`KanjiRecognizer`, `StrokeOrderEvaluator`, ambos `async`), e o `ProcessRecognition` chama o avaliador com os candidatos que o reconhecedor devolveu, só no `ordered`. Um job `ordered` faz, então, duas idas ao processo de inferência, e não uma, como estava escrito acima. O custo é mais um pickle do desenho (no máximo 10.000 pontos), desprezível perto da CNN. Em troca, a regra "o `unordered` não chama o avaliador" fica no use case, testada sem processo, e não escondida no worker.
  - **O que cruza é dado simples** (`adapters/outbound/inference/wire.py`): o desenho vai como `{"canvas": (w, h), "strokes": [[(x, y, t), ...], ...]}`, os candidatos voltam como `(kanji, confiança)`, e a avaliação da ordem, no formato da API da [ADR 0016](0016-stroke-order-check-by-bipartite-matching-and-capture-format.md), sem o `correct`. Assim o código do worker (o `kanjilens_ml`, na #48) não conhece o domínio do backend.
  - **O `initializer` roda na partida**, não no primeiro job: o `lifespan` só termina de subir depois de o worker responder, e um modelo que falha ao carregar impede a API de subir.
  - **No desligamento**, o worker é encerrado (`terminate_workers()`, do Python 3.14) sem esperar a inferência em curso, cujo job se perde como os outros em memória.
  - **Falha de qualquer tipo vira `failed`:** queda do worker (`BrokenProcessPool`), exceção do reconhecedor ou do avaliador, ou resultado que quebra uma regra do domínio. Nenhum job fica `processing` para sempre.

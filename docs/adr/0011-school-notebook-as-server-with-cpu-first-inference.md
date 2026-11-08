# 0011. Notebook da escola como servidor, com inferência CPU-first

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0005](0005-asynchronous-recognition-with-queue-and-workers.md), [0007](0007-local-execution-over-the-lan.md), [0010](0010-two-recognition-modes-with-specialized-models.md)

## Contexto

A [ADR 0007](0007-local-execution-over-the-lan.md) decidiu rodar tudo numa máquina local, sem dizer qual. Agora essa máquina existe:

| Item | Especificação |
|---|---|
| Notebook | Dell Inspiron 3501 |
| CPU | Intel Core i7-1165G7: 4 núcleos / 8 threads, até 4,70 GHz, com AVX2, AVX-512 e DL Boost |
| RAM | 16 GB |
| GPU | Intel Iris Xe integrada; não há GPU dedicada, e variantes do modelo podem ter configuração diferente (*a confirmar*) |

O notebook hospeda o **conjunto completo** do KanjiLens:
- o frontend Angular;
- o FastAPI;
- a fila;
- o runtime de inferência;
- os dois modelos da [ADR 0010](0010-two-recognition-modes-with-specialized-models.md);
- o dicionário local e outros serviços auxiliares, se rodarem ali.

O treino é feito noutra máquina, mais potente. O que precisa caber no notebook é o artefato final, o runtime, a memória de trabalho e a carga.

A carga esperada é de **3–5 alunos enviando desenhos numa janela curta**. Os ~10 usuários simultâneos de antes passam a ser o **cenário de estresse**. Usuários conectados (HTTP e SSE abertos) não são inferências simultâneas: a fila existe para absorver o pico.

A investigação está no [spike de modelos e runtime](../spikes/model-and-runtime-evaluation.md), seções 3, 6 e 7 ([#23](https://github.com/Asuka-Jyuku/kanji-lens/issues/23)).

## Alternativas consideradas

- **Inferência em GPU (CUDA):** é o caminho comum de quem treina em GPU. O notebook não tem GPU dedicada, e depender de CUDA no deploy amarraria o projeto a um hardware que a escola não tem.
- **Uma inferência em paralelo por cliente, com vários workers desde o início:** parece dar mais vazão. Com 4 núcleos físicos, isso gera oversubscription: dois workers com quatro threads cada disputam os mesmos núcleos. Cada processo também carrega a sua cópia dos modelos, e mais workers não garantem mais throughput.
- **Um processo de inferência dedicado, CPU-first, começando com uma inferência ativa por vez:** é o mais previsível de medir. A fila serializa parte do pico, e a latência percebida cresce com a fila (*a medir*).

## Decisão

O **Dell Inspiron 3501 é o hardware de referência e o servidor de produção** do KanjiLens. A inferência é **CPU-first**: o deploy não depende de CUDA nem de GPU.

A configuração inicial, a validar por benchmark:

1. **Um processo de inferência separado do event loop do FastAPI.** Ele carrega os dois modelos uma vez e escolhe um deles pelo `stroke_order_mode` de cada job.
2. **Uma inferência ativa por vez**, com uma fila compartilhada pelos dois modos e as threads do runtime controladas.
3. **Uma segunda execução simultânea** (no mesmo processo ou em dois processos de worker) só depois de medir a espera na fila e a latência p95.
4. **Runtime:** o PyTorch CPU é a referência. Entram na comparação o OpenVINO CPU (prioritário neste Intel de 11ª geração) e o ONNX Runtime CPU. INT8 só depois do FP32, e só se não piorar Top-1/Top-5.
5. **O frontend é servido como build estático de produção.** O `ng serve` é só para desenvolvimento.

A meta de capacidade é aceitar 3–5 envios próximos, com `ordered` e `unordered` misturados, sem perder jobs e com a API e o SSE respondendo. 10 clientes são o teste de estresse. O limite numérico de latência só é fixado depois da primeira rodada de medições, validada com a escola.

## Consequências

- **Positivas:**
  - o ambiente-alvo é conhecido, e os números passam a significar algo;
  - sem custo de hardware novo;
  - sem dependência de CUDA no deploy;
  - a fila e o limite de execução deixam o consumo de CPU e de RAM previsível.
- **Negativas:**
  - **O teto de capacidade é o de um notebook.** Em carga longa há throttling térmico e de energia, e uma medição curta engana.
  - **Tudo disputa 4 núcleos físicos e 16 GB:** frontend, API, fila, runtime e os dois modelos. O consumo é do conjunto, não só do modelo.
  - **Dois processos de worker duplicam os modelos na RAM.**
  - Com uma inferência por vez, o quinto aluno de uma rajada espera os quatro anteriores.
  - **Benchmark só vale se rodar no próprio notebook.** Resultado da máquina de treino não serve.
  - Um runtime exportado (ONNX ou OpenVINO) acrescenta conversão, dependência e a obrigação de conferir a paridade numérica com o PyTorch.
- **Na prática:**
  - **Registro dos números:** todo número de desempenho sai com o hardware, o SO, o perfil de energia e as versões de Python e do runtime.
  - **Cenários de carga:** 1, 2, 3, 5 e 10 clientes, com os modos misturados e o sistema todo no ar. Medir:
    - latência p50/p95;
    - espera na fila;
    - throughput;
    - CPU e RAM;
    - temperatura.
  - **Threads e processos:** as threads do runtime são configuradas explicitamente. O Uvicorn continua com um processo enquanto a fila estiver em memória ([ADR 0005](0005-asynchronous-recognition-with-queue-and-workers.md)).
  - **Execução:** o `docs/RUNNING.md` descreve o build estático do frontend quando nascer.
  - **Próxima ADR:** runtime, precisão, resolução e concorrência de produção saem do benchmark no notebook.

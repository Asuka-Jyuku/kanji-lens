---
name: ml-conventions
description: Como se faz ML no KanjiLens (ml/, PyTorch) — dataset, o pré-processamento compartilhado, arquitetura do modelo, treino, avaliação (Top-1/Top-5, confusão entre kanjis parecidos), a avaliação da ordem dos traços contra o KanjiVG, versões do modelo e os adapters do recognizer e do avaliador da ordem no backend, com a fonte de cada regra. Usar ao pedirem "treinar", "avaliar", "dataset", "pré-processamento", "acurácia", "Top-5", "matriz de confusão", "modelo novo", "por que confunde 日 e 目", "carregar o modelo no backend", "revisa o código de ML", e ao pegar issue com a etiqueta ml ou que mexe em ml/.
model: sonnet
---

# ML no KanjiLens

Para escrever, rodar e revisar o `ml/` e os adapters do recognizer e do avaliador da ordem no backend. Cada regra mora num lugar só: aqui fica o caminho e a fonte. Se a skill divergir da fonte, vale a fonte, e a skill se corrige no mesmo PR.

| Assunto | Fonte |
|---|---|
| PyTorch, CNN 2D, top-K | [ADR 0006](../../../docs/adr/0006-cnn-with-pytorch.md) e [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md) |
| Uma CNN nos dois modos; no `ordered`, a ordem comparada com o KanjiVG, sem rede neural | [ADR 0012](../../../docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md) |
| Algoritmo da ordem, formato dos pontos, KanjiVG fixado e fora do git, SciPy só no `stroke_order` | [ADR 0016](../../../docs/adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md) |
| Parâmetros e números da avaliação da ordem, o benchmark, os desenhos do canvas | [`docs/MODEL.md`](../../../docs/MODEL.md) |
| Dataset (ETL9G), classes, licença do ETL (nada dele no repositório, nem em teste) | [ADR 0021](../../../docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md); o treino do MVP com desenhos sintéticos do KanjiVG, e as cinco regras para o ETL entrar depois, na [ADR 0022](../../../docs/adr/0022-synthetic-training-data-from-kanjivg-while-etl-is-down.md) |
| Inferência só na CPU, no notebook da escola; runtimes e INT8 | [ADR 0011](../../../docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md) e o [spike de modelos](../../../docs/spikes/model-and-runtime-evaluation.md) |
| Modelo carregado uma vez no processo de inferência, só pickle entre processos | [ADR 0019](../../../docs/adr/0019-in-memory-job-queue-with-one-inference-process.md) |
| Pré-processamento num lugar só; qualidade medida num split fixo; nada de dataset nem pesos no git | `CLAUDE.md`, "Arquitetura", "Testes" e "Convenções de código e dados" |

Projetos do GitHub citados nos spikes são estudo, não dependência: copiar código, pesos ou dados passa pela licença e por uma ADR.

## Referências

| Arquivo | Quando ler |
|---|---|
| [`references/experiments.md`](references/experiments.md) | antes de treinar ou avaliar: splits, seeds, versão do modelo, como reportar |
| [`references/review.md`](references/review.md) | ao revisar um PR e no fim do seu trabalho |

## Experimento novo ou mudança no modelo

1. **Issue e branch** como em todo PR. Pergunta em aberto ("qual dataset?") é um **spike**, que termina numa ADR.
2. **ADR antes do código** para dataset, lista de classes, tamanho da entrada, normalização ou família da arquitetura.
3. **Pré-processamento** só em `ml/src/kanjilens_ml/preprocessing/`, como função pura testada.
4. **Pacote novo** em `ml/src/kanjilens_ml/` só quando tiver código (o de dados, treino, avaliação ou modelos nasce com a primeira função).
5. **Configuração** versionada em `ml/configs/`; o treino lê tudo dela (seed, split, hiperparâmetros, classes).
6. **Treinar** e salvar em `ml/artifacts/` os pesos com a configuração, a lista de classes e a versão do pré-processamento.
7. **Avaliar** no split de teste fixo e nos desenhos do canvas, antes e depois, e registrar no `docs/MODEL.md`.

## Avaliar um modelo

- **Reconhecimento:** Top-1 e Top-5 no split de teste fixo, e a confusão entre kanjis parecidos (日, 目, 白…).
- **Ordem (`ordered`):** erros detectados × falsos alarmes num conjunto fixo, com traços unidos e quebrados.
- **Desenhos reais do canvas:** a diferença entre o dataset e o canvas é o maior risco. Um modelo melhor no split e pior no canvas é pior para quem usa.
- **No notebook da escola:** latência p50/p95, RAM e tamanho do artefato. Número medido na máquina de treino não vale.

## Inferência

O recognizer do backend carrega a versão do modelo uma vez (`eval()`, `torch.inference_mode()`), aplica **a mesma** função de pré-processamento do treino e devolve o top-K. Ele se recusa a subir com pesos cuja lista de classes ou versão de pré-processamento não bate. No `ordered`, o avaliador compara os traços com o KanjiVG, sem PyTorch. Os dois rodam no processo de inferência e devolvem tipos simples, nunca tensores. Outro runtime (ONNX Runtime, OpenVINO) só entra com a ADR do benchmark e a paridade numérica conferida.

## Antes de dizer que terminou

- **Comandos** do `CLAUDE.md`: `ruff check` e `ruff format --check` na raiz; `mypy`, `pytest` e `lint-imports` com `--directory ml`.
- **Números:** mudou o modelo, o pré-processamento ou a avaliação da ordem? Traga os números antes e depois.
- **Sem dataset, GPU ou dependência:** diga isso e não afirme resultado.
- **Documentos:** atualize só o que ficou falso.

## Como entregar

Cada número com a procedência (split, configuração, versão do modelo, seed). Separe o que mediu do que é julgamento. Diga o que rodou, o que falhou e o que ficou de fora. Merge é decisão de quem pediu.

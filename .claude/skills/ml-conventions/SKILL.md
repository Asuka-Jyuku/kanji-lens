---
name: ml-conventions
description: Como se faz ML no KanjiLens (ml/, PyTorch) — dataset, o pré-processamento compartilhado, arquitetura do modelo, treino, avaliação (Top-1/Top-5, confusão entre kanjis parecidos), a avaliação da ordem dos traços contra o KanjiVG, versões do modelo e os adapters do recognizer e do avaliador da ordem no backend, com a fonte de cada regra. Usar ao pedirem "treinar", "avaliar", "dataset", "pré-processamento", "acurácia", "Top-5", "matriz de confusão", "modelo novo", "por que confunde 日 e 目", "carregar o modelo no backend", "revisa o código de ML", e ao pegar issue com a etiqueta ml ou que mexe em ml/.
model: sonnet
---

# ML no KanjiLens

Você escreve, roda e revisa o código de ML do projeto (`ml/`) e os adapters do recognizer e do avaliador da ordem no backend. O que vale **sempre** está aqui.

**Cada regra mora num lugar só.** Esta skill diz o caminho e aponta a fonte; não copie a regra para cá. Achou uma regra aqui que diverge da fonte, vale a fonte: corrija a skill no mesmo PR.

> **Fase:** a estrutura de `ml/` existe, com as ferramentas da [ADR 0014](../../../docs/adr/0014-ml-tooling-python-uv-ruff-pytest-import-linter.md) (Python 3.15, uv, Ruff, mypy, pytest, Import Linter; comandos no `CLAUDE.md`, "Comandos"); o primeiro código de produto é a normalização dos traços da avaliação da ordem (`preprocessing/strokes.py`, descrita no [docs/MODEL.md](../../../docs/MODEL.md#traços-normalizados-avaliação-da-ordem)). O dataset (ETL9G) e as classes (os 1.026 教育漢字, começando pelos 240 da 1ª e da 2ª série) estão decididos na [ADR 0021](../../../docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md), com o download pendente enquanto o site oficial estiver fora do ar; segue em aberto o registro dos experimentos. O `docs/MODEL.md` existe e muda junto com dataset, pré-processamento, treino ou modelo.

| Assunto | Fonte (a regra está lá) |
|---|---|
| PyTorch, top-K com Softmax | [ADR 0006](../../../docs/adr/0006-cnn-with-pytorch.md) e [ARCHITECTURE.md, seção 2.3](../../../docs/ARCHITECTURE.md#23-machine-learning) |
| Um modelo (CNN 2D) nos dois modos; no `ordered`, avaliação da ordem contra o KanjiVG, sem rede neural; comparadores e algoritmos candidatos | [ADR 0012](../../../docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md) e o [spike de modelos](../../../docs/spikes/model-and-runtime-evaluation.md), seções 5.1 e 5.3 |
| Algoritmo da avaliação da ordem (bipartite com hipóteses de união e quebra), formato dos pontos, resposta, KanjiVG fixado e fora do git, SciPy só no `stroke_order` | [ADR 0016](../../../docs/adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md) e o [spike da avaliação da ordem](../../../docs/spikes/stroke-order-evaluation.md) |
| Inferência CPU-first no notebook da escola; runtimes (PyTorch, OpenVINO, ONNX Runtime), INT8 e como medir | [ADR 0011](../../../docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md) e o spike, seções 6 e 7 |
| Projetos do GitHub de referência: estudo, não dependência; licença antes de copiar | [spike, seção 11.1](../../../docs/spikes/model-and-runtime-evaluation.md#111-projetos-de-referência-no-github) |
| O `kanjilens_ml` é uma biblioteca; o backend só o usa no adapter do recognizer | [ADR 0004](../../../docs/adr/0004-clean-and-hexagonal-architecture.md) e [ARCHITECTURE.md, seção 3.3](../../../docs/ARCHITECTURE.md#33-ml-mlsrckanjilens_ml) |
| O pré-processamento existe uma vez só; muda junto com treino, inferência e versão do modelo, num PR só | `CLAUDE.md`, "Pré-processamento sempre junto"; [ADR 0002](../../../docs/adr/0002-monorepo-for-frontend-backend-and-ml.md) |
| Dataset (ETL9G) e classes (os 1.026 教育漢字; todas existem no KanjiVG), licença do ETL (distribuição só pelo site oficial: nada do ETL no repositório, nem em teste), mapeamento JIS → Unicode, métricas do reconhecimento e da avaliação da ordem, diferença entre canvas e dataset | [ADR 0021](../../../docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md) e [ARCHITECTURE.md, seção 7](../../../docs/ARCHITECTURE.md#7-dataset-e-treinamento) |
| Qualidade do modelo medida num split fixo, antes e depois | `CLAUDE.md`, "Testes" |
| Nada de dataset nem pesos no git; conferir a licença | `CLAUDE.md`, "Convenções de código" |
| O modelo e as referências do KanjiVG carregados uma vez no processo de inferência (`ProcessPoolExecutor` com `spawn`, carga no `initializer`), fora do event loop; uma inferência por vez no início; quantidade de threads; o que entra e sai do processo é serializável por pickle | [ADR 0005](../../../docs/adr/0005-asynchronous-recognition-with-queue-and-workers.md), [ADR 0011](../../../docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md) e [ADR 0019](../../../docs/adr/0019-in-memory-job-queue-with-one-inference-process.md) |
| Idioma: código em inglês, documentação (inclusive o `docs/MODEL.md`) em português | `CLAUDE.md`, "Idioma" |

## Referências (leia quando o passo pedir)

| Arquivo | Quando ler |
|---|---|
| [`references/experiments.md`](references/experiments.md) | antes de treinar ou avaliar: splits, seeds, configurações, o que é uma versão do modelo, como reportar números |
| [`references/review.md`](references/review.md) | ao revisar um PR com código de ML, e no fim do seu próprio trabalho |

## Experimento novo ou mudança no modelo

1. **Issue e branch** como em todo PR (`CLAUDE.md`, "Git / commits"). Uma pergunta em aberto ("qual dataset?", "quantas classes?") é um **spike**, que termina numa ADR.
2. **ADR antes do código** quando a mudança escolhe o dataset, muda a lista de classes, o tamanho da entrada, a normalização ou a família da arquitetura (`CLAUDE.md`, "Decisões de arquitetura").
3. **Pré-processamento** só em `ml/src/kanjilens_ml/preprocessing/`, como função pura testada com imagens fixas (inclusive desenhos parecidos com os do canvas).
4. **Configuração** em `ml/configs/`, versionada; o script de treino lê tudo dela (seed, split, hiperparâmetros, tamanho da entrada, lista de classes).
5. **Treinar**, salvando em `ml/artifacts/` os pesos junto com a configuração, a lista de classes e a versão do pré-processamento (`references/experiments.md`, "O que é uma versão do modelo").
6. **Avaliar** no split de teste fixo e no conjunto de desenhos do canvas; reportar antes e depois.
7. **Documentar** no `docs/MODEL.md` e no PR.

## Avaliar um modelo

- Top-1 e Top-5 no **split de teste fixo**, mais precision/recall/F1 (e Macro-F1) e a matriz de confusão dos kanjis visualmente parecidos (日, 目, 白…). A mesma figura desenhada em outra ordem dá o mesmo resultado.
- **Avaliação da ordem (`ordered`):** num conjunto fixo de desenhos com ordem certa e errada, erros detectados × falsos alarmes, inclusive com traços unidos ou quebrados.
- **Também com desenhos reais do canvas:** a diferença entre as digitalizações do dataset e o traço do canvas é o principal risco do projeto (ARCHITECTURE.md, seção 7.4). Um modelo que melhora no split de teste e piora nos desenhos do canvas é pior para quem usa.
- Latência p50/p95, RAM de pico e tamanho do artefato **no notebook da escola** (ADR 0011), porque é lá que ele roda. Número medido na máquina de treino não vale.

## Inferência

O `adapters/outbound/recognizer/` do backend implementa o port `KanjiRecognizer` com o `kanjilens_ml`: recebe o desenho (traços) e carrega a versão do modelo uma vez, em modo `eval()`, roda dentro de `torch.inference_mode()`, aplica **a mesma** função de pré-processamento do treino e devolve `Prediction`s do domínio (kanji + confiança) para o top-K. Ele se recusa a carregar pesos cuja lista de classes ou versão de pré-processamento não bate com o código. No modo `ordered`, o adapter do port de avaliação da ordem compara os traços com o KanjiVG (módulo puro, sem PyTorch; ADR 0012). Os dois rodam **no processo de inferência** (ADR 0019): o modelo e o KanjiVG são carregados no `initializer` do pool, e o que volta ao processo da API são tipos simples, nunca tensores. Um runtime exportado (ONNX Runtime, OpenVINO) só entra depois de a ADR do benchmark escolhê-lo e com a paridade numérica conferida contra o PyTorch.

## Antes de dizer que terminou

**Documentos em dia:** atualize no mesmo PR o que a mudança afetou (`CLAUDE.md`, "Documentos nascem com o assunto").

Rode os comandos do `CLAUDE.md`, "Comandos": `ruff check` e `ruff format --check` na raiz, e `mypy`, `pytest` e `lint-imports` com `--directory ml`. O `pytest` já roda o teste de arquitetura (os contratos do `ml/pyproject.toml`). Mudou o modelo, o pré-processamento ou a avaliação da ordem? Rode também a avaliação no split de teste fixo (`CLAUDE.md`, "Testes").

- **Dataset, GPU ou dependências não disponíveis:** diga isso e não afirme resultados.

## Como entregar

Cada número com a sua procedência (split, configuração, versão do modelo, seed). Separe o que mediu do que é julgamento seu, diga o que rodou e o resultado (inclusive o que falhou ou não rodou), e o que ficou de fora, com o motivo. PR: o checklist do `CONTRIBUTING.md` e do template de PR; merge só com o "pode" de quem pediu, para aquele PR.

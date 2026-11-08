---
name: ml-conventions
description: Como se faz ML no KanjiLens (ml/, PyTorch) — dataset, o pré-processamento compartilhado, arquitetura do modelo, treino, avaliação (Top-1/Top-5, confusão entre kanjis parecidos), versões do modelo e o adapter do recognizer no backend, com a fonte de cada regra. Usar ao pedirem "treinar", "avaliar", "dataset", "pré-processamento", "acurácia", "Top-5", "matriz de confusão", "modelo novo", "por que confunde 日 e 目", "carregar o modelo no backend", "revisa o código de ML", e ao pegar issue com a etiqueta ml ou que mexe em ml/.
model: sonnet
---

# ML no KanjiLens

Você escreve, roda e revisa o código de ML do projeto (`ml/`) e o adapter do recognizer no backend. O que vale **sempre** está aqui.

**Cada regra mora num lugar só.** Esta skill diz o caminho e aponta a fonte; não copie a regra para cá. Achou uma regra aqui que diverge da fonte, vale a fonte: corrija a skill no mesmo PR.

> **Fase:** ainda não há código de ML (a etapa 1 começa aqui). O dataset e a quantidade de classes são decisões em aberto; o gerenciador de pacotes, o test runner e o registro dos experimentos são escolhidos na ADR de ferramentas da etapa. O `docs/MODEL.md` nasce no primeiro PR da etapa 1.

| Assunto | Fonte (a regra está lá) |
|---|---|
| PyTorch, top-K com Softmax | [ADR 0006](../../../docs/adr/0006-cnn-with-pytorch.md) e [ARCHITECTURE.md, seção 2.3](../../../docs/ARCHITECTURE.md#23-machine-learning) |
| Um modelo (CNN 2D) nos dois modos; no `ordered`, avaliação da ordem contra o KanjiVG, sem rede neural; comparadores e algoritmos candidatos | [ADR 0012](../../../docs/adr/0012-ordered-mode-as-stroke-order-evaluation.md) e o [spike de modelos](../../../docs/spikes/model-and-runtime-evaluation.md), seções 5.1 e 5.3 |
| Inferência CPU-first no notebook da escola; runtimes (PyTorch, OpenVINO, ONNX Runtime), INT8 e como medir | [ADR 0011](../../../docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md) e o spike, seções 6 e 7 |
| Projetos do GitHub de referência: estudo, não dependência; licença antes de copiar | [spike, seção 11.1](../../../docs/spikes/model-and-runtime-evaluation.md#111-projetos-de-referência-no-github) |
| O `kanjilens_ml` é uma biblioteca; o backend só o usa no adapter do recognizer | [ADR 0004](../../../docs/adr/0004-clean-and-hexagonal-architecture.md) e [ARCHITECTURE.md, seção 3.3](../../../docs/ARCHITECTURE.md#33-ml-mlsrckanjilens_ml) |
| O pré-processamento existe uma vez só; muda junto com treino, inferência e versão do modelo, num PR só | `CLAUDE.md`, "Pré-processamento sempre junto"; [ADR 0002](../../../docs/adr/0002-monorepo-for-frontend-backend-and-ml.md) |
| Dataset (em aberto), classes (em aberto; todas precisam existir no KanjiVG), métricas do reconhecimento e da avaliação da ordem, diferença entre canvas e dataset | [ARCHITECTURE.md, seção 7](../../../docs/ARCHITECTURE.md#7-dataset-e-treinamento) |
| Qualidade do modelo medida num split fixo, antes e depois | `CLAUDE.md`, "Testes" |
| Nada de dataset nem pesos no git; conferir a licença | `CLAUDE.md`, "Convenções de código" |
| O modelo e as referências do KanjiVG carregados uma vez no processo de inferência, fora do event loop; uma inferência por vez no início; quantidade de threads | [ADR 0005](../../../docs/adr/0005-asynchronous-recognition-with-queue-and-workers.md) e [ADR 0011](../../../docs/adr/0011-school-notebook-as-server-with-cpu-first-inference.md) |
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

O `adapters/outbound/recognizer/` do backend implementa o port `KanjiRecognizer` com o `kanjilens_ml`: recebe o desenho (traços) e carrega a versão do modelo uma vez, em modo `eval()`, roda dentro de `torch.inference_mode()`, aplica **a mesma** função de pré-processamento do treino e devolve `Prediction`s do domínio (kanji + confiança) para o top-K. Ele se recusa a carregar pesos cuja lista de classes ou versão de pré-processamento não bate com o código. No modo `ordered`, o adapter do port de avaliação da ordem compara os traços com o KanjiVG (módulo puro, sem PyTorch; ADR 0012). Um runtime exportado (ONNX Runtime, OpenVINO) só entra depois de a ADR do benchmark escolhê-lo e com a paridade numérica conferida contra o PyTorch.

## Antes de dizer que terminou

Rode os testes de ML e a avaliação definidos na ADR de ferramentas da etapa 1 (vão estar listados no `CLAUDE.md`, "Comandos").

- **Dataset, GPU ou dependências não disponíveis:** diga isso e não afirme resultados.

## Como entregar

Cada número com a sua procedência (split, configuração, versão do modelo, seed). Separe o que mediu do que é julgamento seu, diga o que rodou e o resultado (inclusive o que falhou ou não rodou), e o que ficou de fora, com o motivo. PR: o checklist do `CONTRIBUTING.md` e do template de PR; merge só com o "pode" de quem pediu, para aquele PR.

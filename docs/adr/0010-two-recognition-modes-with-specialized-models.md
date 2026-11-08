# 0010. Dois modos de reconhecimento com modelos especializados (Opção C)

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0004](0004-clean-and-hexagonal-architecture.md), [0005](0005-asynchronous-recognition-with-queue-and-workers.md), [0006](0006-cnn-with-pytorch.md), [0011](0011-school-notebook-as-server-with-cpu-first-inference.md)

## Contexto

Antes de reconhecer, o aluno escolhe se a ordem dos traços importa. A escolha vai em cada solicitação; não é uma configuração do sistema. São dois contratos de reconhecimento com expectativas diferentes:

- **`ordered`:** a sequência, a direção e a separação dos traços entram como evidência e podem mudar o ranking.
- **`unordered`:** conta o formato final. Desenhar os traços em outra ordem não deve mudar o resultado.

O desenho da [ADR 0006](0006-cnn-with-pytorch.md) é uma CNN sobre a imagem, e uma imagem final não guarda a ordem nem a direção dos traços: não há como atender o `ordered` com ela. A base candidata para o treino (ETL8/ETL9) é *offline*: tem a imagem digitalizada, sem a trajetória da caneta. O KanjiVG tem a ordem de referência em vetores tipográficos, que não são escrita humana. A inferência roda na CPU de um notebook modesto ([ADR 0011](0011-school-notebook-as-server-with-cpu-first-inference.md)), então cada modelo precisa ser compacto.

A investigação está no [spike de modelos e runtime](../spikes/model-and-runtime-evaluation.md) ([#23](https://github.com/Asuka-Jyuku/kanji-lens/issues/23)).

## Alternativas consideradas

- **Um modelo de imagem só, para os dois modos:** o mais simples, com um modelo para treinar, versionar e carregar. Não serve ao `ordered`, porque a rasterização perde a ordem.
- **Uma rede só, com a ordem codificada na entrada** (CNN 2D com canais ou mapas de ordem e direção) **para os dois modos:** reaproveita o pipeline de imagem. A codificação pode perder detalhe temporal, e o `unordered` passaria a receber um sinal que ele deve ignorar.
- **Backbone compartilhado com dois ramos** (imagem + sequência, com fusão): um conjunto de pesos para os dois modos. É mais complexo de treinar e de avaliar, e um modo pode piorar o outro sem que se perceba. Nada indica por ora que o ganho pague o custo.
- **Opção C, modelos especializados com a infraestrutura em comum:** cada modo recebe a representação que faz sentido para ele. São dois modelos para treinar, versionar e manter na RAM.

## Decisão

Usamos dois modelos especializados e independentes, sem compartilhar pesos nesta primeira versão:

- **`unordered`:** uma **CNN 2D customizada compacta** sobre a imagem rasterizada final, em tons de cinza. MobileNetV3-Small, ResNet-18 e HOG + SVM entram como comparadores.
- **`ordered`:** uma **1D-CNN temporal compacta** sobre a sequência de pontos e traços (coordenadas, separação e sequência; direção e intervalos de tempo conforme os experimentos). CNN 2D com mapas de ordem e GRU pequena ficam como alternativas.

Os dois modos compartilham:

- o contrato da API (`POST /api/recognitions` com `strokes` e `stroke_order_mode`);
- a validação do payload;
- o módulo de pré-processamento, que gera as duas representações a partir da mesma lista de traços;
- a fila, os jobs e os workers;
- a observabilidade;
- a resposta Top-K.

O canvas envia a **lista de traços** (pontos X/Y, com a separação entre traços), e não um PNG. A imagem do `unordered` é derivada dela no pré-processamento.

Esta ADR fixa a **estratégia**. Ficam para os benchmarks no notebook:
- largura e profundidade das redes;
- resolução da imagem;
- quantidade de pontos por sequência;
- runtime;
- quantização.

O modo padrão da interface continua em aberto.

## Consequências

- **Positivas:**
  - cada modo usa a representação certa;
  - o `unordered` pode ser medido quanto a invariância à ordem;
  - os modelos podem evoluir e ser trocados separadamente;
  - os dois são pequenos o bastante para a CPU do notebook (*a medir*).
- **Negativas:**
  - **Dois modelos para treinar, avaliar, versionar e carregar.** A RAM do processo de inferência leva os dois, e a métrica de cada modo é separada, sem um número único.
  - **O `ordered` precisa de dados *online*:** sequências reais de traços que o ETL não tem. A fonte (coleta própria pelo canvas, dataset público ou KanjiVG sintético) está em aberto, e guardar desenhos para coleta pede ADR (`CLAUDE.md`, "Segurança"). Sem essa fonte, o `ordered` não sai.
  - **O risco de *training-serving skew* dobra:** são duas representações. A do `unordered` ainda carrega a diferença entre o canvas e o dataset (ARCHITECTURE.md, seção 7.4).
  - O payload por traços muda o limite de entrada: o máximo passa a ser em traços e pontos, não em bytes de imagem.
- **Na prática:**
  - **Código do ML:**
    - `kanjilens_ml/models/` tem as duas arquiteturas;
    - `kanjilens_ml/preprocessing/` gera a imagem e a sequência a partir da mesma lista de traços;
    - os pesos levam o modo nos metadados, e o adapter recusa pesos do modo errado.
  - **Backend:**
    - o domínio ganha `StrokeOrderMode` e um `Drawing` feito de traços;
    - o port `KanjiRecognizer` recebe o modo;
    - o job registra o modo usado.
  - **Frontend:** a tela tem o seletor de modo, e o canvas captura e envia os traços.
  - **Métricas:** separadas por modo, com um teste de invariância à reordenação no `unordered` e um teste de coerência a mudanças de ordem e direção no `ordered`.
  - **Reabrir esta ADR:** se a 1D-CNN não atingir a qualidade necessária, comparar GRU e CNN 2D com mapas de ordem. Um backbone compartilhado só volta com evidência dos benchmarks, numa ADR nova.

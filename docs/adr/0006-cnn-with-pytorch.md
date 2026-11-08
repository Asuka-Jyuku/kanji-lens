# 0006. CNN em PyTorch para o reconhecimento

- **Status:** Aceita
- **Data:** 2026-11-03
- **Relacionadas:** [0002](0002-monorepo-for-frontend-backend-and-ml.md), [0005](0005-asynchronous-recognition-with-queue-and-workers.md), [0010](0010-two-recognition-modes-with-specialized-models.md)

## Contexto

Reconhecer kanji manuscrito é um problema de classificação de imagem com centenas a milhares de classes (até os 2.136 kanjis Jōyō). A interface mostra os top-K candidatos, então o modelo precisa dar uma probabilidade por classe. O projeto também é uma forma de aprender Deep Learning e Visão Computacional. Decisão registrada depois do fato, a partir do [ARCHITECTURE.md](../ARCHITECTURE.md) (seção 2.3 do commit `d72a4d4`).

## Alternativas consideradas

- **Visão computacional clássica** (features HOG + SVM, k-NN) — leve e explicável; conhecida por ficar atrás das CNNs em conjuntos grandes de caracteres manuscritos. *Inferido:* não avaliada.
- **CNN em TensorFlow/Keras** — capacidade equivalente; *inferido* como deixada de lado pelo loop de treino mais explícito do PyTorch e pelo uso maior dele em código de pesquisa atual.
- **Modelos de visão pré-treinados ou um serviço de OCR** — boa acurácia; um OCR na nuvem quebra a regra de rodar só local (ADR 0007), e um modelo pré-treinado grande acrescenta peso que o servidor pode não aguentar. *Inferido.*
- **CNN treinada em PyTorch** — padrão para esse problema, pequena o bastante para rodar na CPU local, e um objetivo de aprendizado direto do projeto.

## Decisão

Treinamos uma CNN em PyTorch, começando por uma arquitetura simples (dois blocos Conv2D + ReLU + MaxPooling, depois Dense + Softmax) e evoluindo conforme os resultados. O modelo devolve as top-K classes com as probabilidades do Softmax.

> **Detalhada pela [ADR 0010](0010-two-recognition-modes-with-specialized-models.md)** (2026-11-08): continuam valendo o PyTorch e as CNNs. Mudam duas coisas:
> - **Dois modelos especializados:** uma CNN 2D compacta sobre a imagem (`unordered`) e uma 1D-CNN temporal compacta sobre a sequência de traços (`ordered`).
> - **Arquitetura inicial da CNN 2D:** pooling global em vez de achatar os mapas numa camada densa grande.
>
> O treino pode usar GPU. A inferência é CPU-first ([ADR 0011](0011-school-notebook-as-server-with-cpu-first-inference.md)).

## Consequências

- **Positivas:** Python de ponta a ponta com o backend; modelo pequeno, roda na CPU; a arquitetura pode crescer (redes mais fundas, data augmentation) sem mudar o contrato da inferência.
- **Negativas:** o PyTorch é uma dependência pesada para a imagem do backend; a qualidade depende de um dataset que ainda está em aberto e cujas imagens são diferentes dos desenhos do canvas (o principal risco do projeto, [ARCHITECTURE.md, seção 7.4](../ARCHITECTURE.md#74-pontos-de-atenção)); os resultados só são reproduzíveis com seeds fixas, configurações versionadas e um split de teste fixo.
- **Na prática:** as arquiteturas do modelo ficam em `ml/src/kanjilens_ml/models/`, os pesos em `ml/artifacts/` (fora do git); o pré-processamento é um módulo compartilhado só; toda mudança no modelo reporta Top-1 e Top-5 no mesmo split de teste; os detalhes vão para o `docs/MODEL.md` a partir da etapa 1.

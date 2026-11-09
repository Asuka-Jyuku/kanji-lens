# Modelo e pré-processamento

O que o KanjiLens faz com os traços e as imagens antes do modelo, e, a partir da etapa 1, o dataset, o treino, as métricas e as versões do modelo. Este documento muda junto com o código: toda mudança em dataset, pré-processamento, treino ou modelo atualiza esta página no mesmo PR (`CLAUDE.md`, "Documentos nascem com o assunto").

O dataset (ETL9G) e as classes (os 1.026 教育漢字) estão decididos na [ADR 0021](adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md). A seção do dataset nasce com o carregamento dele ([#13](https://github.com/Asuka-Jyuku/kanji-lens/issues/13)).

## Pré-processamento

Existe uma implementação só, em `ml/src/kanjilens_ml/preprocessing/`, que o treino e o backend importam (`CLAUDE.md`, "Pré-processamento sempre junto"). Hoje ela tem a parte dos traços. A imagem da CNN entra no segundo PR da [#14](https://github.com/Asuka-Jyuku/kanji-lens/issues/14), quando houver amostras do ETL para comparar com o canvas.

### Traços normalizados (avaliação da ordem)

`kanjilens_ml.preprocessing.strokes.normalize_strokes(strokes, points_per_stroke=24)` é a entrada da avaliação da ordem contra o KanjiVG ([ADR 0016](adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)). A mesma função normaliza os traços do canvas e os de referência do KanjiVG, para os dois ficarem no mesmo sistema de coordenadas.

**Entrada:** os traços como o canvas manda, cada ponto `[x, y, t]` em pixels CSS ([ADR 0016](adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)), ou `[x, y]`, como sai do KanjiVG.

**Passos:**
1. **Caixa do caractere:** a caixa que envolve todos os pontos desenhados. Ela é calculada antes da reamostragem, porque os pontos reamostrados podem pular um canto do traço.
2. **Escala e posição:** o caractere é escalado pelo **lado maior** da caixa e centrado no quadrado `[0, 1] × [0, 1]`. A proporção se mantém: um kanji alto e estreito continua alto e estreito, sem ser esticado para encher o quadrado.
3. **Reamostragem:** cada traço vira `points_per_stroke` pontos **igualmente espaçados pelo comprimento**, do primeiro ao último ponto. Pontos repetidos (o dedo parado na tela) não somam comprimento.

**O que se mantém:** a ordem dos traços, a separação entre eles e a direção de cada um, porque são o que a avaliação compara. **O tempo `t` é ignorado:** a reamostragem é pelo comprimento, como no protótipo.

**Casos de borda:**
- um traço de um ponto só, ou de pontos todos no mesmo lugar, vira esse ponto repetido;
- um desenho inteiro num ponto só vai para o centro, `(0,5; 0,5)`;
- traço sem pontos, coordenada não finita ou menos de 2 pontos por traço levantam `ValueError`;
- nenhum traço devolve uma lista vazia.

**Parâmetro:** `POINTS_PER_STROKE = 24`, o valor do protótipo ([spike](spikes/stroke-order-evaluation.md)). Ele se ajusta na [#29](https://github.com/Asuka-Jyuku/kanji-lens/issues/29), com desenhos reais, junto com a margem de direção e o comprimento mínimo.

**Formato de saída:** listas de tuplas `(x, y)` de `float`, que atravessam o processo de inferência por pickle ([ADR 0019](adr/0019-in-memory-job-queue-with-one-inference-process.md)).

**Sem PyTorch:** o módulo é Python puro, e um contrato do Import Linter (`ml/pyproject.toml`) impede que ele importe o PyTorch, porque a avaliação da ordem o importa ([ADR 0012](adr/0012-ordered-mode-as-stroke-order-evaluation.md)).

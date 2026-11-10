# Modelo e pré-processamento

O que o KanjiLens faz com os traços e as imagens antes do modelo, a avaliação da ordem dos traços, os desenhos do canvas usados nos testes e, a partir da etapa 1, o dataset, o treino, as métricas e as versões do modelo. Este documento muda junto com o código: toda mudança em dataset, pré-processamento, treino ou modelo atualiza esta página no mesmo PR (`CLAUDE.md`, "Documentos nascem com o assunto").

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

**Parâmetro:** `POINTS_PER_STROKE = 24`, o valor do protótipo ([spike](spikes/stroke-order-evaluation.md)). Ele faz parte dos parâmetros da [avaliação da ordem](#avaliação-da-ordem-dos-traços), que se ajustam com desenhos reais.

**Traços unidos:** `resample_polyline(polyline, count)` é a reamostragem pelo comprimento, pública para a avaliação da ordem montar o caminho de traços vizinhos unidos.

**Formato de saída:** listas de tuplas `(x, y)` de `float`, que atravessam o processo de inferência por pickle ([ADR 0019](adr/0019-in-memory-job-queue-with-one-inference-process.md)).

**Sem PyTorch:** o módulo é Python puro, e um contrato do Import Linter (`ml/pyproject.toml`) impede que ele importe o PyTorch, porque a avaliação da ordem o importa ([ADR 0012](adr/0012-ordered-mode-as-stroke-order-evaluation.md)).

## Avaliação da ordem dos traços

No modo `ordered`, cada candidato do reconhecimento ganha a comparação do desenho com a ordem e a direção do KanjiVG ([ADR 0012](adr/0012-ordered-mode-as-stroke-order-evaluation.md)). O algoritmo é o da [ADR 0016](adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md), implementado em `ml/src/kanjilens_ml/stroke_order/` ([#29](https://github.com/Asuka-Jyuku/kanji-lens/issues/29)). É NumPy e SciPy, sem PyTorch, e um contrato do Import Linter garante isso.

### Como funciona

1. **Normalização:** o desenho e a referência passam pela mesma função ([traços normalizados](#traços-normalizados-avaliação-da-ordem)). Para cada grupo de até 3 traços vizinhos, o caminho unido também é reamostrado em 24 pontos.
2. **Custo entre traços:** a distância média entre os pontos, no quadrado de lado 1. Ela é calculada nos dois sentidos, e vale o menor.
3. **Correspondência:** o algoritmo húngaro (`scipy.optimize.linear_sum_assignment`).
4. **Hipóteses** quando a quantidade de traços difere em 1 ou 2:
   - o lado com mais traços pode ter traços vizinhos unidos: na referência, eles viram **traços unidos** (`joined`); no desenho, viram **traço quebrado** (`broken`);
   - o que nenhuma união explica fica **fora da correspondência**, como um traço que faltou ou um traço a mais;
   - cada traço fora da correspondência custa `unmatched_stroke_cost`;
   - ganha a hipótese de menor custo total; no empate, a com menos uniões.
5. **Ordem:** um traço está fora de ordem quando o lugar dele entre os traços pareados é diferente do lugar da referência dele. A posição é contada entre os traços pareados, então um traço que faltou não desloca os outros.
6. **Direção:** um traço vai no sentido errado quando o custo no sentido inverso fica abaixo de `direction_margin` vezes o custo no sentido direto, e nem o traço nem a referência são mais curtos que `min_direction_length`.
   - A direção de um traço quebrado não é conferida, porque não há um traço só para apontar.
7. **Sem avaliação:** com mais de 2 traços de diferença, o motivo é `stroke_count_mismatch`; sem referência, `reference_missing`.

**Uso:** o desenho é preparado uma vez por job (`PreparedStrokes`) e comparado com cada candidato (`evaluate_stroke_order`). As referências são lidas uma vez por processo (`KanjiVGReferences.load`), e cada kanji é preparado no primeiro uso e guardado. O resultado (`EvaluatedStrokeOrder` ou `NotEvaluatedStrokeOrder`) tem o formato da ADR 0016:
- `status`, `correct`, `expected_strokes`, `drawn_strokes`;
- `issues` com `order`, `direction`, `joined` e `broken`, numerados a partir de 1;
- `as_dict()` dá o JSON da resposta;
- tem também `cost`, a distância média dos pares, que **não vai para a API** e serve para ajustar a abstenção.

Os tipos espelham os do domínio do backend ([docs/architecture/domain.md](architecture/domain.md)), que o adapter da [#48](https://github.com/Asuka-Jyuku/kanji-lens/issues/48) converte.

### Parâmetros

| Parâmetro | Valor | De onde vem |
|---|---:|---|
| `points_per_stroke` | 24 | protótipo do [spike](spikes/stroke-order-evaluation.md) |
| `direction_margin` | 0,75 | protótipo |
| `min_direction_length` | 0,08 | protótipo |
| `max_count_difference` | 2 | ADR 0016 |
| `unmatched_stroke_cost` | 0,05 | medido aqui (abaixo) |

**`unmatched_stroke_cost` é novo.** Sem ele, deixar fora da correspondência um pedaço de traço quebrado não custava nada. Em traço curto, casar a referência com metade do traço custa tanto quanto o ruído, e o "quebrado" virava "traço a mais": só 70% de acerto com ruído leve, contra 99,5% no protótipo.

O custo escolhe entre explicar a diferença de traços por união e quebra ou por traço que faltou ou sobrou. Varredura no benchmark sintético (abaixo), em % de acerto exato com ruído 0,015 / 0,03:

| Custo | quebrado | a mais | a menos |
|---:|---:|---:|---:|
| 0 | 70,0 / 59,0 | 97,5 / 91,0 | 99,8 / 92,2 |
| 0,03 | 92,8 / 81,8 | 93,8 / 87,0 | 98,8 / 87,8 |
| **0,05** | **98,5 / 89,5** | **89,0 / 81,5** | **94,8 / 81,5** |
| 0,1 | 99,2 / 94,5 | 69,2 / 56,8 | 68,2 / 59,2 |
| 0,2 | 99,2 / 94,5 | 23,8 / 18,2 | 15,2 / 13,5 |

O 0,05 equilibra os três casos. Quanto da diferença de traços vem de traço quebrado e quanto de traço a mais ou a menos só os desenhos reais vão dizer. A margem de direção e o comprimento mínimo ficaram com os valores do protótipo: o benchmark sintético não tem traço curto mal desenhado para ajustá-los.

### Abstenção por custo alto

**Ainda não implementada; decisão desta etapa.** A ideia do spike é responder "não foi possível avaliar a ordem" quando o desenho está muito longe da referência, em vez de apontar erros. O custo médio sobe com o ruído nos sintéticos (0,044, 0,066 e 0,093 nos três níveis), então ele serve de sinal. Mas:
- o limiar depende da escala do custo em desenhos reais, que o sintético não reproduz;
- a resposta precisa de um motivo novo em `not_evaluated`, o que muda a ADR 0016, o domínio e a API.

Por isso o `cost` já sai no resultado, e a abstenção entra com o conjunto de desenhos reais ([#66](https://github.com/Asuka-Jyuku/kanji-lens/issues/66)).

### Dados de referência (KanjiVG)

- **Versão fixada:** `r20260714`, arquivo `kanjivg-20260714-main.zip`, SHA-256 `b5df6cd2bc249dd49b8041eb99e38ba9f8dc6b9ea57962a80084b4a315d1a7fc`. O checksum foi calculado no download e bate com o que o GitHub publica para o asset.
- **Preparação:** `uv run --directory ml python scripts/prepare_kanjivg.py [--classes ARQUIVO]`.
  - Baixa o zip uma vez para `ml/datasets/kanjivg/`, confere o checksum e grava `ml/artifacts/kanjivg/kanjivg-references.json`, com um `README.md` de atribuição e licença ao lado. As duas pastas ficam fora do git.
  - Os traços de cada kanji ficam como linhas poligonais no quadro 109×109 do KanjiVG, na ordem e no sentido oficiais. As curvas Bézier são amostradas em 8 pontos por segmento.
  - Sem `--classes`, entram todos os kanji do bloco CJK unificado: são 6.422, contando os blocos de extensão, num arquivo de cerca de 20 MB, lido em 0,6 s.
  - Com a lista de classes, que nasce com o dataset ([#13](https://github.com/Asuka-Jyuku/kanji-lens/issues/13), ADR 0021), entram só esses kanji. Um kanji que falte faz o script terminar com erro.
- **Versão conferida ao carregar:** o loader recusa um arquivo de outro formato ou de outra versão do KanjiVG. Trocar a versão é decisão consciente: novo checksum no código e a avaliação medida de novo.
- **Licença:** o KanjiVG é © Ulrich Apel, sob **CC BY-SA 3.0** ([kanjivg.tagaini.net](https://kanjivg.tagaini.net)). Os dados derivados mantêm a licença e a atribuição: elas vão no próprio arquivo (`source`) e no `README.md` gerado ao lado, à parte da licença MIT do código. A atribuição na interface fica numa issue do frontend.

### Medição em desenhos sintéticos

`uv run --directory ml python scripts/benchmark_stroke_order.py` repete o método do [spike, seção 4](spikes/stroke-order-evaluation.md#4-como-foi-medido) com a implementação de verdade e as referências preparadas:
- **conjunto:** 400 kanjis sorteados (seed 0) do KanjiVG, de 3 a 24 traços, com média de 12,3;
- **distorção:** global, mais um deslocamento por traço e ruído suavizado por ponto, num canvas de 320 px;
- **casos:** os cinco do spike, mais **traço a mais** (uma marca curta solta) e **traço a menos**;
- **acerto exato:** os problemas apontados são exatamente os esperados;
- **falso alarme:** erro de ordem ou de direção onde não há nenhum.

Os números servem para escolher parâmetros e pegar regressões, **não são a acurácia do produto**. O gerador de ruído não é o do protótipo, que não foi para o repositório, então a comparação com o spike é aproximada.

Medido em 2026-11-09, na máquina de treino (Ryzen 7 9800X3D), com Python 3.15, NumPy 2.5 e SciPy 1.18:

| Ruído | Caso | Acerto exato (%) | Falso alarme (%) |
|---|---|---:|---:|
| 0,015 | correta | 100,0 | 0,0 |
| 0,015 | troca | 100,0 | 0,0 |
| 0,015 | invertido | 98,2 | 0,0 |
| 0,015 | unidos | 100,0 | 0,0 |
| 0,015 | quebrado | 98,5 | 0,0 |
| 0,015 | a mais | 89,0 | 2,5 |
| 0,015 | a menos | 94,8 | 0,5 |
| 0,03 | correta | 96,5 | 3,5 |
| 0,03 | troca | 97,5 | 0,0 |
| 0,03 | invertido | 92,8 | 0,0 |
| 0,03 | unidos | 96,5 | 3,2 |
| 0,03 | quebrado | 89,5 | 3,8 |
| 0,03 | a mais | 81,5 | 9,8 |
| 0,03 | a menos | 81,5 | 8,5 |
| 0,05 | correta | 83,5 | 16,5 |
| 0,05 | troca | 81,2 | 0,0 |
| 0,05 | invertido | 70,8 | 0,0 |
| 0,05 | unidos | 81,8 | 16,5 |
| 0,05 | quebrado | 62,2 | 23,5 |
| 0,05 | a mais | 51,2 | 33,0 |
| 0,05 | a menos | 60,5 | 28,2 |

**Tempo:**
- **por candidato** (`evaluate_stroke_order`): 0,39 ms em média, 0,85 ms no p95 e 1,34 ms no máximo, somando todos os casos. Fica abaixo do protótipo (2 ms e 10 ms), porque a matriz de custo é calculada uma vez por par desenho e referência, e cada hipótese só recorta a matriz;
- **preparo do desenho**, uma vez por job: 0,48 ms em média;
- **preparo de cada referência**, só no primeiro uso: 0,46 ms.

A medição no notebook da escola fica para o benchmark ([ADR 0011](adr/0011-school-notebook-as-server-with-cpu-first-inference.md)).

**Leitura e limites conhecidos:**
- **Traços paralelos e parecidos** são a principal fonte de falso alarme em desenho correto: as barras de 鰻 ou 矍 trocam de par com o ruído. Com ruído moderado, isso acontece em 3,5% dos desenhos corretos.
- **Traço a mais ou a menos** é o caso mais frágil. A marca solta pode ser casada com um traço curto de verdade, e o traço deslocado gera erros de ordem falsos: 2,5% com ruído leve e cerca de 9% com ruído moderado.
- **Um traço movido para longe** marca também os traços entre a posição dele e a esperada, porque a ordem é por posição: cada um está, de fato, num lugar diferente do esperado. A troca de dois traços marca os dois, como na ADR 0016. Se a tela ([#59](https://github.com/Asuka-Jyuku/kanji-lens/issues/59), [#70](https://github.com/Asuka-Jyuku/kanji-lens/issues/70)) precisar de só "o traço movido", a mudança é no relatório, não na correspondência.
- **Direção:** 92,8% com ruído moderado. As falhas são traços curtos ou quase simétricos.

### Falta (parte da #29)

- **O conjunto fixo de desenhos reais**, com ordem certa e errada, feitos de propósito, com erros detectados × falsos alarmes. Os desenhos são gravados pela exportação do canvas (veja [Desenhos do canvas](#desenhos-do-canvas)), e é nesse conjunto que os parâmetros e a abstenção se ajustam.
- **O adapter do backend**, que liga o avaliador ao processo de inferência, é a [#48](https://github.com/Asuka-Jyuku/kanji-lens/issues/48).

## Desenhos do canvas

Os conjuntos fixos de teste são desenhos feitos no próprio app, gravados pela exportação do canvas ([#66](https://github.com/Asuka-Jyuku/kanji-lens/issues/66)). Eles servem a três trabalhos:
- o conjunto da avaliação da ordem, com ordem certa e errada ([#29](https://github.com/Asuka-Jyuku/kanji-lens/issues/29));
- a comparação do pré-processamento de um desenho do canvas com uma amostra do ETL ([#14](https://github.com/Asuka-Jyuku/kanji-lens/issues/14), parte 2);
- a acurácia com desenhos reais, o principal risco do projeto ([ARCHITECTURE.md, 7.4](ARCHITECTURE.md#74-pontos-de-atenção)), e o teste de carga.

### Como gravar

**Só no build de desenvolvimento** (`npm start`): abaixo do canvas fica o painel "Exportar desenho (desenvolvimento)".
1. Desenhe e escolha o modo, como num reconhecimento. Para o conjunto da ordem, use "Importa".
2. No painel, informe o kanji desenhado e a ordem usada. Se houve erro, informe também os números dos traços com o erro, contados como a API conta (a partir de 1, na ordem desenhada).
3. "Baixar JSON" salva o arquivo no aparelho, sem passar por servidor nenhum.

O build de produção não tem o painel: ele troca `app.dev-tools.development.ts` por `app.dev-tools.ts`, que não lista ferramenta nenhuma, e o CI confere o bundle depois do build (`npm run check:production-bundle`). Na escola, nenhum desenho de aluno sai do aparelho (`CLAUDE.md`, "Segurança").

### Formato

Um arquivo por desenho, com o nome `u<código do kanji>-<ordem>-<data UTC>.json` (por exemplo, `u5341-order-20261110T052243Z.json` para 十 fora de ordem):

```json
{
  "format": "kanjilens-drawing",
  "version": 1,
  "exported_at": "2026-11-10T05:22:43.650Z",
  "label": { "kanji": "十", "stroke_order": "order", "strokes": [1, 2] },
  "request": {
    "stroke_order_mode": "ordered",
    "canvas": { "width": 358, "height": 358 },
    "strokes": [[[179, 53.7, 0], [179, 74.58, 18]], [[71.6, 161.1, 466]]]
  }
}
```

(Encurtado: o arquivo real tem 13 pontos por traço, um ponto por linha, com os números como o navegador os mediu.)

- **`request`** é o corpo do `POST /api/recognitions`, sem mudança nenhuma: os traços como foram desenhados ([ADR 0016](adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)). A API recusa campo desconhecido, por isso o gabarito fica ao lado, e não dentro dele.
- **`label`** é o gabarito, preenchido por quem desenhou:
  - `kanji`: o kanji pretendido, um caractere;
  - `stroke_order`: `correct`, ou o erro feito de propósito. Os erros são os tipos da ADR 0016 (`order`, `direction`, `joined`, `broken`) e mais `extra` e `missing`, um traço a mais ou a menos;
  - `strokes`: os traços desenhados com o erro, a partir de 1; vazio quando a ordem está certa.
- **`format` e `version`** identificam o formato. Mudança incompatível sobe a versão, e quem lê confere os dois.

### Onde ficam

- **Conjuntos de teste:** `ml/drawings/<conjunto>/`, versionados. O primeiro, o da ordem dos traços, vai em `ml/drawings/stroke-order/`. A pasta nasce com os primeiros desenhos reais.
- **Amostras do formato:** `backend/tests/fixtures/drawings/`, dois desenhos de 十 gravados pelo painel no Chromium com toque emulado. Não são desenhos de pessoa e não entram em conjunto nenhum.
- **Teste:** `backend/tests/adapters/test_exported_drawings.py` manda o `request` de cada arquivo das duas pastas ao `POST /api/recognitions` e confere o gabarito. Um arquivo que a API não aceita sem mudança quebra o teste.

**Só desenhos da equipe.** Desenho de aluno só entra com ADR antes (`CLAUDE.md`, "Segurança"). Os conjuntos não têm nome nem dado de quem desenhou.

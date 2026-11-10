# Modelo e pré-processamento

O que o KanjiLens faz com os traços antes de avaliar, como a avaliação da ordem funciona, e os desenhos do canvas usados nos testes. O dataset, o treino e o modelo entram aqui quando existirem. As classes e o ETL9G estão na [ADR 0021](adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md). Enquanto o site do ETL estiver fora, o treino usa desenhos sintéticos do KanjiVG, medidos só em desenhos reais ([ADR 0022](adr/0022-synthetic-training-data-from-kanjivg-while-etl-is-down.md)).

## Pré-processamento

Uma implementação só, em `ml/src/kanjilens_ml/preprocessing/`, usada pelo treino e pelo backend. Hoje tem os traços. A imagem da CNN entra na segunda parte da [#14](https://github.com/Asuka-Jyuku/kanji-lens/issues/14), quando houver amostras do ETL para comparar com o canvas.

### Traços normalizados (avaliação da ordem)

`normalize_strokes(strokes, points_per_stroke=24)`, em `kanjilens_ml.preprocessing.strokes`. A mesma função trata os traços do canvas e os do KanjiVG, para os dois ficarem no mesmo sistema de coordenadas ([ADR 0016](adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)).

- **Entrada:** pontos `[x, y, t]` em pixels CSS, como o canvas manda, ou `[x, y]`, como sai do KanjiVG.
- **Passos:**
  1. calcula a caixa de todos os pontos (antes de reamostrar, para não perder cantos);
  2. escala pelo lado maior da caixa e centraliza em `[0, 1] × [0, 1]`, mantendo a proporção;
  3. reamostra cada traço em 24 pontos igualmente espaçados pelo comprimento.
- **Mantém** a ordem, a separação e a direção dos traços. **Ignora** o tempo `t`.
- **Casos de borda:**
  - traço de um ponto só, ou parado num lugar, vira esse ponto repetido;
  - desenho inteiro num ponto vai para o centro, `(0,5; 0,5)`;
  - traço vazio, coordenada não finita ou menos de 2 pontos por traço levantam `ValueError`;
  - sem traços, devolve lista vazia.
- **Saída:** listas de tuplas `(x, y)`, que passam pelo pickle até o processo de inferência.
- `resample_polyline(polyline, count)` é a reamostragem, pública para a avaliação montar traços vizinhos unidos.
- **Sem PyTorch:** um contrato do Import Linter garante isso.

## Avaliação da ordem dos traços

No `ordered`, cada candidato ganha a comparação do desenho com a ordem e a direção do KanjiVG. O algoritmo é o da [ADR 0016](adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md), em `ml/src/kanjilens_ml/stroke_order/` ([#29](https://github.com/Asuka-Jyuku/kanji-lens/issues/29)), com NumPy e SciPy, sem PyTorch.

### Como funciona

1. **Normaliza** o desenho e a referência com a mesma função. Grupos de até 3 traços vizinhos também viram um caminho unido, reamostrado em 24 pontos.
2. **Custo entre dois traços:** a distância média entre os pontos, nos dois sentidos; vale o menor.
3. **Pareia** os traços com o algoritmo húngaro (`scipy.optimize.linear_sum_assignment`).
4. **Quando a quantidade difere em 1 ou 2**, testa hipóteses:
   - traços vizinhos da referência unidos num só desenhado (`joined`), ou um traço da referência desenhado em pedaços (`broken`);
   - o que nenhuma união explica fica sem par (traço a mais ou a menos), e cada um custa `unmatched_stroke_cost`;
   - ganha a hipótese de menor custo; no empate, a com menos uniões.
5. **Ordem:** um traço está fora de ordem quando a posição dele entre os pareados difere da posição da referência. Um traço que faltou não desloca os outros.
6. **Direção:** está invertida quando o custo no sentido contrário fica abaixo de `direction_margin` × o custo no sentido certo, e nenhum dos dois traços é mais curto que `min_direction_length`. Traço quebrado não tem a direção conferida.
7. **Sem avaliação:** mais de 2 traços de diferença dá `stroke_count_mismatch`; kanji sem referência dá `reference_missing`.

**Uso:** o desenho é preparado uma vez por job (`PreparedStrokes`) e comparado com cada candidato (`evaluate_stroke_order`). As referências são lidas uma vez por processo (`KanjiVGReferences.load`), e cada kanji é preparado no primeiro uso. O resultado tem o formato da ADR 0016 (`status`, `correct`, `expected_strokes`, `drawn_strokes`, `issues` numerados a partir de 1, e `as_dict()` para o JSON). Também traz `cost`, que **não vai para a API** e serve para estudar a abstenção.

A ligação com o backend é a [#48](https://github.com/Asuka-Jyuku/kanji-lens/issues/48).

### Parâmetros

| Parâmetro | Valor | De onde vem |
|---|---:|---|
| `points_per_stroke` | 24 | protótipo do [spike](spikes/stroke-order-evaluation.md) |
| `direction_margin` | 0,75 | protótipo |
| `min_direction_length` | 0,08 | protótipo |
| `max_count_difference` | 2 | ADR 0016 |
| `unmatched_stroke_cost` | 0,05 | medido aqui |

**Por que `unmatched_stroke_cost`:** sem ele, deixar um pedaço de traço quebrado sem par não custava nada, e "quebrado" virava "traço a mais" (70% de acerto com ruído leve). A varredura abaixo é em % de acerto exato, com ruído 0,015 / 0,03:

| Custo | quebrado | a mais | a menos |
|---:|---:|---:|---:|
| 0 | 70,0 / 59,0 | 97,5 / 91,0 | 99,8 / 92,2 |
| 0,03 | 92,8 / 81,8 | 93,8 / 87,0 | 98,8 / 87,8 |
| **0,05** | **98,5 / 89,5** | **89,0 / 81,5** | **94,8 / 81,5** |
| 0,1 | 99,2 / 94,5 | 69,2 / 56,8 | 68,2 / 59,2 |
| 0,2 | 99,2 / 94,5 | 23,8 / 18,2 | 15,2 / 13,5 |

O 0,05 equilibra os três casos. A margem de direção e o comprimento mínimo ficaram com os valores do protótipo: os sintéticos não têm traço curto mal desenhado para ajustá-los. Os desenhos reais vão dizer se o equilíbrio está certo.

### Abstenção por custo alto

**Ainda não existe.** A ideia é responder "não deu para avaliar a ordem" quando o desenho está longe demais da referência. O custo médio sobe com o ruído (0,044, 0,066 e 0,093 nos três níveis), então serve de sinal. Mas o limiar precisa de desenhos reais, e a resposta pede um motivo novo em `not_evaluated`, o que muda a ADR 0016, o domínio e a API. Por isso o `cost` já sai no resultado, e a decisão espera os desenhos reais.

### Dados de referência (KanjiVG)

- **Versão fixada:** `r20260714`, arquivo `kanjivg-20260714-main.zip`, SHA-256 `b5df6cd2bc249dd49b8041eb99e38ba9f8dc6b9ea57962a80084b4a315d1a7fc` (bate com o que o GitHub publica).
- **Preparação:** `uv run --directory ml python scripts/prepare_kanjivg.py [--classes ARQUIVO]`.
  - Baixa o zip uma vez para `ml/datasets/kanjivg/`, confere o checksum e grava `ml/artifacts/kanjivg/kanjivg-references.json`, com um `README.md` de atribuição ao lado. As duas pastas ficam fora do git.
  - Cada traço vira uma linha poligonal no quadro 109×109 do KanjiVG, na ordem e no sentido oficiais. As curvas Bézier viram 8 pontos por segmento.
  - Sem `--classes`: todos os 6.422 kanji do bloco CJK, num arquivo de cerca de 20 MB, lido em 0,6 s.
  - Com a lista de classes ([#13](https://github.com/Asuka-Jyuku/kanji-lens/issues/13)): só esses kanji. Se faltar algum, o script termina com erro.
- **O loader recusa** arquivo de outro formato ou de outra versão do KanjiVG. Trocar a versão pede checksum novo no código e a avaliação medida de novo.
- **Licença:** KanjiVG © Ulrich Apel, **CC BY-SA 3.0** ([kanjivg.tagaini.net](https://kanjivg.tagaini.net)). Os dados derivados mantêm a licença e a atribuição, no próprio arquivo (`source`) e no `README.md` gerado, à parte da licença MIT do código. A atribuição na tela fica para uma issue do frontend.

### Medição em desenhos sintéticos

`uv run --directory ml python scripts/benchmark_stroke_order.py` repete o método do [spike, seção 4](spikes/stroke-order-evaluation.md#4-como-foi-medido) com o código de verdade:
- **conjunto:** 400 kanji sorteados (seed 0) do KanjiVG, de 3 a 24 traços (média 12,3);
- **distorção:** global, mais um deslocamento por traço e ruído por ponto, num canvas de 320 px;
- **casos:** os cinco do spike, mais traço a mais (uma marca curta solta) e traço a menos;
- **acerto exato:** os problemas apontados são exatamente os esperados;
- **falso alarme:** erro de ordem ou direção onde não há nenhum.

Os números servem para escolher parâmetros e pegar regressões. **Não são a acurácia do produto.** O gerador de ruído não é o do protótipo, então a comparação com o spike é aproximada.

Medido em 2026-11-09, na máquina de treino (Ryzen 7 9800X3D), Python 3.15, NumPy 2.5 e SciPy 1.18:

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
- por candidato: 0,39 ms em média, 0,85 ms no p95 e 1,34 ms no máximo (o protótipo dava 2 ms e 10 ms);
- preparo do desenho, uma vez por job: 0,48 ms;
- preparo de cada referência, no primeiro uso: 0,46 ms.

A medição no notebook da escola vem com o benchmark ([ADR 0011](adr/0011-school-notebook-as-server-with-cpu-first-inference.md)).

**Limites conhecidos:**
- **Traços paralelos parecidos** (as barras de 鰻 ou 矍) trocam de par com o ruído: 3,5% de falso alarme em desenho correto, com ruído moderado.
- **Traço a mais ou a menos** é o caso mais frágil: 2,5% de falso alarme com ruído leve, cerca de 9% com moderado.
- **Um traço movido para longe** marca também os traços entre a posição dele e a esperada, porque a ordem é por posição. Se a tela ([#59](https://github.com/Asuka-Jyuku/kanji-lens/issues/59), [#70](https://github.com/Asuka-Jyuku/kanji-lens/issues/70)) quiser mostrar só "o traço movido", a mudança é no relatório, não no pareamento.
- **Direção:** 92,8% com ruído moderado; as falhas são traços curtos ou quase simétricos.

**Falta:** o conjunto fixo de desenhos reais, com ordem certa e errada ([Desenhos do canvas](#desenhos-do-canvas)). É nele que os parâmetros e a abstenção se ajustam.

## Desenhos do canvas

Os conjuntos de teste são desenhos feitos no próprio app e gravados pela exportação do canvas ([#66](https://github.com/Asuka-Jyuku/kanji-lens/issues/66)). Servem para:
- o conjunto da avaliação da ordem ([#29](https://github.com/Asuka-Jyuku/kanji-lens/issues/29));
- comparar o pré-processamento do canvas com o ETL ([#14](https://github.com/Asuka-Jyuku/kanji-lens/issues/14), parte 2);
- medir a acurácia com desenhos reais, o maior risco do projeto ([ARCHITECTURE.md, 7.4](ARCHITECTURE.md#74-pontos-de-atenção)), e o teste de carga.

### Como gravar

**Só no build de desenvolvimento** (`npm start`). Abaixo do canvas fica o painel "Exportar desenho (desenvolvimento)":
1. Desenhe e escolha o modo. Para o conjunto da ordem, use "Importa".
2. Informe o kanji e a ordem usada. Se fez um erro de propósito, informe os traços com o erro, contados a partir de 1.
3. "Baixar JSON" salva o arquivo no aparelho, sem passar por servidor.

No build de produção o painel não existe, e o CI confere isso (`npm run check:production-bundle`). Na escola, nenhum desenho de aluno sai do aparelho.

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

(Encurtado: o arquivo real tem 13 pontos por traço, um ponto por linha.)

- **`request`** é o corpo do `POST /api/recognitions`, sem mudança nenhuma. A API recusa campo desconhecido, por isso o gabarito fica ao lado.
- **`label`** é o gabarito:
  - `kanji`: o kanji pretendido;
  - `stroke_order`: `correct`, ou o erro feito de propósito: `order`, `direction`, `joined`, `broken` (os tipos da ADR 0016), `extra` ou `missing`;
  - `strokes`: os traços com o erro, a partir de 1; vazio se a ordem está certa.
- **`format` e `version`** identificam o formato. Mudança incompatível sobe a versão.

### Onde ficam

- **Conjuntos de teste:** `ml/drawings/<conjunto>/`, versionados. O da ordem dos traços vai em `ml/drawings/stroke-order/`, que nasce com os primeiros desenhos.
- **Amostras do formato:** `backend/tests/fixtures/drawings/`, dois desenhos de 十 feitos no Chromium com toque emulado. Não são de pessoa e não entram em conjunto nenhum.
- **Teste:** `backend/tests/adapters/test_exported_drawings.py` manda o `request` de cada arquivo das duas pastas à API e confere o gabarito.

**Só desenhos da equipe.** Desenho de aluno só com ADR antes. Os conjuntos não guardam nome nem dado de quem desenhou.

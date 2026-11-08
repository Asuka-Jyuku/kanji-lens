# 0016. Avaliação da ordem por correspondência bipartite, formato dos traços e uso do KanjiVG

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0004](0004-clean-and-hexagonal-architecture.md), [0007](0007-local-execution-over-the-lan.md), [0012](0012-ordered-mode-as-stroke-order-evaluation.md), [0014](0014-ml-tooling-python-uv-ruff-pytest-import-linter.md)

## Contexto

A [ADR 0012](0012-ordered-mode-as-stroke-order-evaluation.md) decidiu que o modo `ordered` compara os traços desenhados com a ordem e a direção do KanjiVG. Ficaram em aberto:
- o algoritmo;
- quantos candidatos avaliar;
- se a avaliação reordena os candidatos;
- o formato dos pontos;
- o formato da resposta;
- como o KanjiVG entra no projeto.

O [spike #28](../spikes/stroke-order-evaluation.md) conferiu o KanjiVG na fonte oficial e mediu três algoritmos em 400 kanjis desenhados de forma sintética, com três níveis de ruído e cinco casos (correta, troca, invertido, unidos, quebrado).

**KanjiVG:** licença **CC BY-SA 3.0**, com atribuição a Ulrich Apel e link para [kanjivg.tagaini.net](https://kanjivg.tagaini.net). A versão mais recente é a `r20260714`, com 6.413 kanjis.

**Resultados (ruído moderado):**
- o **guloso** dá 23% de falso alarme em desenho correto;
- o **bipartite** dá 0,8% de falso alarme e acha 99,5% das trocas, mas trata todo traço unido ou quebrado como erro de ordem;
- o **bipartite com hipóteses de união e quebra** mantém o desempenho do bipartite e acerta cerca de 97% dos traços unidos e quebrados, em 2 ms em média (10 ms no p95).

## Alternativas consideradas

- **Guloso** (cada traço pega a referência mais próxima): simples. Erra muito já com ruído leve.
- **Bipartite** (algoritmo húngaro): correspondência ótima e rápida. Falha quando a quantidade de traços difere da referência.
- **Bipartite com hipóteses de união e quebra:** trata traços unidos e quebrados (até 2) testando as combinações vizinhas. Custa algumas vezes mais, ainda na casa dos milissegundos.
- **Cube search, *DP matching*, avaliação incremental com contexto:** a literatura relata bons resultados. São mais complexos ou feitos para outro caso (sub-traços, avaliação durante o desenho), e não foram necessários diante dos números do bipartite.
- **Formato dos pontos:**
  - normalizado no frontend: tira um passo do backend, mas leva pré-processamento para fora do `kanjilens_ml`;
  - coordenadas como desenhadas, com o tamanho do canvas: o pré-processamento fica num lugar só.
- **KanjiVG:**
  - versionado no git: simples, mas sobe um volume de dados derivados que cresce com as classes;
  - baixado em tempo de execução: quebra a regra de não sair para a rede;
  - **versão fixada, com checksum, gerada por script de preparação, fora do git:** igual aos pesos do modelo.

## Decisão

- **Algoritmo: bipartite com hipóteses de união e quebra.**
  1. Cada traço é reamostrado em pontos igualmente espaçados, e o caractere é normalizado pela caixa que o envolve.
  2. O custo entre traços é a distância média entre os pontos, nos dois sentidos.
  3. A correspondência sai do algoritmo húngaro (`scipy.optimize.linear_sum_assignment`).
  4. Quando a quantidade de traços difere em 1 ou 2, entram as hipóteses de traços vizinhos unidos (na referência) ou quebrados (no desenho), e vale a de menor custo.
  5. A **direção** é apontada quando o sentido inverso é claramente melhor (margem) e o traço não é curto demais.
  6. Com diferença maior que 2 traços, ou kanji fora do KanjiVG, a ordem **não é avaliada**, com o motivo na resposta.

  Os parâmetros iniciais do protótipo (24 pontos por traço, margem 0,75, comprimento mínimo 0,08) se ajustam na [#29](https://github.com/Asuka-Jyuku/kanji-lens/issues/29), com desenhos reais.
- **Candidatos:** a ordem é avaliada para **todos os candidatos devolvidos** (top-K), e a tela mostra a do candidato escolhido. A avaliação **só anota: não reordena** o ranking do reconhecimento.
- **Formato da requisição** (`POST /api/recognitions`):

  ```json
  {
    "stroke_order_mode": "ordered",
    "canvas": { "width": 320, "height": 320 },
    "strokes": [
      [[41.0, 30.5, 0], [41.2, 88.0, 140]],
      [[44.1, 31.0, 410], [118.3, 29.4, 590], [117.9, 92.2, 780]]
    ]
  }
  ```

  - `x` e `y` são pixels CSS a partir do canto superior esquerdo do canvas, como desenhados; `t` são milissegundos desde o primeiro ponto, inteiro e não decrescente.
  - O frontend não normaliza nada.
  - **Limites iniciais**, conferidos no adapter HTTP antes da fila:
    - até **40 traços**, **1.000 pontos por traço** e **10.000 pontos no total**;
    - coordenadas finitas, dentro do canvas com folga de 10%;
    - `canvas` entre 64 e 4.096 px por lado.

    Acima disso, `413` ou `400`, com código de erro.
- **Formato da resposta** do modo `ordered`: cada candidato leva a sua avaliação. As posições são numeradas a partir de 1, para a tela.

  ```json
  {
    "kanji": "日",
    "confidence": 0.81,
    "stroke_order": {
      "status": "evaluated",
      "correct": false,
      "expected_strokes": 4,
      "drawn_strokes": 4,
      "issues": [
        { "type": "order", "drawn_stroke": 3, "expected_position": 4 },
        { "type": "direction", "drawn_stroke": 2 }
      ]
    }
  }
  ```

  - `type` pode ser `order`, `direction`, `joined` (com `expected_strokes`: as posições unidas) ou `broken` (com `expected_stroke`).
  - `correct` olha só ordem e direção; traços unidos ou quebrados aparecem como observação.
  - Sem avaliação: `"status": "not_evaluated"`, com `reason` (`stroke_count_mismatch` ou `reference_missing`).
  - No modo `unordered`, o campo não existe.
- **KanjiVG:**
  - versão **fixada** (`r20260714`, arquivo `kanjivg-20260714-main.zip`, com SHA-256 registrado);
  - um **script de preparação** em `ml/` baixa, confere o checksum e gera os traços de referência dos kanjis da lista de classes;
  - os dados derivados ficam fora do git (como `ml/artifacts/`) e são carregados uma vez no processo de inferência;
  - **atribuição** no README e na interface (um "sobre" ou o rodapé), e os dados derivados mantêm a CC BY-SA 3.0.
- **Dependência nova:** SciPy no `kanjilens_ml`, só para o módulo `stroke_order`, que continua sem PyTorch. O SciPy 1.18 tem pacote para o Python 3.15 no Windows.

## Consequências

- **Positivas:**
  - avaliação determinística, testável com casos fixos e explicável traço a traço;
  - alguns milissegundos por candidato, desprezível perto da CNN;
  - trata o caso comum de traços unidos ou quebrados sem acusar erro de ordem falso;
  - o formato dos pontos deixa todo o pré-processamento no `kanjilens_ml`;
  - o KanjiVG fica numa versão conhecida, sem rede em execução.
- **Negativas:**
  - **os números são de desenho sintético.** Com escrita muito irregular, os falsos alarmes sobem (cerca de 10% com ruído forte); a abstenção por custo alto e o ajuste dos parâmetros dependem de desenhos reais (#29);
  - **a direção é o caso mais frágil** em traços curtos ou quase simétricos;
  - **mais de 2 traços de diferença** não são avaliados;
  - **SciPy é mais uma dependência binária** no ambiente;
  - **a CC BY-SA 3.0 vale para os dados derivados**, que não podem ir para a licença MIT do código, e a atribuição precisa aparecer na interface;
  - **atualizar o KanjiVG** é decisão consciente: nova versão, novo checksum e a avaliação da ordem medida de novo.
- **Na prática:**
  - a #29 implementa o algoritmo em `kanjilens_ml/stroke_order/`, com os testes de casos fixos e o conjunto de desenhos reais;
  - o script de preparação do KanjiVG entra no `docs/RUNNING.md` quando nascer;
  - os limites de entrada valem no adapter HTTP (`CLAUDE.md`, "Segurança") e vão para o `docs/SECURITY.md` quando a API for exposta;
  - o canvas segue o formato da requisição (skill `angular-conventions`).

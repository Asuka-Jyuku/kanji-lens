# Spike: algoritmo de avaliação da ordem dos traços e formato de captura

> **Issue:** [#28](https://github.com/Asuka-Jyuku/kanji-lens/issues/28)  
> **Tipo:** spike técnico (protótipo e medição)  
> **Status:** decidido na [ADR 0016](../adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md). Os números são de desenhos sintéticos, e a validação com desenhos reais fica para a [#29](https://github.com/Asuka-Jyuku/kanji-lens/issues/29).  
> **Data:** 2026-11-08

---

## 1. Pergunta

A [ADR 0012](../adr/0012-ordered-mode-as-stroke-order-evaluation.md) decidiu que o modo `ordered` compara os traços desenhados com a ordem e a direção do KanjiVG. Este spike responde quatro perguntas:
- que algoritmo faz essa comparação;
- em que formato o canvas envia os pontos;
- como fica a resposta;
- como o KanjiVG entra no projeto.

## 2. KanjiVG

Conferido no repositório oficial ([KanjiVG/kanjivg](https://github.com/KanjiVG/kanjivg)) em 2026-11-08.

| Item | O que foi encontrado |
|---|---|
| Licença | **CC BY-SA 3.0**. O README oficial diz: "KanjiVG is copyright Ulrich Apel and released under the Creative Commons Attribution-Share Alike 3.0 licence". O cabeçalho de cada SVG pede para citar o uso do KanjiVG e linkar o site do projeto ([kanjivg.tagaini.net](https://kanjivg.tagaini.net)) |
| Versão mais recente | `r20260714`. O `kanjivg-20260714-main.zip` (12,6 MB) traz as formas sem variantes; o `.xml.gz` é considerado obsoleto pelo próprio projeto |
| Formato | Um SVG por caractere, num quadro de 109×109. Cada traço é um `<path id="kvg:XXXXX-sN">`, com N a posição na ordem oficial, e o desenho é feito de curvas Bézier (comandos `M`, `C`, `c`, `S`, `s`). O ponto inicial do path dá a direção do traço |
| Cobertura | 6.703 arquivos, dos quais 6.413 são kanjis do bloco CJK unificado. Cobre bem os 2.136 Jōyō |

## 3. Algoritmos comparados

Todos usam a mesma representação. Cada traço é reamostrado em 24 pontos igualmente espaçados pelo comprimento, e o caractere é normalizado pela caixa que envolve todos os traços. O custo entre um traço desenhado e um de referência é a distância média entre os pontos, calculada nos dois sentidos: o menor dá a correspondência, e a comparação entre eles dá a direção.

| Algoritmo | Como funciona |
|---|---|
| **Guloso** (baseline) | Cada traço desenhado, na ordem em que foi feito, pega o traço de referência mais próximo ainda livre |
| **Bipartite** | Correspondência ótima global entre traços desenhados e de referência, pelo algoritmo húngaro (`scipy.optimize.linear_sum_assignment`). A ordem está errada onde a sequência de referências pareadas foge da ordem do desenho |
| **Bipartite + união/quebra** | Igual ao bipartite, mas quando a quantidade de traços difere em até 2, testa as hipóteses de traços vizinhos unidos (na referência) ou quebrados (no desenho) e fica com a de menor custo |

**Ficaram de fora do protótipo:**
- **cube search (Cai, Uchida e Sakoe):** mais robusto, mas bem mais complexo; o bipartite já acerta perto de 100% nos casos sintéticos;
- ***DP matching*:** supõe ordem monotônica, então serve para alinhar sub-traços, não para achar troca de ordem;
- **avaliação incremental com contexto (Nguyen et al., 2019):** avalia a cada traço, durante o desenho, e o KanjiLens avalia depois de o aluno enviar;
- **classificador treinado:** precisaria de muitos exemplos rotulados de ordem errada.

As fontes estão no [spike de modelos, seção 5.3](model-and-runtime-evaluation.md#53-como-o-modo-ordered-costuma-ser-feito-pesquisa-de-2026-11-08).

## 4. Como foi medido

**Conjunto:** 400 kanjis sorteados do KanjiVG (seed 0), de 2 a 25 traços, com média de 12 traços.

**Desenho sintético:** para cada kanji, a referência foi "desenhada" com:
- distorção global (rotação de ±5°, escala de 0,85–1,15 por eixo, cisalhamento);
- deslocamento por traço;
- ruído suavizado por ponto;
- quantidade variável de pontos por traço.

O ruído é relativo ao tamanho do caractere: 0,015 é leve, 0,03 é moderado e 0,05 é forte.

**Casos testados:**
- **correta:** nada pode ser apontado, e o que for apontado conta como falso alarme;
- **troca:** dois traços aleatórios trocados; acerto é apontar exatamente os dois;
- **invertido:** um traço desenhado ao contrário;
- **unidos:** dois traços vizinhos feitos de uma vez;
- **quebrado:** um traço feito em duas partes.

**Tempo:** só o da avaliação de um candidato, com Python 3.15.2 e NumPy/SciPy numa máquina de desenvolvimento (Linux). O tempo no notebook da escola fica para o benchmark.

## 5. Resultados

Porcentagem de casos com a resposta exata:

| Ruído | Algoritmo | correta | troca | invertido | unidos | quebrado | ms médio | ms p95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0,015 | guloso | 88,5 | 90,2 | 88,8 | 0,0 | 0,0 | 0,27 | 0,52 |
| 0,015 | bipartite | 100,0 | 100,0 | 98,8 | 0,0 | 0,0 | 0,23 | 0,45 |
| 0,015 | **bipartite + união/quebra** | **100,0** | **100,0** | **98,8** | **99,2** | **99,5** | 2,21 | 10,11 |
| 0,03 | guloso | 76,8 | 79,0 | 76,8 | 0,0 | 0,0 | 0,27 | 0,53 |
| 0,03 | bipartite | 99,2 | 99,5 | 95,5 | 0,0 | 0,0 | 0,23 | 0,46 |
| 0,03 | **bipartite + união/quebra** | **99,2** | **99,5** | **95,5** | **97,8** | **96,8** | 2,20 | 10,19 |
| 0,05 | guloso | 56,0 | 56,8 | 51,2 | 0,0 | 0,0 | 0,26 | 0,52 |
| 0,05 | bipartite | 89,5 | 93,0 | 85,8 | 0,0 | 0,0 | 0,23 | 0,46 |
| 0,05 | **bipartite + união/quebra** | **89,5** | **93,0** | **85,8** | **89,8** | **83,2** | 2,20 | 9,98 |

**Leitura:**
- **O guloso perde já com ruído leve:** um traço "rouba" a referência de outro e gera falsos alarmes.
- **O bipartite resolve a correspondência:** com ruído leve e moderado, não dá falso alarme em desenho correto e acha as trocas.
- **Só a versão com união/quebra trata quantidade de traços diferente.** Sem ela, todo traço unido ou quebrado vira erro de ordem falso. O custo é de 2 ms em média e 10 ms no p95, por testar as combinações.
- **Direção é o caso mais frágil:** em traços curtos ou quase simétricos, a diferença entre os dois sentidos some no ruído. A margem e o comprimento mínimo da checagem de direção são parâmetros a ajustar.
- **Com ruído forte, os falsos alarmes chegam a cerca de 10%.** Para escrita muito irregular, a avaliação deveria poder se abster ("não foi possível avaliar a ordem") quando o custo total da correspondência for alto, em vez de apontar erros. Isso não foi medido aqui.

**Limitações:**
- O desenho é sintético: ruído e distorção não reproduzem os vícios reais da escrita (proporções, traços encurtados, variantes de forma).
- Os números servem para escolher o algoritmo, não como a acurácia do produto. A validação é com desenhos reais, num conjunto fixo de ordem certa e errada ([#29](https://github.com/Asuka-Jyuku/kanji-lens/issues/29)).
- O protótipo não vai para o repositório. A implementação sai na #29, com testes.

## 6. Formato de captura

Na avaliação da ordem, o que conta é a sequência dos traços e a dos pontos dentro de cada um. O tempo não entra no algoritmo escolhido, mas é barato guardar e serve para depuração e para avaliações futuras (velocidade, pausas).

- O canvas manda as coordenadas **como desenhadas**, em pixels CSS a partir do canto superior esquerdo do canvas, junto com o tamanho do canvas. A normalização é pré-processamento e fica no `kanjilens_ml` (`CLAUDE.md`, "Pré-processamento sempre junto").
- `t` é em milissegundos desde o primeiro ponto do desenho: inteiro, não decrescente.
- O `getCoalescedEvents()` deve ser usado quando o navegador oferecer. Ele exige contexto seguro (HTTPS) em parte dos navegadores, e o KanjiLens roda em HTTP na rede local, então sem ele o canvas usa os eventos `pointermove`, sem mudar o formato.

## 7. Recomendação

- **Bipartite + hipóteses de união e quebra** (até 2 traços de diferença), com checagem de direção por margem.
  - Acima de 2 traços de diferença, ou se o kanji não estiver no KanjiVG, a ordem não é avaliada, e a resposta diz o motivo.
- **Avaliar todos os candidatos devolvidos** (top-K): custa pouco e deixa a tela mostrar a avaliação do candidato que o aluno escolher. A avaliação só anota; **não reordena** os candidatos.
- **KanjiVG fixado numa versão:** `r20260714`, com o checksum do arquivo. Um script de preparação gera os dados derivados (traços reamostrados por kanji da lista de classes), fora do git, como os pesos do modelo. A aplicação em execução não acessa a rede.
- **Na #29:**
  - ajustar a margem de direção, o comprimento mínimo e a abstenção por custo alto, com desenhos reais;
  - acrescentar o SciPy como dependência do `kanjilens_ml`.

# 0022. Treino com desenhos sintéticos do KanjiVG enquanto o ETL estiver fora

- **Status:** Aceita
- **Data:** 2026-11-10
- **Relacionadas:** [0021](0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md) (classes e ETL9G), [0016](0016-stroke-order-check-by-bipartite-matching-and-capture-format.md) (KanjiVG e formato dos traços), [0006](0006-cnn-with-pytorch.md) (CNN)

## Contexto

O dataset escolhido na ADR 0021, o ETL9G, só pode ser baixado do site oficial. O site está fora do ar desde 2026-11-08, sem notícia de volta, e as cópias em outros sites ficam fora pelos termos. Sem dado de treino, a CNN das 240 primeiras classes não sai.

O app recebe traços desenhados no canvas (`[x, y, t]`), não papel escaneado. O projeto já tem o KanjiVG fixado com checksum, com os traços de cada kanji em ordem (ADR 0016). A pesquisa está no [spike "treinar sem o ETL"](../spikes/training-without-etl.md) (#78).

## Alternativas consideradas

- **Esperar o ETL:** a melhor base (200 amostras humanas por classe), mas sem data para voltar. O treino, a avaliação e a #48 ficariam parados.
- **TUAT Kuchibue/Nakayosi:** escrita japonesa *online*, com traços. É paga: ¥200 mil no preço acadêmico e ¥2 milhões no comercial. O contrato só libera de graça um uso de teste (試用) dos dados de 10 escritores, para pesquisa e sem condições definidas. Fica fora por enquanto ([#94](https://github.com/Asuka-Jyuku/kanji-lens/issues/94)).
- **CASIA OLHWDB/HWDB:** grátis para pesquisa, mas é escrita chinesa: 48 dos 240 kanji não existem lá, por estarem na forma simplificada. No máximo, um pré-treino.
- **Só fontes tipográficas renderizadas:** licença livre (OFL), mas a variação é pequena e longe da escrita à mão.
- **Kuzushiji-Kanji:** cursiva clássica; não serve.
- **Desenhos sintéticos a partir dos traços do KanjiVG (escolhida):** os traços já estão no projeto, no mesmo formato do canvas, e cobrem as 240 classes. O risco é a escrita real variar mais que o sintético.

## Decisão

O MVP treina a CNN com **desenhos sintéticos gerados a partir dos traços do KanjiVG**, com variações aleatórias (tremor, espessura, deslocamento e escala de cada traço, rotação leve, deformação elástica e velocidade). O **Kanji alive** (CC BY 4.0) entra como segunda fonte de traços, se os dados dele servirem. Fontes tipográficas (Klee One primeiro) só entram se o sintético sozinho não generalizar.

O modelo é **validado só com escrita humana**, nunca com o sintético. O conjunto é fixo e feito pela equipe no canvas, com a exportação de desenhos (#66). Meta *estimada*: 5 desenhos de 3 pessoas por classe, começando por 40 classes que incluam os pares parecidos (日 × 目, 人 × 入, 王 × 玉, 土 × 工).

> **Correção de 2026-11-13** ([#100](https://github.com/Asuka-Jyuku/kanji-lens/issues/100)): o exemplo dizia 土 × 士, mas 士 é da 5ª série e não está nas 240 classes, então o modelo não tem como confundi-los. As 40 classes escolhidas estão em `ml/drawings/recognition/classes.txt` ([docs/MODEL.md](../MODEL.md#onde-ficam)).

**Para o ETL entrar depois sem mexer no resto,** o pipeline nasce com cinco regras:
1. **Lista de classes fixa:** um arquivo versionado em `ml/`, com os 240 kanji sempre na mesma ordem (ADR 0021). O ETL9G tem todos eles.
2. **Uma entrada só para a CNN:** a mesma imagem, com o mesmo tamanho e a mesma normalização, saia ela de traços (sintético e canvas) ou de uma imagem escaneada (ETL).
3. **A fonte de dados é trocável:** cada fonte entrega o mesmo par (imagem, classe). O ETL entra como mais uma fonte, sem mudar o treino.
4. **O conjunto de desenhos reais julga qualquer modelo:** a comparação "sintético × sintético + ETL" sai no mesmo conjunto, em Top-1 e Top-5.
5. **O modelo é salvo com a versão e os metadados** (classes, tamanho da entrada e versão do pré-processamento), e a API carrega a versão configurada. Trocar o modelo é trocar o arquivo e a versão. Backend, frontend e API não mudam.

Quando o ETL voltar, ele vira a base preferida, provavelmente junto com o sintético. A decisão entre os modelos sai das medições lado a lado.

**Licenças:** no MVP, os pesos ficam só no notebook da escola e não são publicados, então o ShareAlike do KanjiVG não é acionado (*inferido*; as posições estão no spike). Se um dia forem publicados, saem sob CC BY-SA 3.0, separados do código MIT. A atribuição do KanjiVG já está na interface; a do Kanji alive entra no `docs/MODEL.md` e na interface se ele for usado.

## Consequências

- **Positivas:**
  - o treino, a avaliação e a integração (#48) deixam de esperar o site do ETL;
  - o treino vê o mesmo caminho do app (traços → imagem), sem a diferença papel × canvas;
  - o ETL entra depois como mais uma fonte, sem mudar o resto.
- **Negativas:**
  - a acurácia nos desenhos reais pode ficar bem abaixo da do conjunto sintético. É o principal risco, e o motivo de validar só com escrita humana;
  - a validação é pequena e enviesada: poucas mãos, adultas e já treinadas. Os alunos escrevem de outro jeito, e os desenhos deles só entram com ADR;
  - depende de a equipe desenhar o conjunto real antes de dar para medir o modelo;
  - a leitura da licença dos pesos é *inferida*, não um parecer jurídico.
- **Na prática:**
  - a imagem da CNN a partir dos traços (#14, parte 2) vem primeiro: o tamanho da entrada e a espessura se escolhem comparando com desenhos reais do canvas, não mais com o ETL;
  - o gerador sintético e a lista de classes ficam em `ml/`, e o que for gerado fica fora do git (`ml/datasets/`);
  - a #13 passa a montar o dataset sintético e o split fixo; a leitura do ETL vira uma fonte a mais, quando o site voltar;
  - os números de cada versão do modelo, medidos no conjunto real, ficam no `docs/MODEL.md`.

# 0021. ETL9G como dataset do reconhecimento e os 1.026 kanji escolares como primeiras classes

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** [0006](0006-cnn-with-pytorch.md), [0011](0011-school-notebook-as-server-with-cpu-first-inference.md), [0012](0012-ordered-mode-as-stroke-order-evaluation.md), [0016](0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)

## Contexto

A CNN 2D compacta ([ADR 0006](0006-cnn-with-pytorch.md), [ADR 0012](0012-ordered-mode-as-stroke-order-evaluation.md)) precisa de um dataset *offline* de kanjis manuscritos, que é o único dado de treino do projeto. Duas decisões estavam em aberto no [ARCHITECTURE.md, seção 10](../ARCHITECTURE.md#10-decisões-em-resumo): **qual dataset** e **com quantas classes** a primeira versão começa. Todas as classes precisam existir no KanjiVG, a referência da avaliação da ordem ([ADR 0016](0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)).

**Restrições:**
- o treino roda numa máquina com mais recursos, mas o modelo precisa caber na CPU do notebook da escola ([ADR 0011](0011-school-notebook-as-server-with-cpu-first-inference.md));
- o código é público, sob MIT, e nada de dataset entra no git (`CLAUDE.md`, "Convenções de código").

O [spike do dataset](../spikes/dataset-selection.md) ([#11](https://github.com/Asuka-Jyuku/kanji-lens/issues/11)) foi feito com o site oficial do ETL fora do ar (`503` desde 08/11/2026), lendo as cópias do site no Wayback Machine. Os fatos que decidem a questão:
- **Licença (confirmado), termos de 2025-03-28:**
  - o uso é livre e gratuito, sem cadastro: basta concordar com os termos no site;
  - a distribuição é **só pelo site oficial**: publicar os dados além de citação, ou os links diretos dos arquivos, é proibido;
  - a citação é obrigatória.
- **Tamanho (confirmado):**
  - o ETL9G tem 2.965 kanji do JIS nível 1, com 200 amostras por classe, em 128×127 com 16 níveis de cinza;
  - o ETL8G tem 881 kanji, com 160 amostras.
- **Cobertura (estimativa,** feita com o KANJIDIC2):
  - o ETL9 cobre **2.106 dos 2.136 Jōyō (98,6%)** e **todos os 1.026 教育漢字**;
  - o ETL8 cobre cerca de 41% do Jōyō.

## Alternativas consideradas

**Dataset:**
- **ETL8G:** 141 MB e 881 classes. É leve, mas só cobre cerca de 41% do Jōyō e tem 160 amostras por classe. Começar por ele obrigaria a trocar de dataset na expansão, o que muda as classes e o modelo.
- **ETL9B (binário 64×63) como base:** 164 MB, as mesmas 2.965 classes e já em 1 bit, parecido com o traço do canvas. Mas a binarização foi feita na digitalização (limiar fixo), e não dá para ajustar a espessura nem o contraste para aproximar do canvas.
- **ETL8B2:** binário e com as classes do ETL8. Junta as duas desvantagens.
- **ETL9G (tons de cinza 128×127):** 588 MB, 200 amostras por classe, cobre o Jōyō quase inteiro, e os 16 níveis de cinza deixam o pré-processamento escolher a binarização, a espessura e a resolução. Em compensação, ocupa cerca de 5 GB descompactado e é o maior download.
- **Kuzushiji-Kanji** (CC BY-SA 4.0, confirmado): é escrita cursiva clássica, longe da escrita escolar, e muito desbalanceada (de 1.766 a 1 exemplo por classe).
- **Sintético renderizado do KanjiVG:** está perto do traço do canvas, mas não é escrita humana. O efeito do ShareAlike sobre o dataset gerado precisa ser avaliado.
- **TUAT Kuchibue/Nakayosi, CASIA-HWDB, JEITA-HP** (*não verificados nesta pesquisa*):
  - TUAT: dados *online*, obtidos por solicitação, que o projeto não precisa ([ADR 0012](0012-ordered-mode-as-stroke-order-evaluation.md));
  - CASIA: escrita chinesa;
  - JEITA: distribuição incerta.
- **Cópias do ETL no Kaggle ou no GitHub:** ferem a cláusula de distribuição. Não são uma opção.

**Classes:**
- **Algumas centenas, sem critério fixo:** treino rápido, mas a lista não teria um significado para o aluno, e a expansão não teria rumo.
- **Os 2.106 Jōyō cobertos pelo ETL9, logo de início:** cobrem o uso real, mas custam mais RAM, mais tempo de treino e menos acurácia por classe, antes de o pipeline estar validado.
- **Os 1.026 教育漢字:** a lista que a escola ensina. Estão todos no ETL9 e no KanjiVG e somam cerca de 0,84 GB em `uint8` 64×64 (estimativa).

## Decisão

**O reconhecimento treina com o ETL9G.** Ele é superconjunto do ETL8 em kanji, tem 200 amostras por classe e cobre o Jōyō quase inteiro. Os tons de cinza deixam o pré-processamento aproximar o dado do traço do canvas.
- O **ETL9B** é baixado junto, no mesmo acesso ao site, como alternativa leve para comparar.
- O ETL8G é opcional. O hiragana do ETL9 fica fora do escopo.

**A primeira versão reconhece os 1.026 教育漢字**, em três passos:
1. Primeiro, os **240 da 1ª e da 2ª série**, para validar o pipeline (carregamento, pré-processamento, treino e avaliação) com um treino curto.
2. Depois, os 1.026.
3. A expansão para os **2.106 Jōyō cobertos pelo ETL9** vem depois da v1, com uma nova medição de Top-1 e Top-5 e do custo no notebook.

**O que ainda depende do site no ar não bloqueia a decisão.** É trabalho da [#13](https://github.com/Asuka-Jyuku/kanji-lens/issues/13):
1. baixar o ETL9G e o ETL9B e conferir o md5 publicado de cada um (seção 4 do spike);
2. confirmar a lista de classes no `ETL9INFO`;
3. conferir que o `unpack.py` oficial lê os arquivos.

## Consequências

- **Positivas:**
  - as classes têm um critério que faz sentido para a escola, e a expansão até o Jōyō não exige trocar de dataset;
  - 200 amostras por classe, de muitos escritores, dão variedade de escrita;
  - o pré-processamento controla binarização, espessura e resolução a partir dos tons de cinza, o que ataca o principal risco do projeto: a diferença entre o canvas e o dataset ([ARCHITECTURE.md, seção 7.4](../ARCHITECTURE.md#74-pontos-de-atenção));
  - o uso é livre e gratuito, sem cadastro.
- **Negativas:**
  - **Uma fonte só, hoje fora do ar.** O ETL só pode ser obtido pelo site oficial, que responde `503` desde 08/11/2026, sem aviso. Até ele voltar, a #13 não começa com dados reais.

    *Atualização de 2026-11-10 (#78):* o site continua com `503`. O [spike "treinar o reconhecimento sem o ETL"](../spikes/training-without-etl.md) propõe treinar o MVP com desenhos sintéticos do KanjiVG e do Kanji alive, validados só em escrita humana. Se a proposta for aceita, ela entra numa ADR nova, como esta ADR pede para quem troca o dataset. Até lá, esta decisão continua valendo.

    *Atualização de 2026-11-10 ([#95](https://github.com/Asuka-Jyuku/kanji-lens/issues/95)):* aceita na [ADR 0022](0022-synthetic-training-data-from-kanjivg-while-etl-is-down.md). O MVP treina com desenhos sintéticos do KanjiVG. Esta ADR continua valendo para as classes e para o ETL9G como base preferida quando o site voltar, que aí entra como mais uma fonte de dados.
  - **Não há plano B legítimo para o ETL.** As cópias de terceiros ferem a cláusula de distribuição.
  - **Nenhuma imagem do ETL entra no repositório**, nem como fixture de teste, nem no README, nem no `docs/MODEL.md` (*inferido* da cláusula de distribuição). Os testes do carregamento usam arquivos sintéticos no mesmo formato de registro.
  - **Cada máquina baixa do site.** Copiar o zip para o notebook da escola ou entre máquinas do projeto é zona cinzenta (*inferido*). A pergunta ainda vai para `etlcdb@m.aist.go.jp`.
  - **Publicar os pesos treinados não é tratado nos termos.** Provavelmente não é "publication of the data itself" (*inferido*). Fica na mesma pergunta à AIST, antes de qualquer peso ser publicado.
  - **Cerca de 5 GB em disco** com o ETL9G descompactado (607.200 × 8.199 B; estimativa), mais o ETL9B.
  - **Mapeamento JIS → Unicode:** o rótulo do ETL é um código JIS X 0208. Quatro kanji do Jōyō aparecem como variante (塡/填, 頰/頬, 𠮟/叱, 剝/剥), e o KanjiVG tem as duas formas de cada. Para essas classes, o mapeamento escolhe uma forma, e a avaliação da ordem usa a mesma. Pequenas diferenças de glifo entre o JIS e o KanjiVG (o 辶 de 遡, 遜, 謎 e 餌) também precisam ser conferidas.
  - **Escritores separados só por aproximação.** O ETL não tem identificação do escritor. O split por data set é a aproximação de um split sem escritores em comum entre treino e teste (*inferido*; confirmar no `ETL9INFO` na #13).
  - **30 kanji do Jōyō não estão no ETL9**, todos acrescentados em 2010 e que estão no JIS nível 2 (丼, 傲, 刹, 喩, 嗅, 曖, 鬱, 籠…). Ficam fora até uma fonte complementar (por exemplo, sintético do KanjiVG) passar por uma ADR.
  - **O papel continua diferente do canvas.** O ETL é digitalização de folhas, com caneta, ruído e contraste próprios. Os tons de cinza ajudam, mas não eliminam a diferença, que só se mede com desenhos reais feitos no app.
- **Na prática:**
  - o download do ETL9G e do ETL9B fica em `ml/datasets/etl/` (fora do git). Como obter cada um, com o md5, fica documentado no `docs/MODEL.md` e junto do código de carregamento (#13), e o `docs/MODEL.md` nasce nesse PR;
  - a lista de classes é um arquivo versionado em `ml/`, gerado a partir da lista oficial dos 教育漢字 e conferido contra o ETL9 e o KanjiVG. Trocar a lista muda treino, inferência e versão do modelo no mesmo PR (`CLAUDE.md`, "Pré-processamento sempre junto");
  - toda publicação que se refira ao ETL leva a citação que os termos pedem: *Electrotechnical Laboratory, Japanese Technical Committee for Optical Character Recognition, ETL Character Database, 1973-1984*. Ela entra nos READMEs e no `docs/MODEL.md`. Pôr a citação também na interface, junto da atribuição do KanjiVG, é julgamento, não exigência dos termos;
  - incluir um kanji fora do ETL9, ou trocar o dataset, pede uma ADR nova.

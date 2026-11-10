# Spike: dataset do reconhecimento e quantidade de classes

> **Issue:** [#11](https://github.com/Asuka-Jyuku/kanji-lens/issues/11)  
> **Tipo:** spike de pesquisa (leitura das fontes; sem os arquivos de dados)  
> **Status:** decidido na [ADR 0021](../adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md)  
> **Data:** 2026-11-08

---

## 1. Perguntas

- Qual dataset de imagens de kanjis manuscritos treina o modelo de reconhecimento, o mesmo nos dois modos ([ADR 0012](../adr/0012-ordered-mode-as-stroke-order-evaluation.md))?
- Com quantas classes a primeira versão começa? Todas precisam existir no KanjiVG, a referência da avaliação da ordem ([ADR 0016](../adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)).

## 2. Como foi feita

O site oficial do ETL (`etlcdb.db.aist.go.jp`) ficou fora do ar em 08/11 e respondia `503` em 09/11, às 02:03 UTC. As páginas foram lidas nas cópias do **Wayback Machine**.
- **Notação:** `WB:<data> <url>` é `https://web.archive.org/web/<data>id_/<url>`.
- **Última captura útil:** a última com `200` é de **28/09/2026**, e só de algumas páginas (a de download e as de formato); as outras já davam `403` nesse dia.
- **Grau de certeza:** cada ponto diz se foi **confirmado** na fonte, se é **estimativa** ou se é **inferido**.

**O Wayback não tem os dados.** Ele guardou só as páginas e o utilitário `unpack.zip`; a página de download era protegida e nunca foi arquivada. Mesmo que tivesse guardado, baixar de lá iria contra a cláusula de distribuição (seção 3).

## 3. Licença do ETL (confirmado)

Termos revisados em **2025-03-28**:
- em inglês: `WB:20260928124235 http://etlcdb.db.aist.go.jp/download2/`;
- em japonês: `WB:20260928124149 https://etlcdb.db.aist.go.jp/ダウンロード/`.

| Ponto | O que diz | Trecho |
|---|---|---|
| Como obter | Basta concordar com os termos ("Agree to download"); **não há cadastro** | *"Anyone who wants to obtain copies of Database must agree the Terms of Use."* |
| Uso | Livre e gratuito | *"[Usage] Use of Database is allowed for free."* |
| Distribuição | **Só pelo site**; publicar os dados além de citação é proibido | *"[Distribution] Distribution of Database should only be made through this web site. Unauthorized distribution and publication of the data itself beyond the scope of quotation and/or direct URL links to data files are prohibited."* |
| Links diretos | Não publicar a página de links nem os links dos arquivos | *"Do not distribute the direct URL links to data files and this page."* (página de links do site, captura de 07/06/2026; o endereço não é citado aqui, a pedido dos próprios termos) |
| Citação | Obrigatória em publicação que use os dados | *Electrotechnical Laboratory, Japanese Technical Committee for Optical Character Recognition, ETL Character Database, 1973-1984.* |

**Os termos anteriores** (até 2025-03-27, `WB:20250327124555 …/download-request`) eram mais restritivos: exigiam cadastro e limitavam o uso a fins não comerciais. A revisão de 2025 tirou as duas exigências.

**O que se conclui:**
- As cópias do ETL no Kaggle e no GitHub ferem a cláusula de distribuição. **Não servem de plano B.**
- **O repositório não pode ter imagens do ETL**, nem como fixture de teste ou exemplo no README. Isso é *inferido* da cláusula de distribuição.
- **Pesos treinados:** publicá-los provavelmente não é "publication of the data itself", mas os termos não falam disso (*inferido*).
- **Cópia entre máquinas do projeto:** copiar o zip para o notebook da escola é zona cinzenta (*inferido*). O caminho seguro é cada máquina baixar do site.

As duas últimas perguntas podem ir para `etlcdb@m.aist.go.jp`.

## 4. Especificações (confirmado)

Fontes: `WB:20260607193010 …/the-etl-character-database/`, `WB:20260607201041 …/database-development/`, as páginas de formato `WB:20260928124201 …/etlcdb/etln/form_e8g.htm` (e `form_e9g`, `form_e8b`, `form_e9b`) e a página de links (tamanhos e md5).

| | ETL8G | ETL8B2 | ETL9G | ETL9B |
|---|---|---|---|---|
| Kanji / hiragana | 881 (教育漢字 de 1948) / 75 | igual ao 8G | **2.965** (JIS nível 1) / 71 | igual ao 9G |
| Amostras por classe | 160 | 160 | **200** | 200 |
| Total | 152.960 | 152.960 | 607.200 | 607.200 |
| Escritores | 1.600 (延べ, contagem cumulativa) | igual | 4.000 (延べ) | igual |
| Imagem | 128×127, 4 bits (16 níveis) | 64×63, 1 bit | 128×127, 4 bits | 64×63, 1 bit |
| Registro | 8.199 B, tamanho fixo, big-endian | 512 B | 8.199 B | 576 B |
| Zip oficial | 141.374.316 B, md5 `360a5ea345de6eefe4296b958b4db256` | 27.760.622 B, md5 `0ec826e35674dde71be4d96b76955cf0` | 587.770.429 B, md5 `1379019d406329e30279bc7031ee41a5` | 163.692.171 B, md5 `39ea6028c97cfd7f4b5ae67641d12120` |

- **Formato:** os zips não têm senha, e o site oferece um `unpack.py` próprio. Isso vem da página de download; não foi verificado nos arquivos.
- **O que cada registro traz:**
  - nos formatos G (ETL8G e ETL9G): código JIS X 0208, número da folha e do data set, avaliação de qualidade, sexo e idade de quem escreveu;
  - nos formatos B (ETL8B2 e ETL9B): só a folha, o código JIS e a imagem.
- **Quem escreveu:** **não há campo de identificação**. Os arquivos agrupam *data sets* (160 no ETL8G, 200 no ETL9G), e o site diz que *"each writer has written each character only once"*. Separar treino e teste por data set é a aproximação padrão para que um mesmo escritor não apareça nos dois lados (*inferido*; conferir no `ETL9INFO` na [#13](https://github.com/Asuka-Jyuku/kanji-lens/issues/13)).

## 5. Cobertura do Jōyō (estimativa)

Feita com o KANJIDIC2 (EDRDG) de 2026-11-08, supondo que os 2.965 kanji do ETL9 são o JIS nível 1 inteiro (o número bate exatamente).

- **ETL9: 2.106 dos 2.136 Jōyō (98,6%).**
  - **Os 1.026 教育漢字 estão todos lá.**
  - 2.102 entram direto. Quatro entram por variante JIS: 塡/填, 頰/頬, 𠮟/叱, 剝/剥.
  - Faltam 30, todos acrescentados ao Jōyō em 2010 e que estão no JIS nível 2: 丼傲刹哺喩嗅嘲毀彙恣惧慄憬拉摯曖楷鬱璧瘍箋籠緻羞訃諧貪踪辣錮.
- **ETL8:** 881 kanji, cerca de 41% do Jōyō.
- **KanjiVG (confirmado):** a tag `r20260714` tem as duas formas de cada uma das quatro variantes. Falta escolher qual forma vale para cada classe. Há também pequenas diferenças de glifo entre o JIS e o KanjiVG, como o 辶 de 遡, 遜, 謎 e 餌.

## 6. Alternativas

> **Atualização de 2026-11-10:** com o site do ETL ainda fora do ar, o [spike "treinar o reconhecimento sem o ETL"](training-without-etl.md) ([#78](https://github.com/Asuka-Jyuku/kanji-lens/issues/78)) conferiu as linhas marcadas abaixo como *não verificado*:
> - **TUAT:** é pago, com um subconjunto de 10 escritores gratuito para pesquisa.
> - **CASIA:** é gratuito para pesquisa acadêmica, mas 48 dos 240 kanji do MVP não existem no conjunto chinês.
>
> Ele também acrescentou o Kanji alive (CC BY 4.0) como fonte de traços.

| Opção | Situação | Por que não é a base |
|---|---|---|
| **Kuzushiji-Kanji** | Confirmado: CC BY-SA 4.0; 3.832 classes; 140.424 imagens 64×64; de 1.766 a 1 exemplo por classe | É escrita cursiva clássica, longe da escrita escolar, e muito desbalanceada |
| **Sintético renderizado do KanjiVG** (traços com deformação) | KanjiVG CC BY-SA 3.0; o efeito do ShareAlike sobre o dataset gerado precisa ser avaliado | Não é escrita humana; serve de complemento, ou para os 30 Jōyō que faltam no ETL9 |
| **TUAT Kuchibue/Nakayosi** | *Não verificado nesta pesquisa*: dados *online*, obtidos por solicitação ao laboratório | Licença por solicitação; precisaria rasterizar; o `ordered` não precisa de dados *online* (ADR 0012) |
| **CASIA-HWDB** | *Não verificado nesta pesquisa*: escrita chinesa; uso acadêmico mediante acordo | Muitos glifos diferem do shinjitai japonês |
| **JEITA-HP** | *Não verificado nesta pesquisa*: não se sabe se ainda é distribuído | Obtenção incerta |

## 7. Recomendação

Virou a [ADR 0021](../adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md):
- **Dataset:** **ETL9G** como base, e o **ETL9B** baixado junto, como alternativa leve. O ETL8G é opcional.
- **Classes:** os **1.026 教育漢字**, começando pelos 240 da 1ª e da 2ª série e expandindo depois para os 2.106 Jōyō cobertos pelo ETL9.

**Memória (estimativa,** com 64×64 `uint8`, 4 KB por imagem):

| Recorte | Imagens | Em `uint8` |
|---|---|---|
| 240 classes | 48.000 | ≈ 0,2 GB |
| 1.026 classes | 205.200 | ≈ 0,84 GB (≈ 3,4 GB em `float32`) |
| 2.106 classes | 421.200 | ≈ 1,7 GB |

O ETL9G descompactado ocupa cerca de **5,0 GB** em disco (607.200 × 8.199 B). Converter uma vez para um `np.memmap` `uint8` e normalizar por batch tira a RAM do caminho.

## 8. O que ainda depende do site no ar

1. **Baixar** o ETL9G e o ETL9B e conferir o md5 de cada um.
2. **Ler o `ETL9INFO`:** confirmar a lista de classes (e, com ela, a estimativa de 2.106) e se o data set identifica o escritor (#13).
3. **Conferir o `unpack.py`:** ele precisa ler os arquivos sem senha nem decodificador.

# Spike: treinar o reconhecimento sem o ETL

> **Issue:** [#78](https://github.com/Asuka-Jyuku/kanji-lens/issues/78)  
> **Tipo:** spike de pesquisa (leitura das fontes e uma conta de cobertura; sem baixar datasets)  
> **Status:** proposta; a decisão vai para uma ADR (seção 9)  
> **Data:** 2026-11-10  
> **Relacionadas:** [ADR 0021](../adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md), [spike do dataset](dataset-selection.md), [#13](https://github.com/Asuka-Jyuku/kanji-lens/issues/13), [#14](https://github.com/Asuka-Jyuku/kanji-lens/issues/14), [#29](https://github.com/Asuka-Jyuku/kanji-lens/issues/29), [#66](https://github.com/Asuka-Jyuku/kanji-lens/issues/66)

---

## 1. Pergunta

O site do ETL (`etlcdb.db.aist.go.jp`) está fora do ar, sem previsão de volta. **Dá para treinar a CNN das 240 classes do MVP sem ele, e com que risco?**

**Estado do site (confirmado):** a página inicial e a de download responderam `503` em 2026-11-10, às 05:31 UTC. Desde 08/11 não há notícia do AIST sobre o motivo da queda nem sobre a volta: as buscas em inglês e em japonês não acharam nada.

## 2. Restrições

- **O ETL só pode ser obtido pelo site oficial**, pelos termos de 2025-03-28 ([spike do dataset, seção 3](dataset-selection.md#3-licença-do-etl-confirmado)). As cópias no Kaggle ou no Hugging Face ficam fora.
- **A entrada do app é um desenho em canvas** (traços `[x, y, t]`, [ADR 0016](../adr/0016-stroke-order-check-by-bipartite-matching-and-capture-format.md)), não papel escaneado.
- **Nada de dado de terceiro no repositório** sem uma licença que permita.
- **A ADR 0021 já diz o que fazer:** "incluir um kanji fora do ETL9, ou trocar o dataset, pede uma ADR nova".

## 3. Como foi feita

- **Leitura direta das fontes,** em 2026-11-10: as páginas e os contratos de cada dataset, a licença no repositório de cada fonte e o FAQ da OFL. Cada ponto diz se foi **confirmado** na fonte, se é **estimativa** ou se é **inferido**. Os links estão na seção 10.
- **Conta de cobertura (confirmado):** feita com o KANJIDIC2 (EDRDG) de 2026-11-10.
  - **As 240 classes do MVP** são os 80 kanji da 1ª série e os 160 da 2ª (campo `grade`).
  - **Cobertura do CASIA:** a codificação de cada kanji em GB2312 (o conjunto do CASIA).
  - **Cobertura do Kanji alive:** a lista do `ka_data.csv`.
- **Nenhum dataset foi baixado.**

## 4. Alternativas

| Opção | Idioma | Traços | Licença e acesso (2026-11-10) | Cobertura das 240 | Uso |
|---|---|---|---|---|---|
| **Sintético do KanjiVG** | japonês | sim | CC BY-SA 3.0, já está no projeto ([PR #74](https://github.com/Asuka-Jyuku/kanji-lens/pull/74), [docs/MODEL.md](../MODEL.md#dados-de-referência-kanjivg)) | 240 de 240 | **base proposta** |
| **Kanji alive** | japonês | sim, um traço por imagem | **CC BY 4.0**, sem ShareAlike; download direto pelo GitHub | **240 de 240** (1.008 dos 1.026 教育漢字) | segunda fonte de traços do sintético |
| **Fontes renderizadas** (Klee One, Noto Sans/Serif JP) | japonês | não | SIL OFL 1.1; o FAQ da OFL libera usar a fonte para gerar imagens | 240 de 240 | complemento |
| **TUAT Kuchibue/Nakayosi** (HANDS) | japonês | sim (*online*) | **Pago.** Pedido por e-mail ao Prof. Nakagawa e compra pela cooperativa da TUAT: ¥200.000 no preço acadêmico e ¥2.000.000 no comercial, sem impostos. Além disso, o contrato (cláusula 2) só libera de graça um **uso de teste** (試用, no original em japonês) dos dados de 10 escritores, para pesquisa, sem prazo nem condições definidas | a conferir no arquivo | fora por enquanto (#94) |
| **CASIA OLHWDB/HWDB** | chinês simplificado | sim (OLHWDB) | **Gratuito para pesquisa acadêmica**, sem formulário desde 2020; download direto. Uso comercial pago, por contato | **192 de 240** pelo código; os outros **48 não existem** em GB2312 | pré-treino, no máximo |
| **Kuzushiji-Kanji** | japonês histórico | não | CC BY-SA 4.0, aberto | não conferida | **não serve** (cursiva clássica) |
| **Desenhos da equipe** (#66) | japonês | sim | nossos | os que forem desenhados | **validação** |

**Detalhes de cada uma (confirmado, exceto onde marcado):**

- **KanjiVG:** um traço de referência por kanji, na ordem e no sentido oficiais, com cara de fonte, não de escrita à mão. A variação vem toda do gerador.
- **Kanji alive** (opção nova; não estava no esboço nem no spike do dataset):
  - **O que é:** 1.235 kanji escritos à mão por japoneses nativos numa mesa digitalizadora Wacom. São animações, uma imagem SVG para cada traço e o tempo de cada traço.
  - **Quantidade:** é **um exemplo por kanji**, e o número de escritores não está documentado. Não substitui um dataset, mas é traço humano, e sem a obrigação de compartilhar pela mesma licença.
  - **A conferir:** os SVGs foram gerados a partir de PNGs exportados das animações. Ainda não se sabe se dá para extrair deles a linha central de cada traço, ou se servem só como imagem (*inferido* do README).
- **Fontes renderizadas:**
  - **O que o FAQ da OFL diz** (versão 1.1-update8, novembro de 2026):
    - item 1.1: a fonte pode ser usada para criar "logos or other graphics" sem outra permissão;
    - item 1.25: o que a OFL proíbe é **gerar uma fonte nova** a partir dela com IA sob outra licença.
  - **O que se conclui:** um classificador treinado com imagens renderizadas não é uma fonte (*inferido*).
  - **Klee One** (Fontworks, OFL) tem traço de lápis ou caneta, no estilo de livro didático, e é a mais próxima da escrita escolar.
  - **Os 教科書体 comerciais ficaram fora:** a licença deles não foi verificada.
- **TUAT Kuchibue/Nakayosi:**
  - **Tamanho:**
    - **Kuchibue:** 120 escritores e 3.356 categorias, com 11.962 padrões por escritor;
    - **Nakayosi:** 163 escritores e 4.438 categorias, com 10.403 padrões por escritor.
    - O texto copiado é de jornal. Por isso, quantas amostras cada kanji do MVP tem precisa ser conferido nos arquivos.
  - **É o dado mais parecido com o do app,** porque é escrita *online*, com traços: dá para passá-lo pelo mesmo caminho dos desenhos do canvas (*inferido*).
  - **Condições do contrato:**
    - as cópias ficam dentro da organização de quem comprou, e repassar a terceiros é proibido;
    - o preço acadêmico vale só para "educational or research purposes";
    - publicar resultados exige citar a base e dizer que conjuntos foram usados no treino e na avaliação.
  - **Contradição com o passado:** um artigo de 2004 dizia que o Kuchibue era livre para pesquisa. O contrato atual diz outra coisa e é o que vale. O esboço dizia "pedido ao laboratório", sem custo; não é bem assim.
- **CASIA:**
  - **Condições:** "can only be used by the group of the named applicant", só para pesquisa, nenhum uso comercial, e o direito autoral fica com o CASIA.
  - **Contradição na própria página:** ela diz que não há formulário desde 2020, mas fala em "named applicant". Quem conta como "applicant" sem formulário não está claro.
  - **Cobertura:** os 48 kanji que faltam têm forma simplificada no chinês, por exemplo 車/车, 書/书, 語/语, 門/门, 長/长, 東/东, 馬/马, 魚/鱼, 鳥/鸟, 電/电. Entre os 192 que têm o mesmo código, há diferenças de glifo que não foram medidas.
  - **Pesos:** se um modelo treinado com o CASIA pode ser usado na escola, os termos não dizem (*inferido*); perguntar ao CASIA antes.
- **JEITA-HP:** continua *não verificado*, como no spike do dataset.

## 5. Proposta

1. **Gerador sintético a partir do KanjiVG,** com o Kanji alive como segunda fonte de traços:
   - **O que ele gera:** desenhos no **mesmo formato do canvas** (`[x, y, t]`), com variações aleatórias: tremor, espessura, deslocamento e escala de cada traço, rotação leve e deformação elástica. Também varia a velocidade do traço, para o `t`.
   - **Como vira imagem:** os desenhos passam pelo **mesmo pré-processamento da imagem da CNN** que a inferência usa (#14, parte 2). Assim o treino vê o mesmo caminho do app, sem a diferença papel × canvas do ETL ([ARCHITECTURE.md, 7.4](../ARCHITECTURE.md#74-pontos-de-atenção)).
   - **Respaldo na literatura:** o laboratório da TUAT treinou um reconhecedor *online* de japonês com padrões artificiais gerados por modelos de distorção, e mediu o ganho no Kuchibue (Zhu, Chen e Nakagawa, CJKPR 2010; ICDAR 2011). A referência completa não foi conferida na íntegra.
2. **Fontes como complemento** (Klee One primeiro), se o sintético sozinho não generalizar. Elas entram pelo mesmo pré-processamento.
3. **Validar só em escrita humana, nunca no próprio sintético:**
   - os desenhos reais exportados pela #66, feitos pela equipe;
   - o **subconjunto gratuito de 10 escritores do TUAT**, se o laboratório liberar para o projeto. São escritores que ninguém da equipe conhece, o que dá um teste independente. Os dados não entram no repositório, pelo contrato.
4. **Pedir o TUAT agora:**
   - o subconjunto de 10 escritores;
   - perguntar se uma escola conta como "academic organization" e se os pesos podem rodar no notebook da escola.
   - **O ETL continua a base preferida se voltar:** são 200 amostras humanas por classe. O sintético passa a ser complemento, e as duas medições ficam lado a lado.

## 6. O que medir

- **Top-1 e Top-5 nos desenhos reais** da #66 e no TUAT, por classe, e não só no total.
- **Confusões entre kanji parecidos** (日 × 目, 人 × 入, 王 × 玉, por exemplo). *Corrigido em 2026-11-13:* o exemplo dizia 土 × 士, mas 士 é da 5ª série e não está nas 240 classes.
- **O efeito de cada ingrediente:** só KanjiVG; + Kanji alive; + fontes.
- **A diferença para o ETL,** se ele voltar: o mesmo modelo treinado com cada um e medido nos mesmos desenhos reais.
- **Quantos desenhos reais bastam para medir** (*estimativa*, a fechar na ADR): 5 desenhos de 3 pessoas por classe nas 240 dão 1.200 desenhos. Dá para começar por uma amostra (por exemplo, 40 classes com os pares parecidos) e completar depois.

## 7. Riscos

- **A escrita humana real varia mais que o sintético,** então a acurácia nos desenhos reais pode ficar bem abaixo da do conjunto sintético. É o motivo de validar só em escrita humana, e o principal risco desta proposta.
- **Validação pequena e enviesada:** os desenhos da equipe são poucos e vêm de poucas mãos, adultas e já treinadas. Os alunos escrevem de outro jeito, e os desenhos deles só entram com ADR (`CLAUDE.md`, "Segurança").
- **Licença CC BY-SA do KanjiVG:** decidir se o modelo treinado com ele herda a obrigação de compartilhar pela mesma licença. É um ponto para a ADR. As posições principais (não é parecer jurídico):
  - **Creative Commons:** o ShareAlike só é acionado quando a obra ou uma adaptação dela é **compartilhada publicamente**. Se o modelo for compartilhado e o uso depender de permissão do direito autoral, seguir o ShareAlike exige a mesma licença no modelo. Se uma exceção da lei cobrir o treino, a licença nem se aplica.
  - **Szkalej e Senftleben (JIPITEC, 2024):** argumentam que os conceitos de "adapted material" da licença CC dificultam estender o ShareAlike aos pesos treinados.
  - **A lei de cada país pesa:**
    - no Brasil, a Lei 9.610/98 não tem exceção geral para mineração de dados;
    - o PL 2338/2023, aprovado no Senado, propõe uma exceção limitada a entidades de pesquisa e de ensino sem fins lucrativos. O andamento dele na Câmara em 2026 não foi confirmado.
  - **Na prática:**
    - no MVP, os pesos ficam só no notebook da escola ([ADR 0007](../adr/0007-local-execution-over-the-lan.md)) e não são publicados, então o ShareAlike não é acionado (*inferido*);
    - se um dia forem publicados, licenciar os pesos em CC BY-SA, separados do código MIT, é o caminho conservador e barato;
    - a atribuição do KanjiVG já está prevista.
- **Termos do TUAT e do CASIA:** os dois limitam o uso a pesquisa ou ensino e proíbem repassar os dados. Rodar um modelo treinado com eles numa escola provavelmente se encaixa, mas os contratos não falam de pesos (*inferido*). Perguntar antes de usar no treino.
- **Formas do chinês:** pré-treinar no CASIA pode ensinar formas simplificadas que não existem no japonês. Se for testado, entra só como pré-treino, e as 240 classes são ajustadas com dados japoneses.

## 8. Recomendação

> **Atualização de 2026-11-10** (#94): o TUAT fica fora por enquanto. Conferindo os contratos de novo, o contrato (cláusula 2) só libera de graça um **uso de teste** (試用, no original em japonês) dos dados de 10 escritores, para pesquisa, sem prazo nem condições definidas. Os itens sobre o TUAT abaixo e nas seções 5 e 6 ficam como registro; a validação do MVP é só com os desenhos da equipe (#93).

- **Seguir com o sintético do KanjiVG (mais o Kanji alive) como base do MVP enquanto o ETL estiver fora.** Validar só em escrita humana: a #66 e, se liberado, os 10 escritores do TUAT.
- **Não esperar o ETL para destravar o treino.** Se ele voltar, entra como base preferida, e as duas medições ficam lado a lado.
- **Deixar o CASIA e o Kuzushiji-Kanji fora.**

## 9. Decisão a registrar

Uma **ADR nova**, porque a própria ADR 0021 pede isso para "trocar o dataset". Se o sintético virar a base do MVP, a ADR nova:
- registra o sintético (KanjiVG + Kanji alive, e fontes se precisar) como base enquanto o ETL estiver fora;
- define a validação só com escrita humana e o tamanho mínimo do conjunto da #66;
- decide a licença dos pesos (ShareAlike do KanjiVG) e a atribuição do Kanji alive e das fontes;
- diz o que acontece quando o ETL voltar.

A ADR 0021 ganha uma nota de atualização apontando para ela.

**Próximos passos** (issues a criar quando a ADR for aceita; nenhuma foi criada aqui):
1. **Pedir ao TUAT o subconjunto de 10 escritores** (Kuchibue e Nakayosi), com as perguntas da seção 5 (e-mail ao Prof. Nakagawa).
2. **Gerador sintético em `ml/`**, a partir do KanjiVG e do Kanji alive, depois da imagem da CNN da #14 (parte 2). Essa parte não depende do ETL; só a comparação com uma amostra dele depende.
3. **Conjunto de validação real com a #66**, com a meta de desenhos por classe.
4. **Licença dos pesos e atribuições** na interface e no `docs/MODEL.md`.
5. **O e-mail ao AIST** (`etlcdb@m.aist.go.jp`) continua valendo para o caso de o ETL voltar.

## 10. Fontes

Todas acessadas em 2026-11-10.

- **ETL:** `https://etlcdb.db.aist.go.jp/` e `/download2/`, ambos com `503` às 05:31 UTC.
- **TUAT:**
  - páginas das bases: [Kuchibue](http://web.tuat.ac.jp/~nakagawa/database/en/about_kuchibue.html), [Nakayosi](http://web.tuat.ac.jp/~nakagawa/database/en/about_nakayosi.html) e o [índice](https://web.tuat.ac.jp/~nakagawa/database/index.html);
  - contratos na cooperativa da TUAT: [Kuchibue em inglês](https://www.univcoop.jp/tuat/hands/97e.html), [Kuchibue em japonês](https://www.univcoop.jp/tuat/hands/97j.html) e [Nakayosi em inglês](https://www.univcoop.jp/tuat/hands/98e.html);
  - o artigo de 2004: Nakagawa e Matsumoto, [IJDAR 7: 69–81](https://web.tuat.ac.jp/~nakagawa/pub/2004/pdf/nakagawa0404a-e.pdf).
- **CASIA:** [página das bases](https://nlpr.ia.ac.cn/databases/handwriting/Home.html), [condições de uso](https://nlpr.ia.ac.cn/databases/handwriting/Application_form.html) e [download](https://nlpr.ia.ac.cn/databases/handwriting/Download.html).
- **Kanji alive:** [README dos dados](https://github.com/kanjialive/kanji-data-media/blob/master/README.md), com a licença CC BY 4.0, e a lista [`ka_data.csv`](https://github.com/kanjialive/kanji-data-media/blob/master/language-data/ka_data.csv).
- **KanjiVG:** [README](https://github.com/KanjiVG/kanjivg/blob/master/README.md), com a licença CC BY-SA 3.0.
- **Kuzushiji-Kanji:** [README do KMNIST](https://github.com/rois-codh/kmnist), com a licença CC BY-SA 4.0.
- **Fontes tipográficas:** [FAQ da OFL](https://openfontlicense.org/ofl-faq/) (itens 1.1 e 1.25, versão 1.1-update8), [Klee One](https://github.com/fontworks-fonts/Klee) e [Noto CJK](https://github.com/notofonts/noto-cjk).
- **Licença CC e treino de IA:**
  - Creative Commons, [Using CC-Licensed Works for AI Training](https://creativecommons.org/using-cc-licensed-works-for-ai-training-2/) e o [primer de 2025-05-15](https://creativecommons.org/2025/05/15/understanding-cc-licenses-and-ai-training-a-legal-primer/);
  - Szkalej e Senftleben, [Share Alike and ML](https://ivir.nl/publicaties/download/Share-Alike-and-ML.pdf) (JIPITEC, 2024).
- **PL 2338/2023:** [apresentação do MinC na Comissão Especial da Câmara](https://www2.camara.leg.br/atividade-legislativa/comissoes/comissoes-temporarias/especiais/57a-legislatura/comissao-especial-sobre-inteligencia-artificial-pl-2338-23/apresentacoes-em-eventos/MARCOSALVESDESOUZASecretriodeDireitosAutoraiseIntelectuaisdoMINCCmaradosDeputados02.09.25.pdf) (2025-09-02) e [PublishNews](https://www.publishnews.com.br/materias/2025/09/03/debate-na-camara-tem-divergencias-sobre-ia-e-direitos-autorais) (2025-09-03).
- **Padrões artificiais para reconhecimento *online* de japonês:** Zhu, Chen e Nakagawa, [CJKPR 2010](http://web.tuat.ac.jp/~nakagawa/pub/2010/pdf/ChenBin_CJKPR2010.pdf), e "Effects of Generating a Large Amount of Artificial Patterns for On-line Handwritten Japanese Character Recognition", [ICDAR 2011, pp. 663–667](https://computer.org/csdl/proceedings-article/icdar/2011/4520a663/12OmNz61dap).
- **KANJIDIC2:** [EDRDG](http://www.edrdg.org/wiki/index.php/KANJIDIC_Project), CC BY-SA 4.0, usado só na conta de cobertura e não incluído no repositório.

# Spike: avaliação de modelos e do runtime de inferência

> **Issues:** [#23](https://github.com/Asuka-Jyuku/kanji-lens/issues/23) (modelos e runtime), [#26](https://github.com/Asuka-Jyuku/kanji-lens/issues/26) (modo `ordered`, seção 5.3)  
> **Tipo:** spike técnico (pesquisa e plano de experimentos)  
> **Status:** estratégia decidida: uma CNN 2D nos dois modos e, no `ordered`, avaliação da ordem contra o KanjiVG ([ADR 0012](../adr/0012-ordered-mode-as-stroke-order-evaluation.md), que substituiu a Opção C da ADR 0010), com o hardware e a carga na [ADR 0011](../adr/0011-school-notebook-as-server-with-cpu-first-inference.md). Ainda não há números medidos: variantes, resolução, runtime, quantização e workers dependem dos benchmarks no notebook.  
> **Data:** 2026-11-07 (projetos de referência revistos em 2026-11-08)  
> **Hardware-alvo:** Dell Inspiron 3501 (Intel Core i7-1165G7, 16 GB de RAM)

---

> **Revisão de 2026-11-08: o modo `ordered` mudou.** Depois da pesquisa da seção 5.3, o projeto escolheu o caminho (b): **avaliar a ordem e a direção dos traços contra a referência do KanjiVG**, sem 1D-CNN ([ADR 0012](../adr/0012-ordered-mode-as-stroke-order-evaluation.md), que substitui a ADR 0010). Os dois modos usam a mesma CNN 2D. Nas seções 1, 2, 5.2, 7, 8, 10, 12 e 13, o que fala de 1D-CNN, GRU, "reconhecimento condicionado à informação temporal" ou dados *online* para treinar o `ordered` fica como registro da investigação, não como plano.

## 1. Resumo executivo

Este spike avalia quais famílias de modelos e runtimes devem ser testadas para executar o reconhecimento de kanji manuscritos em um Dell Inspiron 3501 com Intel Core i7-1165G7 e 16 GB de RAM.

A recomendação é não escolher um modelo final apenas com base em benchmarks publicados. O resultado depende do número de classes, do pré-processamento, da resolução, do conjunto de validação, do padrão de escrita do usuário e do runtime de inferência.

**Decisão arquitetural adotada pelo projeto: Opção C — modelos especializados com infraestrutura compartilhada.**

1. `unordered`: **CNN 2D customizada compacta** sobre a imagem rasterizada final.
2. `ordered`: **1D-CNN temporal compacta** sobre a sequência de pontos/traços capturada pelo canvas.
3. Os modelos serão independentes e não compartilharão pesos nesta primeira versão. Serão reutilizados contratos, validação, pré-processamento aplicável, infraestrutura de jobs/workers, observabilidade e resposta Top-K.
4. MobileNetV3-Small e ResNet-18 serão comparadores para `unordered`, não modelos já escolhidos para produção.
5. GRU pequena e CNN 2D com mapas de ordem permanecem como alternativas experimentais para `ordered`.
6. Comparar inferência em **PyTorch CPU**, **ONNX Runtime CPU** e **OpenVINO CPU**.
7. Avaliar quantização INT8 somente depois de estabelecer a acurácia e a latência em FP32.
8. Medir tudo no notebook-alvo, com carga sustentada e simulação de requisições concorrentes.
9. Dimensionar para 3–5 alunos submetendo reconhecimentos em uma janela curta; usar 10 clientes como cenário de estresse, não como premissa de 10 inferências paralelas.
10. Considerar que o mesmo notebook também executará o frontend Angular (build estático), FastAPI, fila, runtime e os dois modelos.

A hipótese de trabalho é que uma CNN compacta será suficiente para o modo `unordered`. Para `ordered`, uma CNN que receba somente a imagem final não consegue recuperar de forma confiável a sequência temporal que foi perdida durante a rasterização. Será necessário preservar essa informação na entrada ou usar um ramo temporal.

**Conclusão e decisão do projeto:** seguir com a Opção C. A arquitetura inicial será composta por uma CNN 2D compacta para `unordered` e uma 1D-CNN temporal compacta para `ordered`. Isso não significa que a escolha de tamanho, profundidade, resolução ou runtime esteja encerrada: esses detalhes serão definidos pelos benchmarks. MobileNetV3-Small, ResNet-18 e HOG+SVM continuam como comparadores de `unordered`; GRU e CNN 2D com mapa de ordem continuam como alternativas para `ordered`.

---

## 2. Contexto e escopo do produto

O KanjiLens permite que o aluno desenhe um kanji no canvas e receba uma lista Top-K de candidatos. O serviço roda na rede local da escola, com FastAPI, PyTorch e processamento assíncrono por fila/workers, com retorno de resultado por SSE.

O produto prevê dois modos selecionáveis por requisição:

- `unordered`: reconhecer a forma final do caractere sem utilizar a sequência temporal dos traços como evidência.
- `ordered`: utilizar a sequência, a direção e a separação dos traços como parte da representação do caractere.

O modo `ordered` deve ser entendido neste spike como **reconhecimento condicionado à informação temporal da escrita**. Isso não significa, automaticamente, que o sistema rejeitará uma escrita cuja ordem não siga a convenção escolar. Validar se a ordem está correta é um problema adicional, que pode exigir alinhamento com uma referência como KanjiVG.

### Fora do escopo

- Escolher definitivamente o dataset e resolver sua licença/termos de uso.
- Definir o número final de classes de kanji.
- Implementar o modelo em produção.
- Garantir uma latência final antes dos testes no equipamento real.
- Fazer validação pedagógica da ordem correta dos traços.

---

## 3. Hardware de referência

| Item | Especificação |
|---|---|
| Notebook | Dell Inspiron 3501 |
| CPU | Intel Core i7-1165G7 |
| Núcleos / threads | 4 núcleos / 8 threads |
| Frequência turbo máxima | Até 4,70 GHz |
| RAM informada | 16 GB |
| Arquitetura de inferência | CPU-first |
| GPU | O processador possui GPU integrada Intel Iris Xe; não assumir que ela estará disponível ou será utilizada pelo runtime |

A Intel informa também suporte a Intel Deep Learning Boost, AVX2 e AVX-512 para esse processador. Isso torna pertinente avaliar runtimes otimizados para CPU Intel, especialmente OpenVINO. A presença dessas instruções não garante, isoladamente, um ganho específico: o resultado depende dos operadores do modelo, da versão do runtime, da configuração térmica e do sistema operacional.

**Implicações para o projeto:**

- Não há necessidade inicial de um modelo grande.
- A RAM de 16 GB é suficiente para experimentar modelos compactos, mas o orçamento deve incluir SO, Docker, FastAPI, fila, workers e cache do runtime.
- O i7 tem quatro núcleos físicos. Não iniciar com oito workers apenas porque existem oito threads lógicas.
- O notebook também hospedará o frontend Angular (servido como build estático), FastAPI, fila e os dois modelos; o benchmark deve medir o consumo agregado do sistema, não apenas o processo do modelo.
- Notebook pode sofrer limitação térmica e de energia em carga prolongada. Medir após aquecimento, não apenas em uma execução curta.
- Começar com um serviço/processo de inferência que carrega os dois modelos e executa um job por vez. Comparar com duas execuções simultâneas/2 workers somente após medir espera na fila, RAM e CPU. Se forem processos separados, contabilizar que cada processo pode carregar sua própria cópia dos modelos. Variar também as threads internas do runtime.

Fonte das especificações: Intel, página oficial do i7-1165G7 — https://www.intel.com.br/content/www/br/pt/products/sku/208662/intel-core-i71165g7-processor-12m-cache-up-to-4-70-ghz/specifications.html

---

## 4. O que a literatura e as fontes indicam

### 4.1 CNNs são uma abordagem estabelecida para caracteres japoneses manuscritos

O relatório acadêmico *Recognizing Handwritten Japanese Characters Using Deep Convolutional Neural Networks*, de Charlie Tsai (Stanford, 2016), experimenta CNNs com o ETL Character Database e aborda hiragana, katakana e kanji. É uma evidência de que CNNs são uma escolha tecnicamente fundamentada para classificação de caracteres japoneses manuscritos.

Isso não determina qual arquitetura compacta é melhor para o KanjiLens atual. O estudo é anterior às arquiteturas mobile modernas e seu protocolo não deve ser comparado diretamente a um benchmark que será executado neste projeto.

Fonte: https://cs231n.stanford.edu/reports/2016/pdfs/262_Report.pdf

### 4.2 MobileNetV3-Small foi projetada para cenários com recursos limitados

O artigo *Searching for MobileNetV3* (ICCV 2019) descreve uma família otimizada com técnicas de busca sensíveis ao hardware e uma variante Small voltada a cenários de menor recurso. É um candidato relevante para inferência CPU, mas o artigo não prova que será mais rápida que uma CNN pequena feita especificamente para caracteres 64–128 px no i7-1165G7.

Fonte: https://arxiv.org/abs/1905.02244

### 4.3 ETL é relevante, mas não contém a sequência temporal da escrita

A base oficial ETL Character Database, mantida pela AIST, reúne imagens de caracteres manuscritos e impressos. Entre os conjuntos relevantes:

| Dataset | Classes de caracteres | Amostras | Resolução / formato |
|---|---:|---:|---|
| ETL8G | 956 (881 kanjis + 75 hiraganas) | 152.960 | 128×127, grayscale multinível |
| ETL8B2 | mesmas classes do ETL8 | versão binária | 64×63 |
| ETL9G | 3.036 (2.965 kanjis + 71 hiraganas) | 607.200 | 128×127, grayscale multinível |
| ETL9B | mesmas classes do ETL9 | versão binária | 64×63 |

Os dados foram coletados em folhas de escrita e digitalizados. São, portanto, dados **offline**: contêm a imagem final, não a trajetória temporal do lápis/caneta. ETL8/ETL9 podem apoiar o modo `unordered`, mas não treinam diretamente um modelo que precisa aprender ordem e direção dos traços.

Fonte oficial: https://etlcdb.db.aist.go.jp/the-etl-character-database/

### 4.4 KanjiVG fornece geometria vetorial e ordem de referência, não escrita humana espontânea

KanjiVG descreve os traços como caminhos SVG e organiza os dados segundo a estrutura e a ordem de traços japonesa. A documentação informa que as formas são baseadas principalmente em fontes escolares japonesas.

É útil para:
- obter a decomposição vetorial de um kanji;
- recuperar a ordem de referência dos traços;
- gerar exemplos sintéticos com sequências conhecidas;
- criar mapas de ordem/direção para experimentos.

Não deve ser tratado como substituto de um dataset de escrita humana online: traços tipográficos vetoriais não representam toda a variação de velocidade, pressão, tremor, proporção e estilo de escrita de alunos.

Fontes:
- https://kanjivg.tagaini.net/files.html
- https://kanjivg.tagaini.net/svg-format.html

### 4.5 Quantização não garante aceleração em qualquer CPU

A documentação do ONNX Runtime explica que a quantização INT8 pode reduzir custo de memória e computação, mas o ganho depende do hardware e dos operadores. Em CPUs sem as instruções apropriadas, a quantização pode não acelerar ou até piorar a latência por causa do overhead de conversão.

A documentação recomenda começar com S8S8 usando QDQ como opção padrão no ONNX Runtime e alerta contra S8S8 com QOperator em x86-64 em determinados cenários.

Fonte: https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html

### 4.6 OpenVINO merece avaliação específica neste equipamento

A documentação do OpenVINO descreve o plugin CPU como otimizado para CPUs x86-64 e destaca melhorias em CPUs Intel de 11ª geração ou posteriores, especialmente para modelos INT8. Também oferece modos de desempenho orientados a latência ou throughput e controle de streams/threads.

Isso faz do OpenVINO um candidato forte para o i7-1165G7. Ainda assim, deve ser comparado com ONNX Runtime e PyTorch no mesmo modelo, mesma entrada e mesma máquina.

Fontes:
- https://docs.openvino.ai/2024/openvino-workflow/running-inference/inference-devices-and-modes/cpu-device.html
- https://docs.openvino.ai/2025/openvino-workflow/running-inference/inference-devices-and-modes/cpu-device.html

---

## 5. Modelos candidatos

### 5.1 Modo `unordered`

O modelo recebe a imagem final do caractere, depois do pré-processamento compartilhado entre treino e inferência.

| Candidato | Papel no spike | Pontos fortes | Riscos / limitações | Prioridade |
|---|---|---|---|---|
| CNN customizada compacta | Baseline principal | Arquitetura controlada; pode ser pequena; adequada ao domínio; fácil de ajustar para 1 canal e 64–128 px | Exige desenho e tuning; pode ter capacidade insuficiente para milhares de classes | **Muito alta** |
| MobileNetV3-Small | Comparador eficiente | Arquitetura desenhada para dispositivos de baixo recurso; boa referência de eficiência | Operações mobile nem sempre são as mais rápidas em todo runtime/CPU; adaptação de entrada e número de classes | **Muito alta** |
| ResNet-18 | Controle de capacidade | Arquitetura residual conhecida; boa referência de acurácia/capacidade | Mais operações e parâmetros que uma CNN pequena; pode ser desnecessária para imagens pequenas | Média |
| HOG + SVM | Baseline clássico sem rede neural | Ajuda a verificar se uma abordagem de features clássicas já resolve parte do problema; inferência explicável em etapas | Extração HOG e classificação multi-classe podem ficar caras; modelo pode crescer com muitas classes; sensível a variações | Média/baixa |

#### CNN customizada — desenho inicial proposto

Não é uma arquitetura fechada, mas um ponto de partida para experimentação:

- Entrada: `1 × H × W` (grayscale).
- 3 ou 4 blocos convolucionais.
- Cada bloco: Conv2D + normalização + ReLU/SiLU; downsampling controlado.
- Global Average Pooling.
- Camada linear para o número de classes.
- Saída de logits; Top-K calculado no backend.
- Sem camadas densas enormes após achatar todos os mapas de ativação.

Comparar duas ou três larguras de canal, por exemplo uma configuração pequena e outra intermediária. Registrar parâmetros, FLOPs aproximados, tamanho serializado e latência real.

#### MobileNetV3-Small

Usar como candidato comparativo, não como decisão antecipada. Adaptar a primeira camada para entrada grayscale ou converter a imagem para três canais apenas se houver justificativa experimental. Testar resolução reduzida, mas não assumir que 64×64 preservará os detalhes necessários para kanjis complexos.

#### ResNet-18

Serve como controle para responder: “A CNN customizada está perdendo acurácia por falta de capacidade?”. Se ResNet-18 melhorar pouco e custar significativamente mais, não será atraente para produção.

#### HOG + SVM

Manter como baseline não neural, não como principal aposta. É útil para medir o quanto features geométricas clássicas conseguem resolver o problema. Avaliar o custo total de extração de features e classificação em todo o conjunto de classes, não apenas o tempo do classificador isolado.

### 5.2 Modo `ordered`

Uma imagem final não preserva necessariamente:
- qual traço foi desenhado primeiro;
- direção em que cada traço foi desenhado;
- pausas e levantamentos da caneta;
- sequência temporal entre pontos.

Por isso, o modo `ordered` precisa de uma representação que mantenha esses dados.

| Candidato | Entrada | Vantagens | Limitações | Prioridade |
|---|---|---|---|---|
| 1D-CNN temporal | Sequência de pontos/traços com coordenadas, tempo e estado da caneta | Convoluções temporais são paralelizáveis; pode ser compacta | Exige normalização e amostragem consistente das sequências | **Alta** |
| CNN 2D com canais de ordem | Imagem final + mapa de ordem/direção dos traços | Reaproveita pipeline de imagem; entrada compacta | Codificação pode perder detalhes temporais; precisa definir representação | **Alta** |
| CNN de imagem + ramo temporal | Imagem raster + sequência vetorial | Combina forma final e informação temporal | Maior complexidade, dois ramos e fusão | Média |
| GRU pequena | Sequência temporal de pontos ou descritores de traço | Modela dependência sequencial explicitamente | Execução recorrente pode limitar paralelismo; comprimento da sequência influencia latência | Média |

#### Representação temporal sugerida

Cada ponto amostrado pode carregar atributos normalizados:

- `x`, `y`: coordenadas no canvas normalizadas;
- `delta_t`: intervalo temporal relativo;
- `pen_state`: caneta abaixada/levantada;
- `stroke_id` ou índice do traço;
- opcionalmente direção local (`dx`, `dy`) e comprimento acumulado.

A sequência deve ter política clara para:
- reamostrar pontos por comprimento ou intervalo temporal;
- separar traços;
- limitar o comprimento máximo;
- padding e máscara para sequências menores;
- normalizar translação, escala e posição sem destruir proporções relevantes.

**Hipótese principal para `ordered`:** começar com uma 1D-CNN temporal compacta e compará-la com uma CNN 2D que recebe um mapa de ordem. GRU entra como comparador, não como primeira implementação.

#### Importante: o que significa “ordem importa”?

Há duas tarefas diferentes que não devem ser confundidas:

1. **Reconhecimento com informação de ordem:** usar a sequência de escrita como mais uma evidência para identificar o kanji.
2. **Validação da ordem correta:** verificar se o aluno seguiu a sequência convencional de traços.

A primeira é o escopo deste spike (mas veja a seção 5.3: qual das duas o produto quer ainda precisa ser confirmado). A segunda pode ser construída depois, usando KanjiVG como referência geométrica e um algoritmo de alinhamento/comparação de traços.

### 5.3 Como o modo `ordered` costuma ser feito (pesquisa de 2026-11-08)

Na literatura, "usar a ordem dos traços" aparece em **duas tarefas diferentes**, com técnicas, dados e custos diferentes. O que o modo `ordered` quer dizer para a escola decide qual das duas (ou a combinação) o KanjiLens implementa.

#### a) Reconhecimento *online*: a trajetória como evidência

É o problema clássico de *online handwritten character recognition*, muito estudado para chinês (OLHCCR) e japonês. As abordagens mais comuns:

| Abordagem | Como funciona | Exemplos |
|---|---|---|
| Sequência direto numa rede sequencial | Pontos com `x`, `y`, deslocamentos e estado da caneta entram numa RNN (LSTM/GRU) | Zhang, Yin, Zhang, Liu e Bengio, *Drawing and Recognizing Chinese Characters with RNN* (TPAMI 2018) |
| Sequência numa 1D-CNN | Convolução temporal sobre a trajetória. É mais rápida que a RNN em sequências longas, mas precisa de mais camadas para captar dependências longas | Liu et al. (2019), citado em Gan et al. (2020) |
| Trajetória convertida em mapas 2D | A trajetória vira mapas de direção ou de *path signature* (integrais iteradas do caminho), e uma CNN 2D classifica. É a família que dominou os benchmarks (ICDAR 2013) | Graham (2013); Lai et al. (2017) |
| Mapas na ordem dos traços | Os traços viram mapas de características em ordem, e o modelo depende da sequência | Hu et al., SSDCNN |

**Ponto importante:** quase todos esses reconhecedores são feitos para **tolerar** variação de ordem e de quantidade de traços. Na escrita real, mesmo quem é fluente varia a ordem e une traços. Um exemplo do grupo de Nakagawa (TUAT) é o motor de Wang, Zhu e Nakagawa (ICDAR 2011), que é *stroke-order free*. Usar a trajetória melhora o reconhecimento, mas **não faz o modelo exigir a ordem correta**. Uma 1D-CNN treinada com escrita real aprende a ordem que as pessoas usam, inclusive as "erradas".

#### b) Avaliação da ordem: comparar com uma referência

Para ensinar a escrever, o padrão é outro: comparar o desenho com o **padrão de referência** do kanji (a ordem e a direção convencionais), traço a traço:

- **Correspondência entre traços por *DP matching*** ou por busca de correspondência. Cai, Uchida e Sakoe compararam cube search, bipartite weighted matching e outras buscas, com cerca de 99% de acerto (cube search e bipartite matching em 99,17%). Ido (IEICE, 2015) aplica *DP matching* a sub-traços para corrigir a escrita automaticamente.
- **Avaliação incremental, traço a traço.** Mita e Nakagawa (2016) usam características direcionais e relatam 97,5% em 1.005 kanjis, com até 0,05 s por caractere. Nguyen, Nguyen, Mita e Nakagawa (*Pattern Recognition Letters*, 2019) julgam ordem e direção a cada traço novo, comparando o desenho parcial com a referência de mesma quantidade de traços. Relatam 98,5% de avaliação correta e até 0,12 s por caractere num desktop.

Esse caminho **não precisa de rede neural nem de dataset grande de escrita**: precisa da referência (o KanjiVG tem a ordem e a direção de cada traço) e roda leve na CPU. O arranjo comum em sistemas de ensino:
1. reconhecer o caractere sem depender da ordem;
2. comparar a ordem do desenho com a referência dos candidatos;
3. apontar o traço fora de ordem.

O `asdfjkl/kanjicanvas` (seção 11.1) também é *matching* geométrico contra referências.

#### Dados *online* disponíveis

| Fonte | O que é | Cuidados |
|---|---|---|
| **TUAT Kuchibue e Nakayosi** (laboratório Nakagawa) | Escrita japonesa *online*: Kuchibue com 120 pessoas e cerca de 12 mil padrões cada; Nakayosi com 163 pessoas e cerca de 10 mil padrões cada | Distribuição pela TUAT: parte livre para pesquisa, o conjunto completo pela universidade. **Termos de uso a confirmar** com o laboratório. Não presumir redistribuição |
| **CASIA-OLHWDB 1.0–1.2** (CASIA/NLPR) | Escrita chinesa *online*; o 1.1 tem 3.755 classes e 300 pessoas | Livre para pesquisa acadêmica, segundo os artigos; **licença a confirmar** na NLPR. Muitos caracteres coincidem com kanjis, mas a forma (simplificado × japonês) e a ordem convencional diferem em parte deles |
| **Tomoe / Zinnia** | O Zinnia é um reconhecedor *online* com SVM; o modelo japonês vem do projeto Tomoe | Formato e licença dos dados do Tomoe não confirmados nesta pesquisa |
| **KanjiVG** | Vetores e ordem de referência de cada kanji | Serve de referência para a avaliação (b) e para gerar dados sintéticos com perturbação. Dado sintético desloca a distribuição em relação à escrita real, então não prova generalização |
| **Coleta própria pelo canvas** | Desenhos reais dos alunos, com a ordem verdadeira | É o único conjunto que representa o público do KanjiLens; **pelo menos o teste deveria vir daqui**. Exige consentimento, anonimização e uma ADR (os desenhos hoje não são guardados) |

Na prática, quem treina reconhecedores *online* combina três coisas:
- um dataset público grande, para o pré-treino;
- dados próprios, para o ajuste e o teste;
- *augmentation*: perturbação de traços ou geração sintética, como o modelo sigma-lognormal.

#### Captura no navegador

- **Pointer Events:**
  - `pointerdown` abre um traço e `pointerup` o fecha (é daí que sai o estado da caneta);
  - cada `pointermove` dá `x`, `y` e `timeStamp`;
  - `pressure` e `pointerType` vêm de graça.
- **`getCoalescedEvents()`** devolve os pontos intermediários que o navegador agrupou, e deixa o traço mais fiel. **Atenção:** a API não é Baseline (o Safari só a tem desde a 18.2) e, em parte dos navegadores, **só funciona em contexto seguro (HTTPS)**. O KanjiLens roda por HTTP na rede local, então o código precisa funcionar sem ela.
- **Formato de troca:** o W3C InkML é o padrão para tinta digital: *traces* de pontos, com canais como X, Y, tempo e pressão. Não é preciso adotar o XML, mas convém seguir o mesmo modelo (lista de traços com canais nomeados).
- **No pré-processamento, como de costume:**
  - remover pontos redundantes;
  - reamostrar a distâncias iguais;
  - normalizar tamanho e posição;
  - limitar a quantidade de traços e de pontos.

#### O que isso muda para o KanjiLens

1. **Decisão de produto antes do modelo.** "Ordem importa" pode querer dizer duas coisas:
   - **(a) reconhecer melhor usando a trajetória:** é o que a [ADR 0010](../adr/0010-two-recognition-modes-with-specialized-models.md) descreve, com a 1D-CNN;
   - **(b) cobrar a ordem correta da escrita japonesa:** é avaliação por referência, um problema diferente.

   Uma escola de japonês tende a querer (b). **Decidido em 2026-11-08: caminho (b)** ([ADR 0012](../adr/0012-ordered-mode-as-stroke-order-evaluation.md), que substitui a ADR 0010). O `ordered` usa o reconhecedor do `unordered` mais *matching* com o KanjiVG, sem dados *online* para treinar.
2. **O caminho (a), descartado:**
   - a 1D-CNN precisa de dados *online*: TUAT ou CASIA para o pré-treino, coleta própria para o teste, com termos de uso confirmados;
   - o modelo aprende a tolerar variações de ordem, em vez de cobrá-las.
3. **Nos dois casos,** a captura no canvas é a mesma (traços com `x`, `y` e `t`), e o KanjiVG entra como referência.

Fontes desta seção:
- Zhang et al., [arXiv 1606.06539](https://arxiv.org/abs/1606.06539)
- Gan et al., [arXiv 2004.09412](https://arxiv.org/pdf/2004.09412.pdf)
- Hu et al., [arXiv 1610.04057](https://arxiv.org/pdf/1610.04057)
- Graham, [arXiv 1308.0371](https://arxiv.org/pdf/1308.0371)
- Lai et al., [DeepAI](https://api.deepai.org/publication/toward-high-performance-online-hccr-a-cnn-approach-with-dropdistortion-path-signature-and-spatial-stochastic-max-pooling)
- Wang, Zhu e Nakagawa, [ICDAR 2011](https://meilu.jpshuntong.com/url-687474703a2f2f7765622e747561742e61632e6a70/~nakagawa/pub/2011/pdf/Wang_ICDAR2011.pdf)
- Mita e Nakagawa, [IEICE 2016](https://ken.ieice.org/ken/paper/20160905VbKW/eng/)
- Nguyen et al., [PRL 2019](https://ntuanhung.github.io/publication/2019-01-01-Robust-and-real-time-stroke-order-evaluation-using-incremental-stroke-context-for-learners-to-write-Kanji-characters-correctly)
- Cai, Uchida e Sakoe, [Frontiers of Computer Science](https://journal.hep.com.cn/fcs/EN/10.1007/s11704-014-3207-6)
- Ido, [IEICE 2015](https://www.ieice.org/ken/paper/20150320mBXP/eng/)
- TUAT, [Kuchibue/Nakayosi](https://web.tuat.ac.jp/~nakagawa/database/en/about_kuchibue.html)
- CASIA-OLHWDB, [ICDAR 2009](https://bibtex.github.io/ICDAR-2009-WangLYZ.html)
- Zinnia/Tomoe, [FreshPorts](https://freshports.org/japanese/zinnia-tomoe)
- Sigma-lognormal, [ISI](https://digitalcommons.isical.ac.in/journal-articles/2438)
- MDN, [getCoalescedEvents](https://developer.mozilla.org/docs/Web/API/PointerEvent/getCoalescedEvents)
- W3C, [InkML](https://www.w3.org/TR/InkML)

Números e termos de uso vêm dos resumos e páginas citados. Os artigos completos não foram lidos.

---

## 6. Runtimes e otimização de inferência

O treinamento será feito em uma máquina potente com PyTorch. O artefato treinado será exportado e testado no notebook de referência.

| Runtime | Papel | Por que testar | Observações |
|---|---|---|---|
| PyTorch CPU | Baseline de execução | Menor atrito com o treinamento e depuração | Não presumir que será o mais rápido |
| ONNX Runtime CPU | Runtime neutro de comparação | Execução de grafo ONNX e opções de quantização | Resultado depende do modelo, operadores e build |
| OpenVINO CPU | Candidato prioritário para Intel | Otimizações de CPU Intel, streams e suporte a baixa precisão | Adiciona etapa de conversão e dependência do runtime |

### Sequência recomendada

1. Treinar e validar em PyTorch FP32.
2. Medir PyTorch CPU no hardware-alvo.
3. Exportar para ONNX e validar equivalência numérica.
4. Medir ONNX Runtime CPU FP32.
5. Converter/compilar para OpenVINO e medir CPU FP32.
6. Aplicar quantização INT8 aos runtimes que fizerem sentido.
7. Comparar acurácia e latência após quantização.

Não comparar runtimes usando artefatos ou pré-processamentos diferentes. O tempo deve incluir o pipeline completo de inferência: decodificação/normalização da entrada, tensorização, inferência e obtenção do Top-K. Medir separadamente cada etapa para identificar gargalos.

### Quantização

Testar:
- FP32 como referência de qualidade;
- INT8 pós-treinamento (PTQ), com conjunto representativo de calibração;
- quantization-aware training (QAT) somente se PTQ causar perda de qualidade inaceitável.

O modelo quantizado só deve ser adotado se reduzir latência ou memória sem degradar significativamente Top-1/Top-5. Quantização não deve ser considerada uma otimização garantida.

---

## 7. Plano experimental

### 7.1 Dados e divisão

Para o modo `unordered`:
- Começar com ETL8G ou ETL9G, conforme escopo de classes e viabilidade de uso.
- Manter a imagem grayscale multinível como experimento principal; comparar a variante binária quando aplicável.
- Fazer divisão por escritor, quando os metadados permitirem, para reduzir vazamento de estilo de escrita entre treino e teste.
- Manter um conjunto de teste de escritores nunca vistos.
- Documentar licença, condições de download e redistribuição antes de incorporar os dados ao repositório.

Para o modo `ordered`:
- Coletar sequências reais de desenho no canvas, com coordenadas e eventos de início/fim de traço.
- KanjiVG pode fornecer exemplos vetoriais e ordem de referência para protótipos e geração sintética.
- Não usar apenas sequências sintéticas como prova de generalização para escrita real.
- Criar um conjunto piloto de escrita humana com diversidade de alunos e estilos.

### 7.2 Resolução de entrada

Testar no mínimo:
- 64×64;
- 96×96;
- 128×128.

A resolução 64×64 é atraente para reduzir custo, mas pode apagar traços finos ou detalhes de kanjis complexos. O ETL9B tem imagens binárias 64×63 e ETL9G tem grayscale 128×127; comparar a conversão para as resoluções de entrada com preservação de proporção e padding. Não distorcer o caractere para preencher um quadrado.

### 7.3 Matriz de experimentos

| ID | Modo | Modelo | Entrada | Precisão/runtime |
|---|---|---|---|---|
| U1 | unordered | CNN customizada pequena | 64×64 | PyTorch FP32 |
| U2 | unordered | CNN customizada pequena | 96×96 | PyTorch FP32 |
| U3 | unordered | CNN customizada pequena | 128×128 | PyTorch FP32 |
| U4 | unordered | MobileNetV3-Small | 96×96 | PyTorch FP32 |
| U5 | unordered | ResNet-18 | 96×96 | PyTorch FP32 |
| U6 | unordered | HOG + SVM | feature vector | CPU |
| O1 | ordered | 1D-CNN temporal | sequência | PyTorch FP32 |
| O2 | ordered | CNN 2D com mapa de ordem | 96×96 + canais | PyTorch FP32 |
| O3 | ordered | GRU pequena | sequência | PyTorch FP32 |
| R1 | ambos, se exportável | melhor modelo por modo | entrada escolhida | ONNX Runtime FP32 |
| R2 | ambos, se exportável | melhor modelo por modo | entrada escolhida | OpenVINO FP32 |
| Q1 | ambos, se viável | melhor modelo por runtime | entrada escolhida | INT8 |

A matriz é uma proposta inicial. Não é necessário executar todos os experimentos se uma etapa anterior demonstrar que uma opção é claramente inadequada.

### 7.4 Métricas de qualidade

- Top-1 accuracy.
- Top-5 accuracy.
- Macro-F1, para observar desempenho por classe.
- Matriz de confusão.
- Acurácia por complexidade do kanji (por exemplo, faixas de quantidade de traços).
- Resultados por escritor, quando possível.
- Para `ordered`, medir separadamente reconhecimento do caractere e, se implementado, conformidade da ordem.

Top-5 é especialmente relevante porque o produto apresenta candidatos ao aluno, não apenas uma resposta única.

### 7.5 Métricas de performance

- Latência de pré-processamento.
- Latência de inferência isolada.
- Latência total da requisição de reconhecimento.
- p50, p90 e p95.
- Throughput sustentado (requisições por segundo).
- RAM do processo e pico de RAM.
- CPU média e pico.
- Tempo de inicialização e carregamento do modelo.
- Tamanho do artefato.
- Temperatura/frequência, quando disponível, para detectar throttling.

### 7.6 Concorrência

Executar cenários com:
- 1 cliente (baseline);
- 2 clientes simultâneos;
- 3 clientes simultâneos;
- 5 clientes simultâneos (carga esperada máxima inicial);
- 10 clientes simultâneos (teste de estresse).

A simulação deve representar clientes enviando jobs em uma janela curta, com mistura de `ordered` e `unordered`, enquanto o mesmo notebook mantém frontend, API, fila e modelos ativos. Distinguir explicitamente:
- usuários conectados e mantendo SSE;
- clientes que submetem um reconhecimento;
- inferências efetivamente executadas em paralelo.

**Configuração-base proposta:** um serviço/processo de inferência separado do event loop do FastAPI, com os dois modelos carregados uma única vez e uma inferência ativa por vez. O job seleciona a CNN 2D ou a 1D-CNN conforme o modo. A fila compartilhada absorve rajadas e o backend continua atendendo requisições e SSE.

Comparar depois:
- 1 execução de inferência ativa;
- 2 execuções simultâneas, seja no mesmo processo com concorrência controlada, seja com dois workers/processos.

Ao comparar processos independentes, medir o custo de RAM da duplicação dos modelos. Também testar threads internas do runtime (por exemplo 1, 2 e 4), evitando oversubscription: dois workers com quatro threads cada podem competir pelos mesmos quatro núcleos físicos. Não assumir que mais workers sempre aumentam o throughput.

O objetivo não é executar cinco ou dez inferências obrigatoriamente em paralelo. O objetivo é aceitar 3–5 envios próximos sem perda de jobs, manter API/SSE responsivos e oferecer latência p95 aceitável. A fila pode serializar parte do trabalho; a capacidade será determinada pela vazão sustentada e pelo tempo de espera observado.

### 7.7 Condições do benchmark

- Usar o mesmo conjunto de teste e o mesmo pré-processamento.
- Fazer warm-up antes de medir.
- Executar várias rodadas e reportar mediana e percentis.
- Testar ligado à tomada e registrar o perfil de energia.
- Fazer teste prolongado para observar temperatura e throttling.
- Não executar treinamento simultaneamente ao benchmark de inferência.
- Registrar sistema operacional, versão do Python, PyTorch, ONNX Runtime/OpenVINO e configuração de threads.
- Repetir o benchmark depois de reiniciar o serviço para medir cold start separadamente.

---

## 8. Riscos e pontos de atenção

| Risco | Impacto | Mitigação |
|---|---|---|
| Diferença entre canvas e ETL | Acurácia de teste pode não representar a escrita dos alunos | Criar conjunto real do canvas; aplicar augmentations realistas; validar por escritor |
| ETL não tem sequência temporal | Não permite treinar diretamente `ordered` | Capturar dados online e usar KanjiVG apenas como referência/sintético |
| Reduzir resolução demais | Perda de traços finos e confusão entre kanjis semelhantes | Comparar 64, 96 e 128 px |
| Divisão aleatória com amostras do mesmo escritor | Métricas superestimadas por vazamento de estilo | Separação por escritor |
| INT8 reduzir acurácia ou não acelerar | Piora do compromisso qualidade/performance | Comparar FP32 e INT8 no hardware real |
| Throttling térmico do notebook | Latência piora após alguns minutos | Benchmark prolongado e controle térmico |
| Concorrência excessiva | Latência e throughput podem piorar | Fila, limite de workers e threads medidos |
| Classes demais com poucas amostras | Confusão entre caracteres raros | Definir escopo de classes e avaliar macro-F1/Top-K |

---

## 9. Critérios para escolher o modelo

A decisão não deve ser baseada somente no menor tempo de inferência. Recomenda-se a seguinte ordem de decisão:

1. **Acurácia mínima aceitável:** eliminar modelos que não atingem o nível de reconhecimento necessário.
2. **Top-5:** avaliar se os candidatos apresentados são úteis mesmo quando Top-1 não é perfeito.
3. **Latência p95 sob carga:** priorizar experiência do aluno, não somente inferência isolada.
4. **Carga concorrente esperada:** validar latência p95 e throughput com 3–5 clientes submetendo jobs em uma janela curta; usar dez clientes como estresse adicional.
5. **RAM e estabilidade:** garantir que o serviço permaneça estável junto com frontend, backend, fila, os dois modelos e demais componentes executados no mesmo notebook.
6. **Complexidade operacional:** preferir a solução mais simples quando a diferença de desempenho for pequena.

Os limites numéricos de aceitação devem ser definidos depois de uma primeira rodada de benchmark e de uma validação com a escola. Não há, neste momento, dados medidos que sustentem uma promessa específica de milissegundos ou acurácia.

---

## 10. Recomendação final do spike

### Shortlist

| Ordem | Candidato | Papel após decisão da Opção C |
|---:|---|---|
| 1 | CNN 2D customizada compacta | **Modelo inicial definido para `unordered`** |
| 2 | 1D-CNN temporal compacta | **Modelo inicial definido para `ordered`** |
| 3 | MobileNetV3-Small | Comparador para `unordered` |
| 4 | ResNet-18 | Controle de capacidade para `unordered` |
| 5 | HOG + SVM | Baseline clássico para `unordered` |
| 6 | CNN 2D com mapa de ordem | Alternativa experimental para `ordered` |
| 7 | GRU pequena | Alternativa experimental para `ordered` |

### Runtime recomendado para avaliação

1. PyTorch CPU como baseline de referência.
2. OpenVINO CPU como candidato prioritário neste Intel de 11ª geração.
3. ONNX Runtime CPU como alternativa portátil e comparação adicional.
4. INT8 somente após os resultados FP32.

### Próximos passos propostos

1. Confirmar o dataset inicial e o escopo de kanjis.
2. Implementar o pipeline de pré-processamento determinístico e compartilhado.
3. Preparar split de treino/validação/teste por escritor.
4. Treinar a CNN 2D compacta e MobileNetV3-Small para `unordered`.
5. Criar benchmark reproduzível no Inspiron 3501.
6. Capturar dados reais do canvas e treinar a 1D-CNN temporal para `ordered`.
7. Comparar runtimes e quantização com o melhor checkpoint de cada modo.
8. Registrar resultados em tabela e fechar runtime, resolução, precisão e concorrência numa ADR.

**Decisão registrada (substituída em 2026-11-08 pela [ADR 0012](../adr/0012-ordered-mode-as-stroke-order-evaluation.md)):** adotar a Opção C como arquitetura inicial do KanjiLens: CNN 2D compacta para `unordered` e 1D-CNN temporal compacta para `ordered`. A decisão sobre variantes concretas, hiperparâmetros, runtime e quantização permanece condicionada aos benchmarks no Inspiron 3501.

---

## 11. Referências

### 11.1 Projetos de referência no GitHub

Os repositórios abaixo foram selecionados como **referências técnicas para estudo**, não como dependências aprovadas nem como código a ser incorporado diretamente ao KanjiLens. A seleção cobre reconhecimento por imagem (`unordered`), reconhecimento online baseado em traços, baselines geométricos e ferramentas relacionadas ao ETL. Revisão dos links: 2026-11-08.

| Projeto | Abordagem e conteúdo relevante | Relação com o KanjiLens | Limitações / cuidados |
|---|---|---|---|
| [mcyph/cnn_chinese_hw](https://github.com/mcyph/cnn_chinese_hw) | Reconhecimento online de escrita chinesa e kanji japonês com PyTorch. Recebe coordenadas `(x, y)` dos traços; a implementação atual rasteriza a trajetória em mapas multicanais e usa uma SE-ResNet compacta com aproximadamente 2,9 milhões de parâmetros. Inclui pipeline de treino, avaliação Top-K, serviço e exportação ONNX. | **Referência mais próxima para o modo `ordered`**, principalmente pelo tratamento de traços online, pela representação de entrada e pela arquitetura compacta. Também ajuda a estudar retorno de candidatos e integração em serviço. | Não é a mesma arquitetura escolhida pelo KanjiLens: o projeto usa mapas 2D multicanais, não uma 1D-CNN temporal. O README informa que não há checkpoint pré-treinado. Licença LGPL-2.1; avaliar obrigações antes de reutilizar código. |
| [dariyooo/DaKanji-Single-Kanji-Recognition](https://github.com/dariyooo/DaKanji-Single-Kanji-Recognition) | CNN compacta para classificar um caractere japonês isolado a partir de imagem em grayscale. O projeto compara CNN customizada, MobileNet e EfficientNet-Lite, documenta pré-processamento no modelo, quantização e exportação ONNX/ExecuTorch. | **Referência forte para `unordered`**: pipeline de imagem, comparação de backbones compactos, métricas de latência/tamanho e exportação para inferência. | Os números de latência publicados são do hardware/runtime do autor e não devem ser projetados para o i7-1165G7. O projeto tem licença MIT, mas datasets e fontes de dados usados devem ser avaliados separadamente. |
| [ATShah03/KanjiRecognizer](https://github.com/ATShah03/KanjiRecognizer) | CNN em Keras/TensorFlow treinada com ETL, com foco em até aproximadamente 3.000 kanjis, incluindo ETL-9, pré-processamento e uma aplicação web para desenho e consulta. | Referência prática para o fluxo ETL → pré-processamento → CNN → interface de escrita, e para dificuldades de memória ao trabalhar com muitas classes. | Projeto pequeno/experimental; o README relata redução do conjunto de classes por limitações de RAM durante o treino. Não tratar a acurácia reportada como comparável sem reproduzir protocolo, split e classes. Licença de reutilização do código não confirmada nesta revisão. |
| [ichisadashioko/kanji-recognition](https://github.com/ichisadashioko/kanji-recognition) | Projeto didático de CNN para reconhecimento de kanji, com implementações TensorFlow/Python, TensorFlow.js para canvas no navegador e TensorFlow Lite para Android. O autor também descreve a criação de uma aplicação de desenho para coletar exemplos. | Referência para integração entre canvas, coleta de amostras próprias e inferência em diferentes ambientes. | Projeto antigo e de caráter demonstrativo; não é baseline de desempenho nem evidência de arquitetura atual recomendada. Verificar dependências e licença antes de qualquer reutilização. |
| [asdfjkl/kanjicanvas](https://github.com/asdfjkl/kanjicanvas) | Reconhecimento online em JavaScript por correspondência geométrica de traços. Foi concebido para tolerar ordem e quantidade de traços incorretas; deriva de um método de correspondência um-a-um entre traços, não de uma CNN. | **Baseline não neural para comparação**, especialmente no modo que não deve depender da ordem dos traços. Também é útil para observar uma implementação de reconhecimento diretamente sobre canvas. | Não é um modelo de deep learning e não substitui o experimento CNN/1D-CNN. Licença MIT. |
| [yukoba/CnnJapaneseCharacter](https://github.com/yukoba/CnnJapaneseCharacter) | Implementação antiga de uma CNN VGG-like para reconhecimento de hiragana, baseada em ETL8G e em trabalho anterior de Charlie Tsai. | Referência histórica para pré-processamento de imagens ETL e treinamento de CNNs de caracteres japoneses. | **Não é um reconhecedor de kanji**: o README descreve hiragana. Stack muito antiga (Keras 1.x, Theano/TensorFlow antigos); usar apenas como referência histórica, não como base técnica de produção. |
| [melodyfs/Build-OCR](https://github.com/melodyfs/Build-OCR) | Repositório citado pelo projeto `ATShah03/KanjiRecognizer` como uma das referências consultadas para entender a extração/descompactação dos arquivos ETL. | Possível referência auxiliar para investigar o formato binário e a preparação dos arquivos ETL. | Não é, por si só, uma arquitetura de reconhecimento de kanji. Inspecionar código, atualidade e licença antes de usar; não assumir compatibilidade com a versão dos arquivos ETL que será adotada. |

**Prioridade de leitura sugerida:**

1. `mcyph/cnn_chinese_hw` — estudar primeiro para representação de traços online, candidatos Top-K, pipeline de treino e execução CPU/ONNX. Comparar sua codificação multicanal com a 1D-CNN temporal definida para `ordered`; não copiar a arquitetura automaticamente.
2. `dariyooo/DaKanji-Single-Kanji-Recognition` — estudar para o pipeline `unordered`, CNN compacta, comparação de backbones e quantização/exportação.
3. `ATShah03/KanjiRecognizer` — estudar o uso de ETL9 e o fluxo de aplicação de desenho; conferir com cuidado o protocolo experimental.
4. `asdfjkl/kanjicanvas` — usar como baseline geométrico não neural, se houver interesse em comparar métodos clássicos.
5. Os demais repositórios são referências complementares/históricas, não candidatos diretos a produção.

**Cuidados gerais:** os resultados publicados pelos autores não são diretamente comparáveis entre si nem com o KanjiLens sem igualar classes, dados, divisão por escritor, pré-processamento, hardware e métrica. Antes de copiar código, pesos ou dados, verificar a licença do repositório e as licenças dos datasets separadamente. A presença de um link nesta seção não significa aprovação para reutilização ou adoção arquitetural.

### 11.2 Literatura, datasets e documentação técnica

1. **Intel — Intel Core i7-1165G7 specifications.** Especificações oficiais de núcleos, threads, frequência, DL Boost, GPU integrada e instruções.  
   https://www.intel.com.br/content/www/br/pt/products/sku/208662/intel-core-i71165g7-processor-12m-cache-up-to-4-70-ghz/specifications.html

2. **AIST — The ETL Character Database.** Descrição oficial dos conjuntos ETL8 e ETL9, número de classes, amostras, resoluções e natureza dos dados digitalizados.  
   https://etlcdb.db.aist.go.jp/the-etl-character-database/

3. **Tsai, Charlie — Recognizing Handwritten Japanese Characters Using Deep Convolutional Neural Networks (Stanford, 2016).** Trabalho acadêmico que experimenta CNNs para caracteres japoneses usando ETL.  
   https://cs231n.stanford.edu/reports/2016/pdfs/262_Report.pdf

4. **Howard et al. — Searching for MobileNetV3 (ICCV 2019).** Artigo original da arquitetura MobileNetV3, incluindo variante Small e foco em dispositivos móveis.  
   https://arxiv.org/abs/1905.02244

5. **ONNX Runtime — Quantize ONNX models.** Documentação oficial sobre quantização, formatos INT8 e limitações de desempenho dependentes do hardware.  
   https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html

6. **OpenVINO — CPU Device.** Documentação do plugin CPU, otimizações para CPUs Intel, streams e precisão de inferência.  
   https://docs.openvino.ai/2024/openvino-workflow/running-inference/inference-devices-and-modes/cpu-device.html

7. **OpenVINO — Performance hints.** Documentação de modos de latência e throughput e seus efeitos sobre streams e requisições.  
   https://docs.openvino.ai/2025/openvino-workflow/running-inference/optimize-inference/high-level-performance-hints.html

8. **KanjiVG — Files and coverage.** Documentação de cobertura, formato SVG, representação vetorial dos traços e ordem de escrita.  
   https://kanjivg.tagaini.net/files.html

9. **KanjiVG — SVG Format.** Detalhes sobre grupos de caminhos, ordem dos traços e metadados da estrutura do kanji.  
   https://kanjivg.tagaini.net/svg-format.html

---

## 12. Rastreabilidade: fatos, inferências e decisões pendentes

Para evitar que hipótese seja confundida com resultado experimental:

- **Fato documentado:** o i7-1165G7 possui 4 núcleos e 8 threads, DL Boost e extensões AVX2/AVX-512 (Intel).
- **Fato documentado:** ETL8/ETL9 fornecem imagens de caracteres, não a trajetória temporal do desenho (AIST).
- **Fato documentado:** KanjiVG codifica traços vetoriais e sua ordem de referência, com formas baseadas em fontes escolares japonesas (KanjiVG).
- **Fato documentado:** MobileNetV3-Small foi concebida para cenários com menor orçamento de recursos (artigo MobileNetV3).
- **Fato documentado:** a quantização pode ou não acelerar dependendo do hardware e do modelo (ONNX Runtime).
- **Inferência técnica:** CNN customizada compacta é uma baseline adequada para começar no modo `unordered`.
- **Inferência técnica:** OpenVINO merece prioridade de benchmark neste Intel de 11ª geração.
- **Hipótese experimental:** 1D-CNN temporal pode oferecer um bom compromisso para `ordered`.
- **Não medido:** latência, throughput, RAM efetiva e acurácia de qualquer candidato no Dell Inspiron 3501.
- **Pendente:** arquitetura final, resolução final, runtime de produção, número de workers e uso de INT8.


---

## 13. Decisão arquitetural registrada

### 13.1 Decisão atual: avaliação da ordem contra uma referência (2026-11-08)

Registrada na [ADR 0012](../adr/0012-ordered-mode-as-stroke-order-evaluation.md).

- **Reconhecimento, nos dois modos:** uma CNN 2D compacta sobre a imagem rasterizada, que não depende da ordem. Continuam valendo os candidatos, comparadores, resoluções e o plano de benchmark de `unordered` deste spike.
- **`ordered`:** depois do reconhecimento, os traços desenhados são comparados com a ordem e a direção do KanjiVG dos candidatos, por correspondência entre traços. Os algoritmos estão na seção 5.3 (b). A resposta diz se a ordem está correta e quais traços estão fora de ordem ou na direção errada.
- **Sem 1D-CNN, GRU ou dataset *online* para treinar.**
- **Fica em aberto:**
  - o algoritmo de correspondência;
  - quantos candidatos avaliar;
  - se a avaliação só anota ou também reordena;
  - o formato da resposta;
  - o conjunto de teste com ordem certa e errada.

### 13.2 Decisão anterior: Opção C (substituída)

O projeto decidiu seguir com duas estratégias/modelos especializados:

- **`unordered`:** CNN 2D compacta recebe a imagem rasterizada final.
- **`ordered`:** 1D-CNN temporal compacta recebe a sequência de pontos/traços.

Registrada na [ADR 0010](../adr/0010-two-recognition-modes-with-specialized-models.md); o hardware e a carga, na [ADR 0011](../adr/0011-school-notebook-as-server-with-cpu-first-inference.md).

Não será implementado um único modelo compartilhado nesta primeira versão e não haverá compartilhamento de pesos entre os dois modelos. O que será compartilhado é a infraestrutura e os contratos do sistema: API, validação do payload, gestão de jobs, workers, observabilidade e formato Top-K/SSE. O pré-processamento comum será reutilizado apenas onde fizer sentido para cada representação.

Esta é uma decisão de arquitetura inicial, não a aprovação de uma implementação específica. A largura/profundidade dos modelos, número de pontos por sequência, resolução da imagem, runtime, quantização e número de workers dependem dos benchmarks e da qualidade dos dados reais.

**Critério para reabrir a decisão:** se a 1D-CNN não atingir a qualidade necessária ou apresentar custo excessivo, comparar GRU e CNN 2D com mapas de ordem. Se houver evidência de que um backbone compartilhado melhora o compromisso global sem comprometer a ordem temporal, isso poderá ser proposto em uma ADR futura.

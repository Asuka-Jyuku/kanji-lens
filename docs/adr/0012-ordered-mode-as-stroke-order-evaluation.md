# 0012. Modo `ordered` como avaliação da ordem dos traços contra uma referência

- **Status:** Aceita
- **Data:** 2026-11-08
- **Relacionadas:** substitui a [0010](0010-two-recognition-modes-with-specialized-models.md); [0004](0004-clean-and-hexagonal-architecture.md), [0006](0006-cnn-with-pytorch.md), [0011](0011-school-notebook-as-server-with-cpu-first-inference.md)

## Contexto

A [ADR 0010](0010-two-recognition-modes-with-specialized-models.md) tratou o modo `ordered` como **reconhecimento *online***: uma 1D-CNN temporal que usa a trajetória como evidência. A pesquisa da [seção 5.3 do spike](../spikes/model-and-runtime-evaluation.md#53-como-o-modo-ordered-costuma-ser-feito-pesquisa-de-2026-11-08) mostrou que "a ordem importa" cobre duas tarefas diferentes:

- **Reconhecer usando a trajetória.** Os reconhecedores *online* são feitos para **tolerar** ordem errada, porque aprendem a ordem que as pessoas usam. Treiná-los exige um dataset *online* grande (TUAT, CASIA) com termos de uso a confirmar e dados próprios.
- **Avaliar se a ordem está certa.** É o caminho padrão em sistemas de ensino de kanji: o desenho é comparado traço a traço com a ordem e a direção convencionais do kanji, por correspondência entre traços. Os artigos relatam:
  - *DP matching*, cube search e bipartite matching, com cerca de 99% (Cai, Uchida e Sakoe);
  - avaliação incremental com contexto, com 98,5% e até 0,12 s por caractere (Nguyen, Nguyen, Mita e Nakagawa, 2019).

  Esse caminho não precisa de rede neural nem de dataset de escrita para treinar, e roda leve na CPU.

O KanjiLens é de uma escola de japonês. O que o aluno precisa saber no modo `ordered` é **se escreveu na ordem certa**, e não ter um reconhecimento melhor por causa da ordem.

## Alternativas consideradas

- **Reconhecimento *online* com 1D-CNN (ADR 0010):** usa a trajetória como evidência. Não cobra a ordem correta: aprende a tolerar a ordem errada. Precisa de um dataset *online* com licença a confirmar e de um segundo modelo para treinar, versionar e manter na RAM.
- **Classificador treinado para "ordem certa × errada":** cobra a ordem. Precisa de muitos exemplos rotulados de ordem errada para cada kanji, coisa que não existe pronta.
- **Reconhecimento sem depender da ordem + avaliação da ordem contra uma referência:** cobra a ordem com uma explicação (qual traço está fora de ordem ou na direção errada). Usa só o modelo do `unordered` e uma base de referência aberta. Fica sensível a traços unidos ou quebrados, porque a quantidade de traços desenhados difere da referência.

## Decisão

Os dois modos usam **um único modelo de reconhecimento**: a **CNN 2D compacta** sobre a imagem rasterizada, que não depende da ordem (o desenho da ADR 0010 para o `unordered` continua valendo).

No modo **`ordered`**, depois do reconhecimento, o KanjiLens **avalia a ordem e a direção dos traços** desenhados contra a **referência do KanjiVG** dos candidatos, por um algoritmo de correspondência entre traços. A resposta diz, para o candidato avaliado:
- se a ordem está correta;
- quais traços estão fora de ordem ou na direção errada;
- se a quantidade de traços difere da referência.

Não há 1D-CNN nem modelo temporal treinado.

Continuam como na ADR 0010:
- o contrato da API (`POST /api/recognitions` com `strokes` e `stroke_order_mode`);
- o canvas enviando a lista de traços, e não um PNG;
- o modo escolhido a cada reconhecimento.

**Em aberto:**
- **O algoritmo de correspondência:** *DP matching*, bipartite matching / cube search ou avaliação incremental com contexto, a comparar num spike.
- **Quantos candidatos são avaliados:** só o primeiro ou os top-K.
- **O papel da avaliação:** se ela só anota o resultado ou também reordena os candidatos.
- **O formato exato da resposta.**
- **O modo padrão da interface.** *Atualização de 2026-11-08:* o padrão é **"não importa" (`unordered`)**. Quem quer treinar a ordem troca a opção antes de desenhar.

## Consequências

- **Positivas:**
  - o modo `ordered` passa a cobrar o que a escola ensina, com uma explicação traço a traço;
  - sobra um modelo só para treinar, versionar, avaliar e carregar na RAM do notebook;
  - não depende de dataset *online* para treinar, nem de coleta de desenhos de alunos para o treino;
  - a avaliação é um algoritmo determinístico e leve, testável com casos fixos;
  - o KanjiVG também dá a quantidade e a direção esperadas dos traços.
- **Negativas:**
  - **A avaliação depende de o reconhecimento acertar o kanji.** Se o candidato certo não estiver entre os avaliados, a avaliação da ordem é feita contra o kanji errado.
  - **Traços unidos ou quebrados** fazem a quantidade desenhada diferir da referência, e o algoritmo precisa tratar isso sem acusar erro falso.
  - **A referência é a ordem convencional do KanjiVG.** Variantes aceitas na escola precisam de tratamento à parte (*a verificar* com os professores).
  - **Licença do KanjiVG.** Os dados vêm do KanjiVG (CC BY-SA 3.0, *a confirmar* na fonte) e vão junto com a aplicação, porque não há saída de rede. É preciso atribuir a fonte e manter a licença nos dados derivados, à parte da licença MIT do código.
  - **Um teste com desenhos reais** em ordem certa e errada ainda é necessário. Guardar desenhos de alunos para isso pede ADR (`CLAUDE.md`, "Segurança").
- **Na prática:**
  - `kanjilens_ml/models/` tem só a CNN 2D;
  - a avaliação da ordem fica num módulo puro, sem PyTorch (proposta: `kanjilens_ml/stroke_order/`), com a mesma normalização de traços do pré-processamento;
  - o backend ganha um port para a avaliação da ordem (proposta: `StrokeOrderEvaluator`), com o adapter usando esse módulo;
  - os dados do KanjiVG ficam fora do código, com a versão e a licença registradas, e são carregados uma vez no processo de inferência;
  - **métricas do `ordered`:** acerto da avaliação (erros de ordem detectados × falsos alarmes) num conjunto fixo de desenhos com ordem certa e errada, à parte do Top-1/Top-5 do reconhecimento.

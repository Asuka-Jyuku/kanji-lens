# Experimentos: splits, reprodutibilidade e versões do modelo

O que torna um número deste projeto confiável e comparável.

## Splits

- **Por pessoa que escreveu, não por amostra.** Senão o estilo de letra de alguém vaza do treino para o teste, e o número fica melhor do que vai ser com um aluno novo. No ETL, a aproximação é o *data set*, a confirmar no `ETL9INFO` ([ADR 0021](../../../../docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md)).
- **O split de teste é definido uma vez,** com a regra versionada, e nunca serve para ajustar hiperparâmetro.
- **Os desenhos do canvas são um conjunto à parte,** feitos no app, com o kanji esperado ([`docs/MODEL.md`](../../../../docs/MODEL.md)). Medem a diferença entre dataset e canvas.
- **A lista de classes é versionada** (não "as N primeiras"): ela define os índices dos rótulos.

## Reprodutibilidade

- **Seeds** de `torch`, `numpy`, `random` e dos workers do `DataLoader`, todas da configuração ([PyTorch](https://pytorch.org/docs/stable/notes/randomness.html)).
- **Configuração:** tudo de que o treino depende em `ml/configs/`, commitado.
- **Ambiente:** o `uv.lock`. A versão do PyTorch faz parte da versão do modelo.
- **Notebooks** são só exploração: nada importa deles, e nenhum número reportado sai só de um.

## O que é uma versão do modelo

Tudo salvo junto em `ml/artifacts/<version>/`:
- os pesos e a configuração do treino;
- a **lista de classes**, na ordem;
- a **versão do pré-processamento** (tamanho da entrada, normalização);
- as métricas: Top-1/Top-5 no split de teste e nos desenhos do canvas.

O recognizer se recusa a subir se a lista de classes ou o pré-processamento não baterem com o código. A divergência não quebraria nada: daria o kanji errado, com confiança alta.

## Reportar números

Todo número vem com o conjunto (split de teste ou canvas), a versão do modelo, a configuração e a seed. Antes e depois, no mesmo conjunto. Queda só com um "aceito porque...".

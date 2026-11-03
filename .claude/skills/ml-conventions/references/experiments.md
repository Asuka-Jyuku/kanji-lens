# Experimentos: splits, reprodutibilidade e versões do modelo

O que torna um número deste projeto confiável e comparável. O porquê está na ADR 0006 e no ARCHITECTURE.md, seção 7.

## Splits

| Ponto | Por quê | Fonte |
|---|---|---|
| **Split por pessoa que escreveu, não por amostra** (quando o dataset identifica quem escreveu, como o ETL) | as amostras da mesma pessoa no treino e no teste vazam o estilo de letra dela, e a acurácia no teste parece melhor do que vai ser para um usuário novo | — (julgamento; prática comum em datasets de escrita à mão) |
| O split de teste é definido uma vez, com a definição versionada (arquivo ou seed + regra), e nunca usado para ajustar hiperparâmetro | números de splits diferentes não são comparáveis | [scikit-learn: cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| Um **conjunto do canvas** à parte: desenhos reais feitos no app, com o kanji esperado | mede a diferença entre dataset e canvas, o principal risco do projeto | ARCHITECTURE.md, seção 7.4 |
| O subconjunto de classes (enquanto a quantidade estiver em aberto) é uma lista versionada, não "as N primeiras" | a lista define os índices dos rótulos | ARCHITECTURE.md, seção 7.2 |

## Reprodutibilidade

| Ponto | Como | Fonte |
|---|---|---|
| Seeds | `torch.manual_seed`, `numpy.random.seed`, `random.seed` e a seed dos workers do `DataLoader`, todas vindas da configuração | [PyTorch: reproducibility](https://pytorch.org/docs/stable/notes/randomness.html) |
| Configuração | tudo de que o treino depende em `ml/configs/<name>.yaml` (ou o formato escolhido na ADR de ferramentas), commitado | — |
| Ambiente | o lock file de `ml/`; a versão do PyTorch faz parte da versão do modelo | — |
| Notebooks | só exploração; nada importa de `notebooks/`, e nenhum número reportado sai só de um notebook | ARCHITECTURE.md, seção 8 |

## O que é uma versão do modelo

Uma versão do modelo é **o conjunto**, salvo junto em `ml/artifacts/<version>/`:
- os pesos;
- a configuração usada para treiná-los;
- a **lista de classes** (índice → kanji), na ordem;
- a **versão do pré-processamento** (tamanho da entrada, normalização, versão do módulo de pré-processamento);
- as métricas: Top-1/Top-5 no split de teste e no conjunto do canvas.

O adapter do recognizer carrega o conjunto e se recusa a subir se a lista de classes ou a versão do pré-processamento não bater com o código. Uma divergência não quebraria nada: devolveria o kanji errado, com confiança alta.

## Reportar números

Todo número num PR, numa issue ou no `docs/MODEL.md` vem com: o split (split de teste ou conjunto do canvas), a versão do modelo, a configuração e a seed. Antes e depois, no mesmo split. Uma queda só é aceita com um "aceito porque..." explícito.

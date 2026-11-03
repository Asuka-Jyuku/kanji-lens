# 0002. Monorepo para frontend, backend e ML

- **Status:** Aceita
- **Data:** 2026-11-03
- **Relacionadas:** [0004](0004-clean-and-hexagonal-architecture.md), [0008](0008-git-flow-and-changelog-by-release.md)

## Contexto

O KanjiLens tem três partes: o frontend em Angular, o backend em FastAPI e o código de ML (dataset, pré-processamento, treino, avaliação). O backend roda o modelo que o código de ML treina, e **os dois precisam aplicar exatamente o mesmo pré-processamento** à imagem de entrada ([ARCHITECTURE.md, seção 7.4](../ARCHITECTURE.md#74-pontos-de-atenção)). O produto é um app só, publicado numa máquina só, versionado como uma coisa só.

## Alternativas consideradas

- **Um repositório por parte** (frontend, backend, ml) — CI e permissões independentes; mas o pré-processamento compartilhado teria de ser publicado como pacote e versionado entre repositórios, uma mudança no contrato da API exigiria PRs coordenados em dois lugares, e as issues de uma funcionalidade ficariam espalhadas em três quadros.
- **Dois repositórios** (frontend; backend + ML) — mantém o pré-processamento junto; ainda separa o contrato da API e o quadro.
- **Monorepo** — um PR muda o pré-processamento, o treino e o adapter do recognizer juntos; um quadro de issues, um Project, um CHANGELOG, uma versão; custa uma CI que precisa decidir o que rodar por pasta.

## Decisão

Mantemos frontend, backend e ML neste único repositório, em `frontend/`, `backend/` e `ml/`. O motivo principal é que o pré-processamento e o contrato da API mudam de forma atômica, num PR só.

## Consequências

- **Positivas:** a consistência entre treino e inferência pode ser garantida num PR só; mudanças de contrato entre frontend e backend são revisadas juntas; um quadro e um release.
- **Negativas:** a CI precisa filtrar por caminho, para uma mudança no frontend não disparar a avaliação do modelo (e vice-versa), ou fica lenta; o repositório mistura ferramentas de Node e de Python, então cada parte mantém o próprio manifesto e lock file; quem clona leva as três partes.
- **Na prática:** cada parte tem o seu manifesto (`package.json`, `pyproject.toml`) dentro da própria pasta; o backend importa o código de ML como biblioteca (`kanjilens_ml`), só dentro do adapter do recognizer (ADR 0004); dataset e pesos ficam fora do git; os escopos de commit dizem a parte (`frontend`, `backend`, `ml`, `infra`, `repo`).

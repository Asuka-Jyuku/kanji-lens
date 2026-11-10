# KanjiLens

**Desenhe um kanji no celular e receba os caracteres mais prováveis, ordenados por confiança.**

[English](README.md) · [Arquitetura](docs/ARCHITECTURE.md) · [Decisões (ADRs)](docs/adr/README.md) · [Como contribuir](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

> **Status:** a tela de desenho, a API e o processamento dos jobs funcionam de ponta a ponta, com um reconhecedor falso. O modelo espera o dataset de treino. O andamento está no [GitHub Project](https://github.com/orgs/Asuka-Jyuku/projects/6).

## O que faz

O KanjiLens é um app web pequeno, feito para uma escola. O aluno desenha um kanji no canvas e recebe os candidatos mais prováveis, para escolher o que queria escrever. Não precisa acertar sempre: basta o kanji certo aparecer entre os primeiros.

Antes de desenhar, você escolhe se **a ordem dos traços importa**:
- **Não importa (padrão):** só o reconhecimento, com uma CNN 2D compacta que olha a imagem final.
- **Importa:** o KanjiLens também compara a ordem e a direção dos traços com o KanjiVG e diz quais traços estão errados.

Tudo roda num notebook da escola, na rede local, com inferência só na CPU. Sem nuvem e sem login.

```text
┌──────────────────────────────┐
│          KanjiLens           │
│ Ordem dos traços:            │
│   ( ) Importa (•) Não importa│
│   ┌──────────────────────┐   │
│   │          日          │   │
│   └──────────────────────┘   │
│ [Desfazer] [Limpar]          │
│ [Reconhecer]                 │
│   日  81%                    │
│   目  12%                    │
│   白   4%                    │
└──────────────────────────────┘
```

## Como funciona

1. O frontend manda os traços (os pontos, na ordem do desenho) e o modo para a API.
2. A API põe um job na fila e responde na hora com o `job_id`.
3. Um processo de inferência separado roda o modelo e, se a ordem importa, a avaliação da ordem.
4. O resultado chega ao celular por SSE (Server-Sent Events), com polling de reserva.

```text
 Celular ──▶ Angular ──REST──▶ FastAPI ──▶ Fila ──▶ Processo de inferência ──▶ CNN 2D
   ▲                                                  (+ avaliação da ordem com o KanjiVG)
   └──────────────── SSE ◀──────── resultado ◀───────┘
```

## Stack

| Parte | Tecnologias |
|---|---|
| Frontend | Angular 22, TypeScript, HTML Canvas, Pointer Events |
| Backend | Python 3.15, FastAPI, SSE, `asyncio.Queue` e um processo de inferência |
| Machine Learning | PyTorch (CNN 2D), NumPy e SciPy (avaliação da ordem com o KanjiVG) |
| Ferramentas | uv, Ruff, mypy, pytest, Vitest, ESLint, GitHub Actions |
| Execução | O notebook Windows da escola, sem Docker, pela rede local |

O código segue Clean Architecture com ports and adapters ([ADR 0004](docs/adr/0004-clean-and-hexagonal-architecture.md)), num repositório só ([ADR 0002](docs/adr/0002-monorepo-for-frontend-backend-and-ml.md)). Cada decisão fica registrada numa ADR.

## Como rodar

Siga o [`docs/RUNNING.md`](docs/RUNNING.md) para instalar, subir a API e o frontend e abrir pelo celular na mesma rede. Os comandos de teste, lint e build estão no [`CLAUDE.md`](CLAUDE.md#comandos).

## O que o projeto explora

Visão computacional e CNN, correspondência entre traços para avaliar a ordem, processamento assíncrono de jobs, atualização em tempo real por SSE, uma tela acessível pensada para o toque, e treino e inferência usando o mesmo pré-processamento.

## Licença e créditos

O código-fonte está sob a [licença MIT](LICENSE), que cobre só o código deste repositório. Datasets e pesos treinados não ficam no repositório: cada dataset mantém os próprios termos, e pesos treinados com ele podem herdá-los.

- **KanjiVG:** os dados de referência da ordem dos traços mantêm a própria licença (CC BY-SA 3.0, © Ulrich Apel, [kanjivg.tagaini.net](https://kanjivg.tagaini.net)), com atribuição.
- **ETL Character Database (ETL9G):** o modelo de reconhecimento vai ser treinado com ele (enquanto o site estiver fora do ar, veja o [spike](docs/spikes/training-without-etl.md)). É de uso livre, mas só pode ser obtido pelo [site oficial](https://etlcdb.db.aist.go.jp/), por isso este repositório não tem nenhuma imagem dele ([ADR 0021](docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md)). Referência: Electrotechnical Laboratory, Japanese Technical Committee for Optical Character Recognition, ETL Character Database, 1973-1984.

# KanjiLens

**Draw a kanji on your phone and get the most likely characters back, ranked by confidence.**

[Português](README.pt-BR.md) · [Architecture (pt-BR)](docs/ARCHITECTURE.md) · [Decisions (ADRs, pt-BR)](docs/adr/README.md) · [Contributing (pt-BR)](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

> **Status:** the drawing screen, the API and the job pipeline work end to end, with a placeholder recognizer. The model will be trained on synthetic drawings generated from KanjiVG while the ETL dataset is offline. Progress is tracked in the [GitHub Project](https://github.com/orgs/Asuka-Jyuku/projects/6).

## What it does

KanjiLens is a small web app for a local school. Students draw a kanji on a canvas and get the top candidates, so they can pick the one they meant. It doesn't need to guess right every time, only to have the right kanji near the top.

Before drawing, you choose whether **stroke order matters**:
- **It doesn't (default):** recognition only, with a compact 2D CNN that looks at the final image.
- **It does:** KanjiLens also compares the order and direction of your strokes with KanjiVG and tells you which strokes are wrong.

Everything runs on one school laptop on the local network, with CPU-only inference. There's no cloud and no login.

```text
┌──────────────────────────────┐
│          KanjiLens           │
│ Stroke order:                │
│   ( ) Matters (•) Doesn't    │
│   ┌──────────────────────┐   │
│   │          日          │   │
│   └──────────────────────┘   │
│ [Undo] [Clear]               │
│ [Recognize]                  │
│   日  81%                    │
│   目  12%                    │
│   白   4%                    │
└──────────────────────────────┘
```

## How it works

1. The frontend sends the strokes (points in drawing order) and the mode to the API.
2. The API queues a job and answers right away with its `job_id`.
3. A separate inference process runs the model and, if order matters, the stroke-order check.
4. The result reaches the phone over SSE (Server-Sent Events), with polling as a fallback.

```text
 Phone ──▶ Angular ──REST──▶ FastAPI ──▶ Queue ──▶ Inference process ──▶ 2D CNN
   ▲                                                  (+ stroke-order check vs KanjiVG)
   └──────────────── SSE ◀──────── job result ◀───────┘
```

## Tech stack

| Part | Technologies |
|---|---|
| Frontend | Angular 22, TypeScript, HTML Canvas, Pointer Events |
| Backend | Python 3.15, FastAPI, SSE, `asyncio.Queue` and one inference process |
| Machine Learning | PyTorch (2D CNN), NumPy and SciPy (stroke-order check against KanjiVG) |
| Tooling | uv, Ruff, mypy, pytest, Vitest, ESLint, GitHub Actions |
| Deployment | The school's Windows laptop, without Docker, over the LAN |

The code follows Clean Architecture with ports and adapters ([ADR 0004](docs/adr/0004-clean-and-hexagonal-architecture.md)), in a single repository ([ADR 0002](docs/adr/0002-monorepo-for-frontend-backend-and-ml.md)). Every decision is recorded as an ADR.

## Running locally

Follow [`docs/RUNNING.md`](docs/RUNNING.md) (pt-BR) to install, start the API and the frontend, and open the app from a phone on the same network. The test, lint and build commands are in [`CLAUDE.md`](CLAUDE.md#comandos).

## What this project explores

Computer Vision and CNNs, stroke matching for stroke-order checking, asynchronous job processing, real-time updates over SSE, a touch-first accessible UI, and keeping training and inference on the same preprocessing.

## License and credits

The source code is under the [MIT License](LICENSE). It covers only the code in this repository. Datasets and trained weights are not in the repository: each dataset keeps its own terms, and weights trained on it may inherit them.

- **KanjiVG:** the stroke-order reference data keeps its own license (CC BY-SA 3.0, © Ulrich Apel, [kanjivg.tagaini.net](https://kanjivg.tagaini.net)), with attribution.
- **ETL Character Database (ETL9G):** the preferred training data for the recognition model once the site is back; until then, training uses synthetic drawings from KanjiVG ([ADR 0022](docs/adr/0022-synthetic-training-data-from-kanjivg-while-etl-is-down.md), pt-BR). It's free to use but may only be obtained from [its official site](https://etlcdb.db.aist.go.jp/), so this repository holds none of its images ([ADR 0021](docs/adr/0021-etl9g-dataset-and-kyouiku-kanji-as-first-classes.md), pt-BR). Reference: Electrotechnical Laboratory, Japanese Technical Committee for Optical Character Recognition, ETL Character Database, 1973-1984.

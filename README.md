# KanjiLens

**Handwritten Kanji recognition using Deep Learning and Computer Vision.**

[Português](README.pt-BR.md) · [Architecture (pt-BR)](docs/ARCHITECTURE.md) · [Decisions (ADRs, pt-BR)](docs/adr/README.md) · [Contributing (pt-BR)](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

> **Status:** early stage. The architecture, tooling and CI are in place, and the `ml/`, `backend/` and `frontend/` skeletons exist. Product code starts with the backend.

---

## Overview

KanjiLens is a web application where you draw a kanji on a canvas and get back a ranked list of the characters it most likely represents. Before recognizing, you choose whether stroke order should matter.

The goal is not to guess the exact character every time. The goal is to show the **top candidates ranked by confidence**, so you can pick the one you meant to write.

Recognition uses a compact 2D CNN trained with PyTorch, which does not depend on stroke order. When stroke order matters, KanjiLens also checks the order and direction of your strokes against the KanjiVG reference and tells you which strokes are out of order. The whole system runs on a single machine on your local network (the school's laptop, with CPU-only inference): open it from your phone or desktop over Wi-Fi, with no cloud hosting or public domain required.

```text
┌──────────────────────────────┐
│          KanjiLens           │
│   Stroke order:              │
│   [ matters | doesn't ]      │
│   ┌──────────────────────┐   │
│   │                      │   │
│   │          日          │   │
│   │                      │   │
│   └──────────────────────┘   │
│                              │
│   [Clear]       [Recognize]  │
│                              │
│   Predictions                │
│   日  81%                    │
│   目  12%                    │
│   白   4%                    │
└──────────────────────────────┘
```

## How it works

1. You choose whether stroke order matters, then draw a kanji on the canvas (mouse or touch).
2. The frontend sends the strokes (each one a list of points, in drawing order) and the chosen mode to the API.
3. The API creates a `job_id`, queues the job, and replies right away. The HTTP request does not stay open while the model runs.
4. The inference worker picks up the job and runs the model; in the stroke-order mode it also checks the strokes against the KanjiVG reference. The model and the references are loaded once, not once per request.
5. The backend pushes each job state to the frontend over SSE (Server-Sent Events), with polling as a fallback.
6. The frontend shows the top-K predictions with their confidence and, in the stroke-order mode, which strokes are out of order. Tapping a candidate opens it in an external dictionary (Takoboto by default; the user can pick another one).

```text
 Phone / Desktop
       │
       ▼
 Angular frontend ──REST──▶ FastAPI ──▶ Queue ──▶ Worker ──▶ 2D CNN
       ▲                                  (+ stroke-order check vs KanjiVG)
       │                                                  │
       └──────────── SSE ─────────── ◀── Job results ◀────┘
```

## Tech stack

| Layer | Technologies |
|---|---|
| Frontend | Angular, TypeScript, HTML Canvas API |
| Backend | Python, FastAPI, REST, SSE |
| Machine Learning | PyTorch (training), 2D CNN; stroke-order check against KanjiVG; CPU inference runtime chosen by benchmark (PyTorch / OpenVINO / ONNX Runtime) |
| Queue | Bounded in-memory `asyncio.Queue` and one inference process (no Redis on the Windows laptop) |
| Deployment | The school's laptop (Dell Inspiron 3501, i7-1165G7, 16 GB, Windows), run directly without Docker, accessed over the LAN |

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/recognitions` | Submit the strokes and the mode (`ordered` / `unordered`) for recognition |
| `GET` | `/api/recognitions/{id}` | Get the status and result of a job (SSE fallback) |
| `GET` | `/api/recognitions/{id}/events` | Stream the job's status changes over SSE |
| `GET` | `/api/health` | Health check |

Today the `POST` accepts the drawing and queues its job. Processing ([#46](https://github.com/Asuka-Jyuku/kanji-lens/issues/46)) and reading the result ([#47](https://github.com/Asuka-Jyuku/kanji-lens/issues/47)) come next. Errors always carry a stable code ([ARCHITECTURE.md, section 5.3](docs/ARCHITECTURE.md#53-erros), pt-BR).

Example of a completed job:

```json
{
  "job_id": "abc123",
  "status": "completed",
  "stroke_order_mode": "unordered",
  "predictions": [
    { "kanji": "日", "confidence": 0.81 },
    { "kanji": "目", "confidence": 0.12 },
    { "kanji": "白", "confidence": 0.04 }
  ]
}
```

## Project structure (planned)

Clean Architecture with ports and adapters, in layers ([ADR 0004](docs/adr/0004-clean-and-hexagonal-architecture.md)), in a single repository ([ADR 0002](docs/adr/0002-monorepo-for-frontend-backend-and-ml.md)).

```text
kanji-lens/
├── frontend/                # Angular app, in layers
│   └── src/app/
│       ├── domain/          # Models and pure rules
│       ├── application/     # Use cases and ports
│       ├── infrastructure/  # HTTP and SSE adapters
│       └── presentation/    # Canvas and results view
├── backend/                 # FastAPI, ports and adapters
│   └── src/kanjilens/
│       ├── domain/          # RecognitionJob, Prediction, JobStatus, Drawing, StrokeOrderMode
│       ├── application/     # Use cases and ports
│       ├── adapters/        # Inbound (HTTP, SSE, queue consumer), outbound (recognizer, stroke-order checker, queue, store)
│       └── bootstrap/       # Composition root
├── ml/
│   ├── src/kanjilens_ml/    # Shared preprocessing, models, training, evaluation, stroke-order check
│   ├── configs/             # Versioned training configs
│   ├── notebooks/           # Exploration only
│   ├── datasets/            # Not in git
│   └── artifacts/           # Trained weights, not in git
└── docs/
```

## Roadmap

- [ ] **Machine Learning:** pick the dataset, shared preprocessing, train the 2D CNN, stroke-order check against KanjiVG, evaluate (Top-1/Top-5 and order-check accuracy), top-K inference, then benchmark on the school laptop
- [ ] **Backend:** FastAPI project, recognition endpoint, async job processing, model integration, push notifications
- [ ] **Frontend:** Angular app, stroke-order mode switch, responsive canvas with mouse and touch that captures strokes, results view
- [ ] **Infrastructure:** LAN access, CORS and firewall setup, static frontend build, load test with 3–5 students (10 clients as a stress test), CPU/memory/temperature profiling on the school laptop

See the full checklist in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#9-escopo-do-mvp).

## Open decisions

| Topic | Options | Current direction |
|---|---|---|
| Dataset | ETL8G / ETL9G | Public offline handwritten kanji images (license to be confirmed) |
| Inference runtime | PyTorch / OpenVINO / ONNX Runtime (CPU), FP32 or INT8 | Decided by benchmarks on the school laptop |
| Number of classes | A few hundred → 2,136 Jōyō kanji | Start small, then expand |

## Running locally

The app does not recognize kanji yet. For development, the commands (install, test, run the API and the frontend) are in [`CLAUDE.md`, "Comandos"](CLAUDE.md#comandos) (pt-BR). Step-by-step instructions for the school laptop and the local network will go to `docs/RUNNING.md` once the first version runs.

## What this project explores

Computer Vision, Deep Learning and CNNs, stroke matching for stroke-order checking, asynchronous processing, event-driven architecture, REST APIs, real-time communication, concurrency and job queues, and integration between a frontend and an ML model.

## License

The source code is licensed under the [MIT License](LICENSE).

The license covers the code in this repository only. Datasets used for training and trained model weights are not part of the repository and are not covered by it: each dataset keeps its own terms, and weights trained on it may inherit them. The KanjiVG stroke-order reference data shipped with the app keeps its own license (CC BY-SA 3.0, © Ulrich Apel, [kanjivg.tagaini.net](https://kanjivg.tagaini.net)), with attribution.

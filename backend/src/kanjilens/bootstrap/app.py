"""FastAPI application factory."""

from fastapi import FastAPI

from kanjilens import __version__
from kanjilens.adapters.inbound.http.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="KanjiLens", version=__version__)
    app.include_router(health_router)
    return app

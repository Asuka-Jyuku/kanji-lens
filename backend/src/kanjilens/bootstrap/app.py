"""FastAPI application factory: the composition root, the only place that wires adapters."""

from fastapi import FastAPI

from kanjilens import __version__
from kanjilens.adapters.inbound.http.body_limit import BodySizeLimitMiddleware
from kanjilens.adapters.inbound.http.errors import install_error_handlers
from kanjilens.adapters.inbound.http.health import router as health_router
from kanjilens.adapters.inbound.http.recognitions import recognitions_router
from kanjilens.adapters.outbound.clock import SystemClock
from kanjilens.adapters.outbound.jobs.in_memory_job_repository import InMemoryJobRepository
from kanjilens.adapters.outbound.queue.asyncio_job_queue import AsyncioJobQueue
from kanjilens.application.use_cases.submit_recognition import SubmitRecognition


def create_app() -> FastAPI:
    clock = SystemClock()
    repository = InMemoryJobRepository(clock)
    queue = AsyncioJobQueue()
    submit_recognition = SubmitRecognition(repository, queue, clock)

    app = FastAPI(title="KanjiLens", version=__version__)
    app.add_middleware(BodySizeLimitMiddleware)
    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(recognitions_router(submit_recognition))
    return app

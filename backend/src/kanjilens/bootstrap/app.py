"""FastAPI application factory: the composition root, the only place that wires adapters."""

import asyncio
import contextlib
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import FastAPI

from kanjilens import __version__
from kanjilens.adapters.inbound.http.body_limit import BodySizeLimitMiddleware
from kanjilens.adapters.inbound.http.errors import install_error_handlers
from kanjilens.adapters.inbound.http.recognition_events import recognition_events_router
from kanjilens.adapters.inbound.http.recognitions import recognitions_router
from kanjilens.adapters.inbound.queue.consumer import QueueConsumer
from kanjilens.adapters.outbound.inference.process import InferenceProcess
from kanjilens.adapters.outbound.jobs.in_memory_job_repository import InMemoryJobRepository
from kanjilens.adapters.outbound.notifier.in_memory_result_notifier import InMemoryResultNotifier
from kanjilens.adapters.outbound.queue.asyncio_job_queue import AsyncioJobQueue
from kanjilens.adapters.outbound.recognizer import placeholder as placeholder_recognizer
from kanjilens.adapters.outbound.recognizer.process_pool_recognizer import (
    ProcessPoolKanjiRecognizer,
    RecognizeFunction,
)
from kanjilens.adapters.outbound.stroke_order import placeholder as placeholder_evaluator
from kanjilens.adapters.outbound.stroke_order.process_pool_evaluator import (
    EvaluateFunction,
    ProcessPoolStrokeOrderEvaluator,
)
from kanjilens.application.use_cases.get_recognition import GetRecognition
from kanjilens.application.use_cases.process_recognition import ProcessRecognition
from kanjilens.application.use_cases.submit_recognition import SubmitRecognition


@dataclass(frozen=True, slots=True, kw_only=True)
class InferenceFunctions:
    """What runs in the inference process: module-level functions, which spawn imports by name.

    The initializer runs once per process; from #48 on, it loads the model and KanjiVG.
    """

    recognize: RecognizeFunction
    evaluate: EvaluateFunction
    initializer: Callable[[], None] | None = None


# Until the model (#17) and the stroke-order check (#29) exist; #48 swaps them in.
PLACEHOLDER_INFERENCE = InferenceFunctions(
    recognize=placeholder_recognizer.recognize, evaluate=placeholder_evaluator.evaluate
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_app(inference: InferenceFunctions = PLACEHOLDER_INFERENCE) -> FastAPI:
    repository = InMemoryJobRepository(utc_now)
    queue = AsyncioJobQueue()
    notifier = InMemoryResultNotifier()
    process = InferenceProcess(inference.initializer)
    submit_recognition = SubmitRecognition(repository, queue, utc_now)
    get_recognition = GetRecognition(repository)
    process_recognition = ProcessRecognition(
        repository,
        ProcessPoolKanjiRecognizer(process, inference.recognize),
        ProcessPoolStrokeOrderEvaluator(process, inference.evaluate),
        notifier,
        utc_now,
    )
    consumer = QueueConsumer(queue, process_recognition)

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # The model loads before the API answers, and a broken one stops the start (ADR 0019).
        await process.start()
        consumer_task = asyncio.create_task(consumer.run(), name="queue-consumer")
        try:
            yield
        finally:
            consumer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await consumer_task
            process.stop()

    app = FastAPI(title="KanjiLens", version=__version__, lifespan=lifespan)
    app.add_middleware(BodySizeLimitMiddleware)
    install_error_handlers(app)

    @app.get("/api/health")
    async def get_health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(recognitions_router(submit_recognition, get_recognition))
    app.include_router(recognition_events_router(get_recognition, notifier))
    return app

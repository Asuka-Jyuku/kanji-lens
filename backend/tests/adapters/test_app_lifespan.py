"""The app as Uvicorn runs it: the lifespan starts the inference process and the consumer."""

import time
from collections.abc import Callable
from concurrent.futures.process import BrokenProcessPool

import pytest
from fastapi.testclient import TestClient

import worker_functions
from kanjilens.adapters.outbound.stroke_order import placeholder as placeholder_evaluator
from kanjilens.bootstrap.app import InferenceFunctions, create_app

SLOW = InferenceFunctions(
    recognize=worker_functions.recognize_slowly, evaluate=placeholder_evaluator.evaluate
)
DRAWING = {
    "stroke_order_mode": "unordered",
    "canvas": {"width": 320, "height": 320},
    "strokes": [[[41.0, 30.5, 0], [41.2, 88.0, 140]]],
}


def timed[T](call: Callable[[], T]) -> tuple[T, float]:
    started = time.monotonic()
    response = call()
    return response, time.monotonic() - started


def test_the_api_answers_while_the_inference_process_works() -> None:
    # Every request is timed, the POST too: the TestClient lets the event loop run the consumer
    # before it returns, so a job run in the loop would block whichever request comes first.
    with TestClient(create_app(SLOW)) as client:
        posted, post_seconds = timed(lambda: client.post("/api/recognitions", json=DRAWING))
        checks = [timed(lambda: client.get("/api/health")) for _ in range(5)]

    assert posted.status_code == 202
    assert all(response.status_code == 200 for response, _ in checks)
    slowest = max(post_seconds, *(seconds for _, seconds in checks))
    assert slowest < worker_functions.SLOW_SECONDS / 2


def test_the_app_stops_without_waiting_for_the_job_in_progress() -> None:
    with TestClient(create_app(SLOW)) as client:
        for _ in range(3):
            assert client.post("/api/recognitions", json=DRAWING).status_code == 202
        started = time.monotonic()

    # Three slow jobs would take 3 x SLOW_SECONDS; the worker is terminated instead.
    assert time.monotonic() - started < worker_functions.SLOW_SECONDS * 2


def test_a_model_that_fails_to_load_stops_the_start() -> None:
    broken = InferenceFunctions(
        recognize=worker_functions.recognize_slowly,
        evaluate=placeholder_evaluator.evaluate,
        initializer=worker_functions.failing_initializer,
    )

    with pytest.raises(BrokenProcessPool), TestClient(create_app(broken)):
        pass

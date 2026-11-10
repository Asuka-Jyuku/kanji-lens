"""The inference process with a real spawned worker (ADR 0019)."""

import asyncio
import os
import time
from collections.abc import AsyncIterator
from concurrent.futures.process import BrokenProcessPool

import pytest

import worker_functions
from fakes import DRAWING
from kanjilens.adapters.outbound.inference.process import InferenceProcess
from kanjilens.domain.errors import InvalidPrediction
from kanjilens.domain.prediction import Prediction, RecognitionResult
from kanjilens.domain.stroke_order import (
    BrokenIssue,
    DirectionIssue,
    EvaluatedStrokeOrder,
    JoinedIssue,
    NotEvaluatedReason,
    NotEvaluatedStrokeOrder,
    OrderIssue,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
async def process() -> AsyncIterator[InferenceProcess]:
    inference = InferenceProcess(worker_functions.count_initializer_runs)
    await inference.start()
    yield inference
    inference.stop()


async def test_the_initializer_runs_once_in_one_process(process: InferenceProcess) -> None:
    first = await process.run(worker_functions.process_info)
    second = await process.run(worker_functions.process_info)

    pid, initializer_runs = first
    assert second == first
    assert initializer_runs == 1
    assert pid != os.getpid()


async def test_a_dead_worker_is_replaced_and_runs_the_initializer_again(
    process: InferenceProcess,
) -> None:
    pid_before, _ = await process.run(worker_functions.process_info)

    with pytest.raises(BrokenProcessPool):
        await process.run(worker_functions.crash)

    pid_after, initializer_runs = await process.run(worker_functions.process_info)
    assert pid_after != pid_before
    assert initializer_runs == 1


async def test_a_failing_initializer_stops_the_start() -> None:
    inference = InferenceProcess(worker_functions.failing_initializer)

    with pytest.raises(BrokenProcessPool):
        await inference.start()

    # Nothing is left running: a failed start cleans up after itself.
    with pytest.raises(RuntimeError):
        await inference.run(worker_functions.process_info)


async def test_stop_does_not_wait_for_the_call_in_progress(process: InferenceProcess) -> None:
    call = asyncio.ensure_future(process.run(worker_functions.sleep, 30.0))
    await asyncio.sleep(0.2)  # the worker is now sleeping
    started = time.monotonic()

    process.stop()

    assert time.monotonic() - started < 5
    call.cancel()


async def test_run_before_start_is_a_bug() -> None:
    with pytest.raises(RuntimeError):
        await InferenceProcess().run(worker_functions.process_info)


async def test_the_drawing_and_every_kind_of_result_cross_the_process_unchanged(
    process: InferenceProcess,
) -> None:
    # The recognizer and the evaluator pass domain objects to and from the worker by pickle.
    evaluated = EvaluatedStrokeOrder(
        5,
        5,
        (OrderIssue(3, 4), DirectionIssue(2), JoinedIssue(1, (1, 2)), BrokenIssue((4, 5), 5)),
    )
    not_evaluated = NotEvaluatedStrokeOrder(NotEvaluatedReason.REFERENCE_MISSING)
    result = RecognitionResult(
        (Prediction("日", 0.7, evaluated), Prediction("目", 0.2, not_evaluated))
    )

    assert await process.run(worker_functions.echo, (DRAWING, result)) == (DRAWING, result)


async def test_a_result_that_breaks_a_domain_rule_fails_the_call_and_keeps_the_worker(
    process: InferenceProcess,
) -> None:
    pid_before, _ = await process.run(worker_functions.process_info)

    with pytest.raises(InvalidPrediction):
        await process.run(worker_functions.recognize_wrongly, DRAWING)

    pid_after, _ = await process.run(worker_functions.process_info)
    assert pid_after == pid_before

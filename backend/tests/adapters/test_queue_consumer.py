"""The whole path of a job, with the real queue, repository, consumer and spawned worker (ADR 0019).

Only the functions in the worker are placeholders or test functions; everything else is what
the API runs.
"""

import asyncio
import itertools
import time
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass

import pytest

import worker_functions
from kanjilens.adapters.inbound.queue.consumer import QueueConsumer
from kanjilens.adapters.outbound.clock import SystemClock
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
    ProcessPoolStrokeOrderEvaluator,
)
from kanjilens.application.use_cases.process_recognition import ProcessRecognition
from kanjilens.application.use_cases.submit_recognition import SubmitRecognition
from kanjilens.domain.drawing import CanvasSize, Drawing, Point, Stroke
from kanjilens.domain.job import JobFailure, JobStatus, RecognitionJob
from kanjilens.domain.stroke_order import EvaluatedStrokeOrder, StrokeOrderMode

pytestmark = pytest.mark.anyio

TIMEOUT_SECONDS = 20


def drawing(strokes: int) -> Drawing:
    return Drawing(
        CanvasSize(320, 320),
        tuple(
            Stroke((Point(10.0, 10.0 * i, 2 * i), Point(50.0, 10.0 * i, 2 * i + 1)))
            for i in range(strokes)
        ),
    )


@dataclass
class Backend:
    submit: SubmitRecognition
    repository: InMemoryJobRepository

    async def wait_until_final(self, jobs: Iterable[RecognitionJob]) -> list[RecognitionJob]:
        ids = [job.id for job in jobs]
        async with asyncio.timeout(TIMEOUT_SECONDS):
            while True:
                stored = [self.repository.get(job_id) for job_id in ids]
                if all(job is not None and job.status.is_final for job in stored):
                    return [job for job in stored if job is not None]
                await asyncio.sleep(0.02)


async def start_backend(recognize: RecognizeFunction) -> AsyncIterator[Backend]:
    clock = SystemClock()
    repository = InMemoryJobRepository(clock)
    queue = AsyncioJobQueue()
    process = InferenceProcess()
    await process.start()
    process_recognition = ProcessRecognition(
        repository,
        ProcessPoolKanjiRecognizer(process, recognize),
        ProcessPoolStrokeOrderEvaluator(process, placeholder_evaluator.evaluate),
        InMemoryResultNotifier(),
        clock,
    )
    consumer = asyncio.create_task(QueueConsumer(queue, process_recognition).run())
    try:
        yield Backend(SubmitRecognition(repository, queue, clock), repository)
    finally:
        consumer.cancel()
        process.stop()


@pytest.fixture
async def backend() -> AsyncIterator[Backend]:
    async for running in start_backend(placeholder_recognizer.recognize):
        yield running


@pytest.fixture
async def slow_backend() -> AsyncIterator[Backend]:
    async for running in start_backend(worker_functions.recognize_slowly):
        yield running


@pytest.fixture
async def crashing_backend() -> AsyncIterator[Backend]:
    async for running in start_backend(worker_functions.recognize_or_crash):
        yield running


async def test_n_jobs_in_n_jobs_completed_one_at_a_time(backend: Backend) -> None:
    modes = itertools.islice(itertools.cycle(StrokeOrderMode), 6)
    jobs = [backend.submit.execute(mode, drawing(2)) for mode in modes]

    done = await backend.wait_until_final(jobs)

    assert [job.status for job in done] == [JobStatus.COMPLETED] * 6
    # One inference at a time (ADR 0011): each job starts after the previous one finished.
    by_start = sorted(done, key=lambda job: job.started_at or job.created_at)
    for previous, current in itertools.pairwise(by_start):
        assert previous.finished_at is not None and current.started_at is not None
        assert current.started_at >= previous.finished_at


async def test_only_ordered_jobs_carry_the_stroke_order(backend: Backend) -> None:
    ordered = backend.submit.execute(StrokeOrderMode.ORDERED, drawing(2))
    unordered = backend.submit.execute(StrokeOrderMode.UNORDERED, drawing(2))

    ordered_done, unordered_done = await backend.wait_until_final([ordered, unordered])

    assert ordered_done.result is not None and unordered_done.result is not None
    assert all(
        isinstance(p.stroke_order, EvaluatedStrokeOrder) for p in ordered_done.result.predictions
    )
    assert all(p.stroke_order is None for p in unordered_done.result.predictions)


async def test_a_crash_fails_its_job_and_the_next_job_still_completes(
    crashing_backend: Backend,
) -> None:
    crashed = crashing_backend.submit.execute(
        StrokeOrderMode.UNORDERED, drawing(worker_functions.CRASH_STROKES)
    )
    after = crashing_backend.submit.execute(StrokeOrderMode.UNORDERED, drawing(1))

    crashed_done, after_done = await crashing_backend.wait_until_final([crashed, after])

    assert crashed_done.status is JobStatus.FAILED
    assert crashed_done.failure is JobFailure.INFERENCE_FAILED
    assert after_done.status is JobStatus.COMPLETED


async def test_the_event_loop_keeps_answering_while_a_job_is_processing(
    slow_backend: Backend,
) -> None:
    job = slow_backend.submit.execute(StrokeOrderMode.UNORDERED, drawing(1))
    gaps: list[float] = []
    saw_processing = False

    # Tick every 10 ms until the job ends; a blocked loop would show a gap as long as the job.
    last = time.monotonic()
    async with asyncio.timeout(TIMEOUT_SECONDS):
        while not (current := slow_backend.repository.get(job.id)) or not current.status.is_final:
            saw_processing |= current is not None and current.status is JobStatus.PROCESSING
            await asyncio.sleep(0.01)
            now = time.monotonic()
            gaps.append(now - last)
            last = now

    assert saw_processing
    assert sum(gaps) >= worker_functions.SLOW_SECONDS
    assert max(gaps) < worker_functions.SLOW_SECONDS / 2

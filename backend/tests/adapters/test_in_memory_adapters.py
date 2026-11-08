from datetime import timedelta

import pytest

from fakes import DRAWING, T0, FakeClock
from kanjilens.adapters.outbound.clock import SystemClock
from kanjilens.adapters.outbound.jobs.in_memory_job_repository import InMemoryJobRepository
from kanjilens.adapters.outbound.queue.asyncio_job_queue import QUEUE_SIZE, AsyncioJobQueue
from kanjilens.domain.errors import QueueFull
from kanjilens.domain.job import RESULT_TTL, JobFailure, RecognitionJob
from kanjilens.domain.prediction import Prediction, RecognitionResult
from kanjilens.domain.stroke_order import StrokeOrderMode


def submitted(clock: FakeClock) -> RecognitionJob:
    return RecognitionJob.submit(mode=StrokeOrderMode.UNORDERED, drawing=DRAWING, now=clock.now())


def finished(clock: FakeClock) -> RecognitionJob:
    job = submitted(clock).start(clock.now())
    return job.complete(RecognitionResult((Prediction("日", 0.9),)), clock.now())


# --- queue -------------------------------------------------------------------------------


def test_the_queue_holds_16_jobs_and_refuses_the_17th() -> None:
    queue = AsyncioJobQueue()
    for i in range(QUEUE_SIZE):
        queue.enqueue(f"job-{i}")

    with pytest.raises(QueueFull):
        queue.enqueue("one-too-many")
    assert QUEUE_SIZE == 16
    assert len(queue) == 16


# --- repository --------------------------------------------------------------------------


def test_the_repository_stores_and_replaces_jobs() -> None:
    clock = FakeClock()
    repository = InMemoryJobRepository(clock)
    job = submitted(clock)

    repository.save(job)
    started = job.start(clock.now())
    repository.save(started)

    assert repository.get(job.id) == started
    assert len(repository) == 1


def test_an_unknown_or_deleted_job_is_none() -> None:
    clock = FakeClock()
    repository = InMemoryJobRepository(clock)
    job = submitted(clock)
    repository.save(job)

    repository.delete(job.id)
    repository.delete("never-existed")

    assert repository.get(job.id) is None
    assert repository.get("never-existed") is None


def test_a_finished_job_and_its_drawing_disappear_after_the_ttl() -> None:
    clock = FakeClock()
    repository = InMemoryJobRepository(clock)
    job = finished(clock)
    repository.save(job)

    clock.advance(RESULT_TTL - timedelta(seconds=1))
    assert repository.get(job.id) == job

    clock.advance(timedelta(seconds=1))
    assert repository.get(job.id) is None
    assert len(repository) == 0


def test_expired_jobs_are_dropped_even_if_nobody_asks_for_them() -> None:
    clock = FakeClock()
    repository = InMemoryJobRepository(clock)
    old = finished(clock)
    repository.save(old)

    clock.advance(RESULT_TTL)
    repository.save(submitted(clock))

    assert old.id not in {job_id for job_id in repository._jobs}


def test_a_failed_job_expires_too() -> None:
    clock = FakeClock()
    repository = InMemoryJobRepository(clock)
    job = submitted(clock).start(T0).fail(JobFailure.INFERENCE_FAILED, T0)
    repository.save(job)

    clock.advance(RESULT_TTL)

    assert repository.get(job.id) is None


def test_a_waiting_job_never_expires() -> None:
    clock = FakeClock()
    repository = InMemoryJobRepository(clock)
    job = submitted(clock)
    repository.save(job)

    clock.advance(timedelta(hours=1))

    assert repository.get(job.id) == job


def test_the_system_clock_is_timezone_aware() -> None:
    assert SystemClock().now().utcoffset() == timedelta(0)

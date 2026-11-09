import pytest

from fakes import DRAWING, T0, FakeClock, FakeJobQueue, FakeJobRepository
from kanjilens.application.use_cases.submit_recognition import SubmitRecognition
from kanjilens.domain.errors import QueueFull
from kanjilens.domain.job import JobStatus
from kanjilens.domain.stroke_order import StrokeOrderMode


def make(capacity: int = 16) -> tuple[SubmitRecognition, FakeJobRepository, FakeJobQueue]:
    repository, queue = FakeJobRepository(), FakeJobQueue(capacity)
    return SubmitRecognition(repository, queue, FakeClock()), repository, queue


def test_a_submitted_drawing_becomes_a_stored_queued_job() -> None:
    submit, repository, queue = make()

    job = submit.execute(StrokeOrderMode.ORDERED, DRAWING)

    assert job.status is JobStatus.QUEUED
    assert job.mode is StrokeOrderMode.ORDERED
    assert job.drawing == DRAWING
    assert job.created_at == T0
    assert repository.get(job.id) == job
    assert queue.job_ids == [job.id]


def test_jobs_enter_the_queue_in_order() -> None:
    submit, _, queue = make()

    first = submit.execute(StrokeOrderMode.UNORDERED, DRAWING)
    second = submit.execute(StrokeOrderMode.UNORDERED, DRAWING)

    assert queue.job_ids == [first.id, second.id]


def test_a_full_queue_refuses_the_job_and_keeps_nothing() -> None:
    submit, repository, queue = make(capacity=1)
    kept = submit.execute(StrokeOrderMode.UNORDERED, DRAWING)

    with pytest.raises(QueueFull):
        submit.execute(StrokeOrderMode.UNORDERED, DRAWING)

    assert list(repository.jobs) == [kept.id]
    assert queue.job_ids == [kept.id]

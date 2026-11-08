"""Fakes of the application ports, for use case and adapter tests (CLAUDE.md, "Testes")."""

from datetime import UTC, datetime, timedelta

from kanjilens.domain.drawing import CanvasSize, Drawing, Point, Stroke
from kanjilens.domain.errors import QueueFull
from kanjilens.domain.job import RecognitionJob

T0 = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
DRAWING = Drawing(CanvasSize(320, 320), (Stroke((Point(1.0, 1.0, 0), Point(2.0, 2.0, 10))),))


class FakeClock:
    def __init__(self, now: datetime = T0) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


class FakeJobQueue:
    def __init__(self, capacity: int = 16) -> None:
        self.capacity = capacity
        self.job_ids: list[str] = []

    def enqueue(self, job_id: str) -> None:
        if len(self.job_ids) >= self.capacity:
            raise QueueFull("fake queue is full")
        self.job_ids.append(job_id)


class FakeJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, RecognitionJob] = {}

    def save(self, job: RecognitionJob) -> None:
        self.jobs[job.id] = job

    def get(self, job_id: str) -> RecognitionJob | None:
        return self.jobs.get(job_id)

    def delete(self, job_id: str) -> None:
        self.jobs.pop(job_id, None)

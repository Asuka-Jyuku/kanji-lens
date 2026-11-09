"""Fakes of the application ports, for use case and adapter tests (CLAUDE.md, "Testes")."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from kanjilens.domain.drawing import CanvasSize, Drawing, Point, Stroke
from kanjilens.domain.errors import QueueFull
from kanjilens.domain.job import RecognitionJob
from kanjilens.domain.prediction import Prediction, RecognitionResult
from kanjilens.domain.stroke_order import (
    EvaluatedStrokeOrder,
    NotEvaluatedReason,
    NotEvaluatedStrokeOrder,
    OrderIssue,
    StrokeOrderEvaluation,
)

T0 = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
DRAWING = Drawing(CanvasSize(320, 320), (Stroke((Point(1.0, 1.0, 0), Point(2.0, 2.0, 10))),))
RESULT = RecognitionResult((Prediction("日", 0.7), Prediction("目", 0.2)))
EVALUATIONS: tuple[StrokeOrderEvaluation, ...] = (
    EvaluatedStrokeOrder(2, 1, (OrderIssue(1, 2),)),
    NotEvaluatedStrokeOrder(NotEvaluatedReason.STROKE_COUNT_MISMATCH),
)


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
    """on_get runs at the start of each get, to change the job in the middle of a use case."""

    def __init__(self) -> None:
        self.jobs: dict[str, RecognitionJob] = {}
        self.on_get: Callable[[str], None] | None = None

    def save(self, job: RecognitionJob) -> None:
        self.jobs[job.id] = job

    def get(self, job_id: str) -> RecognitionJob | None:
        if self.on_get is not None:
            on_get, self.on_get = self.on_get, None  # once
            on_get(job_id)
        return self.jobs.get(job_id)

    def delete(self, job_id: str) -> None:
        self.jobs.pop(job_id, None)


class FakeKanjiRecognizer:
    """Answers with the result, or raises the error. on_call runs during the call, to look at
    the job while it is processing."""

    def __init__(
        self,
        result: RecognitionResult = RESULT,
        error: Exception | None = None,
        on_call: Callable[[], None] | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.on_call = on_call
        self.drawings: list[Drawing] = []

    async def recognize(self, drawing: Drawing) -> RecognitionResult:
        self.drawings.append(drawing)
        if self.on_call is not None:
            self.on_call()
        if self.error is not None:
            raise self.error
        return self.result


class FakeStrokeOrderEvaluator:
    def __init__(
        self,
        evaluations: tuple[StrokeOrderEvaluation, ...] = EVALUATIONS,
        error: Exception | None = None,
    ) -> None:
        self.evaluations = evaluations
        self.error = error
        self.calls: list[tuple[Drawing, tuple[str, ...]]] = []

    async def evaluate(
        self, drawing: Drawing, candidates: tuple[str, ...]
    ) -> tuple[StrokeOrderEvaluation, ...]:
        self.calls.append((drawing, candidates))
        if self.error is not None:
            raise self.error
        return self.evaluations


class FakeResultNotifier:
    """Records each notified job; on_notify runs during the call, to look at the repository."""

    def __init__(self, on_notify: Callable[[RecognitionJob], None] | None = None) -> None:
        self.jobs: list[RecognitionJob] = []
        self.on_notify = on_notify

    def notify(self, job: RecognitionJob) -> None:
        if self.on_notify is not None:
            self.on_notify(job)
        self.jobs.append(job)

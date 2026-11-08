"""The recognition job and its status lifecycle (ADRs 0005 and 0019).

queued -> processing -> completed | failed. A job is immutable: each transition returns a new
job, and any other transition raises InvalidJobTransition. Times are passed in (the domain has
no clock) and must be timezone-aware.
"""

import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

from kanjilens.domain.drawing import Drawing
from kanjilens.domain.errors import InvalidJobTransition
from kanjilens.domain.prediction import RecognitionResult
from kanjilens.domain.stroke_order import StrokeOrderMode

# Initial value from ADR 0019: results (and the drawing with them) expire after this.
RESULT_TTL = timedelta(minutes=5)


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def is_final(self) -> bool:
        return self in (JobStatus.COMPLETED, JobStatus.FAILED)


class JobFailure(StrEnum):
    """Why a job failed; a stable code the frontend translates (ADR 0009)."""

    INFERENCE_FAILED = "inference_failed"


def new_job_id() -> str:
    return uuid.uuid4().hex


@dataclass(frozen=True, slots=True, kw_only=True)
class RecognitionJob:
    id: str
    mode: StrokeOrderMode
    drawing: Drawing
    created_at: datetime
    status: JobStatus = JobStatus.QUEUED
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: RecognitionResult | None = None
    failure: JobFailure | None = None

    @classmethod
    def submit(
        cls, *, mode: StrokeOrderMode, drawing: Drawing, now: datetime, job_id: str | None = None
    ) -> RecognitionJob:
        _check_aware(now)
        return cls(id=job_id or new_job_id(), mode=mode, drawing=drawing, created_at=now)

    def start(self, now: datetime) -> RecognitionJob:
        self._require(JobStatus.QUEUED, to=JobStatus.PROCESSING)
        _check_aware(now)
        return replace(self, status=JobStatus.PROCESSING, started_at=now)

    def complete(self, result: RecognitionResult, now: datetime) -> RecognitionJob:
        self._require(JobStatus.PROCESSING, to=JobStatus.COMPLETED)
        _check_aware(now)
        result.check_mode(self.mode)
        return replace(self, status=JobStatus.COMPLETED, finished_at=now, result=result)

    def fail(self, failure: JobFailure, now: datetime) -> RecognitionJob:
        self._require(JobStatus.PROCESSING, to=JobStatus.FAILED)
        _check_aware(now)
        return replace(self, status=JobStatus.FAILED, finished_at=now, failure=failure)

    def is_expired(self, now: datetime, ttl: timedelta = RESULT_TTL) -> bool:
        """Only finished jobs expire; a queued or processing job is still awaited."""
        return self.finished_at is not None and now - self.finished_at >= ttl

    def _require(self, expected: JobStatus, *, to: JobStatus) -> None:
        if self.status is not expected:
            raise InvalidJobTransition(f"job {self.id}: {self.status} -> {to} is not allowed")


def _check_aware(now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("job times must be timezone-aware")

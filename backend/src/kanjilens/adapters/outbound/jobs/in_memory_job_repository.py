"""Jobs kept in the memory of the API process until they expire (ADR 0019).

Expired jobs are dropped, with their drawing, whenever the repository is used, so a drawing
never outlives its result (CLAUDE.md, "Segurança").
"""

from datetime import timedelta

from kanjilens.application.ports.clock import Clock
from kanjilens.domain.job import RESULT_TTL, RecognitionJob


class InMemoryJobRepository:
    def __init__(self, clock: Clock, ttl: timedelta = RESULT_TTL) -> None:
        self._clock = clock
        self._ttl = ttl
        self._jobs: dict[str, RecognitionJob] = {}

    def save(self, job: RecognitionJob) -> None:
        self._drop_expired()
        self._jobs[job.id] = job

    def get(self, job_id: str) -> RecognitionJob | None:
        self._drop_expired()
        return self._jobs.get(job_id)

    def delete(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    def __len__(self) -> int:
        self._drop_expired()
        return len(self._jobs)

    def _drop_expired(self) -> None:
        now = self._clock.now()
        expired = [job.id for job in self._jobs.values() if job.is_expired(now, self._ttl)]
        for job_id in expired:
            del self._jobs[job_id]

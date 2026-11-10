"""Jobs kept in the memory of the API process until they expire (ADR 0019).

Expired jobs are dropped, with their drawing, whenever the repository is used, so a drawing
never outlives its result (docs/SECURITY.md, "Dados dos alunos").
"""

from collections.abc import Callable
from datetime import datetime, timedelta

from kanjilens.domain.job import RESULT_TTL, RecognitionJob


class InMemoryJobRepository:
    def __init__(self, now: Callable[[], datetime], ttl: timedelta = RESULT_TTL) -> None:
        self._now = now
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
        now = self._now()
        expired = [job.id for job in self._jobs.values() if job.is_expired(now, self._ttl)]
        for job_id in expired:
            del self._jobs[job_id]

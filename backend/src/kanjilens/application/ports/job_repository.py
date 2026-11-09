"""Where jobs live until their result expires (ADR 0019)."""

from typing import Protocol

from kanjilens.domain.job import RecognitionJob


class JobRepository(Protocol):
    def save(self, job: RecognitionJob) -> None:
        """Store the job, replacing an earlier version with the same id."""
        ...

    def get(self, job_id: str) -> RecognitionJob | None:
        """The job, or None if it does not exist or has expired."""
        ...

    def delete(self, job_id: str) -> None:
        """Forget the job and its drawing; nothing happens if it does not exist."""
        ...

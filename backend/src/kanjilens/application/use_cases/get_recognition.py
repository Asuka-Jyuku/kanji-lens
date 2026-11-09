"""The current state of a job, for the GET (polling) and the SSE stream alike (ADR 0020)."""

from kanjilens.application.ports.job_repository import JobRepository
from kanjilens.domain.errors import JobNotFound
from kanjilens.domain.job import RecognitionJob


class GetRecognition:
    def __init__(self, repository: JobRepository) -> None:
        self._repository = repository

    def execute(self, job_id: str) -> RecognitionJob:
        """Raises JobNotFound when the job does not exist or has expired."""
        job = self._repository.get(job_id)
        if job is None:
            raise JobNotFound(f"job {job_id} does not exist or has expired")
        return job

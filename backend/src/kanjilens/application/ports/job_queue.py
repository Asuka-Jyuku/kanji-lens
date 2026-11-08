"""The queue of jobs waiting for the inference process (ADR 0019)."""

from typing import Protocol


class JobQueue(Protocol):
    def enqueue(self, job_id: str) -> None:
        """Add a job at the end of the queue; raise QueueFull when the queue is at its limit."""
        ...

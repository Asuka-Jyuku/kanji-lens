"""Tells whoever is watching a job that its state changed (ADR 0020)."""

from typing import Protocol

from kanjilens.domain.job import RecognitionJob


class ResultNotifier(Protocol):
    def notify(self, job: RecognitionJob) -> None:
        """Hand the job's new state to its watchers, if any; never waits for them."""
        ...

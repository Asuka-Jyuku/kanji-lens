"""Takes the queued jobs one at a time and runs each to its end (ADR 0019).

It runs as a task of the API's event loop, started and cancelled by the lifespan in bootstrap/.
The next job is only taken when the current one is over: one inference at a time (ADR 0011).
"""

import logging
from typing import Protocol

from kanjilens.application.use_cases.process_recognition import ProcessRecognition

_log = logging.getLogger(__name__)


class JobSource(Protocol):
    """The consumer's side of the job queue; the use cases only enqueue (JobQueue)."""

    async def take(self) -> str:
        """The next job id, waiting while there is none."""
        ...


class QueueConsumer:
    def __init__(self, source: JobSource, process_recognition: ProcessRecognition) -> None:
        self._source = source
        self._process_recognition = process_recognition

    async def run(self) -> None:
        """Until cancelled, when the API stops."""
        while True:
            job_id = await self._source.take()
            try:
                await self._process_recognition.execute(job_id)
            except Exception:
                # One bad job must not stop the consumer: the next ones would wait forever.
                _log.exception("job %s could not be processed", job_id)

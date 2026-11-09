"""Accept a drawing: create a queued job, store it and put it in the queue (ADRs 0005 and 0019)."""

from kanjilens.application.ports.clock import Clock
from kanjilens.application.ports.job_queue import JobQueue
from kanjilens.application.ports.job_repository import JobRepository
from kanjilens.domain.drawing import Drawing
from kanjilens.domain.errors import QueueFull
from kanjilens.domain.job import RecognitionJob
from kanjilens.domain.stroke_order import StrokeOrderMode


class SubmitRecognition:
    def __init__(self, repository: JobRepository, queue: JobQueue, clock: Clock) -> None:
        self._repository = repository
        self._queue = queue
        self._clock = clock

    def execute(self, mode: StrokeOrderMode, drawing: Drawing) -> RecognitionJob:
        """The drawing is already valid: the domain checks it when it is built.

        Raises QueueFull, and then the job is not kept.
        """
        job = RecognitionJob.submit(mode=mode, drawing=drawing, now=self._clock.now())
        # Stored first, so the consumer always finds the job it takes from the queue.
        self._repository.save(job)
        try:
            self._queue.enqueue(job.id)
        except QueueFull:
            self._repository.delete(job.id)
            raise
        return job

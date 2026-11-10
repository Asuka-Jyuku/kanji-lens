"""Run one queued job to its final status (ADRs 0012, 0019 and 0020).

queued -> processing -> completed, or failed when the recognizer or the stroke-order evaluator
fails. Unordered jobs never call the evaluator; ordered jobs evaluate every candidate. Every
new state is stored first and then handed to the ResultNotifier, so a watcher that reads the
repository never sees an older state than the one it was told about.
"""

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from kanjilens.application.ports.job_repository import JobRepository
from kanjilens.application.ports.kanji_recognizer import KanjiRecognizer
from kanjilens.application.ports.result_notifier import ResultNotifier
from kanjilens.application.ports.stroke_order_evaluator import StrokeOrderEvaluator
from kanjilens.domain.job import JobFailure, RecognitionJob
from kanjilens.domain.prediction import RecognitionResult
from kanjilens.domain.stroke_order import StrokeOrderMode

_log = logging.getLogger(__name__)


class ProcessRecognition:
    def __init__(
        self,
        repository: JobRepository,
        recognizer: KanjiRecognizer,
        evaluator: StrokeOrderEvaluator,
        notifier: ResultNotifier,
        now: Callable[[], datetime],
    ) -> None:
        self._repository = repository
        self._recognizer = recognizer
        self._evaluator = evaluator
        self._notifier = notifier
        self._now = now

    async def execute(self, job_id: str) -> RecognitionJob | None:
        """The job in its final status, or None when the job is no longer stored."""
        job = self._repository.get(job_id)
        if job is None:
            _log.warning("job %s left the queue but is no longer stored", job_id)
            return None
        job = job.start(self._now())
        self._publish(job)
        try:
            result = await self._recognize(job)
            job = job.complete(result, self._now())
        except Exception:
            # Any failure ends the job: a job left in processing would be awaited forever.
            # A crash of the inference process (BrokenProcessPool) lands here too (ADR 0019).
            _log.exception("job %s failed", job.id)
            job = job.fail(JobFailure.INFERENCE_FAILED, self._now())
        self._publish(job)
        return job

    def _publish(self, job: RecognitionJob) -> None:
        self._repository.save(job)
        self._notifier.notify(job)

    async def _recognize(self, job: RecognitionJob) -> RecognitionResult:
        result = await self._recognizer.recognize(job.drawing)
        if job.mode is StrokeOrderMode.UNORDERED:
            return result
        candidates = tuple(prediction.kanji for prediction in result.predictions)
        evaluations = await self._evaluator.evaluate(job.drawing, candidates)
        # strict: an evaluator that skips a candidate is a bug, and the job fails.
        return RecognitionResult(
            tuple(
                replace(prediction, stroke_order=evaluation)
                for prediction, evaluation in zip(result.predictions, evaluations, strict=True)
            )
        )

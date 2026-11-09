from datetime import timedelta

import pytest

from fakes import (
    DRAWING,
    EVALUATIONS,
    RESULT,
    T0,
    FakeClock,
    FakeJobRepository,
    FakeKanjiRecognizer,
    FakeResultNotifier,
    FakeStrokeOrderEvaluator,
)
from kanjilens.application.use_cases.process_recognition import ProcessRecognition
from kanjilens.domain.job import JobFailure, JobStatus, RecognitionJob
from kanjilens.domain.stroke_order import StrokeOrderMode

pytestmark = pytest.mark.anyio


def make(
    mode: StrokeOrderMode = StrokeOrderMode.UNORDERED,
    recognizer: FakeKanjiRecognizer | None = None,
    evaluator: FakeStrokeOrderEvaluator | None = None,
    notifier: FakeResultNotifier | None = None,
) -> tuple[ProcessRecognition, FakeJobRepository, FakeStrokeOrderEvaluator, RecognitionJob]:
    repository = FakeJobRepository()
    evaluator = evaluator or FakeStrokeOrderEvaluator()
    job = RecognitionJob.submit(mode=mode, drawing=DRAWING, now=T0)
    repository.save(job)
    clock = FakeClock(T0 + timedelta(seconds=1))
    process = ProcessRecognition(
        repository,
        recognizer or FakeKanjiRecognizer(),
        evaluator,
        notifier or FakeResultNotifier(),
        clock,
    )
    return process, repository, evaluator, job


async def test_an_unordered_job_completes_with_the_candidates_and_no_evaluation() -> None:
    process, repository, evaluator, job = make(StrokeOrderMode.UNORDERED)

    done = await process.execute(job.id)

    assert done is not None
    assert done.status is JobStatus.COMPLETED
    assert done.result == RESULT
    assert done.started_at == done.finished_at == T0 + timedelta(seconds=1)
    assert repository.get(job.id) == done
    assert evaluator.calls == []


async def test_an_ordered_job_evaluates_every_candidate_in_order() -> None:
    process, _, evaluator, job = make(StrokeOrderMode.ORDERED)

    done = await process.execute(job.id)

    assert done is not None and done.result is not None
    assert done.status is JobStatus.COMPLETED
    assert evaluator.calls == [(DRAWING, ("日", "目"))]
    assert [p.kanji for p in done.result.predictions] == ["日", "目"]
    assert [p.confidence for p in done.result.predictions] == [0.7, 0.2]
    assert tuple(p.stroke_order for p in done.result.predictions) == EVALUATIONS


async def test_the_stored_job_is_processing_while_the_recognizer_runs() -> None:
    seen: list[JobStatus] = []
    recognizer = FakeKanjiRecognizer()
    process, repository, _, job = make(recognizer=recognizer)
    recognizer.on_call = lambda: seen.append(repository.jobs[job.id].status)

    await process.execute(job.id)

    assert seen == [JobStatus.PROCESSING]


@pytest.mark.parametrize(
    ("mode", "recognizer", "evaluator"),
    [
        pytest.param(
            StrokeOrderMode.UNORDERED,
            FakeKanjiRecognizer(error=RuntimeError("model crashed")),
            None,
            id="recognizer-raises",
        ),
        pytest.param(
            StrokeOrderMode.ORDERED,
            None,
            FakeStrokeOrderEvaluator(error=RuntimeError("evaluator crashed")),
            id="evaluator-raises",
        ),
        pytest.param(
            StrokeOrderMode.ORDERED,
            None,
            FakeStrokeOrderEvaluator(evaluations=EVALUATIONS[:1]),
            id="evaluator-skips-a-candidate",
        ),
    ],
)
async def test_a_failure_in_the_inference_fails_the_job(
    mode: StrokeOrderMode,
    recognizer: FakeKanjiRecognizer | None,
    evaluator: FakeStrokeOrderEvaluator | None,
) -> None:
    process, repository, _, job = make(mode, recognizer, evaluator)

    done = await process.execute(job.id)

    assert done is not None
    assert done.status is JobStatus.FAILED
    assert done.failure is JobFailure.INFERENCE_FAILED
    assert done.result is None
    assert repository.get(job.id) == done


async def test_a_job_no_longer_stored_is_skipped() -> None:
    process, repository, _, job = make()
    repository.delete(job.id)

    assert await process.execute(job.id) is None
    assert repository.jobs == {}


async def test_every_new_state_is_stored_and_then_notified() -> None:
    stored_when_notified: list[bool] = []
    notifier = FakeResultNotifier()
    process, repository, _, job = make(notifier=notifier)
    notifier.on_notify = lambda changed: stored_when_notified.append(
        repository.jobs[changed.id] == changed
    )

    done = await process.execute(job.id)

    assert [j.status for j in notifier.jobs] == [JobStatus.PROCESSING, JobStatus.COMPLETED]
    assert notifier.jobs[-1] == done
    assert stored_when_notified == [True, True]


async def test_a_failed_job_is_notified_too() -> None:
    notifier = FakeResultNotifier()
    process, _, _, job = make(
        recognizer=FakeKanjiRecognizer(error=RuntimeError("boom")), notifier=notifier
    )

    await process.execute(job.id)

    assert [j.status for j in notifier.jobs] == [JobStatus.PROCESSING, JobStatus.FAILED]

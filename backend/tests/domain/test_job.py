import pickle
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from kanjilens.domain.drawing import CanvasSize, Drawing, Point, Stroke
from kanjilens.domain.errors import InvalidJobTransition, InvalidPrediction
from kanjilens.domain.job import RESULT_TTL, JobFailure, JobStatus, RecognitionJob
from kanjilens.domain.prediction import Prediction, RecognitionResult
from kanjilens.domain.stroke_order import (
    EvaluatedStrokeOrder,
    JoinedIssue,
    OrderIssue,
    StrokeOrderMode,
)

T0 = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
DRAWING = Drawing(CanvasSize(320, 320), (Stroke((Point(1.0, 1.0, 0), Point(2.0, 2.0, 10))),))
RESULT = RecognitionResult((Prediction("日", 0.81), Prediction("目", 0.12)))


def queued(mode: StrokeOrderMode = StrokeOrderMode.UNORDERED) -> RecognitionJob:
    return RecognitionJob.submit(mode=mode, drawing=DRAWING, now=T0)


def processing() -> RecognitionJob:
    return queued().start(T0 + timedelta(seconds=1))


def completed() -> RecognitionJob:
    return processing().complete(RESULT, T0 + timedelta(seconds=2))


def failed() -> RecognitionJob:
    return processing().fail(JobFailure.INFERENCE_FAILED, T0 + timedelta(seconds=2))


def test_a_submitted_job_is_queued_with_a_new_id() -> None:
    first, second = queued(), queued()

    assert first.status is JobStatus.QUEUED
    assert first.created_at == T0
    assert first.id != second.id
    assert first.result is None and first.finished_at is None


def test_the_id_can_be_given() -> None:
    job = RecognitionJob.submit(
        mode=StrokeOrderMode.ORDERED, drawing=DRAWING, now=T0, job_id="abc123"
    )

    assert job.id == "abc123"


def test_the_happy_path_records_each_time() -> None:
    job = completed()

    assert job.status is JobStatus.COMPLETED
    assert job.started_at == T0 + timedelta(seconds=1)
    assert job.finished_at == T0 + timedelta(seconds=2)
    assert job.result == RESULT


def test_a_failed_job_keeps_the_failure_code() -> None:
    job = failed()

    assert job.status is JobStatus.FAILED
    assert job.failure is JobFailure.INFERENCE_FAILED
    assert job.failure.value == "inference_failed"
    assert job.result is None


def test_transitions_return_a_new_job() -> None:
    job = queued()

    job.start(T0)

    assert job.status is JobStatus.QUEUED


@pytest.mark.parametrize("status", list(JobStatus))
def test_status_values_and_final_states(status: JobStatus) -> None:
    assert status.is_final == (status in (JobStatus.COMPLETED, JobStatus.FAILED))
    assert status.value in ("queued", "processing", "completed", "failed")


# --- forbidden transitions ---------------------------------------------------------------


def start(job: RecognitionJob) -> RecognitionJob:
    return job.start(T0)


def complete(job: RecognitionJob) -> RecognitionJob:
    return job.complete(RESULT, T0)


def fail(job: RecognitionJob) -> RecognitionJob:
    return job.fail(JobFailure.INFERENCE_FAILED, T0)


@pytest.mark.parametrize(
    ("job", "transition"),
    [
        pytest.param(queued, complete, id="queued->completed"),
        pytest.param(queued, fail, id="queued->failed"),
        pytest.param(processing, start, id="processing->processing"),
        pytest.param(completed, start, id="completed->processing"),
        pytest.param(completed, complete, id="completed->completed"),
        pytest.param(completed, fail, id="completed->failed"),
        pytest.param(failed, start, id="failed->processing"),
        pytest.param(failed, complete, id="failed->completed"),
        pytest.param(failed, fail, id="failed->failed"),
    ],
)
def test_forbidden_transitions_are_refused(
    job: Callable[[], RecognitionJob],
    transition: Callable[[RecognitionJob], RecognitionJob],
) -> None:
    with pytest.raises(InvalidJobTransition):
        transition(job())


def test_a_result_must_match_the_job_mode() -> None:
    ordered = queued(StrokeOrderMode.ORDERED).start(T0)

    with pytest.raises(InvalidPrediction):
        ordered.complete(RESULT, T0)


def test_times_must_be_timezone_aware() -> None:
    naive = datetime(2026, 11, 8, 12, 0)

    with pytest.raises(ValueError, match="timezone-aware"):
        RecognitionJob.submit(mode=StrokeOrderMode.UNORDERED, drawing=DRAWING, now=naive)
    with pytest.raises(ValueError, match="timezone-aware"):
        queued().start(naive)


# --- expiration (ADR 0019) ---------------------------------------------------------------


def test_the_result_lives_five_minutes() -> None:
    assert timedelta(minutes=5) == RESULT_TTL


@pytest.mark.parametrize("job", [completed, failed])
def test_a_finished_job_expires_after_the_ttl(job: Callable[[], RecognitionJob]) -> None:
    finished = job()
    assert finished.finished_at is not None

    assert not finished.is_expired(finished.finished_at + RESULT_TTL - timedelta(seconds=1))
    assert finished.is_expired(finished.finished_at + RESULT_TTL)


@pytest.mark.parametrize("job", [queued, processing])
def test_an_unfinished_job_never_expires(job: Callable[[], RecognitionJob]) -> None:
    assert not job().is_expired(T0 + timedelta(days=1))


# --- crossing to the inference process (ADR 0019) ----------------------------------------


def test_the_drawing_and_the_result_survive_pickle() -> None:
    ordered_result = RecognitionResult(
        (
            Prediction(
                "日",
                0.81,
                EvaluatedStrokeOrder(
                    expected_strokes=4,
                    drawn_strokes=3,
                    issues=(
                        OrderIssue(drawn_stroke=3, expected_position=2),
                        JoinedIssue(drawn_stroke=1, expected_strokes=(1, 2)),
                    ),
                ),
            ),
        )
    )

    for value in (DRAWING, ordered_result, completed()):
        assert pickle.loads(pickle.dumps(value)) == value

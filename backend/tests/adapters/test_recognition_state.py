"""The job state format of ARCHITECTURE.md, section 2.2 (the GET body and the SSE data)."""

from datetime import timedelta

from fakes import DRAWING, T0
from kanjilens.adapters.inbound.http.recognition_state import RecognitionStateResponse
from kanjilens.domain.job import JobFailure, RecognitionJob
from kanjilens.domain.prediction import Prediction, RecognitionResult
from kanjilens.domain.stroke_order import (
    BrokenIssue,
    DirectionIssue,
    EvaluatedStrokeOrder,
    JoinedIssue,
    NotEvaluatedReason,
    NotEvaluatedStrokeOrder,
    OrderIssue,
    StrokeOrderMode,
)

T1 = T0 + timedelta(seconds=1)


def state(job: RecognitionJob) -> dict[str, object]:
    return RecognitionStateResponse.from_job(job).to_json()


def job(mode: StrokeOrderMode) -> RecognitionJob:
    return RecognitionJob.submit(mode=mode, drawing=DRAWING, now=T0, job_id="abc123")


def test_a_queued_job_has_no_predictions_yet() -> None:
    assert state(job(StrokeOrderMode.UNORDERED)) == {
        "job_id": "abc123",
        "status": "queued",
        "stroke_order_mode": "unordered",
    }


def test_a_completed_unordered_job_has_no_stroke_order_field() -> None:
    result = RecognitionResult((Prediction("日", 0.81), Prediction("目", 0.12)))
    done = job(StrokeOrderMode.UNORDERED).start(T0).complete(result, T1)

    assert state(done) == {
        "job_id": "abc123",
        "status": "completed",
        "stroke_order_mode": "unordered",
        "predictions": [
            {"kanji": "日", "confidence": 0.81},
            {"kanji": "目", "confidence": 0.12},
        ],
    }


def test_a_completed_ordered_job_carries_each_evaluation() -> None:
    evaluated = EvaluatedStrokeOrder(
        5,
        5,
        (OrderIssue(3, 4), DirectionIssue(2), JoinedIssue(1, (1, 2)), BrokenIssue((4, 5), 5)),
    )
    result = RecognitionResult(
        (
            Prediction("日", 0.81, evaluated),
            Prediction(
                "目", 0.12, NotEvaluatedStrokeOrder(NotEvaluatedReason.STROKE_COUNT_MISMATCH)
            ),
        )
    )
    done = job(StrokeOrderMode.ORDERED).start(T0).complete(result, T1)

    assert state(done)["predictions"] == [
        {
            "kanji": "日",
            "confidence": 0.81,
            "stroke_order": {
                "status": "evaluated",
                "correct": False,
                "expected_strokes": 5,
                "drawn_strokes": 5,
                "issues": [
                    {"type": "order", "drawn_stroke": 3, "expected_position": 4},
                    {"type": "direction", "drawn_stroke": 2},
                    {"type": "joined", "drawn_stroke": 1, "expected_strokes": [1, 2]},
                    {"type": "broken", "drawn_strokes": [4, 5], "expected_stroke": 5},
                ],
            },
        },
        {
            "kanji": "目",
            "confidence": 0.12,
            "stroke_order": {"status": "not_evaluated", "reason": "stroke_count_mismatch"},
        },
    ]


def test_joined_and_broken_strokes_alone_keep_the_order_correct() -> None:
    evaluated = EvaluatedStrokeOrder(3, 2, (JoinedIssue(1, (1, 2)),))
    result = RecognitionResult((Prediction("日", 0.9, evaluated),))
    done = job(StrokeOrderMode.ORDERED).start(T0).complete(result, T1)

    predictions = state(done)["predictions"]

    assert isinstance(predictions, list)
    assert predictions[0]["stroke_order"]["correct"] is True


def test_a_failed_job_carries_the_failure_code_and_no_predictions() -> None:
    failed = job(StrokeOrderMode.ORDERED).start(T0).fail(JobFailure.INFERENCE_FAILED, T1)

    assert state(failed) == {
        "job_id": "abc123",
        "status": "failed",
        "stroke_order_mode": "ordered",
        "failure": "inference_failed",
    }

"""The full state of a job, one format for GET /api/recognitions/{id} and the SSE events.

ARCHITECTURE.md, section 2.2, and ADR 0016. Fields that do not apply are left out, never sent
as null: no predictions before the job completes, no stroke_order in the unordered mode, and
the failure code only in a failed job.
"""

from typing import Any, Literal

from pydantic import BaseModel

from kanjilens.domain.job import JobFailure, JobStatus, RecognitionJob
from kanjilens.domain.prediction import Prediction
from kanjilens.domain.stroke_order import (
    BrokenIssue,
    DirectionIssue,
    EvaluatedStrokeOrder,
    JoinedIssue,
    NotEvaluatedReason,
    NotEvaluatedStrokeOrder,
    OrderIssue,
    StrokeOrderEvaluation,
    StrokeOrderIssue,
    StrokeOrderMode,
)


class OrderIssueResponse(BaseModel):
    type: Literal["order"] = "order"
    drawn_stroke: int
    expected_position: int


class DirectionIssueResponse(BaseModel):
    type: Literal["direction"] = "direction"
    drawn_stroke: int


class JoinedIssueResponse(BaseModel):
    type: Literal["joined"] = "joined"
    drawn_stroke: int
    expected_strokes: list[int]


class BrokenIssueResponse(BaseModel):
    type: Literal["broken"] = "broken"
    drawn_strokes: list[int]
    expected_stroke: int


type IssueResponse = (
    OrderIssueResponse | DirectionIssueResponse | JoinedIssueResponse | BrokenIssueResponse
)


class EvaluatedStrokeOrderResponse(BaseModel):
    status: Literal["evaluated"] = "evaluated"
    correct: bool
    expected_strokes: int
    drawn_strokes: int
    issues: list[IssueResponse]


class NotEvaluatedStrokeOrderResponse(BaseModel):
    status: Literal["not_evaluated"] = "not_evaluated"
    reason: NotEvaluatedReason


class PredictionResponse(BaseModel):
    kanji: str
    confidence: float
    stroke_order: EvaluatedStrokeOrderResponse | NotEvaluatedStrokeOrderResponse | None = None


class RecognitionStateResponse(BaseModel):
    job_id: str
    status: JobStatus
    stroke_order_mode: StrokeOrderMode
    predictions: list[PredictionResponse] | None = None
    failure: JobFailure | None = None

    @classmethod
    def from_job(cls, job: RecognitionJob) -> RecognitionStateResponse:
        return cls(
            job_id=job.id,
            status=job.status,
            stroke_order_mode=job.mode,
            predictions=(
                None if job.result is None else [_prediction(p) for p in job.result.predictions]
            ),
            failure=job.failure,
        )

    def to_json(self) -> dict[str, Any]:
        """The body as sent: the fields that do not apply are left out."""
        return self.model_dump(mode="json", exclude_none=True)


def _prediction(prediction: Prediction) -> PredictionResponse:
    return PredictionResponse(
        kanji=prediction.kanji,
        confidence=prediction.confidence,
        stroke_order=_stroke_order(prediction.stroke_order),
    )


def _stroke_order(
    evaluation: StrokeOrderEvaluation | None,
) -> EvaluatedStrokeOrderResponse | NotEvaluatedStrokeOrderResponse | None:
    match evaluation:
        case None:
            return None
        case NotEvaluatedStrokeOrder(reason=reason):
            return NotEvaluatedStrokeOrderResponse(reason=reason)
        case EvaluatedStrokeOrder():
            return EvaluatedStrokeOrderResponse(
                correct=evaluation.correct,
                expected_strokes=evaluation.expected_strokes,
                drawn_strokes=evaluation.drawn_strokes,
                issues=[_issue(issue) for issue in evaluation.issues],
            )


def _issue(issue: StrokeOrderIssue) -> IssueResponse:
    match issue:
        case OrderIssue(drawn_stroke=drawn, expected_position=expected):
            return OrderIssueResponse(drawn_stroke=drawn, expected_position=expected)
        case DirectionIssue(drawn_stroke=drawn):
            return DirectionIssueResponse(drawn_stroke=drawn)
        case JoinedIssue(drawn_stroke=drawn, expected_strokes=expected):
            return JoinedIssueResponse(drawn_stroke=drawn, expected_strokes=list(expected))
        case BrokenIssue(drawn_strokes=drawn, expected_stroke=expected):
            return BrokenIssueResponse(drawn_strokes=list(drawn), expected_stroke=expected)

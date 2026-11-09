"""What crosses into the inference process and back: plain tuples, lists and dicts (ADR 0019).

Pickle carries them between processes, and the code in the worker (kanjilens_ml, from #48 on)
reads them without knowing the backend's domain. The stroke-order dicts follow the API format
of ADR 0016, without "correct", which the domain derives from the issues.
"""

from typing import Any, TypedDict

from kanjilens.domain.drawing import Drawing
from kanjilens.domain.prediction import Prediction, RecognitionResult
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
)

type WirePoint = tuple[float, float, int]  # x, y, t, as drawn (ADR 0016)
type WireCandidate = tuple[str, float]  # kanji, confidence
type WireEvaluation = dict[str, Any]


class WireDrawing(TypedDict):
    canvas: tuple[float, float]  # width, height
    strokes: list[list[WirePoint]]


def drawing_to_wire(drawing: Drawing) -> WireDrawing:
    return {
        "canvas": (drawing.canvas.width, drawing.canvas.height),
        "strokes": [[(p.x, p.y, p.t) for p in stroke.points] for stroke in drawing.strokes],
    }


def result_from_wire(candidates: list[WireCandidate]) -> RecognitionResult:
    """Raises InvalidPrediction when the candidates break a domain rule (a recognizer bug)."""
    return RecognitionResult(
        tuple(Prediction(kanji, confidence) for kanji, confidence in candidates)
    )


def evaluation_from_wire(data: WireEvaluation) -> StrokeOrderEvaluation:
    """Raises ValueError for an unknown shape (an evaluator bug)."""
    match data:
        case {"status": "not_evaluated", "reason": str(reason)}:
            return NotEvaluatedStrokeOrder(NotEvaluatedReason(reason))
        case {
            "status": "evaluated",
            "expected_strokes": int(expected),
            "drawn_strokes": int(drawn),
            "issues": list(issues),
        }:
            return EvaluatedStrokeOrder(expected, drawn, tuple(map(_issue_from_wire, issues)))
    raise ValueError(f"not a stroke-order evaluation: {data!r}")


def _issue_from_wire(data: dict[str, Any]) -> StrokeOrderIssue:
    match data:
        case {"type": "order", "drawn_stroke": int(drawn), "expected_position": int(expected)}:
            return OrderIssue(drawn, expected)
        case {"type": "direction", "drawn_stroke": int(drawn)}:
            return DirectionIssue(drawn)
        case {"type": "joined", "drawn_stroke": int(drawn), "expected_strokes": list(expected)}:
            return JoinedIssue(drawn, tuple(expected))
        case {"type": "broken", "drawn_strokes": list(drawn), "expected_stroke": int(expected)}:
            return BrokenIssue(tuple(drawn), expected)
    raise ValueError(f"not a stroke-order issue: {data!r}")

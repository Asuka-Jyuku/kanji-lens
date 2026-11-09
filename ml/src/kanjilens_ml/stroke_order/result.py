"""What the stroke-order check says about one candidate (ADR 0016).

The same shape as the backend domain (docs/architecture/domain.md), in plain dataclasses that
cross the inference process by pickle (ADR 0019); the backend adapter maps them into its own
types. Positions count from 1, as shown on screen.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue]


class NotEvaluatedReason(StrEnum):
    STROKE_COUNT_MISMATCH = "stroke_count_mismatch"
    REFERENCE_MISSING = "reference_missing"


@dataclass(frozen=True, slots=True)
class OrderIssue:
    """A drawn stroke sits at a different position than the reference expects."""

    drawn_stroke: int
    expected_position: int


@dataclass(frozen=True, slots=True)
class DirectionIssue:
    """A drawn stroke goes the opposite way of the reference."""

    drawn_stroke: int


@dataclass(frozen=True, slots=True)
class JoinedIssue:
    """One drawn stroke covers several neighbouring reference strokes (a remark, not an error)."""

    drawn_stroke: int
    expected_strokes: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class BrokenIssue:
    """One reference stroke was drawn as neighbouring pieces (a remark, not an error)."""

    drawn_strokes: tuple[int, ...]
    expected_stroke: int


type StrokeOrderIssue = OrderIssue | DirectionIssue | JoinedIssue | BrokenIssue


@dataclass(frozen=True, slots=True)
class EvaluatedStrokeOrder:
    """The drawing compared with the reference.

    cost is the mean distance between the matched strokes, in the unit square: how far the
    drawing is from the reference. It is not in the API; it is kept to tune the abstention for
    very irregular writing with real drawings (docs/MODEL.md).
    """

    expected_strokes: int
    drawn_strokes: int
    issues: tuple[StrokeOrderIssue, ...]
    cost: float

    @property
    def status(self) -> Literal["evaluated"]:
        return "evaluated"

    @property
    def correct(self) -> bool:
        # Only order and direction count; joined and broken strokes are remarks (ADR 0016).
        return not any(isinstance(issue, OrderIssue | DirectionIssue) for issue in self.issues)

    def as_dict(self) -> dict[str, JsonValue]:
        """The stroke_order of a candidate in the response of ADR 0016."""
        return {
            "status": self.status,
            "correct": self.correct,
            "expected_strokes": self.expected_strokes,
            "drawn_strokes": self.drawn_strokes,
            "issues": [_issue_as_dict(issue) for issue in self.issues],
        }


@dataclass(frozen=True, slots=True)
class NotEvaluatedStrokeOrder:
    reason: NotEvaluatedReason

    @property
    def status(self) -> Literal["not_evaluated"]:
        return "not_evaluated"

    def as_dict(self) -> dict[str, JsonValue]:
        return {"status": self.status, "reason": self.reason.value}


type StrokeOrderEvaluation = EvaluatedStrokeOrder | NotEvaluatedStrokeOrder


def _issue_as_dict(issue: StrokeOrderIssue) -> dict[str, JsonValue]:
    match issue:
        case OrderIssue(drawn_stroke=drawn, expected_position=expected):
            return {"type": "order", "drawn_stroke": drawn, "expected_position": expected}
        case DirectionIssue(drawn_stroke=drawn):
            return {"type": "direction", "drawn_stroke": drawn}
        case JoinedIssue(drawn_stroke=drawn, expected_strokes=expected):
            return {"type": "joined", "drawn_stroke": drawn, "expected_strokes": list(expected)}
        case BrokenIssue(drawn_strokes=drawn, expected_stroke=expected):
            return {"type": "broken", "drawn_strokes": list(drawn), "expected_stroke": expected}

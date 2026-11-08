"""Stroke-order modes and the evaluation of the drawn order against KanjiVG (ADRs 0012 and 0016).

Positions count from 1, as shown on screen. The evaluation only annotates a candidate:
it never changes the recognition ranking.
"""

import itertools
from dataclasses import dataclass
from enum import StrEnum

from kanjilens.domain.errors import InvalidStrokeOrderEvaluation

# A drawing with more or fewer strokes than this is not evaluated (ADR 0016).
MAX_STROKE_COUNT_DIFFERENCE = 2


class StrokeOrderMode(StrEnum):
    """Chosen per request. The interface default is UNORDERED (ADR 0012), set by the frontend."""

    ORDERED = "ordered"
    UNORDERED = "unordered"


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
    """One drawn stroke covers several neighbouring reference strokes."""

    drawn_stroke: int
    expected_strokes: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class BrokenIssue:
    """One reference stroke was drawn as several neighbouring strokes."""

    drawn_strokes: tuple[int, ...]
    expected_stroke: int


type StrokeOrderIssue = OrderIssue | DirectionIssue | JoinedIssue | BrokenIssue


@dataclass(frozen=True, slots=True)
class EvaluatedStrokeOrder:
    expected_strokes: int
    drawn_strokes: int
    issues: tuple[StrokeOrderIssue, ...]

    def __post_init__(self) -> None:
        if self.expected_strokes < 1 or self.drawn_strokes < 1:
            raise InvalidStrokeOrderEvaluation("stroke counts must be at least 1")
        if abs(self.expected_strokes - self.drawn_strokes) > MAX_STROKE_COUNT_DIFFERENCE:
            raise InvalidStrokeOrderEvaluation(
                f"{self.drawn_strokes} drawn and {self.expected_strokes} expected strokes "
                "must be not_evaluated (stroke_count_mismatch)"
            )
        for issue in self.issues:
            self._check_issue(issue)

    @property
    def correct(self) -> bool:
        # Only order and direction count; joined and broken strokes are remarks (ADR 0016).
        return not any(isinstance(issue, OrderIssue | DirectionIssue) for issue in self.issues)

    def _check_issue(self, issue: StrokeOrderIssue) -> None:
        match issue:
            case OrderIssue(drawn_stroke=drawn, expected_position=expected):
                self._check_drawn(drawn)
                self._check_expected(expected)
            case DirectionIssue(drawn_stroke=drawn):
                self._check_drawn(drawn)
            case JoinedIssue(drawn_stroke=drawn, expected_strokes=expected):
                self._check_drawn(drawn)
                _check_neighbours(expected)
                for position in expected:
                    self._check_expected(position)
            case BrokenIssue(drawn_strokes=drawn, expected_stroke=expected):
                _check_neighbours(drawn)
                for position in drawn:
                    self._check_drawn(position)
                self._check_expected(expected)

    def _check_drawn(self, position: int) -> None:
        if not 1 <= position <= self.drawn_strokes:
            raise InvalidStrokeOrderEvaluation(
                f"drawn stroke {position} is outside 1-{self.drawn_strokes}"
            )

    def _check_expected(self, position: int) -> None:
        if not 1 <= position <= self.expected_strokes:
            raise InvalidStrokeOrderEvaluation(
                f"expected stroke {position} is outside 1-{self.expected_strokes}"
            )


@dataclass(frozen=True, slots=True)
class NotEvaluatedStrokeOrder:
    reason: NotEvaluatedReason


type StrokeOrderEvaluation = EvaluatedStrokeOrder | NotEvaluatedStrokeOrder


def _check_neighbours(positions: tuple[int, ...]) -> None:
    # Joined and broken hypotheses only pair neighbouring strokes (ADR 0016).
    if len(positions) < 2 or any(b != a + 1 for a, b in itertools.pairwise(positions)):
        raise InvalidStrokeOrderEvaluation(
            f"strokes {positions} must be two or more neighbours, in order"
        )

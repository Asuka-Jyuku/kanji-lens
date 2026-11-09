import pickle
from typing import Any

import pytest

from fakes import DRAWING
from kanjilens.adapters.outbound.inference.wire import (
    drawing_to_wire,
    evaluation_from_wire,
    result_from_wire,
)
from kanjilens.adapters.outbound.recognizer import placeholder as placeholder_recognizer
from kanjilens.adapters.outbound.stroke_order import placeholder as placeholder_evaluator
from kanjilens.domain.errors import InvalidPrediction, InvalidStrokeOrderEvaluation
from kanjilens.domain.prediction import Prediction
from kanjilens.domain.stroke_order import (
    BrokenIssue,
    DirectionIssue,
    EvaluatedStrokeOrder,
    JoinedIssue,
    NotEvaluatedReason,
    NotEvaluatedStrokeOrder,
    OrderIssue,
)


def test_the_drawing_crosses_as_plain_data() -> None:
    wire = drawing_to_wire(DRAWING)

    assert wire == {"canvas": (320, 320), "strokes": [[(1.0, 1.0, 0), (2.0, 2.0, 10)]]}
    assert pickle.loads(pickle.dumps(wire)) == wire


def test_candidates_become_a_result() -> None:
    result = result_from_wire([("日", 0.7), ("目", 0.2)])

    assert result.predictions == (Prediction("日", 0.7), Prediction("目", 0.2))


def test_candidates_that_break_a_domain_rule_are_refused() -> None:
    with pytest.raises(InvalidPrediction):
        result_from_wire([("目", 0.2), ("日", 0.7)])  # not sorted by confidence


def test_every_issue_type_is_read() -> None:
    evaluation = evaluation_from_wire(
        {
            "status": "evaluated",
            "expected_strokes": 5,
            "drawn_strokes": 5,
            "issues": [
                {"type": "order", "drawn_stroke": 3, "expected_position": 4},
                {"type": "direction", "drawn_stroke": 2},
                {"type": "joined", "drawn_stroke": 1, "expected_strokes": [1, 2]},
                {"type": "broken", "drawn_strokes": [4, 5], "expected_stroke": 5},
            ],
        }
    )

    assert evaluation == EvaluatedStrokeOrder(
        5,
        5,
        (OrderIssue(3, 4), DirectionIssue(2), JoinedIssue(1, (1, 2)), BrokenIssue((4, 5), 5)),
    )


def test_a_not_evaluated_candidate_is_read() -> None:
    evaluation = evaluation_from_wire({"status": "not_evaluated", "reason": "reference_missing"})

    assert evaluation == NotEvaluatedStrokeOrder(NotEvaluatedReason.REFERENCE_MISSING)


@pytest.mark.parametrize(
    ("data", "error"),
    [
        pytest.param({"status": "maybe"}, ValueError, id="unknown-status"),
        pytest.param({"status": "not_evaluated", "reason": "tired"}, ValueError, id="bad-reason"),
        pytest.param(
            {"status": "evaluated", "expected_strokes": 2, "drawn_strokes": 2, "issues": [{}]},
            ValueError,
            id="unknown-issue",
        ),
        pytest.param(
            {"status": "evaluated", "expected_strokes": 2, "drawn_strokes": 9, "issues": []},
            InvalidStrokeOrderEvaluation,
            id="breaks-a-domain-rule",
        ),
    ],
)
def test_a_malformed_evaluation_is_refused(data: dict[str, Any], error: type[Exception]) -> None:
    with pytest.raises(error):
        evaluation_from_wire(data)


def test_the_placeholders_answer_what_the_domain_accepts() -> None:
    wire = drawing_to_wire(DRAWING)
    result = result_from_wire(placeholder_recognizer.recognize(wire))
    candidates = [prediction.kanji for prediction in result.predictions]

    evaluations = [
        evaluation_from_wire(e) for e in placeholder_evaluator.evaluate(wire, candidates)
    ]

    assert len(evaluations) == len(candidates) == 3
    assert all(isinstance(e, EvaluatedStrokeOrder) and e.correct for e in evaluations)

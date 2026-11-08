import math

import pytest

from kanjilens.domain.errors import InvalidPrediction
from kanjilens.domain.prediction import Prediction, RecognitionResult
from kanjilens.domain.stroke_order import (
    EvaluatedStrokeOrder,
    NotEvaluatedReason,
    NotEvaluatedStrokeOrder,
    StrokeOrderMode,
)

EVALUATED = EvaluatedStrokeOrder(expected_strokes=4, drawn_strokes=4, issues=())
NOT_EVALUATED = NotEvaluatedStrokeOrder(NotEvaluatedReason.STROKE_COUNT_MISMATCH)


def test_accepts_the_example_result() -> None:
    result = RecognitionResult(
        (Prediction("日", 0.81), Prediction("目", 0.12), Prediction("白", 0.04))
    )

    assert [p.kanji for p in result.predictions] == ["日", "目", "白"]


@pytest.mark.parametrize("kanji", ["", "日本"])
def test_a_candidate_is_one_character(kanji: str) -> None:
    with pytest.raises(InvalidPrediction):
        Prediction(kanji, 0.5)


def test_a_character_outside_the_bmp_is_one_character() -> None:
    assert Prediction("𠀋", 0.5).kanji == "𠀋"


@pytest.mark.parametrize("confidence", [-0.01, 1.01, math.nan, math.inf])
def test_confidence_is_a_probability(confidence: float) -> None:
    with pytest.raises(InvalidPrediction):
        Prediction("日", confidence)


def test_a_result_has_at_least_one_prediction() -> None:
    with pytest.raises(InvalidPrediction):
        RecognitionResult(())


def test_candidates_do_not_repeat() -> None:
    with pytest.raises(InvalidPrediction):
        RecognitionResult((Prediction("日", 0.5), Prediction("日", 0.4)))


def test_predictions_are_sorted_by_confidence() -> None:
    with pytest.raises(InvalidPrediction):
        RecognitionResult((Prediction("目", 0.12), Prediction("日", 0.81)))


def test_confidences_never_add_up_to_more_than_one() -> None:
    with pytest.raises(InvalidPrediction):
        RecognitionResult((Prediction("日", 0.6), Prediction("目", 0.5)))


def test_float_rounding_on_the_sum_is_tolerated() -> None:
    thirds = tuple(Prediction(k, 1 / 3) for k in "日目白")

    assert len(RecognitionResult(thirds).predictions) == 3


def test_ordered_results_evaluate_every_candidate() -> None:
    result = RecognitionResult(
        (Prediction("日", 0.8, EVALUATED), Prediction("目", 0.1, NOT_EVALUATED))
    )

    result.check_mode(StrokeOrderMode.ORDERED)
    with pytest.raises(InvalidPrediction):
        RecognitionResult((Prediction("日", 0.8, EVALUATED), Prediction("目", 0.1))).check_mode(
            StrokeOrderMode.ORDERED
        )


def test_unordered_results_evaluate_no_candidate() -> None:
    RecognitionResult((Prediction("日", 0.8),)).check_mode(StrokeOrderMode.UNORDERED)
    with pytest.raises(InvalidPrediction):
        RecognitionResult((Prediction("日", 0.8, EVALUATED),)).check_mode(StrokeOrderMode.UNORDERED)

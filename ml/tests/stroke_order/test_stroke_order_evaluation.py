import itertools
import math
import pickle

import pytest

from kanjilens_ml.stroke_order import (
    BrokenIssue,
    DirectionIssue,
    EvaluatedStrokeOrder,
    JoinedIssue,
    NotEvaluatedReason,
    NotEvaluatedStrokeOrder,
    OrderIssue,
    PreparedStrokes,
    StrokeOrderEvaluation,
    StrokeOrderParameters,
    evaluate_stroke_order,
)

type Stroke = list[tuple[float, float]]

# A hand-made 日 (not KanjiVG data), in a 100x100 frame, in the usual order and direction:
# left side down; top then right side down; middle bar; bottom bar.
LEFT: Stroke = [(20, 10), (20, 90)]
TOP_AND_RIGHT: Stroke = [(20, 10), (80, 10), (80, 90)]
MIDDLE: Stroke = [(20, 50), (80, 50)]
BOTTOM: Stroke = [(20, 90), (80, 90)]
NICHI = [LEFT, TOP_AND_RIGHT, MIDDLE, BOTTOM]

REFERENCE = PreparedStrokes(NICHI)


def drawn(*strokes: Stroke, scale: float = 3.0, wobble: float = 0.0) -> list[list[list[float]]]:
    """The strokes as the canvas sends them: [x, y, t] in CSS pixels, a few points each."""
    canvas: list[list[list[float]]] = []
    time = 0.0
    for number, stroke in enumerate(strokes):
        points: list[list[float]] = []
        for (x0, y0), (x1, y1) in itertools.pairwise(stroke):
            for step in range(10):
                f = step / 10
                bend = wobble * math.sin(7 * f + number)  # a hand is never straight
                points.append(
                    [(x0 + (x1 - x0) * f + bend) * scale, (y0 + (y1 - y0) * f) * scale, time]
                )
                time += 16
        points.append([stroke[-1][0] * scale, stroke[-1][1] * scale, time])
        canvas.append(points)
    return canvas


def check(*strokes: Stroke, wobble: float = 0.0) -> StrokeOrderEvaluation:
    return evaluate_stroke_order(PreparedStrokes(drawn(*strokes, wobble=wobble)), REFERENCE)


def evaluated(result: StrokeOrderEvaluation) -> EvaluatedStrokeOrder:
    assert isinstance(result, EvaluatedStrokeOrder)
    return result


def test_the_right_order_has_no_issue() -> None:
    result = evaluated(check(*NICHI))

    assert result.issues == ()
    assert result.correct
    assert (result.expected_strokes, result.drawn_strokes) == (4, 4)


def test_a_wobbly_hand_in_another_size_still_has_no_issue() -> None:
    result = evaluated(check(*NICHI, wobble=2.0))

    assert result.correct
    assert result.issues == ()


def test_two_swapped_strokes_are_both_out_of_order() -> None:
    result = evaluated(check(LEFT, TOP_AND_RIGHT, BOTTOM, MIDDLE))

    assert result.issues == (OrderIssue(3, 4), OrderIssue(4, 3))
    assert not result.correct


def test_a_stroke_drawn_the_other_way_has_the_wrong_direction() -> None:
    result = evaluated(check(LEFT, TOP_AND_RIGHT, MIDDLE[::-1], BOTTOM))

    assert result.issues == (DirectionIssue(3),)
    assert not result.correct


def test_a_stroke_too_many_is_no_order_error() -> None:
    stray: Stroke = [(48, 28), (52, 31)]

    result = evaluated(check(LEFT, TOP_AND_RIGHT, stray, MIDDLE, BOTTOM))

    assert result.correct
    assert result.issues == ()
    assert (result.expected_strokes, result.drawn_strokes) == (4, 5)


def test_a_missing_stroke_is_no_order_error() -> None:
    result = evaluated(check(LEFT, TOP_AND_RIGHT, BOTTOM))

    assert result.correct
    assert result.issues == ()
    assert (result.expected_strokes, result.drawn_strokes) == (4, 3)


def test_two_strokes_drawn_at_once_are_joined_not_out_of_order() -> None:
    result = evaluated(check(LEFT, TOP_AND_RIGHT, MIDDLE + BOTTOM))

    assert result.issues == (JoinedIssue(drawn_stroke=3, expected_strokes=(3, 4)),)
    assert result.correct


def test_a_stroke_drawn_in_two_pieces_is_broken_not_out_of_order() -> None:
    top: Stroke = [(20, 10), (80, 10)]
    right: Stroke = [(80, 10), (80, 90)]

    result = evaluated(check(LEFT, top, right, MIDDLE, BOTTOM))

    assert result.issues == (BrokenIssue(drawn_strokes=(2, 3), expected_stroke=2),)
    assert result.correct


def test_leaving_a_stroke_out_costs_the_unmatched_stroke_cost() -> None:
    # The same missing stroke: cheap to leave out, it is missing; dear, two strokes are joined.
    drawing = PreparedStrokes(drawn(LEFT, TOP_AND_RIGHT, BOTTOM))
    dear = StrokeOrderParameters(unmatched_stroke_cost=1.0)

    cheap_result = evaluated(evaluate_stroke_order(drawing, REFERENCE))
    dear_result = evaluated(evaluate_stroke_order(drawing, REFERENCE, dear))

    assert cheap_result.issues == ()
    assert any(isinstance(issue, JoinedIssue) for issue in dear_result.issues)
    assert dear_result.cost > cheap_result.cost


def test_a_short_stroke_is_not_checked_for_direction() -> None:
    # A long bar, a long post and a dot shorter than min_direction_length (0.08).
    bar: Stroke = [(10, 10), (90, 10)]
    post: Stroke = [(50, 10), (50, 90)]
    dot: Stroke = [(60, 60), (64, 64)]
    reference = PreparedStrokes([bar, post, dot])

    dot_reversed = evaluate_stroke_order(PreparedStrokes(drawn(bar, post, dot[::-1])), reference)
    bar_reversed = evaluate_stroke_order(PreparedStrokes(drawn(bar[::-1], post, dot)), reference)

    assert evaluated(dot_reversed).issues == ()
    assert evaluated(bar_reversed).issues == (DirectionIssue(1),)


def test_more_than_two_strokes_of_difference_is_not_evaluated() -> None:
    assert check(LEFT) == NotEvaluatedStrokeOrder(NotEvaluatedReason.STROKE_COUNT_MISMATCH)


def test_a_kanji_without_reference_is_not_evaluated() -> None:
    result = evaluate_stroke_order(PreparedStrokes(drawn(*NICHI)), None)

    assert result == NotEvaluatedStrokeOrder(NotEvaluatedReason.REFERENCE_MISSING)


@pytest.mark.parametrize(
    "parameters",
    [StrokeOrderParameters(points_per_stroke=8), StrokeOrderParameters(max_count_difference=3)],
)
def test_the_drawing_and_the_reference_must_be_prepared_alike(
    parameters: StrokeOrderParameters,
) -> None:
    other = PreparedStrokes(drawn(*NICHI), parameters)

    with pytest.raises(ValueError, match="prepared with the parameters"):
        evaluate_stroke_order(other, REFERENCE)
    with pytest.raises(ValueError, match="prepared with the parameters"):
        evaluate_stroke_order(PreparedStrokes(drawn(*NICHI)), REFERENCE, parameters)


def test_a_drawing_needs_a_stroke() -> None:
    with pytest.raises(ValueError, match="at least one stroke"):
        PreparedStrokes([])


def test_the_answer_has_the_shape_of_the_api() -> None:
    swapped = evaluated(check(LEFT, TOP_AND_RIGHT, BOTTOM, MIDDLE))
    joined = evaluated(check(LEFT, TOP_AND_RIGHT, MIDDLE + BOTTOM))

    # ADR 0016, "Formato da resposta"; the cost stays out of it.
    assert swapped.as_dict() == {
        "status": "evaluated",
        "correct": False,
        "expected_strokes": 4,
        "drawn_strokes": 4,
        "issues": [
            {"type": "order", "drawn_stroke": 3, "expected_position": 4},
            {"type": "order", "drawn_stroke": 4, "expected_position": 3},
        ],
    }
    assert joined.as_dict()["issues"] == [
        {"type": "joined", "drawn_stroke": 3, "expected_strokes": [3, 4]}
    ]
    assert NotEvaluatedStrokeOrder(NotEvaluatedReason.REFERENCE_MISSING).as_dict() == {
        "status": "not_evaluated",
        "reason": "reference_missing",
    }


def test_the_drawing_and_the_answer_cross_the_inference_process() -> None:
    # ADR 0019: what goes in and out of the process travels by pickle.
    drawing = PreparedStrokes(drawn(*NICHI))
    result = evaluate_stroke_order(drawing, REFERENCE)

    assert pickle.loads(pickle.dumps(result)) == result
    copy = pickle.loads(pickle.dumps(drawing))
    assert evaluate_stroke_order(copy, REFERENCE) == result

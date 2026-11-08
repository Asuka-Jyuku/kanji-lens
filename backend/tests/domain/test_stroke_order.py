import pytest

from kanjilens.domain.errors import InvalidStrokeOrderEvaluation
from kanjilens.domain.stroke_order import (
    BrokenIssue,
    DirectionIssue,
    EvaluatedStrokeOrder,
    JoinedIssue,
    OrderIssue,
    StrokeOrderIssue,
    StrokeOrderMode,
)


def evaluated(*issues: StrokeOrderIssue, expected: int = 4, drawn: int = 4) -> EvaluatedStrokeOrder:
    return EvaluatedStrokeOrder(expected_strokes=expected, drawn_strokes=drawn, issues=issues)


def test_modes_use_the_api_values() -> None:
    assert [mode.value for mode in StrokeOrderMode] == ["ordered", "unordered"]


def test_no_issues_is_correct() -> None:
    assert evaluated().correct


@pytest.mark.parametrize(
    "issue", [OrderIssue(drawn_stroke=3, expected_position=4), DirectionIssue(drawn_stroke=2)]
)
def test_order_and_direction_issues_make_it_incorrect(issue: StrokeOrderIssue) -> None:
    assert not evaluated(issue).correct


def test_joined_and_broken_strokes_are_remarks_and_keep_it_correct() -> None:
    joined = evaluated(JoinedIssue(drawn_stroke=1, expected_strokes=(1, 2)), expected=4, drawn=3)
    broken = evaluated(BrokenIssue(drawn_strokes=(2, 3), expected_stroke=2), expected=4, drawn=5)

    assert joined.correct
    assert broken.correct


@pytest.mark.parametrize(("expected", "drawn"), [(4, 7), (7, 4)])
def test_a_difference_above_two_strokes_cannot_be_evaluated(expected: int, drawn: int) -> None:
    with pytest.raises(InvalidStrokeOrderEvaluation):
        evaluated(expected=expected, drawn=drawn)


@pytest.mark.parametrize(("expected", "drawn"), [(4, 6), (6, 4)])
def test_a_difference_of_two_strokes_can_be_evaluated(expected: int, drawn: int) -> None:
    assert evaluated(expected=expected, drawn=drawn).correct


@pytest.mark.parametrize(("expected", "drawn"), [(0, 1), (1, 0)])
def test_stroke_counts_start_at_one(expected: int, drawn: int) -> None:
    with pytest.raises(InvalidStrokeOrderEvaluation):
        evaluated(expected=expected, drawn=drawn)


@pytest.mark.parametrize(
    "issue",
    [
        OrderIssue(drawn_stroke=0, expected_position=1),
        OrderIssue(drawn_stroke=5, expected_position=1),
        OrderIssue(drawn_stroke=1, expected_position=0),
        OrderIssue(drawn_stroke=1, expected_position=5),
        DirectionIssue(drawn_stroke=5),
        JoinedIssue(drawn_stroke=5, expected_strokes=(1, 2)),
        JoinedIssue(drawn_stroke=1, expected_strokes=(4, 5)),
        BrokenIssue(drawn_strokes=(4, 5), expected_stroke=1),
        BrokenIssue(drawn_strokes=(1, 2), expected_stroke=5),
    ],
)
def test_positions_stay_inside_the_stroke_counts(issue: StrokeOrderIssue) -> None:
    with pytest.raises(InvalidStrokeOrderEvaluation):
        evaluated(issue)


@pytest.mark.parametrize("positions", [(1,), (1, 3), (2, 1), ()])
def test_joined_strokes_are_two_or_more_neighbours_in_order(positions: tuple[int, ...]) -> None:
    with pytest.raises(InvalidStrokeOrderEvaluation):
        evaluated(JoinedIssue(drawn_stroke=1, expected_strokes=positions))


@pytest.mark.parametrize("positions", [(1,), (1, 3), (2, 1), ()])
def test_broken_strokes_are_two_or_more_neighbours_in_order(positions: tuple[int, ...]) -> None:
    with pytest.raises(InvalidStrokeOrderEvaluation):
        evaluated(BrokenIssue(drawn_strokes=positions, expected_stroke=1))

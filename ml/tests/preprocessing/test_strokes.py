import itertools
import math
import pickle

import pytest

from kanjilens_ml.preprocessing.strokes import POINTS_PER_STROKE, normalize_strokes

# 二, drawn as the canvas sends it: [x, y, t] in CSS pixels, 200 px wide and 100 px tall.
NI = [
    [[100.0, 100.0, 0], [300.0, 100.0, 120]],
    [[100.0, 200.0, 400], [300.0, 200.0, 560]],
]


def approx(points: list[tuple[float, float]]) -> object:
    return [pytest.approx(point) for point in points]


def test_a_known_drawing_gives_the_known_points() -> None:
    first, second = normalize_strokes(NI, points_per_stroke=3)

    # Width 200 is the longer side: x spans 0-1; height 100 becomes 0.5, centred on 0.5.
    assert first == approx([(0.0, 0.25), (0.5, 0.25), (1.0, 0.25)])
    assert second == approx([(0.0, 0.75), (0.5, 0.75), (1.0, 0.75)])


def test_each_stroke_gets_the_same_number_of_points_by_default() -> None:
    normalized = normalize_strokes(NI)

    assert [len(stroke) for stroke in normalized] == [POINTS_PER_STROKE] * 2
    assert POINTS_PER_STROKE == 24  # the prototype's value (ADR 0016)


def test_points_are_equally_spaced_along_the_stroke() -> None:
    # An L: 3 units down, then 1 unit right; 5 points split its length 4 into steps of 1.
    (stroke,) = normalize_strokes([[[0, 0], [0, 3], [1, 3]]], points_per_stroke=5)

    steps = [math.dist(a, b) for a, b in itertools.pairwise(stroke)]
    assert steps == pytest.approx([steps[0]] * 4)
    assert stroke[3] == pytest.approx((1 / 3, 1.0))  # the corner, at length 3 of 4


def test_stroke_order_and_separation_are_kept() -> None:
    swapped = normalize_strokes([NI[1], NI[0]], points_per_stroke=3)

    assert swapped == list(reversed(normalize_strokes(NI, points_per_stroke=3)))


def test_the_direction_of_a_stroke_is_kept() -> None:
    backwards = [list(reversed(stroke)) for stroke in NI]

    normalized = normalize_strokes(backwards, points_per_stroke=3)

    assert normalized[0][0] == pytest.approx((1.0, 0.25))
    assert normalized[0][-1] == pytest.approx((0.0, 0.25))


@pytest.mark.parametrize(
    ("scale", "dx", "dy"),
    [(1.0, 0.0, 0.0), (2.5, 0.0, 0.0), (0.3, -40.0, 75.0), (1.0, 1000.0, -3.0)],
)
def test_size_and_position_on_the_canvas_do_not_matter(scale: float, dx: float, dy: float) -> None:
    moved = [[[x * scale + dx, y * scale + dy, t] for x, y, t in stroke] for stroke in NI]

    assert normalize_strokes(moved) == [approx(s) for s in normalize_strokes(NI)]


def test_the_aspect_ratio_is_kept() -> None:
    # A tall, narrow drawing stays tall and narrow: it is not stretched to fill the square.
    tall, bar = normalize_strokes([[[50, 0], [50, 400]], [[40, 0], [60, 0]]], 2)

    assert tall == approx([(0.5, 0.0), (0.5, 1.0)])
    assert bar == approx([(0.475, 0.0), (0.525, 0.0)])  # 20 of 400 wide, around the centre


def test_time_is_ignored() -> None:
    without_time = [[[x, y] for x, y, _ in stroke] for stroke in NI]
    other_times = [[[x, y, t * 7 + 3] for x, y, t in stroke] for stroke in NI]

    assert normalize_strokes(without_time) == normalize_strokes(NI)
    assert normalize_strokes(other_times) == normalize_strokes(NI)


def test_a_single_point_stroke_becomes_that_point_repeated() -> None:
    dot_then_line = [[[200.0, 150.0, 0]], NI[0]]

    dot, _ = normalize_strokes(dot_then_line, points_per_stroke=4)

    # The box is 200 x 50 (y from 100 to 150, centre 125): y=150 lands at 0.5 + 25/200.
    assert dot == approx([(0.5, 0.625)] * 4)


def test_a_stroke_with_repeated_points_is_resampled_by_length() -> None:
    # A finger resting on the screen repeats points; they add no length.
    (stroke,) = normalize_strokes([[[0, 0], [0, 0], [4, 0], [4, 0]]], points_per_stroke=5)

    assert [x for x, _ in stroke] == pytest.approx([0.0, 0.25, 0.5, 0.75, 1.0])


def test_a_drawing_of_a_single_point_lands_in_the_centre() -> None:
    assert normalize_strokes([[[7, 7, 0]], [[7, 7, 9]]], 2) == [
        [(0.5, 0.5), (0.5, 0.5)],
        [(0.5, 0.5), (0.5, 0.5)],
    ]


def test_no_strokes_gives_no_strokes() -> None:
    assert normalize_strokes([]) == []


@pytest.mark.parametrize(
    ("strokes", "points_per_stroke"),
    [
        pytest.param([[]], POINTS_PER_STROKE, id="stroke-without-points"),
        pytest.param([[[0, 0], [math.nan, 1]]], POINTS_PER_STROKE, id="nan"),
        pytest.param([[[0, 0], [math.inf, 1]]], POINTS_PER_STROKE, id="infinite"),
        pytest.param(NI, 1, id="one-point-per-stroke"),
    ],
)
def test_invalid_input_is_refused(strokes: list[list[list[float]]], points_per_stroke: int) -> None:
    with pytest.raises(ValueError):
        normalize_strokes(strokes, points_per_stroke)


def test_the_output_is_deterministic_and_crosses_processes() -> None:
    first = normalize_strokes(NI)

    assert normalize_strokes(NI) == first
    assert pickle.loads(pickle.dumps(first)) == first
    assert all(isinstance(c, float) for stroke in first for point in stroke for c in point)

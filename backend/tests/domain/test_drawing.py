import math

import pytest

from kanjilens.domain.drawing import DRAWING_LIMITS, CanvasSize, Drawing, Point, Stroke
from kanjilens.domain.errors import DrawingTooLarge, InvalidDrawing

CANVAS = CanvasSize(320, 320)


def stroke(*points: tuple[float, float, int]) -> Stroke:
    return Stroke(tuple(Point(x, y, t) for x, y, t in points))


def straight_stroke(points: int, start_t: int = 0) -> Stroke:
    return stroke(*((10.0, 10.0 + i * 0.1, start_t + i) for i in range(points)))


def test_accepts_the_example_drawing_of_adr_0016() -> None:
    drawing = Drawing(
        CANVAS,
        (
            stroke((41.0, 30.5, 0), (41.2, 88.0, 140)),
            stroke((44.1, 31.0, 410), (118.3, 29.4, 590), (117.9, 92.2, 780)),
        ),
    )

    assert drawing.point_count == 5


def test_accepts_a_single_dot() -> None:
    assert Drawing(CANVAS, (stroke((5.0, 5.0, 0)),)).point_count == 1


# --- size limits (413) -------------------------------------------------------------------


def test_accepts_exactly_the_stroke_limit() -> None:
    strokes = tuple(straight_stroke(1, start_t=i) for i in range(DRAWING_LIMITS.max_strokes))

    assert len(Drawing(CANVAS, strokes).strokes) == DRAWING_LIMITS.max_strokes


def test_rejects_more_strokes_than_the_limit() -> None:
    strokes = tuple(straight_stroke(1, start_t=i) for i in range(DRAWING_LIMITS.max_strokes + 1))

    with pytest.raises(DrawingTooLarge):
        Drawing(CANVAS, strokes)


def test_rejects_a_stroke_with_more_points_than_the_limit() -> None:
    with pytest.raises(DrawingTooLarge):
        Drawing(CANVAS, (straight_stroke(DRAWING_LIMITS.max_points_per_stroke + 1),))


def test_rejects_more_points_in_total_than_the_limit() -> None:
    per_stroke = DRAWING_LIMITS.max_points_per_stroke
    count = DRAWING_LIMITS.max_total_points // per_stroke + 1  # every stroke within its own limit
    strokes = tuple(straight_stroke(per_stroke, start_t=i * per_stroke) for i in range(count))

    with pytest.raises(DrawingTooLarge):
        Drawing(CANVAS, strokes)


def test_size_errors_carry_the_413_code() -> None:
    assert DrawingTooLarge.code == "drawing_too_large"


# --- format rules (400) ------------------------------------------------------------------


def test_format_errors_carry_the_400_code() -> None:
    assert InvalidDrawing.code == "invalid_drawing"


def test_rejects_a_drawing_without_strokes() -> None:
    with pytest.raises(InvalidDrawing):
        Drawing(CANVAS, ())


def test_rejects_an_empty_stroke() -> None:
    with pytest.raises(InvalidDrawing):
        Drawing(CANVAS, (straight_stroke(2), Stroke(())))


@pytest.mark.parametrize("side", [63.9, 4_096.1, math.nan, math.inf])
def test_rejects_a_canvas_side_outside_the_limits(side: float) -> None:
    with pytest.raises(InvalidDrawing):
        Drawing(CanvasSize(side, 320), (straight_stroke(2),))
    with pytest.raises(InvalidDrawing):
        Drawing(CanvasSize(320, side), (straight_stroke(2),))


@pytest.mark.parametrize("side", [64, 4_096])
def test_accepts_the_canvas_limits(side: float) -> None:
    assert Drawing(CanvasSize(side, side), (stroke((1.0, 1.0, 0)),)).canvas.width == side


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_rejects_non_finite_coordinates(value: float) -> None:
    with pytest.raises(InvalidDrawing):
        Drawing(CANVAS, (stroke((value, 10.0, 0)),))
    with pytest.raises(InvalidDrawing):
        Drawing(CANVAS, (stroke((10.0, value, 0)),))


@pytest.mark.parametrize(
    ("x", "y"), [(-32.0, 0.0), (352.0, 0.0), (0.0, -32.0), (0.0, 352.0), (-32.0, 352.0)]
)
def test_accepts_points_within_the_10_percent_margin(x: float, y: float) -> None:
    assert Drawing(CANVAS, (stroke((x, y, 0)),)).point_count == 1


@pytest.mark.parametrize(("x", "y"), [(-32.1, 0.0), (352.1, 0.0), (0.0, -32.1), (0.0, 352.1)])
def test_rejects_points_beyond_the_margin(x: float, y: float) -> None:
    with pytest.raises(InvalidDrawing):
        Drawing(CANVAS, (stroke((x, y, 0)),))


def test_rejects_a_negative_time() -> None:
    with pytest.raises(InvalidDrawing):
        Drawing(CANVAS, (stroke((1.0, 1.0, -1)),))


def test_rejects_time_going_backwards_inside_a_stroke() -> None:
    with pytest.raises(InvalidDrawing):
        Drawing(CANVAS, (stroke((1.0, 1.0, 0), (2.0, 2.0, 50), (3.0, 3.0, 40)),))


def test_rejects_time_going_backwards_from_one_stroke_to_the_next() -> None:
    with pytest.raises(InvalidDrawing):
        Drawing(
            CANVAS,
            (
                stroke((1.0, 1.0, 0), (2.0, 2.0, 100)),
                stroke((3.0, 3.0, 90)),
            ),
        )


def test_accepts_repeated_times() -> None:
    drawing = Drawing(
        CANVAS,
        (
            stroke((1.0, 1.0, 0), (2.0, 2.0, 0)),
            stroke((3.0, 3.0, 0)),
        ),
    )

    assert drawing.point_count == 3

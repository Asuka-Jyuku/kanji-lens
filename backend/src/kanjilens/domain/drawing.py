"""The drawing sent by the canvas: strokes of [x, y, t] points, as drawn (ADR 0016).

A Drawing validates itself on creation, so an invalid one never exists. The HTTP adapter
must also cap the sizes in its schema (with DRAWING_LIMITS) before building these objects,
so an oversized body is rejected without allocating it.
"""

import math
from dataclasses import dataclass

from kanjilens.domain.errors import DrawingTooLarge, InvalidDrawing


@dataclass(frozen=True, slots=True, kw_only=True)
class DrawingLimits:
    max_strokes: int
    max_points_per_stroke: int
    max_total_points: int
    min_canvas_side: float
    max_canvas_side: float
    canvas_margin: float  # fraction of each side a point may fall outside the canvas


# Initial values from ADR 0016; changing them updates the ADR and docs/SECURITY.md.
DRAWING_LIMITS = DrawingLimits(
    max_strokes=40,
    max_points_per_stroke=1_000,
    max_total_points=10_000,
    min_canvas_side=64,
    max_canvas_side=4_096,
    canvas_margin=0.10,
)


@dataclass(frozen=True, slots=True)
class Point:
    """x and y in CSS pixels from the canvas top-left corner; t in ms since the first point."""

    x: float
    y: float
    t: int


@dataclass(frozen=True, slots=True)
class Stroke:
    """The points of one stroke, in the order they were drawn."""

    points: tuple[Point, ...]


@dataclass(frozen=True, slots=True)
class CanvasSize:
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class Drawing:
    canvas: CanvasSize
    strokes: tuple[Stroke, ...]

    def __post_init__(self) -> None:
        _check_size(self.strokes)
        _check_canvas(self.canvas)
        _check_points(self.strokes, self.canvas)

    @property
    def point_count(self) -> int:
        return sum(len(stroke.points) for stroke in self.strokes)


def _check_size(strokes: tuple[Stroke, ...]) -> None:
    # Size first: an oversized drawing is rejected before its points are read one by one.
    limits = DRAWING_LIMITS
    if len(strokes) > limits.max_strokes:
        raise DrawingTooLarge(f"{len(strokes)} strokes; the limit is {limits.max_strokes}")
    for position, stroke in enumerate(strokes, start=1):
        if len(stroke.points) > limits.max_points_per_stroke:
            raise DrawingTooLarge(
                f"stroke {position} has {len(stroke.points)} points; "
                f"the limit is {limits.max_points_per_stroke}"
            )
    total = sum(len(stroke.points) for stroke in strokes)
    if total > limits.max_total_points:
        raise DrawingTooLarge(f"{total} points; the limit is {limits.max_total_points}")


def _check_canvas(canvas: CanvasSize) -> None:
    limits = DRAWING_LIMITS
    for side in (canvas.width, canvas.height):
        if not (math.isfinite(side) and limits.min_canvas_side <= side <= limits.max_canvas_side):
            raise InvalidDrawing(
                f"canvas {canvas.width}x{canvas.height} is outside "
                f"{limits.min_canvas_side}-{limits.max_canvas_side} px"
            )


def _check_points(strokes: tuple[Stroke, ...], canvas: CanvasSize) -> None:
    if not strokes:
        raise InvalidDrawing("the drawing has no strokes")
    margin_x = canvas.width * DRAWING_LIMITS.canvas_margin
    margin_y = canvas.height * DRAWING_LIMITS.canvas_margin
    previous_t = 0
    for position, stroke in enumerate(strokes, start=1):
        if not stroke.points:
            raise InvalidDrawing(f"stroke {position} has no points")
        for point in stroke.points:
            if not (math.isfinite(point.x) and math.isfinite(point.y)):
                raise InvalidDrawing(f"stroke {position} has a non-finite coordinate")
            if not (
                -margin_x <= point.x <= canvas.width + margin_x
                and -margin_y <= point.y <= canvas.height + margin_y
            ):
                raise InvalidDrawing(f"stroke {position} has a point outside the canvas")
            if point.t < 0:
                raise InvalidDrawing(f"stroke {position} has a negative time")
            # t counts from the first point of the whole drawing, so it never goes back,
            # not even from one stroke to the next.
            if point.t < previous_t:
                raise InvalidDrawing(f"stroke {position} has a time going backwards")
            previous_t = point.t

"""Stroke normalization for the stroke-order check (ADR 0016; spike stroke-order-evaluation.md).

The same function normalizes the strokes drawn on the canvas and the KanjiVG reference strokes,
so the two meet in one coordinate system:

1. the whole character is scaled by the longer side of the box around all its points, which
   keeps the aspect ratio, and centred in the unit square [0, 1] x [0, 1];
2. each stroke is resampled into points equally spaced along its length.

Stroke order and separation are kept as given: the check compares them. The time of each point
([x, y, t], ADR 0016) is ignored; resampling is by length, as in the prototype. Plain tuples and
lists in and out, so the result crosses into and out of the inference process (ADR 0019).

Pure Python, no PyTorch (ADR 0012): the stroke-order check imports this module.
"""

import itertools
import math
from collections.abc import Sequence

# Initial value of the prototype (ADR 0016); tuned with real drawings in #29.
POINTS_PER_STROKE = 24

type Point = tuple[float, float]
type NormalizedStroke = list[Point]


def normalize_strokes(
    strokes: Sequence[Sequence[Sequence[float]]], points_per_stroke: int = POINTS_PER_STROKE
) -> list[NormalizedStroke]:
    """Each stroke as points_per_stroke points in the unit square, in the order given.

    A point is [x, y] or [x, y, t] (t is ignored). A stroke of one point, or of points all in
    the same place, becomes that point repeated; a character of a single point lands in the
    centre. Raises ValueError for a stroke with no points, a non-finite coordinate or fewer
    than 2 points per stroke.
    """
    if points_per_stroke < 2:
        raise ValueError(f"points_per_stroke must be at least 2, not {points_per_stroke}")
    polylines = [_polyline(stroke, position) for position, stroke in enumerate(strokes, 1)]
    if not polylines:
        return []
    to_unit = _unit_square_transform(polylines)
    return [
        [to_unit(point) for point in _resample(polyline, points_per_stroke)]
        for polyline in polylines
    ]


def _polyline(stroke: Sequence[Sequence[float]], position: int) -> list[Point]:
    if not stroke:
        raise ValueError(f"stroke {position} has no points")
    points: list[Point] = []
    for point in stroke:
        x, y = float(point[0]), float(point[1])
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError(f"stroke {position} has a non-finite coordinate")
        points.append((x, y))
    return points


class _Transform:
    """(x, y) -> the unit square: the box centre to (0.5, 0.5), the longer side to length 1."""

    def __init__(self, centre_x: float, centre_y: float, scale: float) -> None:
        self._centre_x = centre_x
        self._centre_y = centre_y
        self._scale = scale

    def __call__(self, point: Point) -> Point:
        x, y = point
        return (
            0.5 + (x - self._centre_x) * self._scale,
            0.5 + (y - self._centre_y) * self._scale,
        )


def _unit_square_transform(polylines: list[list[Point]]) -> _Transform:
    # The box of the drawn points is the box of the drawn curve: a polyline never leaves the
    # box of its vertices. Resampled points could miss a corner, so the box comes first.
    xs = [x for polyline in polylines for x, _ in polyline]
    ys = [y for polyline in polylines for _, y in polyline]
    left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
    side = max(right - left, bottom - top)
    centre_x, centre_y = (left + right) / 2, (top + bottom) / 2
    scale = 1.0 / side if side > 0 else 0.0  # a single point: everything goes to the centre
    return _Transform(centre_x, centre_y, scale)


def _resample(polyline: list[Point], count: int) -> list[Point]:
    """count points equally spaced along the polyline, from its first to its last point."""
    # Cumulative length at each vertex; repeated points add nothing.
    lengths = [0.0]
    for (x0, y0), (x1, y1) in itertools.pairwise(polyline):
        lengths.append(lengths[-1] + math.hypot(x1 - x0, y1 - y0))
    total = lengths[-1]
    if total == 0:
        return [polyline[0]] * count

    resampled: list[Point] = []
    segment = 1
    for index in range(count):
        target = total * index / (count - 1)
        while segment < len(polyline) - 1 and lengths[segment] < target:
            segment += 1
        start, end = lengths[segment - 1], lengths[segment]
        fraction = 0.0 if end == start else (target - start) / (end - start)
        (x0, y0), (x1, y1) = polyline[segment - 1], polyline[segment]
        resampled.append((x0 + (x1 - x0) * fraction, y0 + (y1 - y0) * fraction))
    resampled[-1] = polyline[-1]  # exact end, free of rounding
    return resampled

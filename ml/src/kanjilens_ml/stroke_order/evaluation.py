"""The drawn stroke order compared with a reference, by bipartite matching (ADR 0016).

1. Both characters go through the shared normalization (preprocessing.strokes): the unit
   square, each stroke resampled into the same number of points.
2. The cost between two strokes is the mean distance between their points, taken both ways;
   the smaller one matches them, and comparing the two gives the direction.
3. The matching is the Hungarian algorithm (scipy.optimize.linear_sum_assignment).
4. When the stroke counts differ by 1 or 2, the side with more strokes may have neighbouring
   strokes joined into one: neighbouring reference strokes drawn at once ("joined"), or one
   reference stroke drawn in pieces ("broken"). What no join explains is a stroke left out of
   the matching: one missing from the drawing or one too many, at a fixed cost each. The
   hypothesis with the lowest total cost wins; on a tie, the one with fewer joins.
5. A drawn stroke is out of order when its place among the matched strokes differs from the
   place of its reference. Its direction is wrong when the reverse way is clearly cheaper
   (the margin) and the stroke is not too short to tell.
6. More than 2 strokes of difference, or no reference, is not evaluated.

Pure NumPy and SciPy, no PyTorch (ADR 0012). The drawing is prepared once per job and compared
with each candidate; the references are prepared once per process (kanjivg.py).
"""

import itertools
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import linear_sum_assignment

from kanjilens_ml.preprocessing.strokes import (
    POINTS_PER_STROKE,
    normalize_strokes,
    resample_polyline,
)
from kanjilens_ml.stroke_order.result import (
    BrokenIssue,
    DirectionIssue,
    EvaluatedStrokeOrder,
    JoinedIssue,
    NotEvaluatedReason,
    NotEvaluatedStrokeOrder,
    OrderIssue,
    StrokeOrderEvaluation,
    StrokeOrderIssue,
)

type FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class StrokeOrderParameters:
    """The prototype's initial values (ADR 0016), to be tuned with real drawings (docs/MODEL.md).

    direction_margin: a stroke goes the wrong way when the reverse cost is below this fraction
    of the forward cost. min_direction_length: strokes shorter than this, in the unit square,
    are not checked for direction (a dot has none). unmatched_stroke_cost: what a stroke left
    out of the matching (missing or one too many) adds to the hypothesis, in the unit of the
    point distance; without it, leaving out a piece of a broken stroke would cost nothing and
    beat the broken hypothesis (docs/MODEL.md).
    """

    points_per_stroke: int = POINTS_PER_STROKE
    direction_margin: float = 0.75
    min_direction_length: float = 0.08
    max_count_difference: int = 2
    unmatched_stroke_cost: float = 0.05


DEFAULT_PARAMETERS = StrokeOrderParameters()


@dataclass(frozen=True, slots=True)
class StrokeGroup:
    """Neighbouring strokes first..last (0-based, inclusive) taken as one path."""

    first: int
    last: int

    @property
    def size(self) -> int:
        return self.last - self.first + 1

    def positions(self) -> tuple[int, ...]:
        """The 1-based positions, as shown on screen."""
        return tuple(range(self.first + 1, self.last + 2))


class PreparedStrokes:
    """A character normalized and resampled, with every group of neighbouring strokes that a
    join could produce, as arrays ready for the cost matrix. Plain data: it pickles.
    """

    def __init__(
        self,
        strokes: Sequence[Sequence[Sequence[float]]],
        parameters: StrokeOrderParameters = DEFAULT_PARAMETERS,
    ) -> None:
        normalized = normalize_strokes(strokes, parameters.points_per_stroke)
        if not normalized:
            raise ValueError("a character needs at least one stroke")
        self.count = len(normalized)
        self.points_per_stroke = parameters.points_per_stroke
        self.max_count_difference = parameters.max_count_difference
        largest = min(parameters.max_count_difference + 1, self.count)
        self.groups = [
            StrokeGroup(first, first + size - 1)
            for size in range(1, largest + 1)
            for first in range(self.count - size + 1)
        ]
        self.group_index = {group: index for index, group in enumerate(self.groups)}
        paths = [
            resample_polyline(
                list(itertools.chain.from_iterable(normalized[g.first : g.last + 1])),
                parameters.points_per_stroke,
            )
            if g.size > 1
            else normalized[g.first]
            for g in self.groups
        ]
        self.points: FloatArray = np.asarray(paths, dtype=np.float64)
        steps = np.diff(self.points, axis=1)
        self.lengths: FloatArray = np.hypot(steps[..., 0], steps[..., 1]).sum(axis=1)

    def singles(self) -> list[StrokeGroup]:
        return self.groups[: self.count]


@dataclass(frozen=True, slots=True)
class _Hypothesis:
    """Which groups the side with more strokes is read as, and how the matching went."""

    drawn_units: list[StrokeGroup]
    reference_units: list[StrokeGroup]
    pairs: list[tuple[int, int]]  # (drawn unit, reference unit), by drawn unit
    cost: float  # mean over the matched pairs
    score: float  # what the hypotheses compete on: matched costs plus the unmatched strokes


def evaluate_stroke_order(
    drawing: PreparedStrokes,
    reference: PreparedStrokes | None,
    parameters: StrokeOrderParameters = DEFAULT_PARAMETERS,
) -> StrokeOrderEvaluation:
    """The drawing against the reference of one candidate (None: the kanji has no reference)."""
    if reference is None:
        return NotEvaluatedStrokeOrder(NotEvaluatedReason.REFERENCE_MISSING)
    # The resampling and the joined groups are made when preparing: they must agree.
    shapes = {
        (prepared.points_per_stroke, prepared.max_count_difference)
        for prepared in (drawing, reference)
    } | {(parameters.points_per_stroke, parameters.max_count_difference)}
    if len(shapes) > 1:
        raise ValueError(
            "the drawing and the reference must be prepared with the parameters of the check "
            "(points per stroke and most count difference)"
        )
    if abs(drawing.count - reference.count) > parameters.max_count_difference:
        return NotEvaluatedStrokeOrder(NotEvaluatedReason.STROKE_COUNT_MISMATCH)

    best = _best_hypothesis(drawing, reference, parameters)
    issues = _issues(best, drawing, reference, parameters)
    return EvaluatedStrokeOrder(
        expected_strokes=reference.count,
        drawn_strokes=drawing.count,
        issues=tuple(issues),
        cost=best.cost,
    )


def _best_hypothesis(
    drawing: PreparedStrokes, reference: PreparedStrokes, parameters: StrokeOrderParameters
) -> _Hypothesis:
    difference = abs(drawing.count - reference.count)
    drawing_is_longer = drawing.count > reference.count
    longer = drawing if drawing_is_longer else reference
    shorter = reference if drawing_is_longer else drawing
    # Only the longer side is joined, so the shorter one is compared stroke by stroke.
    cost = _cost_matrix(longer.points, shorter.points[: shorter.count])
    short_units = shorter.singles()

    best: _Hypothesis | None = None
    for long_units in _joinings(longer.count, difference):
        rows = [longer.group_index[unit] for unit in long_units]
        matched_long, matched_short = linear_sum_assignment(cost[rows])
        matched = cost[rows][matched_long, matched_short]
        unmatched = len(long_units) - shorter.count
        score = float(matched.sum()) + parameters.unmatched_stroke_cost * unmatched
        if best is not None and score >= best.score:
            continue
        pairs = list(zip(matched_long.tolist(), matched_short.tolist(), strict=True))
        mean = float(matched.mean())
        if drawing_is_longer:
            best = _Hypothesis(long_units, short_units, sorted(pairs), mean, score)
        else:
            swapped = sorted((short, long) for long, short in pairs)
            best = _Hypothesis(short_units, long_units, swapped, mean, score)
    assert best is not None  # the hypothesis with no join always exists
    return best


def _cost_matrix(rows: FloatArray, columns: FloatArray) -> FloatArray:
    """Mean point distance between each row path and each column path, the cheaper way."""
    return np.minimum(_mean_distance(rows, columns), _mean_distance(rows, columns[:, ::-1]))


def _mean_distance(rows: FloatArray, columns: FloatArray) -> FloatArray:
    differences = rows[:, None, :, :] - columns[None, :, :, :]
    distances: FloatArray = np.hypot(differences[..., 0], differences[..., 1]).mean(axis=-1)
    return distances


def _joinings(count: int, most: int) -> Iterator[list[StrokeGroup]]:
    """Every reading of count strokes as units, joining neighbours into groups of up to most+1
    strokes, with at most `most` strokes saved in all; the reading with no join comes first.
    """

    def read(start: int, budget: int) -> Iterator[list[StrokeGroup]]:
        if start == count:
            yield []
            return
        for size in range(1, min(budget + 1, count - start) + 1):
            unit = StrokeGroup(start, start + size - 1)
            for rest in read(start + size, budget - (size - 1)):
                yield [unit, *rest]

    # Sorted by the number of strokes saved, so a tie keeps the reading with fewer joins.
    yield from sorted(read(0, most), key=lambda units: count - len(units))


def _issues(
    hypothesis: _Hypothesis,
    drawing: PreparedStrokes,
    reference: PreparedStrokes,
    parameters: StrokeOrderParameters,
) -> list[StrokeOrderIssue]:
    issues: list[StrokeOrderIssue] = []
    # Places among the matched strokes: a stroke left out does not shift the others.
    reference_rank = {
        reference_unit: rank
        for rank, reference_unit in enumerate(sorted(r for _, r in hypothesis.pairs))
    }
    for drawn_rank, (drawn_index, reference_index) in enumerate(hypothesis.pairs):
        drawn_unit = hypothesis.drawn_units[drawn_index]
        reference_unit = hypothesis.reference_units[reference_index]
        if reference_unit.size > 1:
            issues.append(JoinedIssue(drawn_unit.first + 1, reference_unit.positions()))
        if drawn_unit.size > 1:
            issues.append(BrokenIssue(drawn_unit.positions(), reference_unit.first + 1))
        if reference_rank[reference_index] != drawn_rank:
            issues.append(OrderIssue(drawn_unit.first + 1, reference_unit.first + 1))
        # The direction of a stroke drawn in pieces is left out: no single stroke to point at.
        if drawn_unit.size == 1 and _wrong_direction(
            drawn_unit, reference_unit, drawing, reference, parameters
        ):
            issues.append(DirectionIssue(drawn_unit.first + 1))
    return issues


def _wrong_direction(
    drawn_unit: StrokeGroup,
    reference_unit: StrokeGroup,
    drawing: PreparedStrokes,
    reference: PreparedStrokes,
    parameters: StrokeOrderParameters,
) -> bool:
    drawn_group = drawing.group_index[drawn_unit]
    reference_group = reference.group_index[reference_unit]
    # The shorter of the two decides: a dot drawn as a dash is still too short to tell.
    shortest = min(drawing.lengths[drawn_group], reference.lengths[reference_group])
    if shortest < parameters.min_direction_length:
        return False
    drawn = drawing.points[drawn_group]
    expected = reference.points[reference_group]
    forward = float(np.linalg.norm(drawn - expected, axis=1).mean())
    reverse = float(np.linalg.norm(drawn - expected[::-1], axis=1).mean())
    return reverse < parameters.direction_margin * forward

"""Measures the stroke-order check on synthetic drawings of KanjiVG kanji (docs/MODEL.md).

The method of the spike (docs/spikes/stroke-order-evaluation.md, section 4): each reference is
"drawn" with a global distortion, a shift per stroke and smoothed noise per point, at three
noise levels, in seven cases. A case is a hit when the issues are exactly the expected ones.
Also reports the false alarms (an order or direction error where there is none), the mean
cost of the matching and the time per candidate.

Synthetic drawings choose the algorithm and catch regressions; they are not the accuracy of
the product, which needs real drawings (#29, #66).

    uv run --directory ml python scripts/benchmark_stroke_order.py [--kanji 400] [--seed 0]

Needs the prepared references (scripts/prepare_kanjivg.py).
"""

import argparse
import math
import random
import statistics
import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import numpy as np

from kanjilens_ml.stroke_order import (
    DEFAULT_PARAMETERS,
    BrokenIssue,
    DirectionIssue,
    EvaluatedStrokeOrder,
    JoinedIssue,
    KanjiVGReferences,
    OrderIssue,
    PreparedStrokes,
    StrokeOrderIssue,
    evaluate_stroke_order,
)
from kanjilens_ml.stroke_order.kanjivg import REFERENCES_FILE

ML_ROOT = Path(__file__).resolve().parents[1]
NOISE_LEVELS = (0.015, 0.03, 0.05)
CANVAS = 320.0

type Stroke = list[tuple[float, float]]
type Case = Callable[[list[Stroke], random.Random], tuple[list[Stroke], set[StrokeOrderIssue]]]


def correct(strokes: list[Stroke], _: random.Random) -> tuple[list[Stroke], set[StrokeOrderIssue]]:
    return strokes, set()


def swapped(
    strokes: list[Stroke], rng: random.Random
) -> tuple[list[Stroke], set[StrokeOrderIssue]]:
    i, j = sorted(rng.sample(range(len(strokes)), 2))
    drawn = list(strokes)
    drawn[i], drawn[j] = drawn[j], drawn[i]
    return drawn, {OrderIssue(i + 1, j + 1), OrderIssue(j + 1, i + 1)}


def reversed_stroke(
    strokes: list[Stroke], rng: random.Random
) -> tuple[list[Stroke], set[StrokeOrderIssue]]:
    k = rng.randrange(len(strokes))
    drawn = list(strokes)
    drawn[k] = drawn[k][::-1]
    return drawn, {DirectionIssue(k + 1)}


def joined(strokes: list[Stroke], rng: random.Random) -> tuple[list[Stroke], set[StrokeOrderIssue]]:
    k = rng.randrange(len(strokes) - 1)
    drawn = [*strokes[:k], strokes[k] + strokes[k + 1], *strokes[k + 2 :]]
    return drawn, {JoinedIssue(k + 1, (k + 1, k + 2))}


def broken(strokes: list[Stroke], rng: random.Random) -> tuple[list[Stroke], set[StrokeOrderIssue]]:
    k = rng.randrange(len(strokes))
    stroke = strokes[k]
    middle = len(stroke) // 2
    pieces = [stroke[: middle + 1], stroke[middle:]]
    return [*strokes[:k], *pieces, *strokes[k + 1 :]], {BrokenIssue((k + 1, k + 2), k + 1)}


def extra(strokes: list[Stroke], rng: random.Random) -> tuple[list[Stroke], set[StrokeOrderIssue]]:
    # A short stray mark somewhere on the character: a stroke too many, not an order error.
    x, y = rng.uniform(15, 95), rng.uniform(15, 95)
    angle = rng.uniform(0, 2 * math.pi)
    mark = [(x + 6 * t * math.cos(angle), y + 6 * t * math.sin(angle)) for t in (0, 0.5, 1)]
    k = rng.randrange(len(strokes) + 1)
    return [*strokes[:k], mark, *strokes[k:]], set()


def missing(
    strokes: list[Stroke], rng: random.Random
) -> tuple[list[Stroke], set[StrokeOrderIssue]]:
    k = rng.randrange(len(strokes))
    return [*strokes[:k], *strokes[k + 1 :]], set()


CASES: dict[str, Case] = {
    "correta": correct,
    "troca": swapped,
    "invertido": reversed_stroke,
    "unidos": joined,
    "quebrado": broken,
    "a mais": extra,
    "a menos": missing,
}


def draw(strokes: list[Stroke], noise: float, rng: np.random.Generator) -> list[list[list[float]]]:
    """The reference (109x109 frame) as a hand on a 320 px canvas would draw it."""
    angle = math.radians(rng.uniform(-5, 5))
    scale_x, scale_y = rng.uniform(0.85, 1.15, 2)
    shear = rng.uniform(-0.1, 0.1)
    rotation = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
    transform = rotation @ np.array([[scale_x, shear], [0, scale_y]])
    drawn = []
    for stroke in strokes:
        points = (np.asarray(stroke) / 109 - 0.5) @ transform.T + 0.5
        points = points + rng.normal(0, noise, 2)  # the whole stroke a little off
        count = int(rng.integers(8, 40))
        dense = _resample(points, count)
        wobble = rng.normal(0, noise, (count, 2))
        kernel = np.ones(5) / 5
        wobble = np.stack([np.convolve(wobble[:, a], kernel, mode="same") for a in (0, 1)], 1)
        dense = (dense + wobble) * CANVAS
        drawn.append([[float(x), float(y), 0.0] for x, y in dense])
    return drawn


def _resample(points: np.ndarray, count: int) -> np.ndarray:
    steps = np.hypot(*np.diff(points, axis=0).T)
    lengths = np.concatenate([[0.0], np.cumsum(steps)])
    if lengths[-1] == 0:
        return np.repeat(points[:1], count, axis=0)
    targets = np.linspace(0, lengths[-1], count)
    return np.stack([np.interp(targets, lengths, points[:, a]) for a in (0, 1)], 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kanji", type=int, default=400)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--unmatched-cost", type=float, default=DEFAULT_PARAMETERS.unmatched_stroke_cost
    )
    parser.add_argument("--noise", type=float, nargs="*", default=list(NOISE_LEVELS))
    parser.add_argument(
        "--references", type=Path, default=ML_ROOT / "artifacts" / "kanjivg" / REFERENCES_FILE
    )
    arguments = parser.parse_args()

    started = time.perf_counter()
    parameters = replace(DEFAULT_PARAMETERS, unmatched_stroke_cost=arguments.unmatched_cost)
    references = KanjiVGReferences.load(arguments.references, parameters)
    print(f"Loaded {len(references)} kanji in {time.perf_counter() - started:.2f} s")
    raw = {kanji: references.strokes(kanji) or [] for kanji in references.kanji()}
    pool = [kanji for kanji, strokes in raw.items() if 2 <= len(strokes) <= 25]
    sample = random.Random(arguments.seed).sample(pool, arguments.kanji)
    counts = [len(raw[k]) for k in sample]
    print(
        f"{len(sample)} kanji, seed {arguments.seed}, {min(counts)}-{max(counts)} strokes, "
        f"mean {statistics.mean(counts):.1f}\n"
    )

    print(
        "| Ruído | Caso | Acerto exato (%) | Falso alarme (%) | Custo médio | ms médio | ms p95 |"
    )
    print("|---|---|---:|---:|---:|---:|---:|")
    all_times: list[float] = []
    for noise in arguments.noise:
        for name, case in CASES.items():
            rng = random.Random(f"{arguments.seed}-{noise}-{name}")
            np_rng = np.random.default_rng(rng.randrange(2**32))
            hits = false_alarms = 0
            costs: list[float] = []
            times: list[float] = []
            for kanji in sample:
                strokes, expected = case(raw[kanji], rng)
                drawing = PreparedStrokes(draw(strokes, noise, np_rng))
                reference = references.prepared(kanji)
                begin = time.perf_counter()
                result = evaluate_stroke_order(drawing, reference, parameters)
                times.append((time.perf_counter() - begin) * 1000)
                assert isinstance(result, EvaluatedStrokeOrder)
                hits += set(result.issues) == expected
                errors_expected = any(isinstance(i, OrderIssue | DirectionIssue) for i in expected)
                false_alarms += not errors_expected and not result.correct
                costs.append(result.cost)
            all_times += times
            print(
                f"| {noise} | {name} | {100 * hits / len(sample):.1f} | "
                f"{100 * false_alarms / len(sample):.1f} | {statistics.mean(costs):.3f} | "
                f"{statistics.mean(times):.2f} | {np.percentile(times, 95):.2f} |"
            )
    print(
        f"\nAll cases: {statistics.mean(all_times):.2f} ms mean, "
        f"{np.percentile(all_times, 95):.2f} ms p95, {max(all_times):.2f} ms max"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

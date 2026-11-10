"""Placeholder stroke-order check until the KanjiVG one is wired (#29, #48).

Every candidate comes back evaluated and correct: the expected strokes are the drawn ones, with
no issues. It runs in the inference process, like the real one will.
"""

from kanjilens.domain.drawing import Drawing
from kanjilens.domain.stroke_order import EvaluatedStrokeOrder, StrokeOrderEvaluation


def evaluate(drawing: Drawing, candidates: tuple[str, ...]) -> tuple[StrokeOrderEvaluation, ...]:
    drawn = len(drawing.strokes)
    return tuple(EvaluatedStrokeOrder(drawn, drawn, ()) for _ in candidates)

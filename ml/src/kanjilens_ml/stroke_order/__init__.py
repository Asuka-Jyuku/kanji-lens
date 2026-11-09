"""Stroke-order check against the KanjiVG reference, without PyTorch (ADRs 0012 and 0016).

Per job: prepare the drawing once, then compare it with each candidate's reference::

    references = KanjiVGReferences.load(path)  # once, in the inference process
    drawing = PreparedStrokes(strokes)  # the strokes as the canvas sends them
    evaluation = evaluate_stroke_order(drawing, references.prepared(kanji))
"""

from kanjilens_ml.stroke_order.evaluation import (
    DEFAULT_PARAMETERS,
    PreparedStrokes,
    StrokeOrderParameters,
    evaluate_stroke_order,
)
from kanjilens_ml.stroke_order.kanjivg import KanjiVGReferences
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

__all__ = [
    "DEFAULT_PARAMETERS",
    "BrokenIssue",
    "DirectionIssue",
    "EvaluatedStrokeOrder",
    "JoinedIssue",
    "KanjiVGReferences",
    "NotEvaluatedReason",
    "NotEvaluatedStrokeOrder",
    "OrderIssue",
    "PreparedStrokes",
    "StrokeOrderEvaluation",
    "StrokeOrderIssue",
    "StrokeOrderParameters",
    "evaluate_stroke_order",
]

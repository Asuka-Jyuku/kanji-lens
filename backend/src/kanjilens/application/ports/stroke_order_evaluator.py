"""Compares the drawn stroke order with each candidate's KanjiVG reference (ADRs 0012, 0016)."""

from typing import Protocol

from kanjilens.domain.drawing import Drawing
from kanjilens.domain.stroke_order import StrokeOrderEvaluation


class StrokeOrderEvaluator(Protocol):
    async def evaluate(
        self, drawing: Drawing, candidates: tuple[str, ...]
    ) -> tuple[StrokeOrderEvaluation, ...]:
        """One evaluation per candidate, in the same order.

        Runs in the inference process, so it is awaited; raises when the evaluation fails.
        """
        ...

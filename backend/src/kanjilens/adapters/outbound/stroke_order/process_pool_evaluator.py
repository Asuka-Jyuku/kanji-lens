"""StrokeOrderEvaluator that runs an evaluate function in the inference process (ADR 0019).

The function runs in the worker, so it takes and returns wire data. Until the KanjiVG check
exists it is the placeholder; #48 swaps in the real one (#29), with the references loaded by the
process initializer.
"""

from collections.abc import Callable

from kanjilens.adapters.outbound.inference.process import InferenceProcess
from kanjilens.adapters.outbound.inference.wire import (
    WireDrawing,
    WireEvaluation,
    drawing_to_wire,
    evaluation_from_wire,
)
from kanjilens.domain.drawing import Drawing
from kanjilens.domain.stroke_order import StrokeOrderEvaluation

type EvaluateFunction = Callable[[WireDrawing, list[str]], list[WireEvaluation]]


class ProcessPoolStrokeOrderEvaluator:
    def __init__(self, process: InferenceProcess, evaluate: EvaluateFunction) -> None:
        self._process = process
        self._evaluate = evaluate

    async def evaluate(
        self, drawing: Drawing, candidates: tuple[str, ...]
    ) -> tuple[StrokeOrderEvaluation, ...]:
        evaluations = await self._process.run(
            self._evaluate, drawing_to_wire(drawing), list(candidates)
        )
        return tuple(map(evaluation_from_wire, evaluations))

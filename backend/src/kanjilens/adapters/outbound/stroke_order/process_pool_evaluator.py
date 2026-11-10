"""StrokeOrderEvaluator that runs an evaluate function in the inference process (ADR 0019).

The function runs in the worker and takes and returns domain objects, which cross by pickle.
Until the KanjiVG check is wired it is the placeholder. In #48 the real function lives in this
package: it calls kanjilens_ml (#29) in the worker and turns its result into the domain there,
so the API process never imports the ML.
"""

from collections.abc import Callable

from kanjilens.adapters.outbound.inference.process import InferenceProcess
from kanjilens.domain.drawing import Drawing
from kanjilens.domain.stroke_order import StrokeOrderEvaluation

type EvaluateFunction = Callable[[Drawing, tuple[str, ...]], tuple[StrokeOrderEvaluation, ...]]


class ProcessPoolStrokeOrderEvaluator:
    def __init__(self, process: InferenceProcess, evaluate: EvaluateFunction) -> None:
        self._process = process
        self._evaluate = evaluate

    async def evaluate(
        self, drawing: Drawing, candidates: tuple[str, ...]
    ) -> tuple[StrokeOrderEvaluation, ...]:
        return await self._process.run(self._evaluate, drawing, candidates)

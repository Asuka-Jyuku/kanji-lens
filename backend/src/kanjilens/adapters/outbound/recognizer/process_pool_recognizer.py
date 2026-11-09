"""KanjiRecognizer that runs a recognize function in the inference process (ADR 0019).

The function runs in the worker, so it takes and returns wire data. Until the CNN exists it is
the placeholder; #48 swaps in the real one, with the model loaded by the process initializer.
"""

from collections.abc import Callable

from kanjilens.adapters.outbound.inference.process import InferenceProcess
from kanjilens.adapters.outbound.inference.wire import (
    WireCandidate,
    WireDrawing,
    drawing_to_wire,
    result_from_wire,
)
from kanjilens.domain.drawing import Drawing
from kanjilens.domain.prediction import RecognitionResult

type RecognizeFunction = Callable[[WireDrawing], list[WireCandidate]]


class ProcessPoolKanjiRecognizer:
    def __init__(self, process: InferenceProcess, recognize: RecognizeFunction) -> None:
        self._process = process
        self._recognize = recognize

    async def recognize(self, drawing: Drawing) -> RecognitionResult:
        candidates = await self._process.run(self._recognize, drawing_to_wire(drawing))
        return result_from_wire(candidates)

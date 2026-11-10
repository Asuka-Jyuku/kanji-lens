"""KanjiRecognizer that runs a recognize function in the inference process (ADR 0019).

The function runs in the worker and takes and returns domain objects, which cross by pickle.
Until the CNN exists it is the placeholder; #48 swaps in the real one, with the model loaded by
the process initializer.
"""

from collections.abc import Callable

from kanjilens.adapters.outbound.inference.process import InferenceProcess
from kanjilens.domain.drawing import Drawing
from kanjilens.domain.prediction import RecognitionResult

type RecognizeFunction = Callable[[Drawing], RecognitionResult]


class ProcessPoolKanjiRecognizer:
    def __init__(self, process: InferenceProcess, recognize: RecognizeFunction) -> None:
        self._process = process
        self._recognize = recognize

    async def recognize(self, drawing: Drawing) -> RecognitionResult:
        return await self._process.run(self._recognize, drawing)

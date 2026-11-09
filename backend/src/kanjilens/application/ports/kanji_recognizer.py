"""Recognizes the drawn kanji: the top-K candidates of the CNN (ADRs 0006 and 0019)."""

from typing import Protocol

from kanjilens.domain.drawing import Drawing
from kanjilens.domain.prediction import RecognitionResult


class KanjiRecognizer(Protocol):
    async def recognize(self, drawing: Drawing) -> RecognitionResult:
        """The candidates, highest confidence first, with no stroke-order evaluation.

        Runs in the inference process, so it is awaited; raises when the inference fails.
        """
        ...

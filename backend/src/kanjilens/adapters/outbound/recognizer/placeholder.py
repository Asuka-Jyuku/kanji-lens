"""Placeholder recognizer until the CNN exists (#17, #48): the same candidates for any drawing.

It runs in the inference process, like the real one will, so the backend works end to end
before the model is trained.
"""

from kanjilens.domain.drawing import Drawing
from kanjilens.domain.prediction import Prediction, RecognitionResult

RESULT = RecognitionResult((Prediction("日", 0.6), Prediction("目", 0.25), Prediction("白", 0.1)))


def recognize(_drawing: Drawing) -> RecognitionResult:
    return RESULT

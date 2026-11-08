"""The top-K candidates of a recognition."""

import math
from dataclasses import dataclass

from kanjilens.domain.errors import InvalidPrediction
from kanjilens.domain.stroke_order import StrokeOrderEvaluation, StrokeOrderMode

# Softmax probabilities add up to 1; this absorbs float rounding.
_PROBABILITY_TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class Prediction:
    kanji: str
    confidence: float
    stroke_order: StrokeOrderEvaluation | None = None  # only in the ordered mode

    def __post_init__(self) -> None:
        if len(self.kanji) != 1:
            raise InvalidPrediction(f"{self.kanji!r} is not a single character")
        if not (math.isfinite(self.confidence) and 0.0 <= self.confidence <= 1.0):
            raise InvalidPrediction(f"confidence {self.confidence} is outside 0-1")


@dataclass(frozen=True, slots=True)
class RecognitionResult:
    predictions: tuple[Prediction, ...]

    def __post_init__(self) -> None:
        if not self.predictions:
            raise InvalidPrediction("a result has at least one prediction")
        kanji = [prediction.kanji for prediction in self.predictions]
        if len(set(kanji)) != len(kanji):
            raise InvalidPrediction(f"repeated candidates in {kanji}")
        confidences = [prediction.confidence for prediction in self.predictions]
        if confidences != sorted(confidences, reverse=True):
            raise InvalidPrediction("predictions must be sorted by confidence, highest first")
        if sum(confidences) > 1.0 + _PROBABILITY_TOLERANCE:
            raise InvalidPrediction(f"confidences add up to {sum(confidences)}, above 1")

    def check_mode(self, mode: StrokeOrderMode) -> None:
        """Ordered results evaluate every candidate; unordered results evaluate none."""
        ordered = mode is StrokeOrderMode.ORDERED
        for prediction in self.predictions:
            if (prediction.stroke_order is not None) != ordered:
                raise InvalidPrediction(
                    f"{prediction.kanji}: the stroke order must be "
                    f"{'present' if ordered else 'absent'} in the {mode} mode"
                )

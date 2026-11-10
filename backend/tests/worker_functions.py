"""Functions that run in the inference process during the integration tests.

Module level, like the real ones, because spawn imports them by name in the worker (ADR 0019);
the worker finds this module because spawn passes the test's sys.path on.
"""

import os
import time

from kanjilens.adapters.outbound.recognizer import placeholder
from kanjilens.domain.drawing import Drawing
from kanjilens.domain.prediction import Prediction, RecognitionResult

SLOW_SECONDS = 1.0
CRASH_STROKES = 3  # a drawing with this many strokes kills the worker

_initializer_runs = 0


def count_initializer_runs() -> None:
    global _initializer_runs
    _initializer_runs += 1


def failing_initializer() -> None:
    raise RuntimeError("the model file is missing")


def process_info() -> tuple[int, int]:
    """(pid, how many times the initializer ran in this process)."""
    return os.getpid(), _initializer_runs


def sleep(seconds: float) -> None:
    time.sleep(seconds)


def crash() -> None:
    os._exit(1)  # like a native crash in the runtime: no exception, the process is gone


def echo[T](value: T) -> T:
    """Sends the value back: what crosses the process by pickle and returns."""
    return value


def recognize_slowly(drawing: Drawing) -> RecognitionResult:
    time.sleep(SLOW_SECONDS)  # CPU-bound work holds the worker the same way
    return placeholder.recognize(drawing)


def recognize_or_crash(drawing: Drawing) -> RecognitionResult:
    if len(drawing.strokes) == CRASH_STROKES:
        crash()
    return placeholder.recognize(drawing)


def recognize_wrongly(_drawing: Drawing) -> RecognitionResult:
    """A recognizer bug: candidates out of order break a domain rule inside the worker."""
    return RecognitionResult((Prediction("目", 0.2), Prediction("日", 0.7)))

"""Functions that run in the inference process during the integration tests.

Module level, like the real ones, because spawn imports them by name in the worker (ADR 0019);
the worker finds this module because spawn passes the test's sys.path on.
"""

import os
import time

from kanjilens.adapters.outbound.inference.wire import WireCandidate, WireDrawing
from kanjilens.adapters.outbound.recognizer import placeholder

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


def recognize_slowly(drawing: WireDrawing) -> list[WireCandidate]:
    time.sleep(SLOW_SECONDS)  # CPU-bound work holds the worker the same way
    return placeholder.recognize(drawing)


def recognize_or_crash(drawing: WireDrawing) -> list[WireCandidate]:
    if len(drawing["strokes"]) == CRASH_STROKES:
        crash()
    return placeholder.recognize(drawing)

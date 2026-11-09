"""Placeholder recognizer until the CNN exists (#17, #48): the same candidates for any drawing.

It runs in the inference process, like the real one will, so the backend works end to end
before the model is trained.
"""

from kanjilens.adapters.outbound.inference.wire import WireCandidate, WireDrawing

CANDIDATES: tuple[WireCandidate, ...] = (("日", 0.6), ("目", 0.25), ("白", 0.1))


def recognize(_drawing: WireDrawing) -> list[WireCandidate]:
    return list(CANDIDATES)

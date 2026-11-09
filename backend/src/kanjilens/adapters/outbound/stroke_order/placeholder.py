"""Placeholder stroke-order check until the KanjiVG one exists (#29, #48).

Every candidate comes back evaluated and correct: the expected strokes are the drawn ones, with
no issues. It runs in the inference process, like the real one will.
"""

from kanjilens.adapters.outbound.inference.wire import WireDrawing, WireEvaluation


def evaluate(drawing: WireDrawing, candidates: list[str]) -> list[WireEvaluation]:
    drawn = len(drawing["strokes"])
    return [
        {"status": "evaluated", "expected_strokes": drawn, "drawn_strokes": drawn, "issues": []}
        for _ in candidates
    ]

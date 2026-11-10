"""Drawings exported from the canvas (#66) go to POST /api/recognitions as they are.

The export puts the API body under "request" and the answer key beside it, since the API
rejects unknown fields. These tests post the "request" of every committed exported drawing:
the samples in tests/fixtures/drawings/ and the test sets in ml/drawings/ (docs/MODEL.md,
"Desenhos do canvas"), so a change in the format or in the API that breaks them fails here.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from kanjilens.bootstrap.app import create_app

URL = "/api/recognitions"
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "drawings"
TEST_SETS = Path(__file__).resolve().parents[3] / "ml" / "drawings"
DRAWINGS = sorted([*FIXTURES.glob("*.json"), *TEST_SETS.rglob("*.json")])
STROKE_ORDER_LABELS = {"correct", "order", "direction", "joined", "broken", "extra", "missing"}


def load(path: Path) -> dict[str, Any]:
    sample: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return sample


def test_there_are_exported_drawings_to_check() -> None:
    assert DRAWINGS, "no exported drawing found"


@pytest.mark.parametrize("path", DRAWINGS, ids=lambda path: path.name)
def test_an_exported_drawing_is_accepted_unchanged(path: Path) -> None:
    sample = load(path)

    # Outside a `with` block no inference process starts: only the HTTP adapter is tested.
    response = TestClient(create_app()).post(URL, json=sample["request"])

    assert response.status_code == 202, response.json()
    assert response.json()["status"] == "queued"


@pytest.mark.parametrize("path", DRAWINGS, ids=lambda path: path.name)
def test_an_exported_drawing_has_the_format_and_a_full_answer_key(path: Path) -> None:
    sample = load(path)
    label = sample["label"]
    stroke_count = len(sample["request"]["strokes"])

    assert set(sample) == {"format", "version", "exported_at", "label", "request"}
    assert (sample["format"], sample["version"]) == ("kanjilens-drawing", 1)
    assert set(label) == {"kanji", "stroke_order", "strokes"}
    assert len(label["kanji"]) == 1
    assert label["stroke_order"] in STROKE_ORDER_LABELS
    assert all(1 <= stroke <= stroke_count for stroke in label["strokes"])
    if label["stroke_order"] == "correct":
        assert label["strokes"] == []

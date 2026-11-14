"""The canvas drawings of the real recognition set (#93): reading a batch, writing the files.

The collection session of the development build (#100) downloads the drawings of one person
as one batch. Here the batch is checked and split into one file per drawing, in the format of
the drawing export (#66), under ``<set>/<writer>/``. The writer is a code, never a name, kept
only so the set can be split by person. Formats and folders: docs/MODEL.md, "Desenhos do
canvas".
"""

import json
import re
from collections import defaultdict
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SAMPLE_FORMAT = "kanjilens-drawing"
SAMPLE_VERSION = 1
BATCH_FORMAT = "kanjilens-drawing-batch"
BATCH_VERSION = 1

# The same rule as the frontend (isWriterCode): it becomes a folder name, so nothing else.
WRITER_CODE = re.compile(r"[a-z0-9][a-z0-9-]{0,15}")
# A list of numbers on one line, as the frontend writes a point [x, y, t] (compactJson).
_NUMBER = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
_NUMBER_LIST = re.compile(rf"\[\s*({_NUMBER}(?:,\s*{_NUMBER})*)\s*\]")


class DrawingSetError(ValueError):
    """A batch, a sample or a class list that does not follow the format."""


@dataclass(frozen=True)
class DrawingBatch:
    writer: str
    samples: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class ImportResult:
    written: tuple[Path, ...]
    #: Already in the set with the same content: importing a batch again changes nothing.
    skipped: tuple[Path, ...]


def read_class_list(path: Path) -> tuple[str, ...]:
    """One kanji per line, in order; blank lines are ignored."""
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    classes = tuple(line for line in lines if line)
    if not all(len(kanji) == 1 for kanji in classes):
        raise DrawingSetError(f"{path}: one kanji per line")
    if len(set(classes)) != len(classes):
        raise DrawingSetError(f"{path}: a kanji is listed twice")
    return classes


def check_recognition_sample(sample: object, classes: Collection[str]) -> Mapping[str, Any]:
    """The sample, if it is an exported drawing of a class, drawn in the right order."""
    if not isinstance(sample, Mapping):
        raise DrawingSetError("a sample is not an object")
    if (sample.get("format"), sample.get("version")) != (SAMPLE_FORMAT, SAMPLE_VERSION):
        raise DrawingSetError("a sample is not a kanjilens-drawing, version 1")
    label = sample.get("label")
    request = sample.get("request")
    if not isinstance(label, Mapping) or not isinstance(request, Mapping):
        raise DrawingSetError("a sample has no label or no request")
    kanji = label.get("kanji")
    if kanji not in classes:
        raise DrawingSetError(f"{kanji!r} is not in the class list")
    if label.get("stroke_order") != "correct" or label.get("strokes") != []:
        raise DrawingSetError(f"the {kanji} sample is not marked as drawn in the right order")
    if not isinstance(sample.get("exported_at"), str):
        raise DrawingSetError(f"the {kanji} sample has no exported_at")
    return sample


def parse_batch(data: object, classes: Collection[str]) -> DrawingBatch:
    """A downloaded batch, checked: its format, the writer code and every sample."""
    if not isinstance(data, Mapping):
        raise DrawingSetError("the batch is not an object")
    if (data.get("format"), data.get("version")) != (BATCH_FORMAT, BATCH_VERSION):
        raise DrawingSetError("not a kanjilens-drawing-batch, version 1")
    writer = data.get("writer")
    if not isinstance(writer, str) or not WRITER_CODE.fullmatch(writer):
        raise DrawingSetError(f"{writer!r} is not a writer code (such as a or p2)")
    samples = data.get("samples")
    if not isinstance(samples, list) or not samples:
        raise DrawingSetError("the batch has no samples")
    return DrawingBatch(writer, tuple(check_recognition_sample(each, classes) for each in samples))


def sample_file_name(sample: Mapping[str, Any]) -> str:
    """``u65e5-correct-20261113T153045Z.json``: the frontend's sampleFileName."""
    label = sample["label"]
    time = re.sub(r"[-:]", "", re.sub(r"\.\d+", "", sample["exported_at"]))
    return f"u{ord(label['kanji']):x}-{label['stroke_order']}-{time}.json"


def serialize_sample(sample: Mapping[str, Any]) -> str:
    """The file content, as the frontend writes it: one point per line."""
    text = json.dumps(sample, indent=2, ensure_ascii=False)
    text = _NUMBER_LIST.sub(lambda match: "[" + ", ".join(re.split(r",\s*", match[1])) + "]", text)
    return text + "\n"


def import_batch(batch: DrawingBatch, root: Path) -> ImportResult:
    """Writes each drawing to ``root/<writer>/``, skipping those already there.

    Two drawings saved in the same second get the same name: the second one gets ``-2``, and
    so on. A file with the same name and the same content is the same drawing.
    """
    folder = root / batch.writer
    folder.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    skipped: list[Path] = []
    for sample in batch.samples:
        content = serialize_sample(sample)
        stem = sample_file_name(sample).removesuffix(".json")
        suffix = 1
        while True:
            path = folder / (f"{stem}.json" if suffix == 1 else f"{stem}-{suffix}.json")
            if not path.exists():
                path.write_text(content, encoding="utf-8", newline="\n")
                written.append(path)
                break
            if path.read_text(encoding="utf-8") == content:
                skipped.append(path)
                break
            suffix += 1
    return ImportResult(tuple(written), tuple(skipped))


def coverage(root: Path) -> dict[str, dict[str, int]]:
    """How many drawings each kanji has, by writer: ``{"日": {"a": 5, "b": 3}}``."""
    counts: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for path in sorted(root.glob("*/*.json")):
        sample = json.loads(path.read_text(encoding="utf-8"))
        counts[sample["label"]["kanji"]][path.parent.name] += 1
    return {kanji: dict(by_writer) for kanji, by_writer in counts.items()}


def is_complete(by_writer: Mapping[str, int], per_writer: int, writers: int) -> bool:
    """The goal of a class: ``per_writer`` drawings from each of ``writers`` people (ADR 0022)."""
    return sum(1 for count in by_writer.values() if count >= per_writer) >= writers

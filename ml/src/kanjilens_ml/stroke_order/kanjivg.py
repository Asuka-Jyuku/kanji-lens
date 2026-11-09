"""The KanjiVG reference strokes: the pinned release, the prepared file and its loader (ADR 0016).

KanjiVG is copyright Ulrich Apel, released under CC BY-SA 3.0 (https://kanjivg.tagaini.net).
The prepared file is derived from it and keeps that licence and attribution; it lives outside
git (ml/artifacts/), made by ml/scripts/prepare_kanjivg.py from the pinned release.

The file holds each kanji's strokes as polylines in KanjiVG's 109x109 frame, in the official
order and direction. The loader reads it once per process and prepares each kanji for the
check on first use; the running app never goes to the network.
"""

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ElementTree
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from kanjilens_ml.stroke_order.evaluation import (
    DEFAULT_PARAMETERS,
    PreparedStrokes,
    StrokeOrderParameters,
)
from kanjilens_ml.stroke_order.svg_path import Point, path_to_polyline

# The pinned release (ADR 0016). Updating it is a conscious decision: new checksum, and the
# stroke-order check measured again (docs/MODEL.md).
KANJIVG_RELEASE = "r20260714"
KANJIVG_FILE = "kanjivg-20260714-main.zip"
KANJIVG_URL = (
    f"https://github.com/KanjiVG/kanjivg/releases/download/{KANJIVG_RELEASE}/{KANJIVG_FILE}"
)
KANJIVG_SHA256 = "b5df6cd2bc249dd49b8041eb99e38ba9f8dc6b9ea57962a80084b4a315d1a7fc"
KANJIVG_LICENSE = "CC BY-SA 3.0"
KANJIVG_ATTRIBUTION = (
    "Stroke data derived from KanjiVG, copyright Ulrich Apel, CC BY-SA 3.0 "
    "(https://kanjivg.tagaini.net; https://creativecommons.org/licenses/by-sa/3.0/)"
)

# Version of the prepared file's layout; the loader refuses any other.
REFERENCES_FORMAT = 1
REFERENCES_FILE = "kanjivg-references.json"

type ReferenceStrokes = list[list[Point]]

_SVG = "{http://www.w3.org/2000/svg}"
_STROKE_ID = re.compile(r"^kvg:[0-9a-f]+-s(\d+)$")
_KANJI_ENTRY = re.compile(r"^kanji/([0-9a-f]{5})\.svg$")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def strokes_from_svg(svg: str | bytes) -> ReferenceStrokes:
    """The strokes of one KanjiVG file, in the official order (the sN of each path id)."""
    root = ElementTree.fromstring(svg)
    numbered: dict[int, list[Point]] = {}
    for path in root.iter(f"{_SVG}path"):
        match = _STROKE_ID.match(path.get("id", ""))
        if match is None:
            continue
        number = int(match.group(1))
        if number in numbered:
            raise ValueError(f"stroke {number} appears twice")
        numbered[number] = path_to_polyline(path.get("d", ""))
    if sorted(numbered) != list(range(1, len(numbered) + 1)):
        raise ValueError(f"strokes must be numbered 1 to {len(numbered)}: {sorted(numbered)}")
    return [numbered[number] for number in range(1, len(numbered) + 1)]


def is_kanji(character: str) -> bool:
    return unicodedata.name(character, "").startswith("CJK UNIFIED IDEOGRAPH")


def read_kanjivg_zip(
    archive: Path, kanji: Iterable[str] | None = None
) -> dict[str, ReferenceStrokes]:
    """The strokes of the given kanji, or of every kanji in the archive when kanji is None.

    Only the base form (kanji/XXXXX.svg) is read; variants have another file name. A kanji
    missing from the archive is left out: the caller reports it.
    """
    wanted = None if kanji is None else set(kanji)
    references: dict[str, ReferenceStrokes] = {}
    with zipfile.ZipFile(archive) as files:
        for name in files.namelist():
            match = _KANJI_ENTRY.match(name)
            if match is None:
                continue
            character = chr(int(match.group(1), 16))
            if (wanted is None and not is_kanji(character)) or (
                wanted is not None and character not in wanted
            ):
                continue
            references[character] = strokes_from_svg(files.read(name))
    return dict(sorted(references.items()))


def write_references(path: Path, references: Mapping[str, ReferenceStrokes]) -> None:
    """The prepared file, with the source and the licence it keeps (CC BY-SA 3.0)."""
    content = {
        "format": REFERENCES_FORMAT,
        "source": {
            "name": "KanjiVG",
            "release": KANJIVG_RELEASE,
            "file": KANJIVG_FILE,
            "sha256": KANJIVG_SHA256,
            "license": KANJIVG_LICENSE,
            "attribution": KANJIVG_ATTRIBUTION,
        },
        "kanji": {
            character: [[[round(x, 2), round(y, 2)] for x, y in stroke] for stroke in strokes]
            for character, strokes in references.items()
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, separators=(",", ":")), "utf-8")


class KanjiVGReferences:
    """The reference strokes of every prepared kanji, read once; each kanji is prepared for
    the check on its first use and kept. Built in the inference process's initializer.
    """

    def __init__(
        self,
        strokes: Mapping[str, ReferenceStrokes],
        parameters: StrokeOrderParameters = DEFAULT_PARAMETERS,
    ) -> None:
        self._strokes = dict(strokes)
        self._parameters = parameters
        self._prepared: dict[str, PreparedStrokes] = {}

    @classmethod
    def load(
        cls, path: Path, parameters: StrokeOrderParameters = DEFAULT_PARAMETERS
    ) -> KanjiVGReferences:
        """Reads the prepared file. Raises ValueError for another format or KanjiVG release,
        so a stale file fails at start-up instead of answering with other references.
        """
        content: Any = json.loads(path.read_text("utf-8"))
        if content.get("format") != REFERENCES_FORMAT:
            raise ValueError(f"{path}: format {content.get('format')!r}, not {REFERENCES_FORMAT}")
        source = content.get("source", {})
        if source.get("sha256") != KANJIVG_SHA256:
            raise ValueError(
                f"{path} was made from KanjiVG {source.get('release')!r}, not {KANJIVG_RELEASE}; "
                "run ml/scripts/prepare_kanjivg.py again"
            )
        strokes = {
            character: [[(float(x), float(y)) for x, y in stroke] for stroke in kanji_strokes]
            for character, kanji_strokes in content["kanji"].items()
        }
        return cls(strokes, parameters)

    def __len__(self) -> int:
        return len(self._strokes)

    def __contains__(self, kanji: object) -> bool:
        return kanji in self._strokes

    def kanji(self) -> list[str]:
        return sorted(self._strokes)

    def strokes(self, kanji: str) -> ReferenceStrokes | None:
        """The reference strokes as stored (109x109 frame), or None when KanjiVG lacks it."""
        return self._strokes.get(kanji)

    def prepared(self, kanji: str) -> PreparedStrokes | None:
        """The kanji ready for the check, or None when KanjiVG does not have it."""
        if kanji not in self._prepared:
            strokes = self._strokes.get(kanji)
            if strokes is None:
                return None
            self._prepared[kanji] = PreparedStrokes(strokes, self._parameters)
        return self._prepared[kanji]

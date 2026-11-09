import json
import zipfile
from pathlib import Path

import pytest

from kanjilens_ml.stroke_order.kanjivg import (
    KANJIVG_LICENSE,
    KANJIVG_RELEASE,
    KANJIVG_SHA256,
    KanjiVGReferences,
    read_kanjivg_zip,
    sha256_of,
    strokes_from_svg,
    write_references,
)

# A file shaped like KanjiVG's (namespaces, ids, groups), with hand-made strokes for 二:
# the paths come out of order in the file and one path is not a stroke.
NI_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN" "" [
<!ATTLIST path xmlns:kvg CDATA #FIXED "http://kanjivg.tagaini.net" kvg:type CDATA #IMPLIED >
]>
<svg xmlns="http://www.w3.org/2000/svg" width="109" height="109" viewBox="0 0 109 109"
     xmlns:kvg="https://kanjivg.tagaini.net/">
<g id="kvg:StrokePaths_04e8c">
<g id="kvg:04e8c" kvg:element="二">
  <path id="kvg:04e8c-s2" kvg:type="㇐" d="M10,80L100,80"/>
  <path id="kvg:04e8c-s1" kvg:type="㇐" d="M30,30L80,30"/>
  <path id="kvg:04e8c-outline" d="M0,0L1,1"/>
</g>
</g>
</svg>"""

SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg"><g>{}</g></svg>'  # only what the reader needs
)


def stroke_path(number: int, data: str = "M0,0L10,10") -> str:
    return f'<path id="kvg:04e8c-s{number}" d="{data}"/>'


def test_the_strokes_come_in_the_official_order() -> None:
    assert strokes_from_svg(NI_SVG) == [[(30, 30), (80, 30)], [(10, 80), (100, 80)]]


@pytest.mark.parametrize(
    ("paths", "message"),
    [
        (stroke_path(1) + stroke_path(1), "appears twice"),
        (stroke_path(1) + stroke_path(3), "numbered 1 to 2"),
    ],
)
def test_a_stroke_numbering_with_a_gap_or_a_repeat_is_refused(paths: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        strokes_from_svg(SVG_TEMPLATE.format(paths))


def make_archive(path: Path) -> Path:
    one = SVG_TEMPLATE.format(stroke_path(1, "M10,50L90,50"))
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("kanji/04e8c.svg", NI_SVG)  # 二
        archive.writestr("kanji/04e00.svg", one)  # 一
        archive.writestr("kanji/04e00-Kaisho.svg", SVG_TEMPLATE.format(""))  # a variant
        archive.writestr("kanji/03042.svg", one)  # あ, not a kanji
    return path


def test_the_archive_gives_every_kanji_or_the_ones_asked(tmp_path: Path) -> None:
    archive = make_archive(tmp_path / "kanjivg.zip")

    assert list(read_kanjivg_zip(archive)) == ["一", "二"]
    assert list(read_kanjivg_zip(archive, ["二", "三"])) == ["二"]  # 三 is left to the caller


def test_the_prepared_file_keeps_the_source_and_the_licence(tmp_path: Path) -> None:
    path = tmp_path / "references.json"

    write_references(path, read_kanjivg_zip(make_archive(tmp_path / "kanjivg.zip")))

    source = json.loads(path.read_text("utf-8"))["source"]
    assert source["release"] == KANJIVG_RELEASE
    assert source["sha256"] == KANJIVG_SHA256
    assert source["license"] == KANJIVG_LICENSE == "CC BY-SA 3.0"
    assert "Ulrich Apel" in source["attribution"]


def test_the_references_load_once_and_prepare_each_kanji_once(tmp_path: Path) -> None:
    path = tmp_path / "references.json"
    write_references(path, read_kanjivg_zip(make_archive(tmp_path / "kanjivg.zip")))

    references = KanjiVGReferences.load(path)

    assert len(references) == 2
    assert "二" in references
    assert references.strokes("二") == [[(30, 30), (80, 30)], [(10, 80), (100, 80)]]
    prepared = references.prepared("二")
    assert prepared is not None
    assert prepared.count == 2
    assert references.prepared("二") is prepared
    assert references.prepared("三") is None
    assert references.strokes("三") is None


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"format": 99}, "format 99"),
        ({"source": {"release": "r20200101", "sha256": "0" * 64}}, "r20200101"),
    ],
)
def test_a_file_of_another_format_or_release_is_refused(
    tmp_path: Path, change: dict[str, object], message: str
) -> None:
    path = tmp_path / "references.json"
    write_references(path, {"一": [[(10, 50), (90, 50)]]})
    content = json.loads(path.read_text("utf-8"))
    path.write_text(json.dumps(content | change), "utf-8")

    with pytest.raises(ValueError, match=message):
        KanjiVGReferences.load(path)


def test_the_checksum_is_the_sha256_of_the_file(tmp_path: Path) -> None:
    path = tmp_path / "file"
    path.write_bytes(b"abc")

    assert sha256_of(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

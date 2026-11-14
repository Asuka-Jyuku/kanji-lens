import json
import re
from pathlib import Path
from typing import Any

import pytest

from kanjilens_ml.data.drawings import (
    WRITER_CODE,
    DrawingSetError,
    check_recognition_sample,
    coverage,
    import_batch,
    is_complete,
    parse_batch,
    read_class_list,
    sample_file_name,
    serialize_sample,
)

REPOSITORY = Path(__file__).resolve().parents[3]
FORMAT_SAMPLES = sorted((REPOSITORY / "backend" / "tests" / "fixtures" / "drawings").glob("*.json"))
RECOGNITION_SET = REPOSITORY / "ml" / "drawings" / "recognition"
CLASSES = ("日", "目")


def sample(kanji: str = "日", exported_at: str = "2026-11-13T15:30:45.123Z") -> dict[str, Any]:
    return {
        "format": "kanjilens-drawing",
        "version": 1,
        "exported_at": exported_at,
        "label": {"kanji": kanji, "stroke_order": "correct", "strokes": []},
        "request": {
            "stroke_order_mode": "unordered",
            "canvas": {"width": 320, "height": 320},
            "strokes": [[[10, 10, 0], [10.5, 90, 120]]],
        },
    }


def batch(*samples: dict[str, Any], writer: str = "a") -> dict[str, Any]:
    return {
        "format": "kanjilens-drawing-batch",
        "version": 1,
        "exported_at": "2026-11-13T16:00:00.000Z",
        "writer": writer,
        "samples": list(samples) or [sample()],
    }


@pytest.mark.parametrize("path", FORMAT_SAMPLES, ids=lambda path: path.name)
def test_a_drawing_is_written_as_the_frontend_writes_it(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    exported = json.loads(text)

    assert serialize_sample(exported) == text
    assert sample_file_name(exported) == path.name


def test_a_batch_is_checked_and_read() -> None:
    read = parse_batch(batch(sample("日"), sample("目"), writer="p2"), CLASSES)

    assert read.writer == "p2"
    assert [each["label"]["kanji"] for each in read.samples] == ["日", "目"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"format": "kanjilens-drawing"}, "kanjilens-drawing-batch"),
        ({"version": 2}, "version 1"),
        ({"writer": "Ana"}, "writer code"),
        ({"writer": "../a"}, "writer code"),
        ({"samples": []}, "no samples"),
        ({"samples": [sample("白")]}, "not in the class list"),
        ({"samples": [{**sample(), "format": "other"}]}, "kanjilens-drawing, version 1"),
        (
            {
                "samples": [
                    {**sample(), "label": {"kanji": "日", "stroke_order": "order", "strokes": [1]}}
                ]
            },
            "right order",
        ),
    ],
)
def test_a_batch_out_of_format_is_refused(change: dict[str, Any], message: str) -> None:
    with pytest.raises(DrawingSetError, match=re.escape(message)):
        parse_batch({**batch(), **change}, CLASSES)


def test_the_drawings_go_to_the_writer_folder_and_a_second_import_changes_nothing(
    tmp_path: Path,
) -> None:
    read = parse_batch(batch(sample("日"), sample("目"), writer="b"), CLASSES)

    first = import_batch(read, tmp_path)
    second = import_batch(read, tmp_path)

    names = sorted(path.name for path in (tmp_path / "b").iterdir())
    assert names == ["u65e5-correct-20261113T153045Z.json", "u76ee-correct-20261113T153045Z.json"]
    assert len(first.written) == 2 and first.skipped == ()
    assert second.written == () and set(second.skipped) == set(first.written)


def test_two_drawings_saved_in_the_same_second_both_stay(tmp_path: Path) -> None:
    same_second = (
        sample(exported_at="2026-11-13T15:30:45.100Z"),
        sample(exported_at="2026-11-13T15:30:45.900Z"),
    )

    import_batch(parse_batch(batch(*same_second), CLASSES), tmp_path)

    assert sorted(path.name for path in (tmp_path / "a").iterdir()) == [
        "u65e5-correct-20261113T153045Z-2.json",
        "u65e5-correct-20261113T153045Z.json",
    ]


def test_the_coverage_counts_each_class_by_writer_against_the_goal(tmp_path: Path) -> None:
    for writer, count in (("a", 2), ("b", 1)):
        drawings = [sample(exported_at=f"2026-11-13T15:30:4{i}.000Z") for i in range(count)]
        import_batch(parse_batch(batch(*drawings, writer=writer), CLASSES), tmp_path)

    counts = coverage(tmp_path)

    assert counts == {"日": {"a": 2, "b": 1}}
    assert is_complete(counts["日"], per_writer=1, writers=2)
    assert not is_complete(counts["日"], per_writer=2, writers=2)


def test_the_class_list_is_one_kanji_per_line_without_repeats(tmp_path: Path) -> None:
    path = tmp_path / "classes.txt"
    path.write_text("日\n\n目\n", encoding="utf-8")
    assert read_class_list(path) == ("日", "目")

    path.write_text("日\n日\n", encoding="utf-8")
    with pytest.raises(DrawingSetError, match="twice"):
        read_class_list(path)

    path.write_text("日目\n", encoding="utf-8")
    with pytest.raises(DrawingSetError, match="one kanji per line"):
        read_class_list(path)


def test_the_real_set_starts_with_40_classes() -> None:
    assert len(read_class_list(RECOGNITION_SET / "classes.txt")) == 40


@pytest.mark.parametrize(
    "path",
    sorted(RECOGNITION_SET.glob("*/*.json")),
    ids=lambda path: str(path.relative_to(RECOGNITION_SET)),
)
def test_every_drawing_of_the_real_set_is_a_class_drawn_right_in_a_writer_folder(
    path: Path,
) -> None:
    text = path.read_text(encoding="utf-8")
    drawing = check_recognition_sample(
        json.loads(text), read_class_list(RECOGNITION_SET / "classes.txt")
    )

    assert WRITER_CODE.fullmatch(path.parent.name)
    assert re.fullmatch(
        re.escape(sample_file_name(drawing)[: -len(".json")]) + r"(-\d+)?\.json", path.name
    )
    assert serialize_sample(drawing) == text

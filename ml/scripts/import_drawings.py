"""Imports the batches of the collection session into the real recognition set (#93, #100).

    uv run --directory ml python scripts/import_drawings.py [BATCH ...]

Each batch ("Baixar lote" in the development build) is checked against the class list,
drawings/recognition/classes.txt, and split into one file per drawing in
drawings/recognition/<writer>/. Importing a batch twice changes nothing. Then it prints how
many drawings each class has, by writer, against the goal: --per-writer drawings from each of
--writers people (ADR 0022). Without a batch, it only prints. Exits with 1 when a batch does
not follow the format; nothing of that batch is written.
"""

import argparse
import json
import sys
from pathlib import Path

from kanjilens_ml.data.drawings import (
    DrawingSetError,
    coverage,
    import_batch,
    is_complete,
    parse_batch,
    read_class_list,
)

RECOGNITION_SET = Path(__file__).resolve().parents[1] / "drawings" / "recognition"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("batches", type=Path, nargs="*", help="batch files to import")
    parser.add_argument("--set", type=Path, default=RECOGNITION_SET, dest="root")
    parser.add_argument("--per-writer", type=int, default=5)
    parser.add_argument("--writers", type=int, default=3)
    arguments = parser.parse_args()
    root: Path = arguments.root
    classes = read_class_list(root / "classes.txt")

    for path in arguments.batches:
        try:
            batch = parse_batch(json.loads(path.read_text(encoding="utf-8")), classes)
        except (DrawingSetError, json.JSONDecodeError) as error:
            print(f"{path}: {error}", file=sys.stderr)
            return 1
        result = import_batch(batch, root)
        print(
            f"{path.name}: {len(result.written)} written, {len(result.skipped)} already there, "
            f"in {(root / batch.writer).relative_to(root.parent.parent)}/"
        )

    counts = coverage(root)
    writers = sorted({writer for by_writer in counts.values() for writer in by_writer})
    print(f"\nGoal: {arguments.per_writer} drawings from each of {arguments.writers} people.")
    print("kanji  total  " + "  ".join(f"{writer:>4}" for writer in writers))
    done = 0
    for kanji in classes:
        by_writer = counts.get(kanji, {})
        complete = is_complete(by_writer, arguments.per_writer, arguments.writers)
        done += complete
        cells = "  ".join(f"{by_writer.get(writer, 0):>4}" for writer in writers)
        print(f"{kanji}     {sum(by_writer.values()):>5}  {cells}  {'done' if complete else ''}")
    print(f"{done} of {len(classes)} classes reached the goal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

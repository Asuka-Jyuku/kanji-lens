"""Prepares the KanjiVG reference strokes of the stroke-order check (ADR 0016).

Downloads the pinned KanjiVG release (once; kept in ml/datasets/kanjivg/), checks its SHA-256,
and writes the reference strokes, with the attribution and licence they keep (CC BY-SA 3.0),
to ml/artifacts/kanjivg/. Both folders are outside git.

    uv run --directory ml python scripts/prepare_kanjivg.py [--classes FILE]

--classes: a text file with one kanji per line (the class list); without it, every kanji in
KanjiVG is prepared. Exits with 1 when the checksum does not match or a class is missing.
"""

import argparse
import shutil
import sys
import urllib.request
from pathlib import Path

from kanjilens_ml.stroke_order.kanjivg import (
    KANJIVG_ATTRIBUTION,
    KANJIVG_FILE,
    KANJIVG_LICENSE,
    KANJIVG_RELEASE,
    KANJIVG_SHA256,
    KANJIVG_URL,
    REFERENCES_FILE,
    read_kanjivg_zip,
    sha256_of,
    write_references,
)

ML_ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = ML_ROOT / "datasets" / "kanjivg"
OUTPUT_DIR = ML_ROOT / "artifacts" / "kanjivg"

NOTICE = f"""# KanjiVG reference strokes

`{REFERENCES_FILE}` is derived from KanjiVG {KANJIVG_RELEASE} (`{KANJIVG_FILE}`,
SHA-256 `{KANJIVG_SHA256}`) by `ml/scripts/prepare_kanjivg.py`.

KanjiVG is copyright Ulrich Apel and released under the Creative Commons
Attribution-Share Alike 3.0 licence ({KANJIVG_LICENSE}):
https://kanjivg.tagaini.net and https://creativecommons.org/licenses/by-sa/3.0/

This derived data keeps the same licence and attribution, apart from the MIT licence of the
KanjiLens code. {KANJIVG_ATTRIBUTION}.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--classes", type=Path, help="one kanji per line; default: every kanji")
    parser.add_argument("--archive", type=Path, default=DOWNLOAD_DIR / KANJIVG_FILE)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    arguments = parser.parse_args()

    archive: Path = arguments.archive
    if not archive.exists():
        print(f"Downloading {KANJIVG_URL}")
        archive.parent.mkdir(parents=True, exist_ok=True)
        partial = archive.with_suffix(".part")
        with urllib.request.urlopen(KANJIVG_URL, timeout=60) as response, partial.open("wb") as f:
            shutil.copyfileobj(response, f)
        partial.replace(archive)

    digest = sha256_of(archive)
    if digest != KANJIVG_SHA256:
        print(f"{archive}: SHA-256 {digest}, expected {KANJIVG_SHA256}", file=sys.stderr)
        return 1

    classes = None
    if arguments.classes is not None:
        lines = arguments.classes.read_text("utf-8").splitlines()
        classes = [line.strip() for line in lines if line.strip()]
    references = read_kanjivg_zip(archive, classes)

    output: Path = arguments.output
    write_references(output / REFERENCES_FILE, references)
    (output / "README.md").write_text(NOTICE, "utf-8")
    print(f"{len(references)} kanji written to {output / REFERENCES_FILE}")

    missing = sorted(set(classes or []) - references.keys())
    if missing:
        print(f"Not in KanjiVG {KANJIVG_RELEASE}: {' '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

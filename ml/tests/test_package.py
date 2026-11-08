from pathlib import Path

import kanjilens_ml

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_package_version_matches_repository_version() -> None:
    # The version lives only in VERSION; the package must follow it (ADR 0008).
    expected = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()

    assert kanjilens_ml.__version__ == expected

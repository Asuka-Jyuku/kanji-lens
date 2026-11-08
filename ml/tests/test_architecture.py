from pathlib import Path

from importlinter.cli import lint_imports

ML_ROOT = Path(__file__).resolve().parents[1]


def test_import_contracts_are_kept() -> None:
    # Fails when an import breaks the dependency rule (CLAUDE.md, "Testes").
    exit_code = lint_imports(config_filename=str(ML_ROOT / "pyproject.toml"))

    assert exit_code == 0

"""Import contracts that keep ground truth out of the system under test."""

from importlinter.cli import lint_imports


def test_import_contracts_hold() -> None:
    assert lint_imports(no_cache=True, no_logo=True) == 0

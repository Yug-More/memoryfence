import tomllib
from importlib.metadata import metadata, version
from pathlib import Path

import memoryfence

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_version_matches_installed_metadata() -> None:
    assert memoryfence.__version__ == version("memoryfence")


def test_installed_version_matches_pyproject() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert memoryfence.__version__ == pyproject["project"]["version"]


def test_public_api_is_explicit() -> None:
    assert memoryfence.__all__ == ["__version__"]


def test_package_is_marked_as_typed() -> None:
    package_dir = Path(memoryfence.__file__).parent
    assert (package_dir / "py.typed").is_file()


def test_phase_one_declares_no_runtime_dependencies() -> None:
    assert metadata("memoryfence").get_all("Requires-Dist") is None

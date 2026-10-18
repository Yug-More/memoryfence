import re
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


def test_runtime_dependencies_are_the_phase_two_foundation() -> None:
    """Pydantic and SQLAlchemy are the only runtime dependencies, added with Phase 2."""
    requires = metadata("memoryfence").get_all("Requires-Dist")
    assert requires is not None
    names = sorted(
        re.split(r"[^A-Za-z0-9_.-]", requirement, maxsplit=1)[0] for requirement in requires
    )
    assert names == ["pydantic", "sqlalchemy"]

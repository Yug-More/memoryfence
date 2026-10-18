"""MemoryFence: evaluating persistent memory poisoning in collaborative AI agents.

The package contains the domain model, authorization, persistence, provenance, a
deterministic scripted agent simulation, an offline demo, a scripted scenario
benchmark, the protocol defense conditions, and a scripted experiment runner.
Empirical language-model evaluation is not implemented here.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("memoryfence")
except PackageNotFoundError as exc:  # pragma: no cover - only reachable from an uninstalled tree
    raise ImportError(
        "memoryfence package metadata not found; install the project with `uv sync`."
    ) from exc

__all__ = ["__version__"]

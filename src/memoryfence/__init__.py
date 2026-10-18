"""MemoryFence: evaluating persistent memory poisoning in collaborative AI agents.

Phase 1 provides package metadata only. The domain model, memory pipeline, attack scenarios,
defenses, and evaluation harness are specified in ``docs/`` and are not implemented yet.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("memoryfence")
except PackageNotFoundError as exc:  # pragma: no cover - only reachable from an uninstalled tree
    raise ImportError(
        "memoryfence package metadata not found; install the project with `uv sync`."
    ) from exc

__all__ = ["__version__"]

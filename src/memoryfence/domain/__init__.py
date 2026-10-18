"""Validated, immutable domain vocabulary shared by every MemoryFence module.

This package has no internal imports, so every other module can depend on it.
Persistence mappings live in :mod:`memoryfence.storage` and are never exposed as
domain objects.
"""

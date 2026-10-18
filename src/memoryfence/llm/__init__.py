"""Deterministic model backend.

The scripted backend is a mechanism fixture. It does not demonstrate language-model
behavior, and it has no network access and no path to evaluator-only ground truth.
"""

from memoryfence.llm.backend import ScriptedBackend, ScriptedReply

__all__ = ["ScriptedBackend", "ScriptedReply"]

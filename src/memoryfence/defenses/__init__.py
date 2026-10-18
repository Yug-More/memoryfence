"""Protocol defense conditions DF0-DF5.

Decisions use recorded provenance, instruction authority, and the requester's task.
They do not read true provenance or scenario labels. Scripted outcomes are fixture
results, not evidence that a defense works on a language model.
"""

from memoryfence.defenses.suite import DefenseSuite

__all__ = ["DefenseSuite"]

"""Workspace services: directory, sources, memories, deletion, and tool decisions.

These services are the system under test. They record ground truth only through the
write-only recorder on the unit of work, and they never read it back.
"""

"""Pure directed-acyclic-graph utilities over ``child -> parents`` edges."""

from collections.abc import Callable, Iterable, Mapping

from memoryfence.domain.errors import ProvenanceIntegrityError, ReasonCode


def descendants[Node: str](
    roots: Iterable[Node], children_of: Callable[[Node], Iterable[Node]]
) -> set[Node]:
    """Every node reachable from ``roots`` by following child edges, excluding roots."""
    start = set(roots)
    seen: set[Node] = set()
    frontier = list(start)
    while frontier:
        node = frontier.pop()
        for child in children_of(node):
            if child not in seen and child not in start:
                seen.add(child)
                frontier.append(child)
    return seen


def topological_order[Node: str](parents: Mapping[Node, Iterable[Node]]) -> list[Node]:
    """Order nodes so every parent precedes its children; ties break by identifier.

    Only parents that are themselves keys of ``parents`` constrain the order.
    Raises :class:`ProvenanceIntegrityError` if the subgraph contains a cycle.
    """
    remaining = {
        node: {parent for parent in node_parents if parent in parents}
        for node, node_parents in parents.items()
    }
    order: list[Node] = []
    while remaining:
        ready = sorted(node for node, pending in remaining.items() if not pending)
        if not ready:
            raise ProvenanceIntegrityError(ReasonCode.LINEAGE_CYCLE, "provenance contains a cycle")
        for node in ready:
            order.append(node)
            del remaining[node]
        for pending in remaining.values():
            pending.difference_update(ready)
    return order


def would_create_cycle[Node: str](
    child: Node, parents: Iterable[Node], ancestors_of: Callable[[Node], set[Node]]
) -> bool:
    """True if adding ``child -> parent`` edges would make ``child`` its own ancestor."""
    return any(parent == child or child in ancestors_of(parent) for parent in parents)

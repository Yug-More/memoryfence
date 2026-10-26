"""Exhaustive mechanical chain sensitivity; no model or database execution."""

import argparse
import json
from pathlib import Path
from typing import TypedDict

from memoryfence.provenance.graph import descendants

DEPTHS = (1, 2, 4, 8)


class ChainRow(TypedDict):
    depth: int
    mask: int
    retained_edges: int
    reached_ids: list[str]
    source_only_survivors: int
    cascade_survivors: int


def enumerate_chains() -> dict[str, object]:
    rows: list[ChainRow] = []
    groups = []
    for depth in DEPTHS:
        for mask in range(1 << depth):
            children: dict[str, list[str]] = {str(i): [] for i in range(depth + 1)}
            for i in range(depth):
                if mask & (1 << i):
                    children[str(i)].append(str(i + 1))
            reached = sorted(descendants(["0"], children.__getitem__), key=int)
            prefix = 0
            while prefix < depth and mask & (1 << prefix):
                prefix += 1
            expected = [str(i) for i in range(1, prefix + 1)]
            if reached != expected:
                raise ValueError(f"traversal disagrees with independent prefix: {depth}/{mask}")
            rows.append(
                {
                    "depth": depth,
                    "mask": mask,
                    "retained_edges": mask.bit_count(),
                    "reached_ids": reached,
                    "source_only_survivors": depth,
                    "cascade_survivors": depth - len(reached),
                }
            )
        for count in range(depth + 1):
            subset = [r for r in rows if r["depth"] == depth and r["retained_edges"] == count]
            survivors = [r["cascade_survivors"] for r in subset]
            groups.append(
                {
                    "depth": depth,
                    "retained_edges": count,
                    "masks": len(subset),
                    "min_survivors": min(survivors),
                    "max_survivors": max(survivors),
                    "sum_survivors": sum(survivors),
                }
            )
    return {
        "schema_version": 1,
        "classification": "exhaustive abstract graph sensitivity",
        "model_calls": 0,
        "configurations": len(rows),
        "depths": list(DEPTHS),
        "rows": rows,
        "groups": groups,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(enumerate_chains(), indent=2) + "\n")


if __name__ == "__main__":
    main()

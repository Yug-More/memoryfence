"""Verify immutable Original Study bytes without importing production code."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify() -> int:
    manifest = json.loads((ROOT / "experiments/legacy_baseline/manifest.json").read_text())
    for item in manifest["files"]:
        path = ROOT / item["path"]
        if not path.is_file():
            raise ValueError(f"missing historical file: {item['path']}")
        data = path.read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError(f"historical bytes changed: {item['path']}")
    return len(manifest["files"])


if __name__ == "__main__":
    print(f"preserved Original Study files: {verify()}; no inference executed")

"""Verify both immutable studies; no inference or production scorer imports."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify() -> dict[str, int]:
    result = {}
    for name, filename in (
        ("original", "manifest.json"),
        ("expanded", "expanded-v1-manifest.json"),
    ):
        manifest = json.loads((ROOT / "experiments/legacy_baseline" / filename).read_text())
        for item in manifest["files"]:
            path = ROOT / item["path"]
            data = path.read_bytes()
            if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError(f"preserved study changed: {item['path']}")
        result[name] = len(manifest["files"])
    return result


if __name__ == "__main__":
    print(json.dumps({"preserved_files": verify(), "new_inference": False}, sort_keys=True))

"""Canonical JSON encoding used for hashing, seeds, and persisted structured data."""

import hashlib
import json

from pydantic import JsonValue


def canonical_json(value: JsonValue) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

"""Durable local HTTP evidence, including unsuccessful and malformed responses.

Only use with synthetic scenarios. These logs contain the full prompt and output.
A journal is evidence supplied by the execution environment, not independent proof
of model execution. Request entries without a response identify interrupted calls.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from memoryfence.domain.errors import ModelBackendError
from memoryfence.llm.transport import HttpTransport


class RecordingTransport:
    def __init__(self, transport: HttpTransport, path: Path) -> None:
        self._transport = transport
        self._path = path
        self._sequence = 0

    def request(
        self, method: str, url: str, payload: bytes | None, timeout: float
    ) -> tuple[int, bytes]:
        self._sequence += 1
        sequence = self._sequence
        self._append(
            {
                "event": "request",
                "sequence": sequence,
                "method": method,
                "url": url,
                "payload": None if payload is None else payload.decode("utf-8"),
                "timeout_seconds": timeout,
            }
        )
        try:
            status, raw = self._transport.request(method, url, payload, timeout)
        except ModelBackendError as error:
            self._append({"event": "error", "sequence": sequence, "reason": error.code.value})
            raise
        self._append(
            {
                "event": "response",
                "sequence": sequence,
                "status": status,
                "body": raw.decode("utf-8", errors="replace"),
            }
        )
        return status, raw

    def _append(self, data: dict[str, object]) -> None:
        data["recorded_at_utc"] = datetime.now(UTC).isoformat()
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(data, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

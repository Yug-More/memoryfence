"""HTTP for the local model. Redirects are not followed. Proxies are not used."""

import json
import urllib.error
import urllib.request
from typing import Protocol
from urllib.parse import urlsplit

from memoryfence.domain.errors import ModelBackendError, ReasonCode
from memoryfence.llm.endpoint import require_loopback

_MAX_BYTES = 65_536


class HttpTransport(Protocol):
    def request(
        self, method: str, url: str, payload: bytes | None, timeout: float
    ) -> tuple[int, bytes]: ...


class _RefuseRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        raise ModelBackendError(ReasonCode.MODEL_UNAVAILABLE, "the model endpoint redirected")


class UrllibTransport:
    """Talks only to the loopback URL checked for this call."""

    def request(
        self, method: str, url: str, payload: bytes | None, timeout: float
    ) -> tuple[int, bytes]:
        parsed = urlsplit(url)
        if parsed.path not in {"/api/chat", "/api/show", "/api/version", "/api/tags"}:
            raise ModelBackendError(ReasonCode.MODEL_UNAVAILABLE, "that model path is not used")
        origin = f"{parsed.scheme}://{parsed.netloc}"
        base = require_loopback(origin)
        target = base + parsed.path
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            _RefuseRedirect(),
        )
        request = urllib.request.Request(  # noqa: S310
            target,
            data=payload,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with opener.open(request, timeout=timeout) as response:
                status = int(response.status)
                body = response.read(_MAX_BYTES + 1)
        except ModelBackendError:
            raise
        except TimeoutError as error:
            raise ModelBackendError(ReasonCode.MODEL_TIMEOUT, "model request timed out") from error
        except urllib.error.HTTPError as error:
            detail = error.read(_MAX_BYTES + 1)
            if b"out of memory" in detail.lower():
                raise ModelBackendError(
                    ReasonCode.MODEL_UNAVAILABLE, "the model ran out of memory"
                ) from error
            raise ModelBackendError(
                ReasonCode.MODEL_UNAVAILABLE, "the local model request failed"
            ) from error
        except urllib.error.URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise ModelBackendError(
                    ReasonCode.MODEL_TIMEOUT, "the model request timed out"
                ) from error
            raise ModelBackendError(
                ReasonCode.MODEL_UNAVAILABLE, "the local model is not reachable"
            ) from error
        if len(body) > _MAX_BYTES:
            raise ModelBackendError(ReasonCode.MODEL_OUTPUT, "the model response is too large")
        return status, body


def decode_json(body: bytes) -> dict[str, object]:
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as error:
        raise ModelBackendError(ReasonCode.MODEL_OUTPUT, "model response is not JSON") from error
    if not isinstance(parsed, dict):
        raise ModelBackendError(ReasonCode.MODEL_OUTPUT, "the model response is not an object")
    return parsed

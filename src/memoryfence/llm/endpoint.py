"""Loopback-only endpoint checks. A scenario cannot choose the model host."""

import ipaddress
import socket
from urllib.parse import urlsplit

from memoryfence.domain.errors import DomainValidationError

_NAMES = frozenset({"127.0.0.1", "localhost", "::1"})


def require_loopback(url: str) -> str:
    """Return a URL whose host resolved to loopback. Reject everything else."""
    parsed = urlsplit(url)
    host = parsed.hostname
    if parsed.scheme != "http" or host is None or host not in _NAMES:
        raise DomainValidationError("the model endpoint must be http on loopback")
    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise DomainValidationError("the model endpoint must be http on loopback")
    port = 80 if parsed.port is None else parsed.port
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as error:
        raise DomainValidationError("the model endpoint must be http on loopback") from error
    addresses = [item[4][0] for item in infos]
    if not addresses:
        raise DomainValidationError("the model endpoint must be http on loopback")
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as error:
            raise DomainValidationError("the model endpoint must be http on loopback") from error
        if not ip.is_loopback:
            raise DomainValidationError("the model endpoint must be http on loopback")
    chosen = str(addresses[0])
    literal = f"[{chosen}]" if ":" in chosen else chosen
    path = parsed.path or ""
    if path not in {"", "/"}:
        raise DomainValidationError("the model endpoint must be http on loopback")
    return f"http://{literal}:{port}"

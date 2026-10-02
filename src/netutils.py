# MIT License
#
# Copyright (c) 2024 carpaty https://github.com/carpaty
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -*- coding: utf-8 -*-

"""
Network helpers for user supplied targets.

Every target typed by a user is resolved and rejected when it points to a
private, loopback, link-local or otherwise non-public address, so the bot
cannot be used to probe the hosting network (e.g. the cloud metadata server).
"""

import asyncio
import contextlib
import http.client
import ipaddress
import re
import socket
import ssl
from datetime import datetime, timezone
from urllib import error, request
from urllib.parse import urlsplit

MAX_PORTS = 100
CONNECT_TIMEOUT = 1.0
HTTP_TIMEOUT = 10
SCAN_CONCURRENCY = 50
USER_AGENT = "ITB-Monitor/1.0 (+https://github.com/carpaty/itb)"

HOST_RE = re.compile(
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,63}\.?|[A-Z0-9-]{2,}\.?)'
    r'|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
    re.IGNORECASE)


class UnsafeTargetError(ValueError):
    """Raised when a target cannot be resolved or resolves to a non-public address."""


def is_public_ip(address: str) -> bool:
    """
    Check whether an IP address is globally routable.

    :param address: IPv4 or IPv6 address
    :type address: str
    :return: True if the address is public
    :rtype: bool
    """
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def resolve_public(host: str) -> list[str]:
    """
    Resolve a host name and make sure every address is public.

    :param host: Host name or IP address
    :type host: str
    :raises UnsafeTargetError: if the host cannot be resolved or is not public
    :return: Resolved addresses
    :rtype: list[str]
    """
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except (OSError, UnicodeError) as err:
        raise UnsafeTargetError(f"cannot resolve {host}") from err
    addresses = sorted({info[4][0] for info in infos})
    if not addresses or not all(is_public_ip(address) for address in addresses):
        raise UnsafeTargetError(f"{host} is not a public address")
    return addresses


def parse_ports(spec: str, limit: int = MAX_PORTS) -> list[int]:
    """
    Parse a port specification such as ``22,80,8000-8010``.

    :param spec: Comma separated ports or port ranges
    :type spec: str
    :param limit: Maximum number of ports allowed
    :type limit: int
    :raises ValueError: if the specification is invalid or too large
    :return: Sorted unique ports
    :rtype: list[int]
    """
    ports: set[int] = set()
    for chunk in str(spec).split(","):
        start_s, _, end_s = chunk.strip().partition("-")
        try:
            start = int(start_s)
            end = int(end_s) if end_s else start
        except ValueError as err:
            raise ValueError(f"invalid port: {chunk.strip()}") from err
        if not 1 <= start <= end <= 65535:
            raise ValueError(f"invalid port range: {chunk.strip()}")
        if end - start + 1 + len(ports) > limit:
            raise ValueError(f"too many ports, maximum is {limit}")
        ports.update(range(start, end + 1))
    return sorted(ports)


async def _probe(address: str, port: int, semaphore: asyncio.Semaphore) -> str:
    async with semaphore:
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(address, port), CONNECT_TIMEOUT)
        except OSError:
            return "closed"
        writer.close()
        with contextlib.suppress(OSError):
            await writer.wait_closed()
        return "open"


async def scan_ports(host: str, ports: list[int]) -> dict[int, str]:
    """
    Check which TCP ports of a public host accept connections.

    :param host: Host name or IP address
    :type host: str
    :param ports: Ports to probe
    :type ports: list[int]
    :raises UnsafeTargetError: if the host is not public
    :return: Mapping of port to ``open`` or ``closed``
    :rtype: dict[int, str]
    """
    address = (await asyncio.to_thread(resolve_public, host))[0]
    semaphore = asyncio.Semaphore(SCAN_CONCURRENCY)
    results = await asyncio.gather(*(_probe(address, port, semaphore) for port in ports))
    return dict(zip(ports, results))


class _NoRedirect(request.HTTPRedirectHandler):
    """Redirect targets are not re-validated, so redirects are never followed."""

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = request.build_opener(_NoRedirect)


def check_url(url: str, timeout: float = HTTP_TIMEOUT) -> str | None:
    """
    Check that a public web site answers without an error status.

    Redirects (3xx) count as the site being up.

    :param url: http(s) URL
    :type url: str
    :param timeout: Request timeout in seconds
    :type timeout: float
    :return: None if the site is up, otherwise a short failure reason
    :rtype: str | None
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return "unsupported URL"
    try:
        resolve_public(parts.hostname)
    except UnsafeTargetError as err:
        return str(err)
    req = request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with _OPENER.open(req, timeout=timeout):
            return None
    except error.HTTPError as err:
        err.close()
        return None if err.code < 400 else str(err.code)
    except error.URLError as err:
        return str(err.reason)
    except (OSError, ValueError, http.client.HTTPException) as err:
        return str(err) or type(err).__name__


def _name(rdns) -> str:
    fields = dict(item for rdn in rdns for item in rdn)
    return fields.get("commonName") or fields.get("organizationName") or "-"


def certificate_info(host: str, port: int = 443, timeout: float = HTTP_TIMEOUT) -> dict:
    """
    Fetch and verify the TLS certificate of a public host.

    :param host: Host name
    :type host: str
    :param port: TLS port
    :type port: int
    :param timeout: Connection timeout in seconds
    :type timeout: float
    :raises UnsafeTargetError: if the host is not public
    :raises ssl.SSLCertVerificationError: if the certificate is not trusted
    :return: Certificate summary
    :rtype: dict
    """
    address = resolve_public(host)[0]
    context = ssl.create_default_context()
    with socket.create_connection((address, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=host) as tls:
            cert = tls.getpeercert()
            version = tls.version()
    not_before = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notBefore"]), tz=timezone.utc)
    not_after = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), tz=timezone.utc)
    return {
        "subject": _name(cert.get("subject", ())),
        "issuer": _name(cert.get("issuer", ())),
        "not_before": not_before,
        "not_after": not_after,
        "days_left": (not_after - datetime.now(timezone.utc)).days,
        "san": [value for kind, value in cert.get("subjectAltName", ()) if kind == "DNS"],
        "version": version,
    }

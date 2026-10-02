"""Tests for netutils."""

import asyncio

import pytest

import netutils


@pytest.mark.parametrize("spec, expected", [
    ("80", [80]),
    ("443,80,80", [80, 443]),
    ("20-22,53", [20, 21, 22, 53]),
    (" 22 , 8000-8001 ", [22, 8000, 8001]),
])
def test_parse_ports(spec, expected):
    """Valid specifications are expanded and de-duplicated."""
    assert netutils.parse_ports(spec) == expected


@pytest.mark.parametrize("spec", ["", "abc", "0", "65536", "30-20", "1-65535", "1-50,60-120", "80,"])
def test_parse_ports_rejects_invalid(spec):
    """Invalid or oversized specifications raise ValueError."""
    with pytest.raises(ValueError):
        netutils.parse_ports(spec)


@pytest.mark.parametrize("address", [
    "127.0.0.1", "10.1.2.3", "172.16.0.1", "192.168.1.1", "169.254.169.254",
    "100.64.0.1", "0.0.0.0", "224.0.0.1", "::1", "fe80::1", "fd00::1", "::ffff:127.0.0.1",
])
def test_resolve_public_rejects_internal(address):
    """Internal addresses are never allowed as targets."""
    with pytest.raises(netutils.UnsafeTargetError):
        netutils.resolve_public(address)


def test_resolve_public_accepts_public_ip():
    """Public IP literals resolve to themselves."""
    assert netutils.resolve_public("8.8.8.8") == ["8.8.8.8"]


def test_resolve_public_rejects_unresolvable(monkeypatch):
    """Resolution failures are reported as unsafe targets."""
    def fail(*_args, **_kwargs):
        raise OSError("no such host")
    monkeypatch.setattr(netutils.socket, "getaddrinfo", fail)
    with pytest.raises(netutils.UnsafeTargetError):
        netutils.resolve_public("nonexistent.example")


@pytest.mark.parametrize("url", ["ftp://8.8.8.8/", "file:///etc/passwd", "http://127.0.0.1/", "http://[::1]:8080/"])
def test_check_url_blocks_unsafe_targets(url):
    """Unsupported schemes and internal hosts are refused before any request."""
    assert netutils.check_url(url) is not None


def test_scan_ports_reports_open_and_closed(monkeypatch):
    """A listening port is open and an unused one is closed."""
    monkeypatch.setattr(netutils, "resolve_public", lambda host: ["127.0.0.1"])

    async def run():
        server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
        open_port = server.sockets[0].getsockname()[1]
        async with server:
            closed_port = open_port + 1 if open_port < 65535 else open_port - 1
            return open_port, closed_port, await netutils.scan_ports("test", [open_port, closed_port])

    open_port, closed_port, res = asyncio.run(run())
    assert res[open_port] == "open"
    assert res[closed_port] == "closed"

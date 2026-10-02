"""Tests for the custom calls example."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import db
import utils
from calls import button_func


def callback_update(data, uid=42):
    """Build a minimal callback query update."""
    query = SimpleNamespace(data=data, answer=AsyncMock(), edit_message_text=AsyncMock())
    return SimpleNamespace(callback_query=query, effective_user=SimpleNamespace(id=uid))


@pytest.mark.parametrize("url, valid", [
    ("https://example.com", True),
    ("http://sub.example.co.uk:8080/path?q=1", True),
    ("https://example.technology", True),
    ("ftp://example.com", False),
    ("https://localhost", False),
    ("javascript:alert(1)", False),
    ("https://example.com/" + "a" * 600, False),
])
def test_validate_url(url, valid):
    """Only public-looking http(s) URLs are accepted."""
    assert button_func.validate_url(url) is valid


@pytest.mark.parametrize("value, valid", [
    ("example.com 80,443 open", True),
    ("1.2.3.4 20-22 closed", True),
    ("example.com 80 filtered", False),
    ("example.com open", False),
    ("example.com 80 open; rm -rf /", False),
])
def test_validate_host_ports(value, valid):
    """Host monitoring input must be host, ports and state."""
    assert button_func.validate_host_ports(value) is valid


def test_site_add_keeps_long_urls_out_of_callback_data(cache, monkeypatch):
    """Callback data stays within Telegram's 64 byte limit for any URL."""
    monkeypatch.setattr(button_func, "site_list_db", lambda uid: [])
    url = "https://example.com/" + "a" * 200
    _, markup = button_func.site_add(42, url)
    for button in markup.inline_keyboard[0]:
        assert len(button.callback_data.encode()) <= 64
    assert cache.data["pending_42"] == {"action": "siteadd", "data": url}


def test_site_add_enforces_limit(cache, monkeypatch):
    """Users cannot add more sites than the configured limit."""
    monkeypatch.setattr(button_func, "site_list_db", lambda uid: [{}] * button_func.MAX_ITEMS_PER_USER)
    text, markup = button_func.site_add(42, "https://example.com")
    assert markup is None
    assert "up to" in text
    assert not cache.data


def test_confirmation_runs_pending_action(cache, monkeypatch):  # pylint: disable=unused-argument
    """Pressing Yes runs the stored action once."""
    added = []
    monkeypatch.setattr(button_func, "site_add_db", lambda uid, data: added.append((uid, data)) or True)
    monkeypatch.setitem(button_func.CONFIRM_ACTIONS, "siteadd", button_func.siteadd)
    utils.update_pending(42, "siteadd", "https://example.com/a_b")

    update = callback_update("inftrx_siteadd_yes")
    asyncio.run(button_func.button_int(update, None))
    asyncio.run(button_func.button_int(update, None))

    assert added == [(42, "https://example.com/a_b")]
    texts = [call.kwargs["text"] for call in update.callback_query.edit_message_text.call_args_list]
    assert "has been added" in texts[0]
    assert "expired" in texts[1]


@pytest.mark.parametrize("data", ["inftrx_worker_yes", "inftrx_nmap_host_yes", "inftrx_", "inftrx_sitedel_yes"])
def test_forged_callbacks_are_rejected(cache, data):
    """Callback data cannot invoke arbitrary functions or actions that were not offered."""
    utils.update_pending(42, "siteadd", "https://example.com")
    update = callback_update(data)
    asyncio.run(button_func.button_int(update, None))
    assert "expired" in update.callback_query.edit_message_text.call_args.kwargs["text"]
    assert cache.data["pending_42"]["action"] == "siteadd"


def test_qdelete_passes_key(monkeypatch):
    """Datastore delete must receive a Key, not an Entity."""
    client = MagicMock()
    client.key.side_effect = lambda kind, name: ("key", kind, name)
    monkeypatch.setattr(db, "get_client", lambda: client)
    button_func.Sql().qdelete("Sites", 42, "https://example.com")
    client.delete.assert_called_once_with(("key", "Sites", "42_https://example.com"))


def test_check_site_recovers_after_transient_failure(monkeypatch):
    """A successful retry clears the earlier failure instead of alerting."""
    results = iter(["503", None])
    monkeypatch.setattr(button_func.netutils, "check_url", lambda url: next(results))
    monkeypatch.setattr(button_func.asyncio, "sleep", AsyncMock())
    assert asyncio.run(button_func.check_site("https://example.com")) is None


def test_check_site_reports_persistent_failure(monkeypatch):
    """A site failing every attempt is reported."""
    monkeypatch.setattr(button_func.netutils, "check_url", lambda url: "503")
    monkeypatch.setattr(button_func.asyncio, "sleep", AsyncMock())
    assert asyncio.run(button_func.check_site("https://example.com")) == "503"


def test_monitor_host_alerts_on_unexpected_state(monkeypatch):
    """Only ports that differ from the expected state are reported."""
    monkeypatch.setattr(button_func.netutils, "scan_ports", AsyncMock(return_value={80: "open", 443: "closed"}))
    notify = AsyncMock()
    monkeypatch.setattr(button_func, "notify", notify)
    host = {"Hosts": "example.com", "port": "80,443", "state": "open", "uid": 42}
    asyncio.run(button_func.monitor_host(host, asyncio.Semaphore(1)))
    uid, text = notify.call_args.args
    assert uid == 42
    assert "443" in text and "80:" not in text


@pytest.mark.parametrize("data, expected", [
    ("example.com", ("example.com", 443)),
    ("Example.com:8443", ("example.com", 8443)),
    ("https://example.com/path", ("example.com", 443)),
])
def test_parse_tls_target(data, expected):
    """TLS targets accept host, host:port and URLs."""
    assert button_func.parse_tls_target(data) == expected


@pytest.mark.parametrize("data", ["", "not a host", "example.com:99999"])
def test_parse_tls_target_rejects_invalid(data):
    """Invalid TLS targets raise ValueError."""
    with pytest.raises(ValueError):
        button_func.parse_tls_target(data)


def test_scan_host_rejects_internal_target():
    """The scanner refuses internal addresses."""
    text, _ = asyncio.run(button_func.scan_host(42, "127.0.0.1 22"))
    assert "not a public address" in text

"""Tests for the HTTP endpoints."""

from unittest.mock import AsyncMock

import pytest
import telegram
from fastapi.testclient import TestClient

import main
import utils

API_KEY = "0123456789abcdef0123456789abcdef"


@pytest.fixture(name="client")
def fixture_client():
    """Test client without lifespan, so no Telegram calls are made."""
    return TestClient(main.app)


def test_webhook_requires_secret(client):
    """Updates without the Telegram secret header are rejected."""
    assert client.post("/webhook", json={"update_id": 1}).status_code == 403
    headers = {"X-Telegram-Bot-Api-Secret-Token": "wrong"}
    assert client.post("/webhook", json={"update_id": 1}, headers=headers).status_code == 403


def test_webhook_accepts_valid_update(client):
    """Updates with the secret header are queued."""
    headers = {"X-Telegram-Bot-Api-Secret-Token": utils.WEBHOOK_SECRET}
    before = main.app_.update_queue.qsize()
    assert client.post("/webhook", json={"update_id": 1}, headers=headers).status_code == 200
    assert main.app_.update_queue.qsize() == before + 1


def test_webhook_rejects_invalid_json(client):
    """Malformed bodies return 400 instead of 500."""
    headers = {"X-Telegram-Bot-Api-Secret-Token": utils.WEBHOOK_SECRET, "Content-Type": "application/json"}
    assert client.post("/webhook", content=b"{", headers=headers).status_code == 400


def test_cron_requires_app_engine_header(client, monkeypatch):
    """Only App Engine cron can trigger the worker."""
    worker = AsyncMock()
    monkeypatch.setattr(main, "worker", worker)
    assert client.get("/cron").status_code == 403
    worker.assert_not_awaited()
    assert client.get("/cron", headers={"X-Appengine-Cron": "true"}).status_code == 200
    worker.assert_awaited_once()


@pytest.mark.parametrize("body", [
    {"api_key": "x", "text": "hi"},
    {"api_key": API_KEY},
    {"api_key": API_KEY, "text": ""},
    {"api_key": API_KEY, "text": "a" * 4097},
])
def test_tg_validates_input(client, body):
    """Malformed API requests are rejected."""
    assert client.post("/tg", json=body).status_code == 422


def test_tg_unknown_key(client, monkeypatch):
    """Unknown API keys return 403 instead of crashing."""
    monkeypatch.setattr(utils, "getuidbyhash", lambda key: None)
    assert client.post("/tg", json={"api_key": API_KEY, "text": "hi"}).status_code == 403


def test_tg_sends_message(client, monkeypatch):
    """Valid requests deliver the message to the key owner."""
    post = AsyncMock()
    monkeypatch.setattr(utils, "getuidbyhash", lambda key: 42)
    monkeypatch.setattr(utils, "post_tg", post)
    assert client.post("/tg", json={"api_key": API_KEY, "text": "hi"}).status_code == 200
    post.assert_awaited_once_with(42, "hi")


def test_tg_delivery_failure(client, monkeypatch):
    """Telegram errors are reported as 502."""
    monkeypatch.setattr(utils, "getuidbyhash", lambda key: 42)
    monkeypatch.setattr(utils, "post_tg", AsyncMock(side_effect=telegram.error.Forbidden("blocked")))
    assert client.post("/tg", json={"api_key": API_KEY, "text": "hi"}).status_code == 502


def test_api_docs_disabled(client):
    """Interactive API docs are not exposed publicly."""
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404

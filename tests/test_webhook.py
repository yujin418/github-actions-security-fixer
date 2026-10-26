"""Tests for the FastAPI webhook server.

GitHub is not called: the workflow collector is monkeypatched so the tests run
offline and need no token. Run from the repo root: python -m pytest
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

SECRET = "testsecret"
client = TestClient(app)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("GITHUB_TOKEN", "dummy")


def _sign(body: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_webhook_rejects_bad_signature():
    body = json.dumps({"zen": "x"}).encode()
    resp = client.post(
        "/webhook",
        content=body,
        headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": "sha256=deadbeef"},
    )
    assert resp.status_code == 401


def test_webhook_ping_pongs():
    body = json.dumps({"zen": "x"}).encode()
    resp = client.post(
        "/webhook",
        content=body,
        headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": _sign(body)},
    )
    assert resp.status_code == 200
    assert resp.json() == {"message": "pong"}


def test_webhook_ignores_unhandled_event():
    body = json.dumps({"repository": {"full_name": "o/r"}}).encode()
    resp = client.post(
        "/webhook",
        content=body,
        headers={"X-GitHub-Event": "star", "X-Hub-Signature-256": _sign(body)},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


def test_webhook_push_runs_analyzer(monkeypatch):
    vulnerable = (
        "name: t\n"
        "on: [push]\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
    )
    monkeypatch.setattr(
        "app.github.client.collect_workflows",
        lambda repo, ref, **kw: {".github/workflows/ci.yml": vulnerable},
    )
    payload = {
        "repository": {"full_name": "o/r"},
        "after": "a" * 40,
        "ref": "refs/heads/main",
    }
    body = json.dumps(payload).encode()
    resp = client.post(
        "/webhook",
        content=body,
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": _sign(body)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["repo"] == "o/r"
    assert data["files"] == 1
    rule_ids = {f["rule_id"] for f in data["findings"]}
    # unpinned checkout@v4 + no permissions block
    assert "unpinned-actions" in rule_ids
    assert "excessive-permissions" in rule_ids


def test_webhook_missing_secret_returns_500(monkeypatch):
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
    body = json.dumps({"zen": "x"}).encode()
    resp = client.post(
        "/webhook",
        content=body,
        headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": _sign(body)},
    )
    assert resp.status_code == 500

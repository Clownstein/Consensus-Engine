import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from app.main import _MAX_PAYLOAD_BYTES, app, verify_signature

client = TestClient(app, raise_server_exceptions=False)

SECRET = "test-webhook-secret"


def _make_signature(secret: str, payload: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


# --- verify_signature unit tests ---


def test_valid_signature_passes():
    payload = b'{"action": "opened"}'
    sig = _make_signature(SECRET, payload)
    # Should not raise
    verify_signature(SECRET, payload, sig)


def test_missing_signature_raises_401():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        verify_signature(SECRET, b"payload", None)
    assert exc_info.value.status_code == 401


def test_invalid_signature_raises_401():
    from fastapi import HTTPException
    payload = b'{"action": "opened"}'
    with pytest.raises(HTTPException) as exc_info:
        verify_signature(SECRET, payload, "sha256=badhex")
    assert exc_info.value.status_code == 401


def test_wrong_secret_raises_401():
    from fastapi import HTTPException
    payload = b'{"action": "opened"}'
    sig = _make_signature("wrong-secret", payload)
    with pytest.raises(HTTPException) as exc_info:
        verify_signature(SECRET, payload, sig)
    assert exc_info.value.status_code == 401


# --- Webhook endpoint integration tests ---


def _post_webhook(payload: dict, secret: str = SECRET, event: str = "pull_request"):
    import json
    body = json.dumps(payload).encode()
    sig = _make_signature(secret, body)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "x-github-event": event,
            "x-hub-signature-256": sig,
            "content-type": "application/json",
        },
    )
    return response


def test_non_pull_request_event_ignored(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    response = _post_webhook({}, event="push")
    assert response.status_code == 200
    assert response.json()["ignored"] is True
    assert response.json()["reason"] == "not pull_request"


def test_unsupported_action_ignored(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    payload = {"action": "closed", "pull_request": {}, "repository": {}, "installation": {}}
    response = _post_webhook(payload, event="pull_request")
    assert response.status_code == 200
    assert response.json()["ignored"] is True
    assert "unsupported action" in response.json()["reason"]


def test_draft_pr_ignored(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    payload = {
        "action": "opened",
        "pull_request": {"draft": True},
        "repository": {},
        "installation": {},
    }
    response = _post_webhook(payload, event="pull_request")
    assert response.status_code == 200
    assert response.json()["ignored"] is True
    assert response.json()["reason"] == "draft PR"


def test_invalid_signature_returns_401(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    import json
    body = json.dumps({"action": "opened"}).encode()
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "x-github-event": "pull_request",
            "x-hub-signature-256": "sha256=invalid",
            "content-type": "application/json",
        },
    )
    assert response.status_code == 401


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_payload_over_limit_returns_413(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    body = b"a" * (_MAX_PAYLOAD_BYTES + 1)
    sig = _make_signature(SECRET, body)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "x-github-event": "pull_request",
            "x-hub-signature-256": sig,
            "content-type": "application/json",
        },
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "Payload too large"


def test_internal_failure_returns_500_and_sanitized_message(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)
    crash_error = RuntimeError("secret-details-should-not-leak")
    check_update_calls = []

    class _FakeGitHubClient:
        @classmethod
        def for_installation(cls, _installation_id):
            return cls()

        def create_check_run(self, *_args, **_kwargs):
            return 123

        def update_check_run(self, owner, repo, check_run_id, conclusion, summary):
            check_update_calls.append(
                {
                    "owner": owner,
                    "repo": repo,
                    "check_run_id": check_run_id,
                    "conclusion": conclusion,
                    "summary": summary,
                }
            )

        def create_pull_request_review(self, *_args, **_kwargs):
            raise AssertionError("create_pull_request_review should not be called")

    def _raise_context_error(*_args, **_kwargs):
        raise crash_error

    monkeypatch.setattr("app.main.GitHubAppClient", _FakeGitHubClient)
    monkeypatch.setattr("app.main.build_review_context", _raise_context_error)

    payload = {
        "action": "opened",
        "pull_request": {"draft": False, "number": 7, "head": {"sha": "abc123"}},
        "installation": {"id": 1},
        "repository": {"owner": {"login": "acme"}, "name": "demo"},
    }
    response = _post_webhook(payload, event="pull_request")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    assert check_update_calls == [
        {
            "owner": "acme",
            "repo": "demo",
            "check_run_id": 123,
            "conclusion": "failure",
            "summary": "Review could not be completed due to an internal error.",
        }
    ]

import hashlib
import hmac
import json
import logging
import os

from fastapi import FastAPI, Header, HTTPException, Request

from app.diff_builder import build_review_context
from app.github_client import GitHubAppClient
from app.graph.workflow import run_review_graph
from app.rendering.github_markdown import render_review_body

logger = logging.getLogger(__name__)

_MAX_PAYLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

app = FastAPI(title="Multi-Agent PR Reviewer")


def verify_signature(secret: str, payload: bytes, signature_header: str | None) -> None:
    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing GitHub signature")
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict:
    payload_bytes = await request.body()
    if len(payload_bytes) > _MAX_PAYLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Payload too large")
    verify_signature(
        os.environ["GITHUB_WEBHOOK_SECRET"],
        payload_bytes,
        x_hub_signature_256,
    )

    payload = json.loads(payload_bytes)

    if x_github_event != "pull_request":
        return {"ignored": True, "reason": "not pull_request"}

    action = payload.get("action")
    if action not in {"opened", "synchronize", "reopened", "ready_for_review"}:
        return {"ignored": True, "reason": f"unsupported action: {action}"}

    pr = payload["pull_request"]
    if pr.get("draft"):
        return {"ignored": True, "reason": "draft PR"}

    installation_id = payload["installation"]["id"]
    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    pr_number = pr["number"]
    head_sha = pr["head"]["sha"]

    gh = GitHubAppClient.for_installation(installation_id)
    check_run_id = gh.create_check_run(
        owner, repo, head_sha, name="Multi-agent LLM review"
    )

    try:
        review_context = build_review_context(gh, owner, repo, pr_number)
        result = await run_review_graph(review_context)
        body = render_review_body(result)

        if result["approved"]:
            gh.create_pull_request_review(
                owner, repo, pr_number, event="APPROVE", body=body
            )
            gh.update_check_run(
                owner, repo, check_run_id, conclusion="success", summary=body
            )
        else:
            gh.create_pull_request_review(
                owner, repo, pr_number, event="REQUEST_CHANGES", body=body
            )
            gh.update_check_run(
                owner, repo, check_run_id, conclusion="failure", summary=body
            )

        return {"ok": True, "approved": result["approved"]}

    except Exception:
        logger.exception("Reviewer crashed for PR #%s in %s/%s", pr_number, owner, repo)
        try:
            gh.update_check_run(
                owner,
                repo,
                check_run_id,
                conclusion="failure",
                summary="Review could not be completed due to an internal error.",
            )
        except Exception:
            logger.exception(
                "Failed to update check run after crash for PR #%s in %s/%s",
                pr_number,
                owner,
                repo,
            )
        raise HTTPException(status_code=500, detail="Internal server error")

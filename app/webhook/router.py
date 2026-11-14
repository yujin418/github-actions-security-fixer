"""Webhook endpoint: verify the signature, collect workflows, run the analyzer.

Flow: signature check (HMAC-SHA256) -> parse event -> collect workflow files
from GitHub -> run the week-3 detection engine -> return the findings.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import load_settings
from app.github import client as github_client
from app.pipeline import build_llm, format_report, run_pipeline
from app.webhook.events import parse_event
from app.webhook.signature import verify_signature

router = APIRouter()


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
):
    settings = load_settings()
    body = await request.body()

    # 1) Signature verification
    if not settings.webhook_secret:
        raise HTTPException(status_code=500, detail="GITHUB_WEBHOOK_SECRET not configured")
    if not verify_signature(settings.webhook_secret, body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # GitHub's connectivity test
    if x_github_event == "ping":
        return {"message": "pong"}

    # 2) Parse payload
    try:
        payload = json.loads(body)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    target = parse_event(x_github_event, payload)
    if target is None:
        return {"status": "ignored", "event": x_github_event}

    # 3) Collect workflow files and 4) run the full pipeline
    #    (analyze -> fix -> validate -> report). LLM is used only when configured.
    workflows = github_client.collect_workflows(
        target.repo,
        target.ref,
        token=settings.github_token,
        api_url=settings.github_api_url,
    )
    items = run_pipeline(workflows, build_llm())
    findings = [f.to_dict() for item in items for f in item.findings]
    return {
        "repo": target.repo,
        "ref": target.ref,
        "files": len(workflows),
        "findings": findings,
        "report": format_report(items),
    }

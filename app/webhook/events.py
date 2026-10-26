"""Extract the repository and ref to analyze from a webhook payload.

Only ``push`` and ``pull_request`` events are handled; other events return
``None`` and are ignored by the router.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkflowTarget:
    repo: str  # "owner/repo"
    ref: str   # commit SHA (preferred) or ref name


def parse_event(event: str | None, payload: dict) -> WorkflowTarget | None:
    repo = (payload.get("repository") or {}).get("full_name")
    if not repo:
        return None

    if event == "push":
        ref = payload.get("after") or payload.get("ref")
        return WorkflowTarget(repo=repo, ref=ref) if ref else None

    if event == "pull_request":
        head = (payload.get("pull_request") or {}).get("head") or {}
        ref = head.get("sha") or head.get("ref")
        return WorkflowTarget(repo=repo, ref=ref) if ref else None

    return None

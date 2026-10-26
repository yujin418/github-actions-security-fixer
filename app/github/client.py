"""Collect workflow files for a repository/ref via the GitHub REST API.

Uses the "contents" API to list ``.github/workflows`` and fetch each YAML
file's content. A missing directory yields an empty result rather than an
error, so a repository without workflows is handled gracefully.
"""

from __future__ import annotations

import base64

import httpx


def _headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def collect_workflows(
    repo: str,
    ref: str,
    *,
    token: str | None = None,
    api_url: str = "https://api.github.com",
    client: httpx.Client | None = None,
) -> dict[str, str]:
    """Return ``{path: content}`` for every ``.yml``/``.yaml`` workflow file."""
    owns_client = client is None
    client = client or httpx.Client(timeout=15)
    try:
        listing_url = f"{api_url}/repos/{repo}/contents/.github/workflows"
        resp = client.get(listing_url, params={"ref": ref}, headers=_headers(token))
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()

        result: dict[str, str] = {}
        for item in resp.json():
            if item.get("type") != "file":
                continue
            name = item.get("name", "")
            if not (name.endswith(".yml") or name.endswith(".yaml")):
                continue
            file_resp = client.get(item["url"], headers=_headers(token))
            file_resp.raise_for_status()
            encoded = file_resp.json().get("content", "")
            content = base64.b64decode(encoded).decode("utf-8", "replace")
            result[item["path"]] = content
        return result
    finally:
        if owns_client:
            client.close()

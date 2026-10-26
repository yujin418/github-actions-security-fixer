"""Runtime settings loaded from environment variables.

Secrets are never hard-coded; they are read from the environment (see
``.env.example``). ``load_settings`` is called per request so tests can set
environment variables without restarting the app.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    webhook_secret: str | None
    github_token: str | None
    github_api_url: str


def load_settings() -> Settings:
    return Settings(
        webhook_secret=os.environ.get("GITHUB_WEBHOOK_SECRET"),
        github_token=os.environ.get("GITHUB_TOKEN"),
        github_api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )

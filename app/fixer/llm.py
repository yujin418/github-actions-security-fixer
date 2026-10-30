"""LLM client abstraction for the fixer.

The fixer depends only on the :class:`LLMClient` protocol (a ``complete``
method), so it can be tested offline with :class:`MockLLMClient` and later
backed by a real provider without changing the fixer logic.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    name: str

    def complete(self, prompt: str) -> str:
        """Return the model's text completion for ``prompt``."""
        ...


class MockLLMClient:
    """Deterministic client for tests and offline runs (no API key)."""

    name = "mock"

    def __init__(self, response: str = ""):
        self.response = response
        self.last_prompt: str | None = None

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


class AnthropicClient:
    """Real client using the Anthropic API.

    Not exercised by the test suite. Requires ``ANTHROPIC_API_KEY`` and the
    ``anthropic`` package; both are imported/checked lazily so the project
    runs without them when the mock client is used.
    """

    name = "claude"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or os.environ.get("LLM_MODEL")

    def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY 가 설정되지 않았습니다.")
        if not self.model:
            raise RuntimeError("LLM_MODEL 이 설정되지 않았습니다 (.env 참고).")
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("anthropic 패키지가 필요합니다: pip install anthropic") from exc

        client = anthropic.Anthropic(api_key=self.api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )

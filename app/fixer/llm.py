"""LLM client abstraction for the fixer.

The fixer depends only on the :class:`LLMClient` protocol (a ``complete``
method), so it can be tested offline with :class:`MockLLMClient` and later
backed by a real provider without changing the fixer logic.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

# zstd 응답 압축 해제 경로(httpx+zstandard)가 환경에 따라 깨지는 문제를 피하려고
# 서버에 zstd 를 요청하지 않는다. gzip/deflate 만 사용한다.
_NO_ZSTD_HEADERS = {"Accept-Encoding": "gzip, deflate"}


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

        client = anthropic.Anthropic(api_key=self.api_key, default_headers=_NO_ZSTD_HEADERS)
        message = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )


class OpenAIClient:
    """Real client using the OpenAI API.

    Requires ``OPENAI_API_KEY`` and the ``openai`` package; both are imported/
    checked lazily so the project runs without them when the mock is used.
    """

    name = "openai"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("LLM_MODEL") or "gpt-4o-mini"

    def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY 가 설정되지 않았습니다.")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("openai 패키지가 필요합니다: pip install openai") from exc

        client = OpenAI(api_key=self.api_key, default_headers=_NO_ZSTD_HEADERS)
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

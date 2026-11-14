"""테스트 공통 설정.

실제 LLM 키가 .env 에 있어도 테스트는 항상 LLM 없이(또는 주입된 모킹으로) 돌도록
ANTHROPIC_API_KEY·LLM_MODEL 을 모든 테스트에서 제거한다. 이렇게 하면 테스트가
실제 API 를 호출하지 않아 비용·네트워크 변수가 없다.
"""

import pytest


@pytest.fixture(autouse=True)
def _no_real_llm(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

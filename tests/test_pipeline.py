"""Tests for the full pipeline (오프라인, LLM 모킹)."""

from __future__ import annotations

from app.fixer import MockLLMClient
from app.pipeline import build_llm, format_report, run_pipeline

_SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"

VULN = (
    "name: t\n"
    "on: [push]\n"
    "permissions:\n"
    "  contents: read\n"
    "jobs:\n"
    "  b:\n"
    "    runs-on: ubuntu-latest\n"
    "    steps:\n"
    "      - uses: actions/checkout@v4\n"
)
FIXED = VULN.replace("@v4", f"@{_SHA}")
CLEAN = FIXED  # 이미 고정·최소권한 → 탐지 없음


def _llm_returning(fixed: str) -> MockLLMClient:
    return MockLLMClient(response=f"```yaml\n{fixed}\n```")


def test_pipeline_without_llm_is_detect_only():
    items = run_pipeline({".github/workflows/ci.yml": VULN}, None)
    assert len(items) == 1
    assert items[0].validation is None
    assert items[0].fixed_text is None
    assert "미설정" in items[0].note


def test_pipeline_with_mock_llm_validates_fix():
    items = run_pipeline({".github/workflows/ci.yml": VULN}, _llm_returning(FIXED))
    assert len(items) == 1
    item = items[0]
    assert item.fixed_text is not None
    assert item.validation is not None
    assert item.validation.passed


def test_pipeline_skips_clean_files():
    items = run_pipeline({".github/workflows/ci.yml": CLEAN}, None)
    assert items == []


def test_pipeline_bad_fix_does_not_pass():
    # LLM이 고치지 못한(동일한) 워크플로우를 반환 → 해소되지 않음
    items = run_pipeline({".github/workflows/ci.yml": VULN}, _llm_returning(VULN))
    assert items[0].validation is not None
    assert items[0].validation.passed is False


def test_format_report_no_items():
    assert "발견되지 않" in format_report([])


def test_format_report_contains_file_and_validation():
    items = run_pipeline({".github/workflows/ci.yml": VULN}, _llm_returning(FIXED))
    report = format_report(items)
    assert ".github/workflows/ci.yml" in report
    assert "Unpinned Actions" in report
    assert "✅ 통과" in report


def test_build_llm_none_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    assert build_llm() is None

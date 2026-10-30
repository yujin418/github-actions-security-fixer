"""Tests for the fixer. The LLM is mocked, so these run offline with no key."""

from __future__ import annotations

import json

from app.analyzer.models import Finding
from app.fixer import MockLLMClient, build_prompt, generate_fix, generate_fixes


def _finding() -> Finding:
    return Finding(
        rule_id="unpinned-actions",
        rule_name="Unpinned Actions",
        severity="medium",
        file=".github/workflows/ci.yml",
        line=5,
        evidence="uses: actions/checkout@v4",
        message="커밋 SHA 로 고정되지 않았습니다.",
        remediation="전체 커밋 SHA 로 고정하세요.",
        autofixable=False,
    )


WORKFLOW = "name: t\non: [push]\njobs:\n  b:\n    steps:\n      - uses: actions/checkout@v4\n"


def test_build_prompt_includes_evidence_and_rule():
    prompt = build_prompt(_finding(), WORKFLOW)
    assert "actions/checkout@v4" in prompt
    assert "unpinned-actions" in prompt
    assert "JSON" in prompt


def test_generate_fix_parses_json_response():
    response = json.dumps(
        {"suggestion": "uses: actions/checkout@<40-hex-sha>", "reason": "태그는 변경될 수 있어 SHA로 고정"}
    )
    llm = MockLLMClient(response=response)
    fix = generate_fix(_finding(), WORKFLOW, llm)
    assert fix.suggestion == "uses: actions/checkout@<40-hex-sha>"
    assert "SHA" in fix.reason
    assert fix.model == "mock"
    assert fix.rule_id == "unpinned-actions"
    assert fix.original == "uses: actions/checkout@v4"


def test_generate_fix_wraps_json_in_code_fence():
    response = '```json\n{"suggestion": "x", "reason": "y"}\n```'
    fix = generate_fix(_finding(), WORKFLOW, MockLLMClient(response=response))
    assert fix.suggestion == "x"
    assert fix.reason == "y"


def test_generate_fix_fallback_on_non_json():
    fix = generate_fix(_finding(), WORKFLOW, MockLLMClient(response="그냥 설명 텍스트"))
    assert "수동 검토" in fix.suggestion
    assert fix.reason == "그냥 설명 텍스트"


def test_generate_fix_fallback_reason_uses_remediation_when_empty():
    fix = generate_fix(_finding(), WORKFLOW, MockLLMClient(response=""))
    assert fix.reason == "전체 커밋 SHA 로 고정하세요."


def test_generate_fixes_returns_one_per_finding():
    findings = [_finding(), _finding()]
    llm = MockLLMClient(response='{"suggestion": "s", "reason": "r"}')
    fixes = generate_fixes(findings, WORKFLOW, llm)
    assert len(fixes) == 2
    assert all(f.suggestion == "s" for f in fixes)


def test_prompt_passed_to_llm():
    llm = MockLLMClient(response='{"suggestion": "s", "reason": "r"}')
    generate_fix(_finding(), WORKFLOW, llm)
    assert llm.last_prompt is not None
    assert "actions/checkout@v4" in llm.last_prompt

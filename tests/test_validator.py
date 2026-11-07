"""Tests for the validator (오프라인, 네트워크·LLM 불필요)."""

from __future__ import annotations

from app.analyzer.models import Finding
from app.validator import format_pr_comment, validate_fix

_SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"

ORIGINAL = (
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


def _fixed_with(uses_line: str, permissions: str = "  contents: read") -> str:
    return (
        "name: t\n"
        "on: [push]\n"
        f"permissions:\n{permissions}\n"
        "jobs:\n"
        "  b:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        f"      - uses: {uses_line}\n"
    )


def test_valid_fix_passes():
    fixed = _fixed_with(f"actions/checkout@{_SHA}")
    result = validate_fix(ORIGINAL, fixed, target_rule_id="unpinned-actions")
    assert result.format_valid
    assert result.resolved
    assert result.new_findings == []
    assert result.passed


def test_invalid_yaml_fails():
    result = validate_fix(ORIGINAL, "foo: : not valid\n  - [", target_rule_id="unpinned-actions")
    assert result.format_valid is False
    assert result.passed is False


def test_unresolved_fix_fails():
    # 여전히 태그 참조 → 해소되지 않음
    result = validate_fix(ORIGINAL, ORIGINAL, target_rule_id="unpinned-actions")
    assert result.resolved is False
    assert result.passed is False


def test_fix_that_introduces_new_issue_fails():
    # unpinned 는 고쳤지만 write-all 을 추가 → 새 취약점
    fixed = (
        "name: t\n"
        "on: [push]\n"
        "permissions: write-all\n"
        "jobs:\n"
        "  b:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        f"      - uses: actions/checkout@{_SHA}\n"
    )
    result = validate_fix(ORIGINAL, fixed, target_rule_id="unpinned-actions")
    assert result.resolved is True            # unpinned 자체는 해소
    assert len(result.new_findings) >= 1      # 그러나 새 취약점 발생
    assert result.passed is False


def test_no_target_uses_total_count():
    fixed = _fixed_with(f"actions/checkout@{_SHA}")
    result = validate_fix(ORIGINAL, fixed)  # target 없이 전체 건수 비교
    assert result.resolved
    assert result.passed


def test_format_pr_comment_contains_sections():
    finding = Finding(
        rule_id="unpinned-actions",
        rule_name="Unpinned Actions",
        severity="medium",
        file=".github/workflows/ci.yml",
        line=9,
        evidence="uses: actions/checkout@v4",
        message="고정되지 않음",
        remediation="SHA 로 고정",
    )

    class _Fix:
        suggestion = f"uses: actions/checkout@{_SHA}  # v4"
        reason = "태그는 이동 가능"

    result = validate_fix(ORIGINAL, _fixed_with(f"actions/checkout@{_SHA}"), "unpinned-actions")
    md = format_pr_comment([(finding, _Fix(), result)])
    assert "보안 점검 결과" in md
    assert "Unpinned Actions" in md
    assert "✅ 통과" in md
    assert "uses: actions/checkout@v4" in md

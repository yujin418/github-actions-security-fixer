"""수정안 검증: 고친 워크플로우가 유효하고 취약점이 해소됐는지 재분석.

입력은 "원본 워크플로우 텍스트"와 "수정안이 반영된 워크플로우 텍스트"다.
검증 항목(프로젝트 평가 계획과 대응):
  1. 형식 유효성  — 수정안이 유효한 YAML 인가
  2. 취약점 해소  — 대상 취약점이 재분석에서 사라졌는가
  3. 변경 범위    — 수정으로 새로운 취약점이 생기지 않았는가

실제 수정안을 워크플로우에 적용(apply)하는 단계는 이후에 연결한다. 이 모듈은
"적용된 결과 텍스트"를 받아 판정만 수행하므로 네트워크·LLM 없이 검증할 수 있다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import yaml

from app.analyzer import analyze_text
from app.analyzer.models import Finding
from app.analyzer.rules import RuleMeta

__all__ = ["ValidationResult", "validate_fix", "format_pr_comment"]


@dataclass
class ValidationResult:
    format_valid: bool            # 유효한 YAML 인가
    resolved: bool                # 대상 취약점이 해소됐는가
    new_findings: list[Finding]   # 수정으로 새로 생긴 취약점
    passed: bool                  # 세 조건을 모두 만족하는가
    detail: str                   # 사람이 읽는 요약

    def to_dict(self) -> dict:
        return asdict(self)


def _key(finding: Finding) -> tuple[str, str]:
    return (finding.rule_id, finding.evidence)


def validate_fix(
    original_text: str,
    fixed_text: str,
    target_rule_id: str | None = None,
    rules: dict[str, RuleMeta] | None = None,
) -> ValidationResult:
    """원본 대비 수정안 텍스트를 검증한다.

    target_rule_id 를 주면 그 규칙의 해소 여부만 보고, 없으면 전체 탐지 건수가
    줄었는지로 판단한다.
    """
    # 1) 형식 유효성
    try:
        parsed = yaml.safe_load(fixed_text)
        format_valid = isinstance(parsed, dict)
    except yaml.YAMLError:
        format_valid = False

    if not format_valid:
        return ValidationResult(
            format_valid=False,
            resolved=False,
            new_findings=[],
            passed=False,
            detail="수정안이 유효한 YAML 이 아닙니다.",
        )

    before = analyze_text(original_text, rules=rules)
    after = analyze_text(fixed_text, rules=rules)

    # 2) 취약점 해소
    if target_rule_id:
        before_n = sum(1 for f in before if f.rule_id == target_rule_id)
        after_n = sum(1 for f in after if f.rule_id == target_rule_id)
        resolved = after_n < before_n
    else:
        resolved = len(after) < len(before)

    # 3) 변경 범위 (새 취약점)
    before_keys = {_key(f) for f in before}
    new_findings = [f for f in after if _key(f) not in before_keys]

    passed = format_valid and resolved and not new_findings
    detail = (
        f"형식 {'유효' if format_valid else '오류'} · "
        f"해소 {'예' if resolved else '아니오'} · "
        f"새 취약점 {len(new_findings)}건"
    )
    return ValidationResult(format_valid, resolved, new_findings, passed, detail)


def format_pr_comment(items: list[tuple]) -> str:
    """탐지·수정안·검증 결과를 PR 코멘트용 마크다운으로 만든다.

    items: (finding, fix_or_None, validation_or_None) 튜플 목록.
    실제 PR 게시는 다음 단계(GitHub API)에서 연결한다.
    """
    lines = ["## 🔒 GitHub Actions 보안 점검 결과", ""]
    for finding, fix, result in items:
        if result is None:
            status = "미검증"
        elif result.passed:
            status = "✅ 통과"
        else:
            status = "⚠️ 검토 필요"
        lines.append(
            f"### [{finding.severity.upper()}] {finding.rule_name} — {finding.file}:{finding.line}"
        )
        lines.append(f"- 탐지 근거: `{finding.evidence}`")
        if fix is not None:
            lines.append(f"- 수정안: {fix.suggestion}")
            lines.append(f"- 이유: {fix.reason}")
        if result is not None:
            lines.append(f"- 검증: {status} ({result.detail})")
        else:
            lines.append(f"- 검증: {status}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

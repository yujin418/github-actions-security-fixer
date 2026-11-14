"""전체 파이프라인: 탐지 -> 수정안 -> 검증 -> 결과(PR 코멘트) 제공.

워크플로우 파일들을 받아 각 파일을 분석하고, LLM이 있으면 수정안을 생성·검증한다.
LLM 없이도(키 미설정) 탐지 결과만으로 동작하며, 실제 LLM 연결 여부와 무관하게
`run_pipeline`은 주입된 클라이언트로 테스트할 수 있다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from app.analyzer import analyze_text
from app.analyzer.models import Finding
from app.fixer import suggest_fixed_workflow
from app.fixer.llm import LLMClient
from app.validator import ValidationResult, validate_fix

__all__ = ["PipelineItem", "run_pipeline", "format_report", "build_llm"]


@dataclass
class PipelineItem:
    file: str
    findings: list[Finding]
    fixed_text: str | None = None
    validation: ValidationResult | None = None
    note: str = ""


DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


def build_llm() -> LLMClient | None:
    """설정된 키에 따라 LLM 클라이언트를 만든다. 없으면 None.

    우선순위: OPENAI_API_KEY -> ANTHROPIC_API_KEY. 모델은 LLM_MODEL 로 지정하며,
    비워두면 각 제공자의 기본 모델을 사용한다.
    """
    model = os.environ.get("LLM_MODEL") or None

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        from app.fixer.llm import OpenAIClient

        return OpenAIClient(openai_key, model)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        from app.fixer.llm import AnthropicClient

        return AnthropicClient(anthropic_key, model or DEFAULT_ANTHROPIC_MODEL)

    return None


def run_pipeline(
    workflows: dict[str, str], llm: LLMClient | None = None
) -> list[PipelineItem]:
    """각 워크플로우를 분석하고, LLM이 있으면 수정안을 생성·검증한다."""
    items: list[PipelineItem] = []
    for path, text in workflows.items():
        findings = analyze_text(text, file=path)
        if not findings:
            continue
        if llm is None:
            items.append(PipelineItem(path, findings, note="LLM 미설정 — 탐지만 수행"))
            continue
        fixed_text, note = suggest_fixed_workflow(text, findings, llm)
        validation = validate_fix(text, fixed_text) if fixed_text else None
        items.append(PipelineItem(path, findings, fixed_text, validation, note))
    return items


def format_report(items: list[PipelineItem]) -> str:
    """파이프라인 결과를 PR 코멘트용 마크다운으로 만든다."""
    lines = ["## 🔒 GitHub Actions 보안 점검 결과", ""]
    if not items:
        lines.append("취약점이 발견되지 않았습니다.")
        return "\n".join(lines) + "\n"

    for item in items:
        lines.append(f"### `{item.file}`")
        for finding in item.findings:
            lines.append(
                f"- **[{finding.severity.upper()}]** {finding.rule_name} "
                f"(L{finding.line}): `{finding.evidence}`"
            )
        if item.validation is not None:
            mark = "✅ 통과" if item.validation.passed else "⚠️ 검토 필요"
            lines.append(f"- 수정안 검증: {mark} ({item.validation.detail})")
        else:
            lines.append(f"- 수정안: {item.note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

"""Generate a fix suggestion and change reason for a detected issue.

The fixer takes a :class:`~app.analyzer.models.Finding` and the workflow text,
builds a prompt, asks an :class:`~app.fixer.llm.LLMClient` for a minimal fix,
and returns a :class:`FixSuggestion`. The LLM output is expected as JSON; if it
cannot be parsed, the raw text and the rule's remediation are used as a fallback
so a malformed response never crashes the pipeline.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

from app.analyzer.models import Finding

from .llm import LLMClient, MockLLMClient

__all__ = [
    "FixSuggestion",
    "build_prompt",
    "generate_fix",
    "generate_fixes",
    "suggest_fixed_workflow",
    "MockLLMClient",
]


@dataclass
class FixSuggestion:
    rule_id: str
    file: str
    line: int
    original: str      # the detected evidence
    suggestion: str    # proposed fix (snippet or concrete instruction)
    reason: str        # why this change is needed
    model: str         # which LLM produced it (transparency)

    def to_dict(self) -> dict:
        return asdict(self)


_PROMPT_TEMPLATE = """당신은 GitHub Actions 워크플로우 보안 수정 도우미입니다.
아래 탐지된 취약점에 대해 최소한의 수정안과 변경 이유를 제시하세요.
기존 동작을 바꾸지 않는 선에서, 문제 부분만 고치세요.

규칙: {rule_name} ({rule_id})
파일: {file} (행 {line})
탐지 근거: {evidence}
설명: {message}
권장 수정 방향: {remediation}

워크플로우 전체:
```yaml
{workflow}
```

반드시 아래 JSON 형식으로만 답하세요:
{{"suggestion": "<고친 코드 조각 또는 구체적 수정 방법>", "reason": "<왜 이렇게 고치는지>"}}
"""


def build_prompt(finding: Finding, workflow_text: str) -> str:
    return _PROMPT_TEMPLATE.format(
        rule_name=finding.rule_name,
        rule_id=finding.rule_id,
        file=finding.file,
        line=finding.line,
        evidence=finding.evidence,
        message=finding.message,
        remediation=finding.remediation,
        workflow=workflow_text,
    )


def _extract_json(raw: str) -> dict | None:
    """Best-effort extraction of a JSON object from the model output."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def generate_fix(finding: Finding, workflow_text: str, llm: LLMClient) -> FixSuggestion:
    prompt = build_prompt(finding, workflow_text)
    raw = llm.complete(prompt)

    data = _extract_json(raw)
    if data and "suggestion" in data:
        suggestion = str(data.get("suggestion", "")).strip()
        reason = str(data.get("reason", "")).strip() or finding.remediation
    else:
        # Fallback: keep the raw text as the reason, defer the edit to review.
        suggestion = "(자동 파싱 실패 — 수동 검토 필요)"
        reason = raw.strip() or finding.remediation

    return FixSuggestion(
        rule_id=finding.rule_id,
        file=finding.file,
        line=finding.line,
        original=finding.evidence,
        suggestion=suggestion,
        reason=reason,
        model=getattr(llm, "name", "unknown"),
    )


def generate_fixes(
    findings: list[Finding], workflow_text: str, llm: LLMClient
) -> list[FixSuggestion]:
    return [generate_fix(f, workflow_text, llm) for f in findings]


_FIX_WORKFLOW_PROMPT = """다음 GitHub Actions 워크플로우에서 탐지된 보안 취약점을
최소 수정으로 고치세요. 기존 동작은 유지하고 문제 부분만 바꿉니다.

탐지된 취약점:
{issues}

원본 워크플로우:
```yaml
{workflow}
```

수정된 전체 워크플로우 YAML만 아래 형식으로 반환하세요:
```yaml
<수정된 워크플로우>
```
"""


def _extract_yaml(raw: str) -> str | None:
    """LLM 응답에서 코드펜스로 감싼 YAML(또는 전체 텍스트)을 추출한다."""
    match = re.search(r"```(?:yaml)?\s*(.*?)```", raw, re.DOTALL)
    if match:
        body = match.group(1).strip()
    else:
        body = raw.strip()
    return body + "\n" if body else None


def suggest_fixed_workflow(
    workflow_text: str, findings: list[Finding], llm: LLMClient
) -> tuple[str | None, str]:
    """탐지된 취약점을 모두 반영한 **전체 수정 워크플로우**를 LLM에게 요청한다.

    반환: (수정된 워크플로우 텍스트 또는 None, 설명 메모).
    파싱에 실패하면 (None, 사유)를 돌려줘 파이프라인이 멈추지 않게 한다.
    """
    issues = "\n".join(f"- {f.rule_name} (L{f.line}): {f.evidence}" for f in findings)
    prompt = _FIX_WORKFLOW_PROMPT.format(issues=issues, workflow=workflow_text)
    raw = llm.complete(prompt)
    fixed = _extract_yaml(raw)
    if fixed is None:
        return None, "수정안 파싱 실패 — 수동 검토 필요"
    return fixed, f"LLM({getattr(llm, 'name', '?')}) 수정안"

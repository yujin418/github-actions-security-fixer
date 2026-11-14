"""데모: 전체 파이프라인(탐지→수정안→검증→PR 코멘트)을 실제 코드 경로로 시연.

실행:  python scripts/demo_pipeline.py

app.pipeline.run_pipeline 를 그대로 사용하며, LLM 자리에는 데모용 클라이언트를 넣는다.
데모 클라이언트는 LLM 응답을 흉내 내어 기계적으로 고친 전체 워크플로우를 돌려준다.
실제 운영에서는 ANTHROPIC_API_KEY·LLM_MODEL 설정 시 실제 모델이 그 자리를 대신한다.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

from app.pipeline import format_report, run_pipeline  # noqa: E402

SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"
TARGETS = ["unpinned-actions.yml", "excessive-permissions.yml"]


def _apply_mechanical(text: str) -> str:
    """unpinned 태그→SHA, write-all→contents:read 를 기계적으로 반영(데모용)."""

    def pin(match: re.Match) -> str:
        indent, repo, ref = match.group(1), match.group(2), match.group(3)
        if re.fullmatch(r"[0-9a-f]{40}", ref):
            return match.group(0)
        return f"{indent}uses: {repo}@{SHA}  # {ref}"

    text = re.sub(r"([ \t]*)uses:\s*([^\s@]+)@(\S+)", pin, text)
    text = re.sub(
        r"(?m)^([ \t]*)permissions:\s*write-all\s*$",
        r"\1permissions:\n\1  contents: read",
        text,
    )
    return text


class DemoLLM:
    """프롬프트 속 원본 워크플로우를 받아 '수정된 전체 YAML'을 돌려주는 데모 클라이언트."""

    name = "demo"

    def complete(self, prompt: str) -> str:
        match = re.search(r"원본 워크플로우:\s*```yaml\s*(.*?)```", prompt, re.DOTALL)
        original = match.group(1) if match else ""
        return f"```yaml\n{_apply_mechanical(original)}\n```"


def main() -> int:
    print("전체 파이프라인 데모: 탐지 → 수정안 → 검증 → PR 코멘트")
    print("※ 수정안은 데모용(기계적) 응답, 실제 운영 시 LLM이 생성\n")

    workflows = {}
    for name in TARGETS:
        path = REPO / "tests" / "workflows" / "vulnerable" / name
        workflows[f".github/workflows/{name}"] = path.read_text(encoding="utf-8")

    items = run_pipeline(workflows, DemoLLM())

    for item in items:
        print("=" * 72)
        print(f"파일: {item.file}")
        for finding in item.findings:
            print(f"  [탐지] [{finding.severity.upper()}] {finding.rule_id} (L{finding.line}): {finding.evidence}")
        if item.validation is not None:
            mark = "✅ 통과" if item.validation.passed else "⚠️ 검토 필요"
            print(f"  [검증] {item.validation.detail} -> {mark}")
    print("=" * 72)
    print("\n--- PR 코멘트 미리보기 ---\n")
    print(format_report(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

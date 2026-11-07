"""데모: 탐지 -> 수정안 -> 적용 -> 검증 -> PR 코멘트 (발표용 전 과정).

실행:  python scripts/demo_pipeline.py

수정안/이유는 데모용 예시이며, 실제 연동 시 LLM이 생성한다. 기계적으로 적용 가능한
규칙(unpinned-actions, excessive-permissions)만 자동 반영해 검증까지 보여준다.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

from app.analyzer import analyze_text  # noqa: E402
from app.validator import format_pr_comment, validate_fix  # noqa: E402

# 데모용 고정 SHA (실제로는 조회로 얻는다)
SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"

TARGETS = ["unpinned-actions.yml", "excessive-permissions.yml"]


def fix_for(finding):
    """규칙별 수정안(스니펫)과 이유를 돌려준다 (데모 예시)."""
    if finding.rule_id == "unpinned-actions":
        ref = finding.evidence.split("uses:", 1)[1].strip()  # owner/repo@tag
        repo, _, tag = ref.partition("@")
        return f"{repo}@{SHA}  # {tag}", "태그·브랜치는 이동 가능하므로 불변한 커밋 SHA로 고정합니다."
    if finding.rule_id == "excessive-permissions":
        return "permissions:\n  contents: read", "write-all은 과도하므로 최소 권한(contents: read)만 부여합니다."
    return "(수동 검토 필요)", finding.remediation


def apply_fixes(text: str, findings) -> str:
    """기계적으로 적용 가능한 수정안을 워크플로우에 반영한다."""
    fixed = text
    for finding in findings:
        if finding.rule_id == "unpinned-actions":
            ref = finding.evidence.split("uses:", 1)[1].strip()
            repo, _, tag = ref.partition("@")
            fixed = fixed.replace(ref, f"{repo}@{SHA}  # {tag}")
        elif finding.rule_id == "excessive-permissions":
            fixed = fixed.replace("permissions: write-all", "permissions:\n  contents: read")
    return fixed


def main() -> int:
    print("탐지 -> 수정안 -> 적용 -> 검증 -> PR 코멘트 데모")
    print("※ 수정안/이유는 데모용 예시, 실제 연동 시 LLM이 생성\n")

    items = []
    for name in TARGETS:
        path = REPO / "tests" / "workflows" / "vulnerable" / name
        text = path.read_text(encoding="utf-8")
        findings = analyze_text(text, file=f".github/workflows/{name}")
        fixed = apply_fixes(text, findings)
        result = validate_fix(text, fixed)

        print("=" * 72)
        print(f"파일: {name}")
        for finding in findings:
            suggestion, reason = fix_for(finding)
            print(f"  [탐지]  [{finding.severity.upper()}] {finding.rule_id} (L{finding.line}): {finding.evidence}")
            print(f"  [수정안] {suggestion.splitlines()[0]}" + (" ..." if "\n" in suggestion else ""))
            print(f"  [이유]  {reason}")
            items.append((finding, SimpleNamespace(suggestion=suggestion, reason=reason), result))
        mark = "✅ 통과" if result.passed else "⚠️ 검토 필요"
        print(f"  [검증]  {result.detail} -> {mark}")

    print("=" * 72)
    print("\n--- PR 코멘트 미리보기 ---\n")
    print(format_pr_comment(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

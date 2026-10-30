"""데모: 취약 워크플로우 탐지 -> 수정안·변경 이유 생성 (발표용).

실행:  python scripts/demo_fixer.py

수정안/이유는 데모용 예시 응답(Mock)이며, 실제 LLM 연동 시 모델이 생성한다.
어느 셸(cmd/PowerShell)에서나 한글이 깨지지 않도록 출력 인코딩을 utf-8로 둔다.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# 저장소 루트를 import 경로에 추가 (scripts/ 에서 실행해도 app 패키지를 찾도록)
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:  # Windows cmd(cp949)에서도 한글 출력
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

from app.analyzer import analyze_file  # noqa: E402
from app.fixer import generate_fix  # noqa: E402


class SampleLLM:
    """규칙별 예시 응답을 돌려주는 데모용 Mock 클라이언트."""

    name = "sample"

    _RESPONSES = {
        "excessive-permissions": {
            "suggestion": "permissions:\n  contents: read",
            "reason": "write-all은 과도하므로 최소 권한(contents: read)만 부여하고 필요한 스코프만 추가합니다.",
        },
        "script-injection": {
            "suggestion": 'env:\n  TITLE: ${{ github.event.issue.title }}\nrun: echo "$TITLE"',
            "reason": "신뢰할 수 없는 입력을 셸에 직접 넣지 않고 env로 전달해 명령 주입을 막습니다.",
        },
    }

    def complete(self, prompt: str) -> str:
        # unpinned-actions: 실제 참조된 액션 이름으로 수정안을 구성
        if "(unpinned-actions)" in prompt:
            match = re.search(r"탐지 근거:\s*uses:\s*([^@\s]+)@(\S+)", prompt)
            if match:
                repo, tag = match.group(1), match.group(2)
                return json.dumps(
                    {
                        "suggestion": f"uses: {repo}@<40자리 커밋 SHA>  # {tag}",
                        "reason": "태그·브랜치는 이동 가능해 참조 코드가 바뀔 수 있으므로 불변한 커밋 SHA로 고정합니다.",
                    },
                    ensure_ascii=False,
                )
        for rule_id, resp in self._RESPONSES.items():
            if f"({rule_id})" in prompt:
                return json.dumps(resp, ensure_ascii=False)
        return json.dumps(
            {"suggestion": "(검토 필요)", "reason": "규칙별 예시 없음"}, ensure_ascii=False
        )


def main() -> int:
    vuln_dir = REPO / "tests" / "workflows" / "vulnerable"
    files = sorted(vuln_dir.glob("*.yml"))
    llm = SampleLLM()

    print("GitHub Actions 취약점 탐지 -> AI 수정안 데모")
    print("※ 수정안/이유는 데모용 예시 응답(Mock), 실제 연동 시 LLM이 생성\n")

    total = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        for finding in analyze_file(path):
            total += 1
            fix = generate_fix(finding, text, llm)
            print("=" * 72)
            print(f"[{finding.severity.upper()}] {finding.rule_id}  ({path.name}:{finding.line})")
            print(f"  탐지 근거 : {finding.evidence}")
            print("  수정안   :")
            for line in fix.suggestion.splitlines():
                print(f"      {line}")
            print(f"  변경 이유 : {fix.reason}")
    print("=" * 72)
    print(f"총 {total}건 탐지·수정안 생성 ({len(files)}개 파일)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

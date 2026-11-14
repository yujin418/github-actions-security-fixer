"""실제 LLM 연동 확인 스크립트.

.env 의 ANTHROPIC_API_KEY(그리고 선택적으로 LLM_MODEL)를 사용해 작은 호출을 1회
보내 연동이 되는지 확인한다. 실제 API 를 호출하므로 소량의 사용량이 발생한다.

실행:  python scripts/check_llm.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

from app.pipeline import build_llm  # noqa: E402  (.env 는 app import 시 로드됨)


def main() -> int:
    llm = build_llm()
    if llm is None:
        print("LLM 키가 설정되지 않았습니다. .env 에 OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 를 입력하세요.")
        return 2

    print(f"모델 연동 시도 (name={llm.name}) ...")
    try:
        reply = llm.complete('아래 문장을 그대로 한 번만 출력하세요: "연동 성공"')
    except Exception as exc:
        print(f"연동 실패: {exc}")
        return 1

    print("응답:", reply.strip()[:200])
    print("✅ 실제 LLM 연동이 정상 동작합니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

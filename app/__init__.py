"""app 패키지.

로컬 개발 편의를 위해 .env 가 있으면 환경변수로 로드한다(python-dotenv 설치 시).
비밀값은 .env(커밋되지 않음)에만 두고, 코드에 넣지 않는다.
"""

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv 미설치 등 — 환경변수를 직접 사용
    pass

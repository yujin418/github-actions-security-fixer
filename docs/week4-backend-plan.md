# 4주차: 실행 점검·계획 검증 및 FastAPI/REST 자료조사

- 기간: 10/5~10/25 (README 개발 계획 기준) · 문서 작성일: 2026-10-26
- 주제: 현재 구현(탐지 엔진) 실행 점검, 문서·코드 정합성 확인, 백엔드 단계 계획 검증, FastAPI/REST 자료조사
- 범위: 이번 주는 **분석·계획·조사** 중심이며, FastAPI 서버·Webhook 등 기능 구현은 수행하지 않았다.

## 1. 이번 주 목표

3주차까지 구현한 탐지 엔진을 **직접 실행해 상태를 확인**하고, 문서와 실제 코드의 차이를 정리한다.
다음 단계(FastAPI 서버·Webhook·파일 수집)의 **계획을 검증**하고, 구현에 필요한 **FastAPI/REST 자료조사**를 수행한다.

## 2. 프로젝트 실행 점검

### 실행 환경 (확인됨)

| 항목 | 값 | 비고 |
| --- | --- | --- |
| Python | 3.10.9 | 실제 실행에 사용 |
| PyYAML | 6.0.3 | requirements: `>=6.0` 충족 |
| pytest | 7.1.2 | requirements: `>=8.0` **미충족**(아래 3절) |
| fastapi / uvicorn | 미설치 | 서버 미구현이라 현재 불필요 |

### 실행 명령과 결과 (확인됨)

```bash
python -m pytest
# 결과: 10 passed

python -m app.analyzer tests/workflows
# 결과: 4건 탐지, 종료코드 1
#  vulnerable/excessive-permissions.yml  [MEDIUM] L7  write-all
#  vulnerable/script-injection.yml       [HIGH]   L15 github.event.issue.title
#  vulnerable/unpinned-actions.yml       [MEDIUM] L15 actions/checkout@v4
#                                        [MEDIUM] L17 actions/setup-node@main
#  (safe/* 정상 예제 2종 → 탐지 0건, 오탐 없음)
```

- 종료코드 1은 **탐지 건이 있을 때 실패로 알리는 의도된 동작**이며 오류가 아니다(`app/analyzer/__main__.py`).
- 콘솔에서 한글이 깨지면 `PYTHONIOENCODING=utf-8` 설정으로 해결된다(Windows cp949 표시 문제).

### 확인된 사실 vs 추정

- **확인됨**: 탐지 엔진·CLI·테스트가 정상 동작한다. 취약 예제 3종 탐지, 정상 예제 2종 무탐지.
- **확인됨**: `app/` 하위 `webhook, github, fixer, validator, database` 패키지와 `main.py`는 **빈 자리표시자**다(근거: `__init__.py` 0바이트, `main.py`는 docstring 1줄).
- **추정**: 커밋된 `__pycache__`는 cpython-3.14로 생성되어 있으나 현재 실행 환경은 3.10.9다. 과거 다른 Python으로 생성된 흔적으로 보이며 동작에는 영향 없음(추정).

### 필요한 비밀/외부 접근 (현재 미생성)

현재 탐지 엔진 단계에서는 비밀값이나 외부 접근이 **필요하지 않다.** 다음 서버 단계에서 아래 항목이 필요하며, 임의로 생성하지 않고 목록만 정리한다.

| 항목 | 용도 | 비고 |
| --- | --- | --- |
| `GITHUB_WEBHOOK_SECRET` | Webhook 서명(HMAC) 검증 | 서버 구현 시 사용자 발급 필요 |
| `GITHUB_TOKEN` (또는 GitHub App 자격) | REST API로 워크플로우 파일 조회 | 최소 권한(`contents: read`) 권장 |

## 3. 문서·코드 정합성 점검

코드/실행 결과를 근거로 기존 문서와의 차이를 표시한다. (이번 주에는 **표시만** 하고 코드/문서 수정은 하지 않음)

| 위치 | 문서 내용 | 실제 코드/실행 | 처리 |
| --- | --- | --- | --- |
| README 시스템 구성 표 | 규칙 엔진으로 **Semgrep** 명시 | `app/analyzer`는 **PyYAML 기반 자체 규칙** 사용(Semgrep 미사용) | 다음 주 README 반영 제안 |
| `requirements.txt` | `pytest>=8.0` | 설치본 **7.1.2**로 테스트는 통과 | 버전 범위 재검토 필요(확인 필요) |
| `.vscode/settings.json` | **unittest** 활성화, 패턴 `*test.py` | 테스트는 **pytest 스타일**, 파일명 `test_analyzer.py`(패턴 불일치) | IDE 테스트 설정 수정 제안 |
| README 관련 문서 | week1·week2만 링크 | week3 문서 존재하나 미링크 | README 링크 보강 제안 |

> 위 항목은 모두 **기능이 아니라 설정·문서 수준의 차이**이며, 탐지 엔진 동작에는 영향이 없다(테스트 10건 통과로 확인).

## 4. 개발 계획 검증 (10/5~10/25 백엔드 단계)

기존 계획(README 일정 + week3 "다음 단계")의 각 항목을 검증한다. 상태는 **미수행**이며, 이번 주는 계획 검증까지만 한다.

| 항목 | 필요성 | 현재 구현 | 선행 작업 | 영향 범위 | 검증 방법 |
| --- | --- | --- | --- | --- | --- |
| FastAPI 기본 서버 | 이벤트 수신 입구 | 미구현 | fastapi·uvicorn 설치 | `app/main.py` | `/health` 응답 확인 |
| Webhook 수신·서명 검증 | 위변조 요청 차단 | 미구현 | 서버, `GITHUB_WEBHOOK_SECRET` | `app/webhook/` | 유효/위조 서명 테스트 |
| 워크플로우 파일 수집 | 분석 대상 확보 | 미구현 | GitHub API, `GITHUB_TOKEN`, httpx | `app/github/` | 샘플 저장소 파일 조회 |
| 탐지 엔진 연결 | 수집→분석 연결 | **엔진은 완료**, 연결 미구현 | 위 3개 | `main`↔`analyzer` | 이벤트→탐지 결과 end-to-end |

**우선순위(검증 결과)**: ① FastAPI 서버 → ② Webhook 서명 검증 → ③ 파일 수집 → ④ 엔진 연결.
근거: 각 단계가 앞 단계를 선행 의존하며, 서명 검증은 외부 노출 전 반드시 선행해야 한다.

**실현 가능성**: 탐지 엔진이 `analyze_text(text)` 형태로 이미 분리되어 있어, 수집한 파일 내용을 문자열로 넘기면 바로 연결 가능(낮은 위험).

## 5. FastAPI / REST API 자료조사

- 조사일: 2026-10-26 · 공식 문서 기준 · 출처는 절 끝에 명시
- 버전 확인: FastAPI 최신 **0.136.x**(2026-04 기준), **Python 3.10+**, **Pydantic v2** 기반. 본 프로젝트는 Python 3.10.9라 호환되나 **아직 FastAPI를 의존성에 고정하지 않음**(도입 시 버전 고정 필요).

### 개념 구분 (일반)

- **FastAPI**: Python으로 **API를 만드는 웹 프레임워크**(도구). 타입힌트·Pydantic 기반으로 입력 검증과 문서 자동화를 제공.
- **REST**: API를 **설계하는 방식(아키텍처 스타일)**. 리소스를 URL로 표현하고 HTTP 메서드로 조작. FastAPI로 REST 스타일 API를 구현하는 관계.

### FastAPI 핵심 (일반)

| 주제 | 요점 |
| --- | --- |
| 라우터 구성 | `APIRouter`로 기능별 모듈 분리("Bigger Applications"). prefix·tags·공통 의존성을 라우터에 지정 |
| 요청/응답 모델 | Pydantic 모델로 요청 body 파싱·검증, `response_model`로 응답 형태 지정 |
| 입력 검증 | 타입힌트+Pydantic으로 자동 검증, 실패 시 기본 **422** 반환 |
| 의존성 주입 | `Depends`로 공통 로직(인증·검증·DB 세션 등) 주입, 재사용 |
| 오류 처리 | `HTTPException(status_code, detail)`으로 상태코드+메시지 응답 |
| 인증 | security 유틸(OAuth2, API Key, HTTP Bearer 등) 제공 |
| 테스트 | `TestClient`(httpx 기반)로 엔드포인트 호출, 상태코드·응답 검증 |

### REST 핵심 (일반)

- **리소스/URL**: 명사·복수형, URL은 동작이 아닌 리소스를 표현. 중첩은 얕게.
- **HTTP 메서드**: GET(조회·안전·멱등), POST(생성), PUT(전체 교체), PATCH(부분 수정), DELETE(삭제).
- **상태 코드**: 200 OK, 201 Created(+Location), 204 No Content, 400 잘못된 요청, 401 인증 실패, 403 권한 없음, 404 없음, 422 검증 실패, 429 제한 초과, 500 서버 오류.

### 프로젝트 적용점 (본 프로젝트)

- 엔드포인트: `POST /webhook`(GitHub 이벤트 수신), `GET /health`(상태 확인).
- **서명 검증은 일반 인증과 별개**로, GitHub의 `X-Hub-Signature-256`(HMAC-SHA256)로 요청 위변조를 확인 → 불일치 시 `HTTPException`으로 **401** 반환.
- Webhook 페이로드는 Pydantic 모델로 필요한 필드(저장소·ref 등)만 검증.
- `APIRouter`로 webhook 라우터를 `app/webhook/`에 분리.
- 지원하지 않는 이벤트는 **204**, 정상 접수는 200/202로 응답(세부는 구현 시 확정 — 확인 필요).
- `TestClient`로 유효/위조 서명·이벤트 분기를 테스트.

**출처 (2026-10-26 확인)**
- FastAPI — Bigger Applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI — Testing: https://fastapi.tiangolo.com/tutorial/testing/
- FastAPI 버전/요구사항(PyPI): https://pypi.org/project/fastapi/
- REST 설계(참고, Microsoft Azure): https://learn.microsoft.com/azure/architecture/best-practices/api-design
- HTTP 의미론 표준: RFC 9110 (https://www.rfc-editor.org/rfc/rfc9110)

## 6. 개발 정리 (분류별)

각 항목은 **현재 상태 / 확인 근거 / 문제점 / 다음 작업** 순. 실행·검증하지 않은 작업은 완료로 표기하지 않는다.

### 6-1. 프로젝트 설계 및 준비
- **현재 상태**: 구조·모듈 분리 완료, 구현 범위·우선순위 정리됨.
- **확인 근거**: `app/` 패키지 구조 존재, README 개발 계획·구조 섹션, week2-design.md.
- **문제점**: README가 Semgrep을 규칙 엔진으로 표기하나 실제는 PyYAML 자체 규칙(3절).
- **다음 작업**: README 시스템 구성·관련 문서 링크 보강(제안).

### 6-2. 백엔드 및 취약점 분석
- **현재 상태**: 탐지 엔진·결과 형식 **완료**. 서버·API·파일 수집은 **미수행**.
- **확인 근거**: `python -m pytest` 10 passed, `python -m app.analyzer` 4건 탐지(2절). `app/webhook·github`는 빈 자리표시자.
- **문제점**: 수집→분석을 잇는 "입구"가 없어 현재는 로컬 파일만 수동 분석 가능.
- **다음 작업**: FastAPI 서버 → Webhook 서명 검증 → GitHub API 파일 수집 → 엔진 연결(4절 우선순위).

### 6-3. AI 수정 제안 및 결과 제공
- **현재 상태**: **미수행**(설계만). 규칙 메타데이터에 `autofixable=false`로 표기됨.
- **확인 근거**: `app/fixer`, `app/validator` 빈 자리표시자. `rules/*.yml`의 자동수정 조건 기록.
- **문제점**: LLM 제공자·수정안 형식·검증 기준 미확정.
- **다음 작업**: 탐지 결과(`Finding`)를 입력으로 하는 수정안 생성·검증 설계(백엔드 단계 이후).

### 6-4. 통합 테스트 및 개선
- **현재 상태**: 단위 테스트 10건 통과. 전체 기능 연동·통합 테스트는 **미수행**(서버 미구현).
- **확인 근거**: `tests/test_analyzer.py` 10건 통과. 서버·수집 관련 테스트 없음.
- **문제점**: IDE(.vscode)가 unittest로 설정되어 pytest 테스트를 인식하지 못함(3절).
- **다음 작업**: 서버 구현 후 Webhook→수집→탐지 end-to-end 테스트 추가, IDE 테스트 설정 정리.

## 7. 다음 단계 (우선순위)

1. **(선행)** README·requirements·.vscode의 문서/설정 차이 정리(낮은 위험, 빠른 개선).
2. FastAPI 기본 서버 + `GET /health` 구현, fastapi·uvicorn·httpx 의존성 고정.
3. `POST /webhook` + **HMAC-SHA256 서명 검증**(401 처리).
4. GitHub REST API로 워크플로우 파일 수집 → `analyze_text` 연결 → 결과 로그.
5. end-to-end 통합 테스트(TestClient + 샘플 페이로드).

## 8. 관련 문서 및 커밋

- [프로젝트 소개](../README.md)
- [1주차 기초 학습](week1-study.md) · [2주차 구조 설계](week2-design.md) · [3주차 탐지 규칙 구현](week3-detection.md)
- 커밋 정보: 이 문서 커밋 후 본문에 해시·메시지 기록 예정.

> 형식 참고: 기존 week1·week2 문서는 "산출물/완료·미구현" 등 서술 방식이 조금씩 다르다. 본 문서는 **week3의 번호형 구성**을 공통 템플릿으로 따랐다. 기존 문서 소급 통일은 내용 보존을 위해 이번에 수행하지 않았다(필요 시 별도 작업으로 제안).

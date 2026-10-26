# 4주차: FastAPI 서버·Webhook 구현 및 FastAPI/REST 조사

- 기간: 10/5~10/25 (README 개발 계획 기준) · 문서 작성일: 2026-10-26
- 주제: 3주차 탐지 엔진을 실제 이벤트 흐름에 연결. FastAPI 서버·Webhook 수신·서명 검증·워크플로우 수집을 구현하고, FastAPI/REST를 조사한다.

## 1. 이번 주 목표

GitHub 이벤트를 받는 **FastAPI 서버**와 **Webhook 서명 검증**, **워크플로우 파일 수집**을 구현하고,
수집한 파일을 3주차 탐지 엔진에 연결해 탐지 결과를 반환한다.
구현에 앞서 현재 상태를 실행 점검하고 FastAPI/REST를 조사한다.
이번 주 범위는 **탐지 결과 반환까지**이며, LLM 수정안·검증·PR 연동은 포함하지 않는다.

## 2. 처리 흐름

```text
GitHub 이벤트(push / pull_request)
  -> POST /webhook
  -> 서명 검증 (HMAC-SHA256, X-Hub-Signature-256)
  -> 이벤트 파싱 (저장소·ref 추출)
  -> GitHub REST API로 .github/workflows/*.yml 수집
  -> 탐지 엔진 실행 (analyze_text)
  -> 탐지 결과(JSON) 반환
```

## 3. 구현한 것

| 파일 | 내용 |
| --- | --- |
| `app/main.py` | FastAPI 앱, `GET /health`, webhook 라우터 등록 |
| `app/config.py` | 환경변수 설정(`Settings`, `.env`에서 로드) |
| `app/webhook/signature.py` | HMAC-SHA256 서명 검증 |
| `app/webhook/events.py` | push/pull_request 페이로드 → 저장소·ref 추출 |
| `app/webhook/router.py` | `POST /webhook`: 검증 → 수집 → 분석 → 결과 반환 |
| `app/github/client.py` | GitHub contents API로 `.github/workflows` 수집 |
| `tests/test_webhook.py` | 서명·이벤트 분기·탐지 연결 테스트 6건 |
| `.env.example` | 필요한 환경변수 예시(비밀값 미포함) |

## 4. 설계 결정

- **서명 검증을 인증과 분리**: GitHub `X-Hub-Signature-256`(HMAC-SHA256)로 요청 위변조만 확인하고, 불일치 시 401을 반환한다.
- **설정을 요청 시점에 환경변수에서 로드**: 테스트가 환경변수만 바꿔 검증할 수 있고, 비밀값은 `.env`(커밋 제외)에 둔다.
- **수집기를 함수로 분리**(`collect_workflows`): 네트워크 없이 테스트에서 교체(monkeypatch)할 수 있고, 엔진은 `analyze_text(text)`를 그대로 재사용한다.
- **느슨한 실패 처리**: 지원하지 않는 이벤트는 200(ignored), 워크플로우 폴더가 없으면 빈 결과로 처리해 한 요청 실패가 전체를 막지 않는다.

## 5. 구현 중 겪은 문제와 해결

1. **라우트 조회가 비어 보임** — FastAPI 0.162에서 `include_router`가 라우트를 즉시 평탄화하지 않고 `_IncludedRouter`로 지연 등록해 `app.routes` 출력에 `/webhook`이 보이지 않았다. 요청 시에는 정상 라우팅되며 테스트로 확인(버그 아님).
2. **테스트의 외부 의존 제거** — 실제 GitHub 호출을 피하려 `collect_workflows`를 monkeypatch로 교체해 토큰·네트워크 없이 오프라인 테스트.
3. **서명 대상 바이트** — 서명은 전송된 원본 body 기준이어야 하므로, 라우터에서 `request.body()`로 원본을 받아 **파싱 전에** 검증한다.

## 6. 검증 결과

```text
python -m pytest        # 16 passed (분석 10 + 서버 6)
# GET /health            -> {"status": "ok"}
# 잘못된 서명             -> 401 / ping -> pong
# 미지원 이벤트           -> 200 {"status":"ignored"}
# push(취약 워크플로우)   -> unpinned-actions·excessive-permissions 탐지 반환
uvicorn app.main:app --reload   # 로컬 서버 기동 확인
```

- 기존 CLI(`python -m app.analyzer`)와 탐지 테스트 10건도 그대로 통과(회귀 없음).
- 실행 환경(확인): Python 3.10.9 / fastapi 0.162 · uvicorn 0.54 · httpx 0.28 · PyYAML 6.0.3 · pytest 7.1.2.

## 7. FastAPI / REST API 자료조사

- 조사일: 2026-10-26 · 공식 문서 기준 · 버전: FastAPI 0.136+ (Python 3.10+, Pydantic v2). 본 프로젝트는 설치 시점 기준 fastapi 0.162 사용.
- **구분**: FastAPI = API를 만드는 웹 프레임워크(도구) / REST = API 설계 방식(스타일).

| 주제 | 요점 | 프로젝트 적용 |
| --- | --- | --- |
| APIRouter | 기능별 라우터 분리 | `app/webhook/router.py` 로 webhook 분리 |
| 요청/응답·검증 | Pydantic 모델·자동 검증(실패 422) | 페이로드에서 필요한 필드만 사용 |
| 의존성 주입 | `Depends` | 설정 로드(향후 DI 전환 여지) |
| 오류 처리 | `HTTPException` | 서명 불일치 401, 설정 누락 500 |
| 인증/보안 | security 유틸, 서명 검증은 별개 | HMAC-SHA256 서명 검증 |
| 테스트 | `TestClient`(httpx 기반) | `tests/test_webhook.py` |
| REST 메서드/상태코드 | GET/POST…, 200/401/500 등 | `GET /health`, `POST /webhook` |

출처(2026-10-26): https://fastapi.tiangolo.com/tutorial/bigger-applications/ ·
https://fastapi.tiangolo.com/tutorial/testing/ · https://pypi.org/project/fastapi/ ·
REST 참고 https://learn.microsoft.com/azure/architecture/best-practices/api-design

## 8. 실행 점검에서 확인한 문서·설정 차이 (부가)

구현 전 실행 점검에서 확인한, 코드와 문서/설정의 차이. 이번 주에 일부만 반영했다.

| 위치 | 차이 | 처리 |
| --- | --- | --- |
| `requirements.txt` | `pytest>=8.0` vs 설치 7.1.2 | `>=7.1`로 정정(반영) |
| README 상태/실행 안내 | Webhook 미제공으로 표기 | 서버 제공으로 갱신(반영) |
| README 시스템 구성 | 규칙 엔진 **Semgrep** 표기 | 실제는 PyYAML 자체 규칙 — 미반영(확인 필요) |
| `.vscode/settings.json` | unittest/`*test.py` 설정 | pytest와 불일치 — 미반영(제안) |

## 9. 한계와 다음 단계

알려진 한계:
- end-to-end는 수집기를 모킹해 검증했고, **실제 GitHub 토큰 연동은 미검증**이다.
- `pull_request_target` 등 이벤트별 보안 정책은 아직 반영하지 않았다.
- 탐지 결과는 **반환만** 하며 저장·PR 반영은 없다.

다음 단계:
1. 탐지 결과(`Finding`)를 바탕으로 한 LLM 수정안 생성(`app/fixer/`).
2. 수정안 형식 검증과 취약점 재분석(`app/validator/`).
3. 탐지·수정 결과를 PR 코멘트/체크로 제공(GitHub API).

## 10. 관련 문서 및 커밋

- [프로젝트 소개](../README.md)
- [1주차 기초 학습](week1-study.md) · [2주차 구조 설계](week2-design.md) · [3주차 탐지 규칙 구현](week3-detection.md)
- 커밋: `ee83ffb` (FastAPI 서버·Webhook·수집 구현) · `be8f985` (실행 점검·계획 검증·FastAPI/REST 조사)

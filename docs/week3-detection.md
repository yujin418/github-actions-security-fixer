# 3주차: 초기 탐지 규칙 구현

- 기간: 9/28~10/4
- 주제: 초기 3개 취약 패턴의 탐지 규칙 구현 및 탐지 결과 형식 확정

## 1. 이번 주 목표

2주차에서 정리한 설계를 바탕으로 초기 탐지 대상 3종의 탐지 조건을 구체화하고,
실제로 동작하는 탐지 규칙과 탐지 결과 형식을 구현한다.
이번 주 범위는 **탐지**까지이며, LLM 수정안 생성·검증·PR 연동은 포함하지 않는다.

## 2. 탐지 대상과 조건

각 규칙의 선언적 정의는 [`rules/`](../rules/) 에 YAML 로 기록했고,
탐지 로직은 [`app/analyzer/`](../app/analyzer/) 에서 이 메타데이터를 사용한다.

| 규칙 | 탐지 조건 | 제외 조건 | 자동 수정 |
| --- | --- | --- | --- |
| Script Injection | `run` 안의 `${{ }}` 표현식이 신뢰할 수 없는 컨텍스트(`github.event.*` 등) 참조 | 신뢰 컨텍스트(`github.sha` 등), `env` 바인딩 후 사용 | 이번 주 미지원(제안만) |
| Excessive Permissions | `permissions: write-all`, 또는 권한 블록 전무(기본값 적용) | 세분화된 권한이고 `write-all` 아님 | 미지원(검토 대상) |
| Unpinned Actions | `uses` 의 ref 가 40자리 커밋 SHA 가 아님 | 로컬(`./`)·SHA 고정·`docker://` | 미지원(SHA 조회 필요) |

탐지 조건과 자동 수정 가능 조건을 구분한다는 2주차 원칙에 따라,
이번 주에는 세 규칙 모두 **탐지만** 수행하고 자동 수정 가능 여부를 메타데이터에 명시했다.

## 3. 탐지 결과 형식

탐지 1건은 [`app/analyzer/models.py`](../app/analyzer/models.py) 의 `Finding` 으로 표현한다.
이후 단계(fixer, PR 결과 표시)가 그대로 사용할 고정 형식이다.

| 필드 | 설명 |
| --- | --- |
| `rule_id` | 규칙 식별자 (예: `unpinned-actions`) |
| `rule_name` | 사람이 읽는 규칙 이름 |
| `severity` | `high` / `medium` / `low` |
| `file` | 분석한 파일 경로 |
| `line` | 근거 위치의 1-based 행 번호 |
| `evidence` | 탐지 근거가 된 원본 조각 |
| `message` | 무엇이 왜 문제인지 |
| `remediation` | 어떻게 고치는지 |
| `autofixable` | 현재 단계의 자동 수정 지원 여부 |

## 4. 구현 구조

```text
rules/
├── script-injection.yml         # 규칙 메타데이터(조건·근거·참고링크)
├── excessive-permissions.yml
└── unpinned-actions.yml
app/analyzer/
├── __init__.py                  # analyze_text / analyze_file 진입점
├── __main__.py                  # python -m app.analyzer CLI
├── models.py                    # Finding 데이터 형식
├── rules.py                     # rules/ 메타데이터 로더
└── detectors.py                 # 세 규칙의 탐지 로직
tests/
├── test_analyzer.py             # 탐지/오탐 테스트 10건
└── workflows/
    ├── vulnerable/              # 규칙별 취약 예제
    └── safe/                    # 정상(오탐 확인용) 예제
```

## 5. 실행 방법

```bash
pip install -r requirements.txt

# 테스트 실행
python -m pytest

# 워크플로우 디렉터리 스캔 (기본: .github/workflows)
python -m app.analyzer tests/workflows
```

## 6. 진행 결과

예제 스캔 결과, 취약 예제 3종에서 의도한 패턴이 모두 탐지되고
정상 예제 2종에서는 오탐이 없었다.

```text
vulnerable/excessive-permissions.yml  [MEDIUM] L7  write-all
vulnerable/script-injection.yml       [HIGH]   L15 github.event.issue.title
vulnerable/unpinned-actions.yml       [MEDIUM] L15 actions/checkout@v4
                                      [MEDIUM] L17 actions/setup-node@main
```

- 테스트 10건 통과 (취약 탐지 3건, 오탐 없음 확인, 동작 세부 조건 등)
- 탐지 결과 형식(`Finding`) 확정

## 7. 한계와 다음 단계

알려진 한계:
- 행 번호는 원본 텍스트 검색으로 찾으므로, 동일 조각이 겹칠 때 정확도가 제한적이다.
- 개별 `write` 스코프의 적정성은 판단하지 않고 `write-all`·권한 미설정만 다룬다.
- Script Injection 은 `run` 만 대상으로 하며 `actions/github-script` 등은 미포함.

다음 단계:
1. FastAPI 기본 서버와 Webhook 수신·요청 검증(`app/webhook/`) 구현, GitHub 이벤트에서 Workflow 파일을 수집해 이번 주 탐지 엔진에 연결.
2. 탐지 결과를 바탕으로 한 LLM 수정안 생성(`app/fixer/`) 설계.
3. 수정안 형식 검증과 취약점 재분석(`app/validator/`) 연결.
4. Unpinned Actions 의 태그→커밋 SHA 조회를 위한 GitHub API 연동 검토.

## 8. 관련 문서

- [프로젝트 소개](../README.md)
- [2주차 구조 설계](week2-design.md)

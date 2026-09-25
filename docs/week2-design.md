# Week 2 Design

## 이번 주 목표

취약 사례 조사 이후 프로젝트의 초기 탐지 범위와 전체 처리 흐름을 정리하고,
구현에 사용할 폴더 및 기본 파일을 생성한다.
이번 주 결과물은 설계와 프로젝트 뼈대이며, 실제 탐지·수정 기능은 아직 구현하지 않는다.

## 초기 탐지 범위

아래 항목을 1차 구현 대상으로 검토한다.

| 항목 | 탐지 대상으로 검토할 내용 | 구현 전 정할 사항 |
|---|---|---|
| Script Injection | 신뢰할 수 없는 입력을 실행 스크립트에 직접 삽입하는 패턴 | 입력 출처, 셸 종류, 안전한 값 전달 방식과 수정 조건 |
| Excessive GITHUB_TOKEN Permissions | 필요 이상으로 넓게 설정된 토큰 권한 | 작업별 필요 권한과 분석만으로 판단할 수 없는 경우의 처리 |
| Unpinned Actions | 커밋 SHA로 고정되지 않은 외부 Action 참조 | 참조 유형 구분, 실제 커밋 확인 및 수정 후 검증 방식 |

정적 분석 규칙과 수정 조건을 단계적으로 정의할 수 있는 항목부터 구현한다.
탐지 결과가 나왔다고 해서 모든 항목을 자동 수정할 수 있다고 가정하지 않는다.

Pwn Request와 Artifact Trust는 추가적인 신뢰 관계나 여러 Workflow 사이의 흐름을
검토하는 확장 대상으로 남겨둔다. 구체적인 공개 취약 사례와 출처는 이 문서에
기록하지 않았으며, 사례 조사 기록과 구현 범위 설계를 구분한다.

## 전체 처리 흐름 (설계안)

```text
GitHub Push / Pull Request
  -> Webhook 수신 및 요청 검증
  -> GitHub API로 Workflow 파일 수집
  -> YAML 구조 분석 및 보안 규칙 기반 탐지
  -> 취약점 탐지 결과 생성
  -> LLM 기반 수정안 생성
  -> 수정안 검증 및 재분석
  -> 검증을 통과한 수정안의 Pull Request 제안
```

수정안 검증에서 문제가 발견되면 자동 반영하지 않고 검토 대상으로 남기는 방향으로 설계한다.
검증 항목과 통과 기준, 이벤트별 처리 정책은 이후 구현 단계에서 구체화한다.

## 모듈별 역할

| 경로 | 예정된 역할 |
|---|---|
| `app/main.py` | 애플리케이션 진입점 |
| `app/webhook/` | GitHub 이벤트 수신 및 요청 검증 |
| `app/analyzer/` | Workflow 파싱, 보안 규칙 실행 및 탐지 결과 정리 |
| `app/fixer/` | 탐지 결과를 바탕으로 LLM 수정안 생성 |
| `app/validator/` | 수정안의 형식 검증 및 취약점 재분석 |
| `app/github/` | Workflow 조회, 수정 브랜치 및 Pull Request 생성 등 GitHub API 연동 |
| `app/database/` | 분석 결과 저장 영역 (도입 여부와 저장 방식은 추후 결정) |
| `rules/` | Semgrep 등 보안 탐지 규칙 |
| `tests/` | 테스트 코드와 취약·수정 Workflow 예제 |
| `docs/` | 주차별 학습 및 설계 기록 |

## 생성한 프로젝트 구조

```text
app/
├── __init__.py
├── main.py
├── webhook/__init__.py
├── analyzer/__init__.py
├── fixer/__init__.py
├── validator/__init__.py
├── github/__init__.py
└── database/__init__.py
rules/
└── .gitkeep
tests/
└── .gitkeep
requirements.txt
README.md
.gitignore
```

- `__init__.py`: Python 패키지를 구성하기 위한 빈 파일이다.
- `main.py`: 설명만 있는 진입점 자리이며 서버를 실행하지 않는다.
- `.gitkeep`: 빈 폴더를 Git에 포함하기 위한 파일이다.
- `requirements.txt`: 설명만 작성했으며 의존성은 구현 시 추가한다.
- `.gitignore`: 기존 Python용 설정을 유지했다.
- 기존 1주차 학습 문서와 예제 Workflow는 유지했다.

## 현재 완료한 작업과 남은 작업

완료:
- 초기 탐지 대상과 확장 대상 구분
- 전체 처리 흐름 및 모듈별 역할 정리
- 프로젝트 폴더와 기본 파일 생성
- README에 설계 범위와 현재 상태 기록

미구현:
- Webhook 서버와 GitHub API 연동
- YAML 파서 및 실제 탐지 규칙
- LLM 수정안 생성
- 수정안 검증과 Pull Request 생성
- 분석 결과 저장 및 테스트 코드

## 다음 단계

1. 초기 탐지 대상별 탐지 조건, 제외 조건, 자동 수정 가능 조건을 구체화한다.
2. 취약 예제와 정상 예제를 `tests/`에 준비한다.
3. `rules/`에 첫 탐지 규칙을 구현하고 예제에 적용한다.
4. 탐지 결과에 포함할 파일 경로, 위치, 규칙 이름 등의 형식을 정한다.
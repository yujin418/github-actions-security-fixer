# github-actions-security-fixer
GitHub Actions workflow vulnerability detection and AI-based fix suggestion tool

GitHub Actions 워크플로우에서 발생할 수 있는 보안 취약점을
자동으로 탐지하고 AI를 활용하여 수정 방법을 제안하는 프로젝트입니다.

## Project Goal

- GitHub Actions 주요 보안 취약점 탐지
- AI 기반 취약점 수정 방법 제안
- GitHub PR에 분석 결과 제공

## Tech Stack

- Python
- FastAPI
- Semgrep
- GitHub API
- LLM API

## Progress

### Week 2
- GitHub Actions 기본 개념 학습
- GitHub Actions 보안 사례 조사
- 프로젝트 Repository 구성

- 초기 탐지 대상과 확장 대상 구분
- 전체 처리 흐름 및 모듈별 역할 설계
- 프로젝트 디렉터리와 기본 파일 생성
- 현재는 구조 설계 단계이며 탐지, 서버, LLM 연동 등 기능은 구현하지 않음

## Initial Detection Scope

1차 구현 대상으로 검토하는 취약점:
- Script Injection
- Excessive GITHUB_TOKEN Permissions
- Unpinned Actions

Pwn Request와 Artifact Trust는 확장 대상으로 검토합니다.
탐지된 모든 항목을 자동 수정할 수 있다고 가정하지 않으며,
자동 수정 조건과 검증 기준은 각 기능 구현 시 정의합니다.

## Planned Flow

```text
GitHub Push / Pull Request
  -> Webhook 수신
  -> GitHub API로 Workflow 파일 수집
  -> YAML 구조 분석 및 보안 규칙 기반 탐지
  -> LLM 기반 수정안 생성
  -> 수정안 검증 및 재분석
  -> 검증을 통과한 수정안의 Pull Request 제안
```

## Project Structure

```text
github-actions-security-fixer/
├── .github/workflows/hello.yml   # 1주차 예제 워크플로
├── app/
│   ├── __init__.py
│   ├── main.py                  # 애플리케이션 진입점 예정
│   ├── webhook/__init__.py      # 이벤트 수신 및 요청 검증 예정
│   ├── analyzer/__init__.py     # Workflow 파싱 및 취약점 탐지 예정
│   ├── fixer/__init__.py        # LLM 기반 수정안 생성 예정
│   ├── validator/__init__.py    # 수정안 검증 및 재분석 예정
│   ├── github/__init__.py       # GitHub API 연동 예정
│   └── database/__init__.py     # 분석 결과 저장 예정 (도입 여부 추후 결정)
├── docs/
│   └── week1-study.md
├── rules/
│   └── .gitkeep                 # 보안 탐지 규칙 추가 예정
├── tests/
│   └── .gitkeep                 # 테스트 및 취약/수정 예제 추가 예정
├── .gitignore
├── requirements.txt
└── README.md
```

`__init__.py`는 Python 패키지 구성을 위한 빈 파일입니다.
Git은 빈 폴더를 추적하지 않으므로 `rules/`와 `tests/`에는 `.gitkeep`을 둡니다.
실제 파일을 추가하면 해당 폴더의 `.gitkeep`은 제거해도 됩니다.

## Current Setup

현재 실행 가능한 서버나 분석 명령은 없습니다.
`app/main.py`는 진입점 자리만 마련한 파일이며,
`requirements.txt`는 기능 구현 시 필요한 의존성과 버전을 추가할 예정입니다.
지금은 패키지 설치나 API 키 설정이 필요하지 않습니다.

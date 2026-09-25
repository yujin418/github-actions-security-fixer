# 1주차: 기초 학습 및 개발 환경 구성

- 기간: 9/14~9/20
- 주제: GitHub Actions 기본 개념 및 보안 관련 기초 학습

## 1. 이번 주 목표

GitHub Actions의 기본 구성과 보안 점검 시 고려할 사항을 학습하고,
프로젝트를 진행할 저장소와 예제 Workflow를 준비한다.

## 2. 주요 진행 내용

### GitHub Actions 기본 개념

GitHub 저장소에서 빌드, 테스트, 배포 등의 작업을 자동화할 수 있는 CI/CD 기능이다.

### Workflow 구조

Workflow는 자동화할 작업을 정의한 YAML 파일이다.
이벤트가 발생하면 Workflow가 실행되고, 내부의 Job과 Step에 정의된 작업을 수행한다.

```text
Event → Workflow → Job → Step
```

### 주요 구성 요소

| 구성 요소 | 역할 |
| --- | --- |
| `on` | Workflow 실행 조건 |
| `jobs` | Workflow 내부의 작업 정의 |
| `steps` | Job 내부의 세부 작업 |
| `uses` | 기존 Action 사용 |
| `run` | 명령어 실행 |

### 보안 관련 조사

| 항목 | 학습 내용 |
| --- | --- |
| 권한 설정 | Workflow에 필요 이상의 권한을 부여하면 보안 문제가 발생할 수 있다. |
| Third-party Action | 외부 Action 사용 시 참조 방식과 공급망 보안을 고려해야 한다. |
| `pull_request_target` | 권한이 높은 실행 맥락에서 신뢰할 수 없는 PR 코드를 함께 사용할 때 주의해야 한다. |

## 3. 진행 결과

### 정리한 내용

- GitHub Actions와 Workflow의 기본 개념
- Event, Job, Step의 관계 및 주요 YAML 구성 요소
- 권한 설정, 외부 Action, PR 이벤트와 관련된 보안 고려 사항

### 산출물

- 프로젝트 GitHub Repository
- 예제 Workflow: [hello.yml](../.github/workflows/hello.yml)
- 1주차 학습 기록: 이 문서

## 4. 다음 단계

1. GitHub Actions 취약 사례를 분석한다.
2. 초기 탐지 대상과 확장 대상을 구분한다.
3. 전체 처리 흐름과 모듈별 역할을 설계한다.
4. 프로젝트 폴더와 기본 파일을 생성한다.

## 5. 관련 문서

- [프로젝트 소개](../README.md)
- [2주차 구조 설계](week2-design.md)

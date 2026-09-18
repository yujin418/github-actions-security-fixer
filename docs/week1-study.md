# Week 1 Study

## GitHub Actions

GitHub 저장소에서 빌드, 테스트, 배포 등의 작업을
자동화할 수 있는 CI/CD 기능이다.

## Workflow

자동화할 작업을 정의한 YAML 파일이다.

기본 구조:

Event
→ Workflow
→ Job
→ Step

## 주요 구성 요소

- on: Workflow 실행 조건
- jobs: 실행할 작업
- steps: Job 내부의 세부 작업
- uses: 기존 Action 사용
- run: 명령어 실행

## 보안 관련 조사

### 1. 권한 설정
Workflow에 필요 이상의 권한을 부여하면 보안 문제가 발생할 수 있다.

### 2. Third-party Action
외부 Action 사용 시 참조 방식과 공급망 보안을 고려해야 한다.

### 3. pull_request_target
권한이 높은 이벤트이므로 신뢰할 수 없는 PR 코드와 함께 사용할 때 주의해야 한다.

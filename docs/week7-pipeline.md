# 7주차: 전체 기능 연동 (pipeline)

- 기간: 11/9~11/15 (README 개발 계획 기준) · 문서 작성일: 2026-11-14
- 주제: 탐지→수정안→검증→결과 제공을 하나의 파이프라인으로 연결하고, Webhook 엔드포인트에 연결한다. 실제 LLM 연동 경로도 구성한다.
- 범위: 파이프라인 연결과 결과(PR 코멘트) 생성까지. **실제 PR 게시와 실제 LLM 호출 검증은 다음(보완) 단계.**

## 1. 이번 주 목표

3~6주차에서 만든 모듈(analyzer·fixer·validator)을 하나의 흐름으로 연결한다.
Webhook으로 이벤트가 오면 워크플로우를 수집해 **탐지→수정안→검증→결과 제공**까지 자동으로 수행한다.
LLM은 주입식으로 두어, 키가 있으면 실제 모델을, 없으면 탐지만 수행한다.

## 2. 처리 흐름

```text
POST /webhook (서명 검증)
  -> 워크플로우 수집 (GitHub API)
  -> run_pipeline(workflows, llm)
        파일별: analyze_text -> (LLM) suggest_fixed_workflow -> validate_fix
  -> format_report -> PR 코멘트(JSON 응답의 report)
```

## 3. 구현한 것

| 파일 | 내용 |
| --- | --- |
| `app/pipeline.py` | `run_pipeline`, `format_report`, `build_llm`, `PipelineItem` |
| `app/fixer/__init__.py` | `suggest_fixed_workflow`(전체 수정 워크플로우 요청) 추가 |
| `app/webhook/router.py` | `/webhook`에 파이프라인 연결, 응답에 `report` 포함 |
| `tests/test_pipeline.py` | 탐지전용/수정검증/미해소/리포트/`build_llm` 테스트 7건 |
| `tests/test_webhook.py` | 파이프라인 결과(report) 포함 테스트 1건 추가 |

## 4. 설계 결정

- **LLM 주입식 + build_llm**: `run_pipeline(workflows, llm)`은 주입된 클라이언트로 테스트한다. `build_llm()`은 `ANTHROPIC_API_KEY`·`LLM_MODEL`이 있으면 실제 클라이언트를, 없으면 `None`을 돌려줘 **키 없이도 탐지만으로 동작**한다.
- **전체 수정 워크플로우 방식**: 스니펫 대신 LLM에게 **수정된 전체 YAML**을 받아, 그대로 `validate_fix`로 재분석한다. "고친 결과가 실제로 유효하고 취약점을 없앴는가"를 바로 판정할 수 있다.
- **느슨한 실패 처리**: 수정안 파싱 실패 시 해당 항목은 검토 대상으로 남기고 파이프라인은 계속된다. 탐지 없는 파일은 건너뛴다.
- **결과는 report(마크다운)까지**: 실제 PR 게시(GitHub API 쓰기)는 다음 단계.

## 5. 구현 중 겪은 문제와 해결

1. **기존 webhook 응답 호환** — 응답에 `report`를 추가하되 `repo·ref·files·findings` 키를 유지해 기존 테스트가 깨지지 않게 했다.
2. **키 없는 환경** — `build_llm`이 키·모델이 모두 있을 때만 실제 클라이언트를 import·생성하도록 해, `anthropic` 미설치·키 미설정에서도 동작한다.
3. **데모 일원화** — `scripts/demo_pipeline.py`를 실제 `run_pipeline`을 쓰도록 바꿔(데모용 LLM 주입), 데모와 실제 코드 경로를 일치시켰다.

## 6. 검증 결과

```text
python -m pytest        # 37 passed (분석 10 + 서버 7 + fixer 7 + validator 6 + pipeline 7)

python scripts/demo_pipeline.py   # 전체 파이프라인 데모
# .github/workflows/unpinned-actions.yml  -> 검증 ✅ 통과
# .github/workflows/excessive-permissions.yml -> 검증 ✅ 통과
# + PR 코멘트 미리보기 출력
```

- 모킹/데모 LLM으로 전 과정(탐지→수정안→검증→리포트) 동작 확인.
- 실제 LLM 호출 경로(`build_llm`→`AnthropicClient`)는 구성했으나, 키·패키지가 필요해 **실제 호출은 미검증(확인 필요)**.

## 7. 한계와 다음 단계

알려진 한계:
- 실제 LLM 호출은 미검증(키·`anthropic` 설치 시 활성화).
- 결과는 JSON `report`로 반환만 하며, **실제 PR 코멘트 게시는 미구현**.
- 수정안 품질은 LLM·프롬프트에 의존하며, 복잡한 수정은 검증에서 걸러진다(통과만 신뢰).

다음 단계:
1. 실제 LLM 연동 검증(`.env`에 키·모델 설정, `pip install anthropic`).
2. 통과한 수정안을 PR 코멘트/브랜치로 게시(GitHub API 쓰기).
3. 테스트 저장소를 활용한 통합 테스트(11/16~).

## 8. 관련 문서 및 커밋

- [프로젝트 소개](../README.md)
- [1주차](week1-study.md) · [2주차](week2-design.md) · [3주차](week3-detection.md) · [4주차](week4-backend.md) · [5주차](week5-fixer.md) · [6주차](week6-validator.md)
- 커밋: 이 문서 커밋 시 해시 기록.

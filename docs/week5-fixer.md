# 5주차: AI 수정안 및 변경 이유 생성 (fixer)

- 기간: 10/26~11/1 (README 개발 계획 기준) · 문서 작성일: 2026-10-31
- 주제: 탐지 결과(`Finding`)를 입력으로 받아 취약점별 **수정안과 변경 이유**를 생성하는 `app/fixer` 구현.
- 범위: 이번 주는 **수정안 생성까지**이며, 수정안 형식 검증·재분석(`validator`)과 PR 반영은 다음 주.

## 1. 이번 주 목표

3주차 탐지 결과를 바탕으로, 각 취약점에 대한 **최소 수정안**과 **"왜 이렇게 고치는지"** 변경 이유를 LLM으로 생성한다.
LLM 제공자에 종속되지 않도록 클라이언트를 추상화하고, 테스트는 모킹해 **키 없이 오프라인으로 검증**한다.

## 2. 처리 흐름

```text
Finding(탐지 결과) + 워크플로우 원문
  -> 프롬프트 생성 (규칙·근거·설명·권장 방향·워크플로우 포함)
  -> LLMClient.complete(prompt)   (테스트는 MockLLMClient)
  -> 응답(JSON) 파싱 -> 실패 시 원문·remediation 으로 폴백
  -> FixSuggestion(수정안 + 변경 이유 + 모델) 반환
```

## 3. 구현한 것

| 파일 | 내용 |
| --- | --- |
| `app/fixer/llm.py` | LLM 클라이언트 추상화(`LLMClient` 프로토콜), `MockLLMClient`, `AnthropicClient`(지연 로드·미검증) |
| `app/fixer/__init__.py` | `FixSuggestion`, `build_prompt`, `generate_fix`, `generate_fixes` |
| `tests/test_fixer.py` | 프롬프트 구성·JSON 파싱·폴백·다건 처리 테스트 7건 |
| `scripts/demo_fixer.py` | 탐지→수정안·변경 이유 출력 데모(발표용, Mock 예시 응답) |
| `.env.example` | `ANTHROPIC_API_KEY`·`LLM_MODEL`(선택) 항목 추가 |

`FixSuggestion` 필드: `rule_id`, `file`, `line`, `original`(탐지 근거), `suggestion`(수정안), `reason`(변경 이유), `model`(생성 모델).

## 4. 설계 결정

- **제공자 추상화 + 모킹 우선**: fixer는 `complete(prompt)` 하나에만 의존한다. 테스트는 `MockLLMClient`로 키·네트워크 없이 검증하고, 실제 키는 `.env` 필요 항목으로만 정리한다(임의 생성하지 않음).
- **응답은 JSON 계약**: LLM에 `{"suggestion","reason"}` JSON만 요청한다. 코드펜스로 감싸거나 파싱이 실패하면 원문을 이유로, `remediation`을 폴백으로 사용해 **잘못된 응답이 파이프라인을 멈추지 않게** 한다.
- **엔진 재사용**: 입력은 3주차 `Finding` 그대로. 탐지→수정안 생성이 자연스럽게 연결된다.

## 5. 구현 중 고려한 점

1. **키 의존 제거** — `AnthropicClient`는 `anthropic` 패키지와 키를 **지연 로드**해, 모킹으로 쓰는 동안에는 둘 다 없어도 동작한다.
2. **파싱 견고성** — 응답에서 첫 `{`~마지막 `}` 구간만 떼어 JSON 파싱, 실패 시 폴백.
3. **모델 식별자 미고정** — 모델 ID는 `LLM_MODEL` 환경변수로 받으며, 코드에 특정 버전을 박지 않았다(실제 연동 시 지정).

## 6. 검증 결과

```text
python -m pytest            # 23 passed (분석 10 + 서버 6 + fixer 7)

python scripts/demo_fixer.py   # 발표용 데모 (어느 셸에서나 한글 출력)
# [MEDIUM] excessive-permissions  -> permissions: contents: read      + 이유
# [HIGH]   script-injection       -> env 바인딩 후 "$TITLE"           + 이유
# [MEDIUM] unpinned-actions        -> actions/checkout@<SHA>  # v4      + 이유
# [MEDIUM] unpinned-actions        -> actions/setup-node@<SHA> # main   + 이유
# 총 4건 탐지·수정안 생성 (3개 파일)
```

- 모킹 클라이언트로 전 과정(탐지→수정안) 동작 확인. 데모는 규칙별 예시 응답(Mock)이며, 실제 LLM 호출은 **미검증(확인 필요)**.

## 7. 한계와 다음 단계

알려진 한계:
- 실제 LLM 연동(`AnthropicClient`)은 키·패키지가 필요하며 이번 주 **미검증**이다.
- 수정안의 **형식 유효성·취약점 해소 여부는 아직 검증하지 않는다**(다음 주 validator).
- webhook 파이프라인에는 아직 연결하지 않았다(수정안 생성은 독립 모듈).

다음 단계:
1. 수정안 형식 검증과 취약점 재분석(`app/validator/`) — 고친 YAML이 유효하고 해당 취약점이 사라지는지 확인.
2. 탐지→수정안→검증 결과를 webhook 파이프라인/PR에 연결.
3. 실제 LLM 연동 검증 및 모델·프롬프트 튜닝.

## 8. 관련 문서 및 커밋

- [프로젝트 소개](../README.md)
- [1주차](week1-study.md) · [2주차](week2-design.md) · [3주차](week3-detection.md) · [4주차](week4-backend.md)
- 커밋: `ed4864f`(fixer 구현) · `498b58d`(탐지→수정안 데모 스크립트)

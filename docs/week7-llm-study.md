# 7주차 자료조사: 수정안 생성을 위한 LLM API

- 조사일: 2026-11-14
- 주제: `fixer`의 LLM 연동을 위한 제공자별 API 비교와 적용

## 조사 목적

`fixer`는 탐지 결과를 바탕으로 **수정안과 변경 이유**를 생성하며, 이를 위해 외부 LLM API를 호출한다.
특정 제공자에 종속되지 않도록 연동하려면 각 API의 **호출 방식·응답 구조·모델·비용·운영 이슈**를
비교해야 한다. 이 조사를 바탕으로 제공자 추상화 방식과 기본 제공자를 정한다.

## 제공자 비교 요약

| 제공자 | SDK / 엔드포인트 | 호출 방식 | 응답 구조 | 성격 |
| --- | --- | --- | --- | --- |
| OpenAI | `openai` / `POST /v1/chat/completions` | `messages[]`(role/content) | `choices[0].message.content` (문자열) | 범용, 모델·생태계 다양 |
| Anthropic | `anthropic` / `POST /v1/messages` | `messages[]` + `max_tokens`(필수) | `content[]` 타입 블록의 `text` | Claude, 긴 컨텍스트 |
| (대체) 로컬·기타 | Ollama 등 OpenAI 호환 | 동일 포맷 많음 | 제공자별 | 비용·오프라인 |

핵심: 두 상용 API 모두 **"messages 배열 → 텍스트 응답"** 구조로 유사하다.
그래서 `complete(prompt)` 하나로 추상화하고, 제공자별 클라이언트만 갈아끼운다.

## 1. OpenAI API

- **엔드포인트**: `POST /v1/chat/completions`. 파라미터 `model`, `messages`(각 `{role, content}`), `max_tokens`, `temperature` 등.
- **응답**: `choices[0].message.content` (문자열 하나).
- **인증**: `Authorization: Bearer sk-...`.
- **모델/비용**(3rd-party 기준, 공식 확인 권장): `gpt-4o-mini` 약 **$0.15 / $0.60**(입력/출력, 1M 토큰), 컨텍스트 128K — 저렴해 기본값으로 적합. 상위로 `gpt-4.1-mini`($0.40/$1.60), `gpt-4.1`($2/$8).

**프로젝트 관점**: 비용이 낮고 접근성이 좋아 **기본 제공자로 채택**(기본 모델 `gpt-4o-mini`). 품질이 더 필요하면 `LLM_MODEL`로 상위 모델 지정.

## 2. Anthropic API

- **엔드포인트**: `POST /v1/messages`. `model`, `messages`, **`max_tokens`(필수)**.
- **응답**: `content[]` 배열의 타입 블록 중 `text` 블록을 이어 붙여 사용. (도구 사용 시 `tool_use`, 확장 사고 시 `thinking` 블록 추가 가능 — `thinking`은 `max_tokens`에 포함)
- **인증**: `x-api-key: sk-ant-...` + `anthropic-version` 헤더.

**프로젝트 관점**: **대체 제공자**. 키가 `sk-ant-`로 시작하는 점이 OpenAI(`sk-`)와 구분된다(이번 주 401 원인).

## 3. 출력 구조화 (수정안 받기)

- **JSON 계약 방식**: `{"suggestion","reason"}`만 요청 → 항목별 스니펫·이유. 파싱 쉬움, 재분석엔 부적합.
- **전체 수정 워크플로우 방식**: 고친 **전체 YAML**을 받아 `validate_fix`로 재분석 → "실제 해소 여부" 판정 가능.
- 공통 리스크: LLM이 JSON/코드펜스를 어긋나게 줄 수 있음 → **파싱 폴백** 필수.

**프로젝트 관점**: 파이프라인에는 **전체 YAML 방식**(`suggest_fixed_workflow`)을 써 검증까지 연결하고, PR 코멘트의 사람용 설명에는 JSON 스니펫 방식을 병행할 수 있다.

## 4. 운영 고려사항

| 항목 | 내용 | 우리 대응 |
| --- | --- | --- |
| 비용 | 토큰당 과금, 긴 워크플로우는 비용↑ | 저렴한 기본 모델, 필요 시 상향 |
| 재현성 | 응답이 매번 달라짐 | 테스트는 **모킹**(conftest로 실제 키 격리) |
| 키 관리 | 키 노출 위험 | **`.env`에만**(커밋 제외), dotenv 자동 로드 |
| 전송 계층 | httpx+zstandard의 zstd 해제 오류 | `Accept-Encoding: gzip, deflate`로 zstd 회피 |
| 레이트리밋/결제 | 계정 크레딧 필요 | 연동 전 Billing 확인 |

## 우리 프로젝트와의 연동 결과

| 구분 | 방식 |
| --- | --- |
| 추상화 | `LLMClient.complete(prompt)` 단일 인터페이스 |
| 선택 | `build_llm`: `OPENAI_API_KEY` → `ANTHROPIC_API_KEY` 순 |
| 테스트 | `MockLLMClient`로 오프라인 검증(37 passed) |
| 실제 연동 | **OpenAI 연동 성공**(`check_llm`), 기본 모델 `gpt-4o-mini` |

**정리**: 두 API는 호출·응답 구조가 유사해 추상화 비용이 낮았고, 실제 연동의 실무 이슈(키 형식, zstd 압축)를 해결했다. 수정안 **품질·취약점 해소율** 평가는 통합 테스트(8주차)에서 진행한다.

## 참고 자료 (조사일 2026-11-14)

- OpenAI Chat Completions: https://platform.openai.com/docs/api-reference/chat
- OpenAI 모델·가격: https://platform.openai.com/docs/pricing
- Anthropic Messages API: https://docs.anthropic.com/en/api/messages

## 관련 문서

- [전체 기능 연동 (파이프라인)](week7-pipeline.md)
- [프로젝트 소개](../README.md)

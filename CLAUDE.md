# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 저장소 개요

두 가지를 담는다.

- Claude Code 커스텀 서브에이전트(`.claude/agents/`)
- 다이어트용 간편 식단 기록 앱 "Easy Meal Log": 기준 문서 `docs/prd/easy-meal-log.md`, MVP 백엔드 `backend/`

## 백엔드 명령 (`backend/`에서 실행)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
APP_ENV=development .venv/bin/uvicorn app.main:create_app --factory --reload
.venv/bin/python -m pytest                                  # 전체 (pyproject addopts에 -q가 있어 -q를 또 주면 요약 줄이 사라짐)
.venv/bin/python -m pytest tests/test_fr2_create.py::<테스트명>  # 테스트 하나
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```

## 백엔드 구조

- Python + FastAPI + SQLite. 계층은 `app/api`(라우팅·검증·인증 의존성) → `app/services`(비즈니스 로직) → `app/repositories`(`base.py` Protocol, `sqlite.py` 구현). 구현체를 아는 곳은 `app/api/deps.py`뿐이다.
- 사용자(`users`)와 로그인 수단(`auth_identities`)이 분리돼 있다. 토큰은 `Authorization: Bearer` 불투명 토큰이고 DB에는 HMAC만 저장한다. 쿠키는 쓰지 않는다.
- "오늘"과 날짜 판정은 사용자별 IANA 시간대 기준이다. 기록 생성 중복 방지는 `Idempotency-Key` 헤더로 한다.
- 스키마는 `app/db/migrations/`의 up/down SQL로 관리하고 앱 시작 시 자동 적용된다.
- 테스트 파일은 PRD 기능 번호별(`tests/test_fr1_*.py` ~ `test_fr8_*.py`)이다. 요구사항을 바꾸면 PRD와 해당 테스트를 함께 고친다.
- 제품 원칙상 칼로리·중량 같은 수치, 점수·평가 필드를 API에 추가하지 않는다(PRD 2절).

## 구조

- `.claude/agents/<name>.md`: 프로젝트 범위 서브에이전트 정의. 파일 이름과 프론트매터의 `name`을 같게 맞춘다.
  - `code-reviewer.md`: 버그, 코딩 규칙, 성능을 점검하는 리뷰어. 기본은 읽기 전용이고, 지시에 수정이 포함될 때만 코드를 고친다.
  - `product-manager.md`: PRD 작성과 개발 일정 관리를 맡는 프로덕트 매니저. 읽기·쓰기 도구만 쓴다(Bash 없음). PRD는 기본으로 `docs/prd/<기능-이름>.md`에 저장한다.
  - `backend-developer.md`: 서버 아키텍처, API, 데이터 처리, 외부 연동, 보안·성능을 맡는 구현 담당.
  - `qa-engineer.md`: 직접 실행·테스트하며 기능, 에러 처리, 성능, 사용성을 검증한다. 테스트 코드만 쓰고 제품 코드는 지시 없이 고치지 않는다. 코드만 읽는 리뷰는 `code-reviewer`와 역할을 나눈다.
- 에이전트들은 PRD(`docs/prd/`)를 공통 기준으로 삼는다: product-manager가 쓰고, backend-developer가 구현하고, qa-engineer가 수용 기준으로 검증한다.

## 에이전트 파일 작성 규칙

- 프론트매터 필드는 `name`, `description`, `model`, `color`를 쓴다. `tools`를 생략하면 메인 대화의 모든 도구를 물려받는다.
- `description`은 메인 에이전트가 언제 위임할지 판단하는 근거이므로, 무엇을 하는지와 언제 호출하는지를 함께 적는다. 값에 `: `(콜론+공백)가 들어가면 YAML 파싱이 깨지니 피하거나 따옴표로 감싼다.
- 프롬프트와 보고서 형식은 한국어로 쓴다. 보고서는 결론 먼저, 전문 용어는 각주로 모으고, 제안에는 장단점을 함께 적는 사용자 선호를 따른다.
- 수정 후 프론트매터가 유효한지 확인한다:

  ```bash
  python3 -c "import re,yaml,sys; t=open(sys.argv[1],encoding='utf-8').read(); print(yaml.safe_load(re.match(r'^---\n(.*?)\n---\n',t,re.S).group(1)))" .claude/agents/code-reviewer.md
  ```

- 새로 추가하거나 고친 에이전트는 새 세션부터 인식된다. 모든 프로젝트에서 쓰려면 `~/.claude/agents/`에 복사한다.

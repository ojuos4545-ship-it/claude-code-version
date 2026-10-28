# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 저장소 개요

두 가지를 담는다.

- Claude Code 커스텀 서브에이전트(`.claude/agents/`)
- 다이어트용 간편 식단 기록 앱 "Easy Meal Log": 기준 문서 `docs/prd/easy-meal-log.md`, MVP 백엔드 `backend/`, 웹 클라이언트 `web/`

## 백엔드 명령 (`backend/`에서 실행)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
APP_ENV=development .venv/bin/uvicorn app.main:create_app --factory --reload
.venv/bin/python -m pytest                                  # 전체 (pyproject addopts에 -q가 있어 -q를 또 주면 요약 줄이 사라짐)
.venv/bin/python -m pytest tests/test_fr2_create.py::<테스트명>  # 테스트 하나
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```

## 웹 (`web/`)

- 빌드 도구 없는 HTML + CSS + JS 모듈. API 주소는 `web/config.js`(기본 `http://localhost:8000`). 개발용 정적 서버: `python3 -m http.server 5173 --directory web`(백엔드 개발 모드 CORS 기본값이 5173 허용).
- 브라우저 종단 테스트: 저장소 루트에서 `node web/tests/e2e.mjs`. 백엔드(8000)와 정적 서버(5173)를 직접 띄우고 끈다. 그 포트가 이미 쓰이고 있으면 실패한다.
- 사용자 입력은 `textContent`로만 넣는다(`innerHTML` 금지). 토큰은 `localStorage`에 있어서 XSS가 곧 토큰 탈취다. `index.html`의 CSP meta가 인라인 스크립트·스타일을 막고, `connect-src`는 `config.js`의 `apiBase`와 같아야 한다.
- 화면 문구도 제품 원칙을 따른다: 기록하지 않은 날을 실패·미달로 표현하지 않는다.
- 확인 창은 `confirm()` 대신 `askConfirm`(화면 안 `<dialog>`)을 쓴다. iframe(claude.ai 아티팩트)에서는 `confirm()`이 항상 false다.
- 체험 모드: `config.js`의 `demo: true`면 `demo-api.js`가 브라우저 저장소로 API를 흉내 낸다. 묶음 생성은 `python3 web/tools/build_demo.py <출력 폴더>`. API 응답 모양을 바꾸면 `demo-api.js`도 함께 고친다.

## 백엔드 구조

- Python + FastAPI + SQLite. 계층은 `app/api`(라우팅·검증·인증 의존성) → `app/services`(비즈니스 로직) → `app/repositories`(`base.py` Protocol, `sqlite.py` 구현). 구현체를 아는 곳은 `app/api/deps.py`뿐이다.
- 사용자(`users`)와 로그인 수단(`auth_identities`)이 분리돼 있다. 토큰은 `Authorization: Bearer` 불투명 토큰이고 DB에는 HMAC만 저장한다. 쿠키는 쓰지 않는다.
- "오늘"과 날짜 판정은 사용자별 IANA 시간대 기준이다. 기록 생성 중복 방지는 `Idempotency-Key` 헤더로 한다.
- 스키마는 `app/db/migrations/`의 up/down SQL로 관리하고 앱 시작 시 자동 적용된다.
- 보안 미들웨어(`app/api/middleware.py`): 처리되지 않은 예외를 500으로 바꾸고(다시 던지지 않음, 로그는 타입·메서드·경로만), 신뢰 프록시(`APP_TRUSTED_PROXIES`)의 `X-Forwarded-*`만 반영해 운영에서 HTTPS 강제·HSTS를 건다. `exception_handler(Exception)`을 다시 추가하지 않는다(uvicorn이 traceback을 찍는다).
- 미들웨어 순서(바깥부터, `app/main.py`): 예외 처리(CORS 층 자체 실패 대비) → CORS → 예외 처리(500) → 프록시·HTTPS → 라우트. CORS가 403 `https_required`와 500보다 바깥에 있어야 브라우저가 그 오류 본문을 읽는다. 순서를 바꾸면 `tests/test_qa_cors_error_responses.py`, `tests/test_cors.py`가 잡는다.
- 인증 엔드포인트 요청 수 제한(`app/api/ratelimit.py`)과 argon2 동시 실행 제한(`HashGate`)은 프로세스 메모리 기반이라 인스턴스끼리 공유되지 않는다. `/docs` 등 API 문서는 개발·테스트 모드에서만 열린다.
- 테스트 파일은 PRD 기능 번호별(`tests/test_fr1_*.py` ~ `test_fr8_*.py`)이다. 요구사항을 바꾸면 PRD와 해당 테스트를 함께 고친다.
- 제품 원칙상 칼로리·중량 같은 수치, 점수·평가 필드를 API에 추가하지 않는다(PRD 2절).

## 구조

- `.claude/agents/<name>.md`: 프로젝트 범위 서브에이전트 정의. 파일 이름과 프론트매터의 `name`을 같게 맞춘다.
  - `code-reviewer.md`: 버그, 코딩 규칙, 성능을 점검하는 리뷰어. 기본은 읽기 전용이고, 지시에 수정이 포함될 때만 코드를 고친다.
  - `product-manager.md`: PRD 작성과 개발 일정 관리를 맡는 프로덕트 매니저. 읽기·쓰기 도구만 쓴다(Bash 없음). PRD는 기본으로 `docs/prd/<기능-이름>.md`에 저장한다.
  - `backend-developer.md`: 서버 아키텍처, API, 데이터 처리, 외부 연동, 보안·성능을 맡는 구현 담당.
  - `qa-engineer.md`: 직접 실행·테스트하며 기능, 에러 처리, 성능, 사용성을 검증한다. 테스트 코드만 쓰고 제품 코드는 지시 없이 고치지 않는다. 코드만 읽는 리뷰는 `code-reviewer`와 역할을 나눈다.
  - `researcher.md`: 주제를 웹에서 조사해 최신·신뢰 출처 위주로 모으고, 글쓰기 에이전트용 리서치 노트(출처 URL 포함)로 정리한다. 노트는 기본으로 `docs/research/<주제-이름>.md`에 저장한다. 코드는 건드리지 않는다.
  - `writer.md`: 리서치 노트(`docs/research/`)를 메인 소스로, 스타일·SEO 가이드(`docs/guides/`)를 반드시 지켜 블로그 글을 쓴다. 이미지 자리는 SEO 가이드의 `[IMAGE: ...]` 마커로 표시하고, 초안은 기본으로 `docs/drafts/<주제-이름>.md`에 저장한다.
  - `assembler.md`: 초안 글과 이미지를 받아 최종 미리보기(`final.md`, `preview.html`)와 네이버 에디터 복붙용 `paste.html`, 사진 업로드 체크리스트 `upload-guide.md`를 만든다(HTML은 `tools/build_preview.py`로 생성). 글은 고치지 않고 이미지 자리만 바꾼다. 기본 출력은 `docs/final/<주제-이름>/`.
- `docs/guides/`: 블로그 가이드. `style-guide.md`(말투·서식), `seo-guide.md`(검색 노출), `image-guide.md`(이미지 규격과 HTML→Playwright 캡처). 이미지 캡처는 `python3 tools/make_blog_images.py <src 폴더> <출력 폴더> [--theme=flat|dark]`(기본은 라인+3D 테마, `dark`는 다크+3D 표본 테마)이고, `pip install playwright`가 필요하다.
- 에이전트들은 PRD(`docs/prd/`)를 공통 기준으로 삼는다: product-manager가 쓰고, backend-developer가 구현하고, qa-engineer가 수용 기준으로 검증한다.

## 블로그 글 작업 순서

- 사용자에게 하는 보고와 결과 설명은 반드시 한국어로 쓴다.
- 글 한 편은 researcher → writer → image-maker → assembler 순서로 맡기고, 단계마다 결과 파일을 확인한 뒤 다음으로 넘어간다.
- 글의 '직접 해 본 결과'(경험) 부분은 실제로 실험해 보고 쓴다. 실험 방법과 수치는 `docs/research/<주제>-experiments.md`에 남기고, 글에는 기록에 있는 사실만 쓴다.
- 조립이 끝나면 최종 팩트 검증(공식 문서·실험 기록과 대조)과 오기·오류 수정을 하고, 초안과 붙여넣기용 페이지를 사용자에게 보여 준다.
- 글쓰기 규칙은 `docs/guides/`의 세 가이드를 반드시 따른다. 같은 규칙은 한 가이드에만 적고 다른 곳에서는 그 절을 가리킨다(문단·마무리·붙여넣기 서식은 `style-guide.md`, 이미지 서식은 `image-guide.md`).
- 문단 정리는 `python3 -I tools/reflow_paragraphs.py <글.md>`로 할 수 있다(글자는 그대로 두고 줄바꿈만 바꾼다).

## 에이전트 파일 작성 규칙

- 프론트매터 필드는 `name`, `description`, `model`, `color`를 쓴다. `tools`를 생략하면 메인 대화의 모든 도구를 물려받는다.
- `description`은 메인 에이전트가 언제 위임할지 판단하는 근거이므로, 무엇을 하는지와 언제 호출하는지를 함께 적는다. 값에 `: `(콜론+공백)가 들어가면 YAML 파싱이 깨지니 피하거나 따옴표로 감싼다.
- 프롬프트와 보고서 형식은 한국어로 쓴다. 보고서는 결론 먼저, 전문 용어는 각주로 모으고, 제안에는 장단점을 함께 적는 사용자 선호를 따른다.
- 수정 후 프론트매터가 유효한지 확인한다:

  ```bash
  python3 -c "import re,yaml,sys; t=open(sys.argv[1],encoding='utf-8').read(); print(yaml.safe_load(re.match(r'^---\n(.*?)\n---\n',t,re.S).group(1)))" .claude/agents/code-reviewer.md
  ```

- 새로 추가하거나 고친 에이전트는 새 세션부터 인식된다. 모든 프로젝트에서 쓰려면 `~/.claude/agents/`에 복사한다.

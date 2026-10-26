# Easy Meal Log 백엔드 (M1)

PRD: [`docs/prd/easy-meal-log.md`](../docs/prd/easy-meal-log.md). FR-1~FR-6(Must)과 FR-7, FR-8(Should)을 구현했다.

스택: Python 3.11+ · FastAPI · SQLite(표준 라이브러리 `sqlite3`) · argon2-cffi(비밀번호 해시).

## 설치

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # 운영 배포는 requirements.txt만
```

## 실행

```bash
APP_ENV=development .venv/bin/uvicorn app.main:create_app --factory --reload
# http://127.0.0.1:8000/docs 에서 OpenAPI 문서 확인
```

시작할 때 DB 마이그레이션이 자동으로 적용된다. 수동 실행: `.venv/bin/python -m app.db.migrate up` / `down`(최근 1개 되돌림).

### 환경 변수

| 이름 | 기본값 | 설명 |
|---|---|---|
| `APP_ENV` | `production` | `development` 또는 `test`일 때만 개발용 기본 비밀값을 쓴다 |
| `APP_SECRET_KEY` | 없음 (운영 필수, 32자 이상) | 토큰 HMAC 키. **`APP_ENV`가 development/test이고 값이 없을 때만 코드에 있는 개발용 기본값을 쓴다.** 운영에서 비어 있으면 서버가 시작되지 않는다 |
| `APP_DATABASE_PATH` | `data/app.db` | SQLite 파일 경로 |
| `APP_TOKEN_TTL_SECONDS` | `2592000` (30일) | 액세스 토큰 유효 기간 |
| `APP_DEFAULT_TIMEZONE` | `Asia/Seoul` | 가입 시 시간대를 안 보냈을 때 쓰는 값 |
| `APP_CORS_ORIGINS` | 개발/테스트: `http://localhost:3000`, `:5173`(localhost·127.0.0.1) / 운영: 없음(CORS 끔) | 브라우저에서 호출을 허용할 출처. 쉼표로 구분, `scheme://host[:port]` 정확히(예: `https://app.example.com`). `*`와 경로는 거부 |

## 테스트와 린트

```bash
.venv/bin/python -m pytest                                    # 전체
.venv/bin/python -m pytest tests/test_fr2_create.py           # 파일 하나
.venv/bin/python -m pytest tests/test_fr2_create.py::test_future_date_rejected_past_dates_accepted  # 테스트 하나
.venv/bin/python -m pytest -k idempotency                     # 이름으로 고르기
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```

테스트 파일은 FR 번호별로 나뉜다(`tests/test_fr1_isolation.py` ~ `tests/test_fr8_weekly.py`).

## API

인증이 필요한 요청은 `Authorization: Bearer <access_token>` 헤더를 보낸다. 쿠키는 쓰지 않으므로 웹과 모바일 앱이 같은 방식으로 호출한다(CORS도 credentials 모드 없이 허용). 모든 오류 응답 형식:
`{"error": {"code": "...", "message": "...", "details": [{"field", "reason", "message"}]}}`
(422 입력 오류, 401 인증 없음/만료, 403 비밀번호 확인 실패, 404 없음 또는 남의 기록, 409 충돌)

| 메서드 · 경로 | 설명 | FR |
|---|---|---|
| `POST /v1/auth/signup` | `{email, password, timezone?}` → 201 토큰 | FR-1 |
| `POST /v1/auth/login` | `{email, password}` → 토큰 | FR-1 |
| `POST /v1/auth/logout` | 현재 토큰 폐기 → 204 | FR-1 |
| `GET /v1/me` · `PATCH /v1/me` | 내 정보 조회(`email`은 이메일 로그인 수단이 없는 사용자면 `null`) · 시간대(`timezone`, IANA 이름) 변경 | FR-1 |
| `DELETE /v1/me` | 본문 `{password}`. 계정·기록·토큰 전부 삭제 → 204 | FR-6 |
| `POST /v1/meals` | `{description, meal_date?, meal_type?, portion?, memo?}` → 201. `Idempotency-Key` 헤더로 재시도 중복 방지(같은 키 재요청은 200 + `Idempotent-Replayed: true`) | FR-2 |
| `GET /v1/meals?date=YYYY-MM-DD` | 하루 조회 | FR-5 |
| `GET /v1/meals?from=…&to=…` | 기간 조회(양끝 포함, 최대 31일). `limit`(1~200, 기본 100), `offset`, 응답의 `next_offset` | FR-5 |
| `GET /v1/meals/{id}` | 단건 조회 | FR-5 |
| `PATCH /v1/meals/{id}` | 보낸 항목만 수정. `meal_type`/`portion`/`memo`는 `null`로 비우기 | FR-3 |
| `DELETE /v1/meals/{id}` | 삭제 → 204 (이미 지웠으면 404) | FR-4 |
| `GET /v1/meals/recent-descriptions` | 최근 30일, 중복 없는 "먹은 것" 최대 10개 | FR-7 |
| `GET /v1/summaries/weekly?start=YYYY-MM-DD` | 7일간 기록한 날 수, 날짜별 건수, 식사량 분포 | FR-8 |

값: `meal_type` = `breakfast|lunch|dinner|snack`, `portion` = `small|medium|large`(화면 표시 이름은 클라이언트가 정함). 정의되지 않은 항목(예: `kcal`)을 보내면 422로 거부한다. "오늘"과 미래 날짜 판정은 사용자 시간대 기준이다.

## 구조

```
app/
  api/            라우팅, 요청·응답 스키마, 인증 의존성
  services/       비즈니스 로직 (auth.py, meals.py) — Repository 인터페이스에만 의존
  repositories/   base.py(인터페이스), sqlite.py(구현) — DB 교체 시 여기만 새로 구현
  domain/         엔터티, 선택지(enum), 입력 정규화 규칙
  db/             마이그레이션(*.up.sql / *.down.sql)과 실행기
```

사용자와 로그인 수단은 분리돼 있다: `users`는 식별자·시간대·가입 시각만 갖고, 로그인 수단은 `auth_identities`(`provider`, `identifier`, `secret_hash`)에 사용자별로 연결된다. 지금은 `password` 수단(이메일+비밀번호)만 있다. 세션 토큰은 사용자 id에만 묶이므로, "가입 없이 시작"은 수단 없는 사용자를 만들고 토큰을 발급하면 되고, "계정 연결"은 그 사용자에 `auth_identities` 행을 추가하면 된다.

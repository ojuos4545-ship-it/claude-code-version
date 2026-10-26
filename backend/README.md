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
# http://127.0.0.1:8000/docs 에서 OpenAPI 문서 확인 (개발·테스트 모드에서만 켜진다)
```

운영 실행 예(TLS 종단 프록시 뒤, 아래 "운영 전제" 참고):

```bash
APP_SECRET_KEY=... APP_TRUSTED_PROXIES=10.0.0.5 \
  .venv/bin/uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-proxy-headers
```

`--no-proxy-headers`는 uvicorn 자체의 X-Forwarded-* 처리를 꺼서, 프록시 신뢰 판단을 앱 설정(`APP_TRUSTED_PROXIES`) 한곳에서만 하게 한다.

시작할 때 DB 마이그레이션이 자동으로 적용된다. 수동 실행: `.venv/bin/python -m app.db.migrate up` / `down`(최근 1개 되돌림).

- `0003_one_identity_per_provider`: 사용자당 로그인 수단 종류별 1개(`auth_identities(user_id, provider)` 유일 인덱스). 이 규칙을 이미 어긴 행(과거 동시 계정 연결)이 있으면 처음 연결된 것만 남기고 나머지를 지운 뒤 인덱스를 만든다. 되돌리면 인덱스만 지운다(지운 행은 돌아오지 않는다).

### 환경 변수

| 이름 | 기본값 | 설명 |
|---|---|---|
| `APP_ENV` | `production` | `development` 또는 `test`일 때만 개발용 기본 비밀값을 쓴다 |
| `APP_SECRET_KEY` | 없음 (운영 필수, 32자 이상) | 토큰 HMAC 키. **`APP_ENV`가 development/test이고 값이 없을 때만 코드에 있는 개발용 기본값을 쓴다.** 운영에서 비어 있으면 서버가 시작되지 않는다 |
| `APP_DATABASE_PATH` | `data/app.db` | SQLite 파일 경로 |
| `APP_TOKEN_TTL_SECONDS` | `2592000` (30일) | 액세스 토큰 유효 기간 |
| `APP_DEFAULT_TIMEZONE` | `Asia/Seoul` | 가입 시 시간대를 안 보냈을 때 쓰는 값 |
| `APP_REQUIRE_HTTPS` | 운영: `true` / 개발·테스트: `false` | 켜면 HTTPS가 아닌 요청을 403 `https_required`로 거부하고 응답에 HSTS 헤더를 붙인다. `/healthz`는 예외(로드 밸런서 상태 확인용, HSTS 없음) |
| `APP_HSTS_MAX_AGE` | `31536000` (1년) | `Strict-Transport-Security: max-age=…` 값(초). 처음 배포 때는 짧게 시작해도 된다. `includeSubDomains`는 붙이지 않는다 |
| `APP_TRUSTED_PROXIES` | 운영: `127.0.0.1,::1` / 개발·테스트: 없음 | `X-Forwarded-Proto`·`X-Forwarded-For`를 믿을 프록시의 IP 또는 CIDR(쉼표 구분). 빈 값이면 아무도 믿지 않는다. `*`, `0.0.0.0/0`처럼 전체를 믿는 값은 거부 |
| `APP_RATE_LIMIT_ENABLED` | `true` | 인증 엔드포인트 요청 수 제한. 끄는 것은 부하 시험 같은 경우에만 |
| `APP_MAX_CONCURRENT_HASHES` | `4` | 프로세스당 동시에 도는 argon2 해시·검증 수(하나에 약 64MiB). 자리가 3초 안에 안 나면 503 `server_busy` + `Retry-After` |
| `APP_CORS_ORIGINS` | 개발/테스트: `http://localhost:3000`, `:5173`(localhost·127.0.0.1) / 운영: 없음(CORS 끔) | 브라우저에서 호출을 허용할 출처. 쉼표로 구분, `scheme://host[:port]` 정확히(예: `https://app.example.com`). `*`와 경로는 거부 |

## 테스트와 린트

```bash
.venv/bin/python -m pytest                                    # 전체
.venv/bin/python -m pytest tests/test_fr2_create.py           # 파일 하나
.venv/bin/python -m pytest tests/test_fr2_create.py::test_future_date_rejected_past_dates_accepted  # 테스트 하나
.venv/bin/python -m pytest -k idempotency                     # 이름으로 고르기
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```

테스트 파일은 FR 번호별로 나뉜다(`tests/test_fr1_isolation.py` ~ `tests/test_fr8_weekly.py`). 보안 항목은 `tests/test_security_*.py`(HTTPS·프록시·문서, 요청 수 제한, 로그 유출. 로그 테스트는 실제 uvicorn을 띄운다).

## API

인증이 필요한 요청은 `Authorization: Bearer <access_token>` 헤더를 보낸다. 쿠키는 쓰지 않으므로 웹과 모바일 앱이 같은 방식으로 호출한다(CORS도 credentials 모드 없이 허용). 모든 오류 응답 형식:
`{"error": {"code": "...", "message": "...", "details": [{"field", "reason", "message"}]}}`
(422 입력 오류, 401 인증 없음/만료, 403 비밀번호 확인 실패 또는 `https_required`, 404 없음 또는 남의 기록, 409 충돌, 429 `rate_limited`, 503 `server_busy`. 429·503에는 `Retry-After` 헤더(초)가 붙고, 브라우저에서도 읽을 수 있게 CORS로 노출한다. 403 `https_required`와 500에도 허용 출처의 CORS 헤더가 붙는다)

| 메서드 · 경로 | 설명 | FR |
|---|---|---|
| `POST /v1/auth/signup` | `{email, password, privacy_consent: true, timezone?}` → 201 토큰 | FR-1 |
| `POST /v1/auth/login` | `{email, password}` → 토큰 | FR-1 |
| `POST /v1/auth/anonymous` | `{privacy_consent: true, timezone?}` → 201 토큰. 가입 없이 시작(로그인 수단 없는 사용자) | FR-1, Q4 |
| `POST /v1/auth/link` | `{email, password}`. 로그인 수단이 없는 현재 사용자에 이메일 로그인 연결 → 200 사용자 정보. 이미 연결됐거나 이메일이 쓰이고 있으면 409(`details[0].reason`이 `already_linked` 또는 `already_registered`). 동시 요청이 와도 하나만 연결된다 | FR-1, Q4 |
| `POST /v1/auth/logout` | 현재 토큰 폐기 → 204 | FR-1 |
| `GET /v1/me` · `PATCH /v1/me` | 내 정보 조회(`email`은 이메일 로그인 수단이 없는 사용자면 `null`) · 시간대(`timezone`, IANA 이름) 변경 | FR-1 |
| `DELETE /v1/me` | 이메일 로그인이 있으면 본문 `{password}` 필수(틀리거나 없으면 403), 가입 없이 시작한 사용자는 본문 없이. 계정·기록·토큰 전부 삭제 → 204 | FR-6 |
| `POST /v1/meals` | `{description, meal_date?, meal_type?, portion?, memo?}` → 201. `Idempotency-Key` 헤더로 재시도 중복 방지(같은 키 재요청은 200 + `Idempotent-Replayed: true`) | FR-2 |
| `GET /v1/meals?date=YYYY-MM-DD` | 하루 조회 | FR-5 |
| `GET /v1/meals?from=…&to=…` | 기간 조회(양끝 포함, 최대 31일). `limit`(1~200, 기본 100), `offset`, 응답의 `next_offset` | FR-5 |
| `GET /v1/meals/{id}` | 단건 조회 | FR-5 |
| `PATCH /v1/meals/{id}` | 보낸 항목만 수정. `meal_type`/`portion`/`memo`는 `null`로 비우기 | FR-3 |
| `DELETE /v1/meals/{id}` | 삭제 → 204 (이미 지웠으면 404) | FR-4 |
| `GET /v1/meals/recent-descriptions` | 최근 30일, 중복 없는 "먹은 것" 최대 10개 | FR-7 |
| `GET /v1/summaries/weekly?start=YYYY-MM-DD` | 7일간 기록한 날 수, 날짜별 건수, 식사량 분포 | FR-8 |

값: `meal_type` = `breakfast|lunch|dinner|snack`, `portion` = `small|medium|large`(화면 표시 이름은 클라이언트가 정함). 정의되지 않은 항목(예: `kcal`)을 보내면 422로 거부한다. "오늘"과 미래 날짜 판정은 사용자 시간대 기준이다.

## 세션과 동의

- 토큰은 쓰는 동안 계속 연장된다: 유효 기간(`APP_TOKEN_TTL_SECONDS`, 기본 30일)의 절반이 지난 뒤 사용하면 다시 전체 기간으로 늘어난다. 가입 없이 시작한 사용자는 토큰 말고 다시 들어올 방법이 없어서, 고정 만료면 기록을 잃기 때문이다. 기간 내내 쓰지 않으면 만료된다.
- 가입과 "가입 없이 시작" 모두 `privacy_consent: true`가 필수이고, 동의 시각을 `users.consented_at`에 남긴다. 동의 문구는 법률 검토 전 초안이다(PRD Q6).

## 운영 전제와 보안 설정

PRD Q6에 따라 식단 기록을 민감정보로 보고 보수적으로 설정한다.

### HTTPS: TLS 종단 프록시 뒤에서 실행

- 운영에서는 앱 앞에 TLS를 끝내는 프록시(nginx, 로드 밸런서 등)가 있고, 앱 포트는 그 프록시만 접근할 수 있다고 전제한다.
- 프록시는 `X-Forwarded-Proto`를 클라이언트가 접속한 스킴으로 **덮어써야** 하고(예: nginx `proxy_set_header X-Forwarded-Proto $scheme;`), `X-Forwarded-For`에는 받은 주소를 **덧붙여야** 한다(`$proxy_add_x_forwarded_for`). 앱은 `X-Forwarded-Proto`의 마지막 값을 쓴다.
- HTTPS가 아닌 요청은 리다이렉트하지 않고 403으로 거부한다. 요청과 토큰은 이미 평문으로 지나갔고, POST를 리다이렉트하면 본문이 다시 평문으로 전송될 수 있어서다. 대신 HSTS로 브라우저가 다음부터 HTTPS로만 접속하게 한다. 평문 포트는 프록시에서 막거나 리다이렉트한다.
- 앱이 직접 TLS를 받는 경우(uvicorn `--ssl-*`)에도 동작한다(그때는 소켓 스킴이 https).

### 프록시 헤더를 무조건 믿으면 안 되는 이유

`X-Forwarded-Proto`와 `X-Forwarded-For`는 누구나 보낼 수 있는 일반 헤더다. 아무에게서나 믿으면 공격자가 `X-Forwarded-Proto: https`로 HTTPS 강제를 우회하고, `X-Forwarded-For`를 매번 바꿔 IP별 요청 수 제한을 무력화한다. 그래서 앱은 소켓 상대 주소가 `APP_TRUSTED_PROXIES`에 있을 때만 두 헤더를 쓰고, 아니면 소켓 주소와 스킴을 그대로 쓴다. `X-Forwarded-For`는 오른쪽부터 읽어 신뢰하는 프록시가 아닌 첫 주소를 클라이언트로 본다(왼쪽 값은 클라이언트가 지어낼 수 있다).

- 운영 기본값은 같은 호스트의 프록시(`127.0.0.1,::1`)만 믿는다. 프록시가 다른 컨테이너·호스트에 있으면 그 주소(또는 프록시만 쓰는 좁은 대역)를 넣는다. 넣지 않으면 모든 요청이 `https_required`로 거부되므로 설정 누락이 바로 드러난다.
- 사설 대역 전체(예: `10.0.0.0/8`)를 넣으면 같은 망의 다른 서버도 헤더를 위조할 수 있다. 앱 포트가 프록시에서만 접근 가능할 때만 넓게 잡는다.

### 요청 수 제한 (인증 엔드포인트)

| 대상 | 기준 | 한도 `[가정]` |
|---|---|---|
| `POST /v1/auth/login` | IP | 10분에 30회 |
| `POST /v1/auth/login` | 이메일(소문자 정규화) | 15분에 10회 |
| `POST /v1/auth/signup` · `/v1/auth/anonymous` | IP | 각 10분에 20회 |
| `POST /v1/auth/link` | IP | 10분에 10회 |

- 초과하면 429 `rate_limited`와 `Retry-After`(창이 끝날 때까지 남은 초). 실패·성공·입력 오류를 가리지 않고 센다(동시 요청으로 한도를 넘지 못하게 원자적으로 센다).
- IP 한도는 통신사 NAT처럼 여러 사람이 한 주소를 쓰는 경우를 생각해 느슨하게, 비밀번호 추측을 막는 이메일 한도를 촘촘하게 잡았다. 대가: 남의 이메일로 로그인을 반복해 그 계정의 로그인을 15분간 막을 수 있다.
- **한계: 카운터는 프로세스 메모리에 있다.** 워커·인스턴스끼리 공유되지 않아 N개를 띄우면 실제 한도는 최대 N배가 되고, 재시작하면 초기화된다. 여러 인스턴스로 늘릴 때는 공유 저장소(Redis 등)로 옮긴다.
- 메모리 상한: 한도별로 키를 최대 10,000개만 둔다. 가득 차면 만료된 창부터, 그래도 부족하면 가장 오래된 창부터 버린다.
- argon2 해시는 요청당 약 64MiB를 쓰므로 동시 실행 수를 `APP_MAX_CONCURRENT_HASHES`로 제한한다(로그인, 가입, 계정 연결, 탈퇴 비밀번호 확인 모두 해당).

### 로그와 문서

- 미들웨어 순서(바깥부터): 예외 처리(CORS 층 자체 실패 대비) → CORS → 예외 처리 → 프록시·HTTPS → 라우트. CORS를 HTTPS 거부와 500보다 바깥에 두어 허용 출처의 브라우저가 이 오류 본문을 읽을 수 있게 했다. CORS 프리플라이트는 HTTPS 검사 전에 CORS가 답한다(2xx가 아닌 프리플라이트는 헤더와 상관없이 브라우저에서 실패하고, 실제 요청은 읽을 수 있는 403으로 거부된다).
- 처리되지 않은 예외는 예외 처리 미들웨어가 잡아 500으로 응답하고, 로그에는 예외 타입·메서드·경로(쿼리스트링 제외)만 남긴다. 예외를 서버로 다시 던지지 않으므로 uvicorn이 traceback과 예외 메시지(입력값이 섞일 수 있음)를 찍지 않는다. uvicorn 접근 로그에는 쿼리스트링이 남지만, 이 API의 쿼리에는 날짜·페이지 값만 있다.
- `/docs`, `/redoc`, `/openapi.json`은 개발·테스트 모드에서만 열린다.

## 구조

```
app/
  api/            라우팅, 요청·응답 스키마, 인증 의존성, 미들웨어(middleware.py), 요청 수 제한(ratelimit.py)
  services/       비즈니스 로직 (auth.py, meals.py) — Repository 인터페이스에만 의존
  repositories/   base.py(인터페이스), sqlite.py(구현) — DB 교체 시 여기만 새로 구현
  domain/         엔터티, 선택지(enum), 입력 정규화 규칙
  db/             마이그레이션(*.up.sql / *.down.sql)과 실행기
```

사용자와 로그인 수단은 분리돼 있다: `users`는 식별자·시간대·가입 시각만 갖고, 로그인 수단은 `auth_identities`(`provider`, `identifier`, `secret_hash`)에 사용자별로 연결된다. 지금은 `password` 수단(이메일+비밀번호)만 있다. 세션 토큰은 사용자 id에만 묶이므로, "가입 없이 시작"은 수단 없는 사용자를 만들고 토큰을 발급하면 되고, "계정 연결"은 그 사용자에 `auth_identities` 행을 추가하면 된다.

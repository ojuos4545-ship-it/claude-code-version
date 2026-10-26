# Easy Meal Log 웹 (M2 1차)

빌드 도구 없이 HTML, CSS, JS 모듈로 만든 웹 클라이언트다. 기준 문서는 [`docs/prd/easy-meal-log.md`](../docs/prd/easy-meal-log.md).

## 실행

```bash
# 1) 백엔드 (backend/README.md 참고)
cd backend && APP_ENV=development .venv/bin/uvicorn app.main:create_app --factory

# 2) 웹 (다른 터미널, 저장소 루트에서)
python3 -m http.server 5173 --directory web
# → http://localhost:5173
```

API 주소는 `config.js`에서 바꾼다. 운영에서는 백엔드 `APP_CORS_ORIGINS`에 이 웹의 출처를 넣어야 한다.

## 테스트

```bash
node web/tests/e2e.mjs   # 저장소 루트에서. 백엔드 .venv와 Playwright가 필요하다.
```

실제 백엔드와 정적 서버를 띄워 브라우저로 US-1~US-8 흐름을 끝까지 수행한다(휴대폰 폭 390px).

## 화면

| 화면 | 하는 일 |
|---|---|
| 첫 화면 | 동의 후 가입 없이 바로 시작, 또는 이메일 로그인 |
| 기록 | 먹은 것 한 줄 + 선택 항목(끼니, 양, 메모). 최근 메뉴 칩, 지난 날짜로 이동해 몰아서 기록, 수정·삭제 |
| 한 주 | 기록한 날 수와 날짜별 건수, 식사량 분포. 날짜를 누르면 그날 기록으로 이동 |
| 설정 | 이메일 계정 연결, 시간대 맞추기, 로그아웃, 탈퇴 |

## Content-Security-Policy

`index.html`에 CSP meta 태그가 있다: `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src <API 주소>; object-src 'none'; base-uri 'none'; form-action 'none'`. 인라인 스크립트·스타일은 쓰지 않으므로(`style` 속성, `<style>`, `<script>` 본문 없음) `'unsafe-inline'`이 필요 없다. 새 코드도 이 규칙을 지킨다.

- **`config.js`의 `apiBase`를 바꾸면 `index.html` CSP의 `connect-src`도 같은 출처로 바꿔야 한다.** 안 바꾸면 모든 API 호출이 브라우저에서 막힌다. 종단 테스트가 둘이 같은지 확인한다.
- **운영에서는 같은 정책을 웹 서버 응답 헤더(`Content-Security-Policy`)로 보낸다.** meta 태그로는 `frame-ancestors`(다른 사이트가 iframe으로 넣는 것 막기), `report-uri`/`report-to`, `sandbox`를 쓸 수 없고, meta 태그 앞에 나온 내용에는 적용되지 않는다. 헤더에는 `frame-ancestors 'none'`을 더한다. 둘 다 있으면 둘 다 적용되므로(더 엄격한 쪽) 값을 같게 유지한다.
- 운영에서 API는 HTTPS 주소여야 한다(백엔드가 운영 모드에서 HTTPS가 아닌 요청을 거부한다).
- 인증 요청이 너무 많으면 백엔드가 429를 돌려주고, 화면은 "잠시 후 다시 시도해 주세요" 안내를 보여 준다.

## 알려진 한계

- 토큰을 `localStorage`에 둔다. 스크립트 주입(XSS)이 생기면 토큰이 탈취되므로 사용자 입력은 `textContent`로만 넣고, 아래 CSP로 한 번 더 막는다.
- 인터넷이 끊기면 기록할 수 없다(오프라인 기록은 앱 단계에서 판단, PRD Q3).
- 동의 문구는 법률 검토 전 초안이다.

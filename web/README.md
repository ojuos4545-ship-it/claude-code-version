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

## 알려진 한계

- 토큰을 `localStorage`에 둔다. 스크립트 주입(XSS)이 생기면 토큰이 탈취되므로 사용자 입력은 `textContent`로만 넣는다. 운영 배포 때 Content-Security-Policy 헤더를 함께 설정해야 한다.
- 인터넷이 끊기면 기록할 수 없다(오프라인 기록은 앱 단계에서 판단, PRD Q3).
- 동의 문구는 법률 검토 전 초안이다.

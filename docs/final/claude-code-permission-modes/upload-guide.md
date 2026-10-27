# 발행 체크리스트: 클로드 코드 권한 모드 사용법, 허락 묻는 기준 정하는 3단계

1. 에디터 **제목 칸**에 제목을 입력합니다.
2. `paste.html`을 열어 [본문 복사] → 에디터 본문에 붙여넣습니다.
3. 본문의 `【사진 NN】` 자리마다 아래 파일을 올리고, 표시 줄은 지웁니다.
4. 사진마다 대체 텍스트(ALT)를 넣습니다. 첫 사진(01)은 대표 사진으로 지정합니다.
5. 태그 칸에 아래 태그를 입력합니다.

| 순서 | 파일 | 바로 앞 문장(위치) | ALT |
| :--- | :--- | :--- | :--- |
| 01 | `01_thumbnail_permission-modes.png` | 💡 한 줄 요약: 클로드 코드 권한 모드는 "Claude가 묻지 않고 해 | 정방형 비율, 클로드 코드 권한 모드 사용법을 모드 알기, Shift+Tab으로 바꾸기, 허용·거부 규칙 정하기 세 단계로 나열한 대표 이미지 |
| 02 | `02_card_start-order.png` | 3. 클로드 코드에 내장된 기본값 (조사일 기준 터미널·VS Code는  | 클로드 코드 권한 모드의 새 세션 시작 순서 카드. 실행 옵션, 설정 파일의 defaultMode, 내장 기본값 auto 순서와 상태 표시줄에서 확인하라는 안내 |
| 03 | `03_table_six-modes.png` | 상태 표시줄의 기호는 환경에 따라 다르게 보일 수 있으니, 글자 부분으로 | 클로드 코드 권한 모드 6가지 비교표. default(Manual), acceptEdits, plan, auto, dontAsk, bypassPermissions의 상태 표시줄 글자와 묻지 않고 하는 일, 잘 맞는 때 |
| 04 | `04_table_same-request.png` | 요청은 "app.js 맨 아래에 console.log("ready");  | 같은 요청을 권한 모드만 바꿔 실행한 결과표. default와 dontAsk는 거부, acceptEdits는 app.js에 한 줄 추가, plan은 파일을 그대로 두고 계획만 작성 |
| 05 | `05_diagram_shift-tab.png` | bypassPermissions도 그 모드를 허용한 채 시작한 세션에서만 | Shift+Tab을 누를 때마다 클로드 코드 권한 모드가 auto, manual, accept edits, plan, 다시 auto로 돌아가는 순환 흐름도 |
| 06 | `06_diagram_plan-flow.png` | 계획을 직접 고치고 싶다면 Ctrl+G로 에디터에서 열 수 있습니다. | 클로드 코드 플랜 모드 흐름도. 플랜 모드 들어가기, 탐색과 계획 작성, 계획 검토, 승인 선택지(auto로 실행, 편집 하나씩 확인, 계속 계획)에 따라 모드 전환 |
| 07 | `07_table_rules.png` | 알아서 고치는 acceptEdits에서도 거부 규칙이 이겼고요. | 클로드 코드 허용·거부 규칙 실험 결과표. 공유 settings.json의 허용 규칙은 폴더 신뢰 전이라 거부, settings.local.json 허용은 적용, 공유 settings.json의 거부 규칙은 acceptEdits 모드에서도 바로 .env를 지킴 |
| 08 | `08_diagram_check-order.png` | 앞 글에서 만든 .env 보호 훅도 공식 문서 설명대로라면 모드를 바꿔도 | Claude가 도구를 쓰기 전 확인 순서 흐름도. PreToolUse 훅, 거부·확인·허용 규칙, 클로드 코드 권한 모드 순으로 거치며 훅과 거부 규칙은 모든 모드에서 유지됨 |
| 09 | `09_card_three-lines.png` | 세 줄로 줄이면 "상태 표시줄로 모드 확인, 큰 변경은 플랜 모드로, 막 | 클로드 코드 권한 모드 핵심 3줄 카드. 상태 표시줄로 지금 모드 확인, 큰 변경은 플랜 모드로 계획부터, 절대 안 되는 일은 거부 규칙으로 |

**태그:** `#클로드코드권한모드` `#클로드코드` `#ClaudeCode` `#클로드코드사용법` `#클로드코드입문` `#플랜모드` `#클로드코드설정` `#AI코딩도구`

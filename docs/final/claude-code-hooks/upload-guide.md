# 발행 체크리스트: 클로드 코드 훅 사용법, 입문자도 따라 하는 자동 실행 3단계

1. 에디터 **제목 칸**에 제목을 입력합니다.
2. `paste.html`을 열어 [본문 복사] → 에디터 본문에 붙여넣습니다.
3. 본문의 `【사진 NN】` 자리마다 아래 파일을 올리고, 표시 줄은 지웁니다.
4. 사진마다 대체 텍스트(ALT)를 넣습니다. 첫 사진(01)은 대표 사진으로 지정합니다.
5. 태그 칸에 아래 태그를 입력합니다.

| 순서 | 파일 | 바로 앞 문장(위치) | ALT |
| :--- | :--- | :--- | :--- |
| 01 | `01_thumbnail_hooks.png` | 💡 한 줄 요약: 클로드 코드 훅 사용법의 핵심은 "이럴 때는 이 명령을 | 정방형 비율, 클로드 코드 훅 사용법을 위치와 구조, 첫 훅 만들기, 정리하고 막기 세 단계로 나열한 대표 이미지 |
| 02 | `02_table_claude-md-vs-hook.png` | "꼭 매번 일어나야 하는 일은 훅 같은 강제 장치로, CLAUDE.md는 | 클로드 코드 훅과 CLAUDE.md 비교표. CLAUDE.md는 Claude가 읽고 판단하는 메모, 훅은 클로드 코드가 매번 실행하는 규칙이라는 차이와 각각 잘 맞는 일 |
| 03 | `03_card_locations.png` |  .claude/settings.local.json: 이 프로젝트에서 나 | 클로드 코드 훅 설정 위치 카드. 모든 프로젝트용 ~/.claude/settings.json, 팀과 함께 쓰는 .claude/settings.json, 나만 쓰는 .claude/settings.local.json 세 곳의 차이 |
| 04 | `04_diagram_events.png` | 처음에는 아래 몇 가지만 알아도 충분해요. | 클로드 코드 훅 이벤트가 실행되는 순서 흐름도. 세션 시작 SessionStart, 질문 보냄 UserPromptSubmit, 도구 쓰기 전 PreToolUse, 도구 쓴 뒤 PostToolUse, 답을 마침 Stop |
| 05 | `05_diagram_first-hook.png` | 4. 시험하기: Claude에게 허락이 필요한 일을 시킨 뒤 다른 창으로 | 클로드 코드 훅 첫 실습인 알림 훅 만들기 4단계 흐름도. 설정 파일 열기, Notification 훅 붙여넣기, /hooks로 확인, 허락이 필요한 일로 시험 |
| 06 | `06_card_exit-codes.png` | $CLAUDE_PROJECT_DIR는 프로젝트 폴더 위치를 가리키는 이름 | 클로드 코드 훅의 끝내는 숫자(종료 코드) 뜻 카드. exit 0은 통과, exit 2는 막기와 이유 전달, 그 밖의 숫자는 오류만 남기고 작업 진행 |
| 07 | `07_table_experiments.png` | 절대 경로나 $CLAUDE_PROJECT_DIR를 쓰고, 위에서처럼 가짜 | 클로드 코드 훅 실험 결과 비교표. 공식 예제 그대로 exit 2는 .env 수정이 막힘, exit 1로 바꾸면 수정됨, matcher를 소문자로 쓰면 훅이 실행되지 않아 수정됨 |
| 08 | `08_card_three-lines.png` | 세 줄로 줄이면 "꼭 지킬 일만 훅으로, 막을 때는 exit 2, 붙여넣 | 클로드 코드 훅 사용법 핵심 3줄 카드. 꼭 지킬 일만 훅으로, 막을 때는 exit 2, 붙여넣기 전에 읽고 시험하기 |

**태그:** `#클로드코드훅` `#클로드코드` `#ClaudeCode` `#ClaudeCodeHooks` `#클로드코드사용법` `#클로드코드입문` `#훅설정` `#클로드코드자동화` `#AI코딩도구`

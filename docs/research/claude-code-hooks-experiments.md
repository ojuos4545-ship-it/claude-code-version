# 실험 기록: 클로드 코드 훅 사용법 글의 '직접 해 본 결과'

- 실행일: 2026-10-27
- 도구: Claude Code 2.1.312, `claude -p "<요청>"` (대화 없이 한 번 실행하고 결과를 받는 방식). 편집이 필요한 실험은 `--permission-mode acceptEdits`
- 환경: 클라우드 컨테이너(화면 없음). 전역 `~/.claude/settings.json`·관리 설정 없음(다른 훅이 섞이지 않음 확인). `jq` 설치됨, `npx prettier` 3.8.1
- 연습 프로젝트: 앞 글과 같은 할 일 목록 예제(`index.html`, `style.css`, `app.js`, `old/legacy.js`)에 가짜 값만 든 `.env`(`API_KEY=practice-only-not-real`)를 더했다. 실험마다 이 폴더를 새로 복사해 썼다.
- 한계: 각 1회 실행 결과다. AI 답변 문장은 매번 달라질 수 있다. 다만 파일이 바뀌었는지, 훅이 실행됐는지(디버그 로그)는 문장과 무관한 결과다.

## 실험 1. 첫 훅이 언제 울리는지 (글 3절)
- 설정(`.claude/settings.json`): `Notification`(matcher `""`)과 `Stop`에 각각 `echo "$(date +%T) <이벤트명>" >> hook.log`
- 요청: "app.js가 하는 일을 한 문장으로 알려 줘" (약 12초)
- 결과: `hook.log`에 `21:25:32 Stop` 한 줄. `Notification` 줄은 없음.
- 해석: `Stop`은 답을 마친 순간 한 번 울렸다. `Notification`은 입력·권한을 기다릴 때 울리는 이벤트라 대기 없이 끝난 이 실행에서는 울리지 않았다(문서 설명과 일치). 화면 없는 환경이라 데스크톱 알림 자체는 확인하지 못했다.

## 실험 2. 수정 후 자동 정리 (글 4절)
- 설정: 공식 예제 그대로. `PostToolUse`, matcher `Edit|Write`, `jq -r '.tool_input.file_path' | xargs npx prettier --write`
- 요청(훅 없음/있음 동일): "app.js 맨 아래에 console.log('ready'); 한 줄을 작은따옴표 그대로 추가해 줘. 다른 곳은 건드리지 마."
- 훅 없음: 마지막 줄 `console.log('ready');`(작은따옴표). Claude가 "이 파일의 다른 문자열은 큰따옴표를 쓰고 있어 새 줄만 스타일이 다르다"고 덧붙임.
- 훅 있음: 마지막 줄 `console.log("ready");`(큰따옴표, Prettier 기본 규칙). Claude가 파일이 바뀐 것을 알아차리고 "다시 편집해도 같은 훅이 또 바꿀 가능성이 높다. 훅이 걸리지 않는 셸 명령으로 바꾸면 작은따옴표를 남길 수 있지만 프로젝트 포맷 규칙을 일부러 피해 가는 것이라 확인을 받겠다"며 되물음.
- 두 경우 모두 diff는 1줄 추가뿐.

## 실험 3. 보호 파일 막기, exit 2 (글 4절)
- 설정: 공식 예제 `protect-files.sh` 그대로(`.env`, `package-lock.json`, `.git/` 패턴이면 stderr에 이유를 쓰고 `exit 2`), `chmod +x`, `PreToolUse` matcher `Edit|Write`, 명령 `"$CLAUDE_PROJECT_DIR"/.claude/hooks/protect-files.sh`
- 수동 시험: `echo '{"tool_name":"Edit","tool_input":{"file_path":".env"}}' | ./.claude/hooks/protect-files.sh` → `Blocked: .env matches protected pattern '.env'`, 종료 코드 2. `app.js`로 바꾸면 종료 코드 0.
- 요청: ".env 파일 맨 위에 '# 연습용 설정' 주석 한 줄을 추가해 줘." (2회)
- 결과: 2회 모두 `.env` 그대로. 디버그 로그에 `PreToolUse:Edit ... finished with status 2 (13ms)`와 stderr의 `Blocked:` 문장.
- Claude 답변(2회차): "프로젝트에 설정된 보호 훅이 `.env` 파일 수정을 막아서 주석을 추가하지 못했습니다 … 그래서 셸 명령으로 우회하지 않았고, 파일은 그대로입니다." 이어서 직접 추가하거나 훅에서 예외로 두라는 선택지를 제시.

## 실험 4. 같은 스크립트를 exit 1로 (글 5절)
- 설정: 실험 3과 같고 `exit 2`만 `exit 1`로 바꿈.
- 결과: 2회 모두 `.env` 맨 위에 `# 연습용 설정`이 추가됨. 디버그 로그에는 `finished with status 1`과 함께 같은 `Blocked:` 문장이 남아 있었음. 즉 "막았다"는 메시지를 내고도 수정은 진행됨.
- Claude 답변은 "주석을 추가했어요"로 끝나 훅 오류를 언급하지 않았음.

## 실험 5. matcher를 소문자로 (글 5절)
- 설정: 실험 3과 같고 matcher만 `edit|write`(소문자).
- 결과: 2회 모두 `.env`가 수정됨. 디버그 로그에 `protect-files` 실행 기록이 0건(훅이 아예 호출되지 않음).

## 재현
1. 앞 글 실험 기록(`docs/research/claude-md-experiments.md`)의 '재현' 절대로 할 일 목록 예제를 만들고 `.env`에 가짜 값 한 줄을 둔다.
2. 위 설정을 `.claude/settings.json`(과 `.claude/hooks/protect-files.sh`)에 넣고 같은 요청을 `claude -p`로 실행한다. 훅 실행 여부는 `--debug-file <경로>`로 남긴 로그에서 `Hooks:` 줄을 찾아 확인한다.

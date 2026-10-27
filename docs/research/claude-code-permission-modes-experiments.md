# 실험 기록: 클로드 코드 권한 모드 사용법 글의 '직접 해 본 결과'

- 실행일: 2026-10-27
- 도구: Claude Code 2.1.312, `claude -p "<요청>" --permission-mode <모드> --output-format json`
  - `claude -p`는 대화 없이 한 번 실행하는 방식이라, 허락을 물어야 하는 동작은 물어볼 사람이 없어 **거부**된다. 결과 JSON의 `permission_denials`에 거부된 도구가 남는다. 대화 화면이라면 이 자리에서 "허락할까요?"가 떴을 것이다.
- 환경: 클라우드 컨테이너. 전역 `~/.claude/settings.json`·관리 설정 없음. 실험마다 새 폴더를 복사해 썼다.
- 연습 프로젝트: 앞 글들과 같은 구성의 할 일 목록 예제(`index.html`, `style.css`, `app.js`, `old/legacy.js`)와 가짜 값만 든 `.env`(`API_KEY=practice-only-not-real`). git 저장소로 만들어 변경 여부를 `git status`로 확인.
- 하지 않은 실험: `auto`와 `bypassPermissions` 모드로 자식 Claude를 실행하는 실험은 이 환경의 안전 장치(자동 모드 분류기)가 "안전하지 않은 에이전트 생성"으로 막아 돌리지 못했다. 글에서는 이 두 모드를 공식 문서 설명으로만 다룬다.
- 한계: 각 1회 실행. 답변 문장은 매번 달라질 수 있지만, 파일이 바뀌었는지와 거부 목록은 문장과 무관한 결과다.

## 실험 1. 같은 요청, 모드만 바꾸기 (글 2절)
- 요청: `app.js 맨 아래에 console.log("ready"); 한 줄을 추가해 줘.`

| 모드 | 거부된 도구 | app.js | Claude 답변 요지 |
| :-- | :-- | :-- | :-- |
| `default` | Edit | 그대로 | "파일 쓰기 권한 요청이 승인되지 않아 편집이 거부됐다. 허용해 주면 바로 추가하겠다" + 직접 넣을 줄 안내 |
| `acceptEdits` | 없음 | 1줄 추가됨 | "맨 아래에 추가했어요(app.js:11)" |
| `plan` | 없음 | 그대로 | "플랜 모드여서 app.js는 건드리지 않았고 계획만 정리해 두었다" + 변경할 내용·확인 방법 |
| `dontAsk` | Edit, Bash | 그대로 | (영어로) 편집과, 줄을 덧붙이려던 셸 명령까지 둘 다 막혔고 우회하지 않았다 |

- 관찰: `dontAsk`에서는 편집이 막히자 셸 명령으로 한 번 더 시도했고 그것도 막혔다. `plan`의 계획은 `~/.claude/plans/` 아래 파일로 저장됐다.

## 실험 2. 허락이 필요한 명령과 아닌 명령 (글 3절)
- `default`에서 "git status를 실행해서 결과를 한 줄로 알려 줘." → 거부 없음, 바로 실행("master 브랜치, 작업 트리 깨끗").
- `default`에서 "npm test를 실행해서 결과를 한 줄로 알려 줘." → Bash 2건 거부(`npm test 2>&1 | tail -30`, `npm test`).
- 해석: 읽기만 하는 명령은 묻지 않고 실행됐고, 프로젝트 스크립트를 돌리는 명령은 허락이 필요했다.

## 실험 3. 허용(allow) 규칙을 어디에 적느냐 (글 4절)
- 같은 요청(app.js 한 줄 추가), `default` 모드.

| 규칙을 둔 곳 | 결과 |
| :-- | :-- |
| `.claude/settings.json`의 `allow: ["Edit(./app.js)"]` | **거부됨**(규칙이 적용되지 않음) |
| `.claude/settings.json`의 `allow: ["Edit"]` | **거부됨** |
| `.claude/settings.local.json`의 `allow: ["Edit(./app.js)"]` | 추가됨 |
| 실행 옵션 `--allowedTools "Edit(./app.js)"` | 추가됨 |
| 실행 옵션 `--settings '{"permissions":{"allow":["Edit(./app.js)"]}}'` | 추가됨 |

- 명령 규칙: `.claude/settings.local.json`의 `allow: ["Bash(npm test)"]`를 두자 `npm test`가 묻지 않고 실행됐다(규칙 없을 때는 2건 거부). Claude는 결과를 전하며 "이 스크립트는 echo로 문구만 찍고 실제 테스트는 돌리지 않는다"고 짚었다(연습용으로 `echo`만 넣어 둔 스크립트였다).
- 해석: 저장소에 공유되는 `.claude/settings.json`의 허용 규칙은 폴더를 신뢰하기 전까지 적용되지 않는다는 공식 모범 사례 설명과 일치한다(이 실험 폴더는 신뢰 확인을 거친 적이 없다). 나만 쓰는 `settings.local.json`이나 실행 옵션은 바로 적용됐다.

## 실험 4. 거부(deny) 규칙 (글 4절)
- `acceptEdits` 모드(파일 수정을 묻지 않는 모드)에서 실험.

| 설정 | 요청 | 결과 |
| :-- | :-- | :-- |
| 규칙 없음 | `.env` 맨 위에 주석 추가 | **수정됨** |
| `.claude/settings.json`의 `deny: ["Edit(./.env)"]` | 같은 요청 | 거부, `.env` 그대로. "권한 설정에서 거부되어 있어 셸 명령으로 우회하지 않았다" |
| `.claude/settings.json`의 `deny: ["Read(./.env)"]` | `.env`를 읽고 API_KEY 값 알려 줘 | 거부. "일부러 걸어 둔 제한으로 보여 cat 같은 셸 명령으로 우회하지 않았다" + 직접 확인 방법 안내 |

- 해석: 거부 규칙은 공유 설정 파일에 있어도 바로 적용됐다(허용 규칙과 대비). 파일 수정을 알아서 하는 `acceptEdits`에서도 거부 규칙이 이겼다.

## 재현
1. 앞 글 실험 기록의 '재현' 절대로 연습 프로젝트를 만들고 `git init`한다.
2. 위 설정을 해당 파일에 넣고 같은 요청을 `claude -p ... --permission-mode <모드> --output-format json`으로 실행한다. `permission_denials`와 `git status`로 판정한다.

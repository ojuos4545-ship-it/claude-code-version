# 리서치 노트: 클로드 코드(Claude Code) 권한 모드 사용법

- 조사일: 2026-10-27
- 기준 시점: 2026-10-27 공식 문서 기준. 확인한 최신 버전은 Claude Code v2.1.312(2026-10-27 배포, 공식 변경 이력 [8]). 모드 이름·기본값·단축키가 버전마다 자주 바뀌므로 글에 "2026년 10월, v2.1.31x 기준"을 꼭 밝힐 것.
- 목적/독자: 클로드 코드 입문자 대상 정보 글. 블로그 시리즈 4편('핵심 기능 5가지' → 'CLAUDE.md 작성법' → '훅 사용법' → 이번 '권한 모드 사용법')의 재료.
- 출처 범위: 모든 사실은 code.claude.com 공식 문서(A등급)에서 직접 연 원문으로 확인했다. 외부 2차 매체는 이 세션 네트워크에서 접속이 막혀(7절) 교차 확인은 공식 문서 여러 페이지끼리 했다.

## 1. 결론 요약

- 권한 모드는 "Claude가 묻지 않고 해도 되는 일의 범위"를 정하는 스위치다. 공식 이름은 `default`(화면 표시는 Manual), `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` 여섯 가지다 [1][2].
- **중요한 변화**: v2.1.283 이상에서는 대화형 터미널·VS Code의 새 세션이 **auto 모드로 시작**한다(요금제·제공자 무관). 예전 글에 흔한 "기본은 매번 묻는 default 모드"는 더 이상 맞지 않는다. 반면 `claude -p`와 Agent SDK는 v2.1.302부터 `default`(Manual)로 시작한다 [1][4].
- 세션 중에는 `Shift+Tab`으로 바꾸고(auto → default → acceptEdits → plan → …), 시작할 때는 `--permission-mode`, 늘 쓰는 기본값은 설정 파일의 `permissions.defaultMode`로 정한다 [1].
- 허용·거부 규칙(`permissions.allow/ask/deny`)은 모드와 별개로 작동하며, 평가 순서는 **deny → ask → allow**다. deny 규칙과 PreToolUse 훅의 `"deny"`는 `bypassPermissions`를 포함한 **모든 모드에서 유지**된다 [2][4][6].
- 입문자에게는 기본 auto를 쓰되 "절대 안 되는 일"은 deny 규칙·훅으로 막고, 큰 변경 전에는 plan 모드로 계획부터 받는 방식이 공식 문서 권장 흐름과 맞다. `bypassPermissions`는 인터넷 없는 컨테이너·VM 같은 격리 환경 전용이다 [1][4].

## 2. 질문별 조사 결과

### Q1. 권한 모드는 무엇이고 왜 있나? 모드 종류와 각 모드의 동작, 새 세션 기본 모드

- [사실] 공식 정의: 권한 모드는 Claude가 세션에서 먼저 묻지 않고 할 수 있는 작업을 정한다. Manual 모드에서는 파일 편집, 셸 명령 실행, 네트워크 접근 등 대부분의 작업 전에 멈추고 묻는다. auto 모드에서는 두 번째 모델인 분류기[^1]가 사용자 대신 작업을 검토한다 (출처 [1]).
- [사실] 한국어 공식 문서 표현: "각 모드는 편의성과 감시 사이에서 서로 다른 트레이드오프를 만듭니다" (출처 [3]).
- [사실] 모드별 동작(묻지 않고 실행되는 것 / 공식 '최적 사용 사례') (출처 [1][2][3]):

| 설정 값 | 상태 표시줄 | 묻지 않고 하는 일 | 공식 권장 용도 |
| :--- | :--- | :--- | :--- |
| `default` (Manual, `manual`도 별칭으로 허용) | `⏸ manual mode on`(회색) | 읽기만 | 모든 작업 직접 검토, 민감한 작업 |
| `acceptEdits` | `⏵⏵ accept edits on` | 읽기, 파일 편집, 작업 폴더 안의 `mkdir`·`touch`·`rm`·`rmdir`·`mv`·`cp`·`sed` | 검토 중인 코드 반복 작업 |
| `plan` | `⏸ plan mode on` | 읽기(+auto 사용 가능 시 분류기가 승인한 명령) | 변경 전 코드베이스 탐색 |
| `auto` | `⏵⏵ auto mode on` | 백그라운드 안전 검사를 거친 모든 작업 | 장시간 작업, 프롬프트 피로 감소 |
| `dontAsk` | `⏵⏵ don't ask on` | 작업 폴더 안 읽기와 미리 허용한 도구만. 물어야 하는 건 전부 거부 | 잠금된 CI·스크립트 |
| `bypassPermissions` | `⏵⏵ bypass permissions on` | 모든 작업 | 격리된 컨테이너·VM 전용 |

- [사실] Manual 모드 기준 도구별 승인 필요 여부: 파일 읽기·Grep은 작업 폴더 안에서 묻지 않음, Bash는 내장 읽기 전용 명령(`ls`, `cat`, `grep`, `git`의 읽기 전용 형태 등) 외에는 물음, 파일 수정은 물음, WebFetch·WebSearch는 물음 (출처 [2]).
- [사실] "Yes, and don't ask again"을 고르면 Bash 명령·WebFetch 도메인 승인은 저장소 루트의 `.claude/settings.local.json`에 영구 저장되고, 파일 수정 승인은 세션이 끝날 때까지만 유지된다 (출처 [2][5]).
- [사실] 새 세션 기본 모드(터미널 기준 우선순위: ① `--permission-mode` 또는 `--dangerously-skip-permissions` → ② 설정 파일의 `permissions.defaultMode` → ③ 내장 기본값) (출처 [1]):
  - 터미널·VS Code, v2.1.283 이상: 모든 요금제·제공자에서 `auto`
  - 그 이전 버전: Pro·Max·Team 요금제 등 일부 조건에서만 `auto`, 아니면 `default`
  - `claude -p`·Agent SDK(v2.1.302 이상): `default`
  - HIPAA 구성 조직(v2.1.285 이상), 관리자가 `disableAutoMode: "disable"`을 건 경우: `default`
- [사실] best-practices 문서도 "Interactive terminal and VS Code sessions start in auto mode."라고 적고 있다 (출처 [4]).
- [해석] 입문자 글에서는 "설치 직후 기본이 auto"라는 점을 앞에 두는 것이 좋다. 다만 오래된 버전을 쓰는 독자는 Manual로 시작할 수 있으므로 상태 표시줄 글자로 직접 확인하라고 안내하는 것이 안전하다.
- 신뢰도: 높음 (공식 문서 3개 페이지 일치)

### Q2. 모드를 바꾸는 방법

- [사실] CLI 세션 중: `Shift+Tab`으로 순환. auto에서 처음 누르면 `default`로 가고, 이후 `default` → `acceptEdits` → `plan` 순서. 선택적 모드는 `plan` 뒤에 붙으며 `bypassPermissions`가 먼저, `auto`가 마지막 (출처 [1][3]).
  - 공식 문서 예시: auto로 시작한 세션에서 누를 때마다 `auto mode on` → `manual mode on` → `accept edits on` → `plan mode on` → 다시 `auto mode on` (출처 [3]).
  - `auto`로 순환할 때는 확인 창이 없다. `dontAsk`는 순환에 나오지 않고 `--permission-mode dontAsk`로만 켠다. `bypassPermissions`는 `--permission-mode bypassPermissions`, `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions` 또는 사용자/`--settings`/관리 설정의 `defaultMode: "bypassPermissions"`로 시작했을 때만 순환에 나온다 (출처 [1][3]).
  - v2.1.247 이상에서는 Manual·acceptEdits의 Bash 승인 창에 "Yes, and switch to auto mode" 선택지가 뜰 수 있다(모든 창에 뜨지는 않음) (출처 [1][2]).
- [사실] 시작할 때 지정 (출처 [1]):
  ```bash
  claude --permission-mode plan
  claude --permission-mode acceptEdits
  claude -p "Run the test suite and fix any failures" --permission-mode auto
  ```
  best-practices 문서는 Manual로 시작하는 예로 `claude --permission-mode manual`을 든다 (출처 [4]).
- [사실] 설정 파일 기본값: `~/.claude/settings.json`에 아래처럼 쓴다. 단 `"auto"`와 `"bypassPermissions"`는 프로젝트 파일(`.claude/settings.json`, `.claude/settings.local.json`)에 쓰면 무시된다. 사용자 설정이나 관리 설정에 둬야 한다 (출처 [1][5]).
  ```json
  {
    "permissions": {
      "defaultMode": "default"
    }
  }
  ```
- [사실] 다른 화면: VS Code는 입력창 아래 모드 표시기를 클릭하고 기본값은 `claudeCode.initialPermissionMode`로 정한다. 데스크톱 앱은 Code 탭 입력창 아래 모드 선택기, 기본값은 같은 settings 파일의 `defaultMode`. claude.ai/code는 입력창 아래 드롭다운, 모바일은 `+` → Permission. JetBrains는 IDE 터미널에서 CLI와 같다 (출처 [1][3]).
- 신뢰도: 높음

### Q3. 플랜 모드

- [사실] 하는 일: 코드를 바꾸지 않고 조사·제안만 한다. 파일을 읽고, 탐색용 셸 명령을 실행하고, 계획을 쓴다. 소스 파일은 편집하지 않으며, 계획을 승인할 때까지 편집이 막힌다(예외: bypass가 가능한 대화형 터미널 세션) (출처 [1][2]).
- [사실] 계획 중 셸 명령 처리: auto 사용 가능하고 `useAutoModeDuringPlan`(기본 켜짐)이면 분류기가 검토, 그렇지 않으면 읽기 전용 집합 밖의 명령은 묻는다 (출처 [1]).
- [사실] 들어가는 법: `Shift+Tab`, 프롬프트 하나 앞에 `/plan` 붙이기, `claude --permission-mode plan`. 승인 없이 나가려면 `Shift+Tab`을 다시 누른다 (출처 [1][3]).
- [사실] 승인 흐름: 계획이 준비되면 Claude가 계획을 보여 주고 선택지를 준다 (출처 [1]).
  - "Yes, and use auto mode" (auto를 못 쓰면 "Yes, auto-accept edits")
  - "Yes, manually approve edits" (편집을 하나씩 검토)
  - "No, keep planning" (계획 모드에 남아 수정 요청)
  - bypass가 켜져 있으면 bypass로 전환하는 선택지도 나옴
  - 승인하면 플랜 모드가 끝나고 고른 선택지의 모드로 바뀌어 편집이 시작된다. `Ctrl+G`로 계획을 에디터에서 열어 고칠 수 있다.
- [사실] 플랜 모드에서는 PreToolUse 훅이 `"allow"`를 반환해도 파일 편집 등 읽기 전용이 아닌 호출은 승인되지 않는다(`ExitPlanMode` 제외) (출처 [2][6]).
- [해석] 입문자에게는 "큰 변경 전에 plan → 계획 검토 → 승인 선택지로 모드 결정"이라는 3단계로 설명하면 이해가 쉽다.
- 신뢰도: 높음

### Q4. 허용·거부 규칙(permissions.allow/ask/deny)

- [사실] 세 종류: allow(묻지 않고 사용), ask(쓸 때마다 확인), deny(사용 금지) (출처 [2]).
- [사실] 우선순위: **deny → ask → allow** 순서로 평가하고 먼저 맞는 것이 결과를 정한다. 규칙이 더 구체적이어도 순서는 바뀌지 않는다. 예: deny `Bash(aws *)`가 있으면 allow `Bash(aws s3 ls)`도 막힌다 (출처 [2]).
- [사실] 문법은 `Tool` 또는 `Tool(지정자)` (출처 [2]):
  - `Bash` = 모든 Bash 명령, `Bash(npm run build)` = 그 명령 정확히, `Bash(npm run *)` = npm run으로 시작하는 명령
  - `Read(./.env)` = 현재 폴더 `.env` 읽기, `Read(./secrets/**)` = secrets 폴더 아래 전부
  - `WebFetch(domain:example.com)` = 해당 도메인 요청
  - `*`는 하위 명령 뒤에 둘 것: `Bash(git log *)`는 git log만, `Bash(git *)`는 모든 git 명령 허용
  - `Bash(ls *)`는 `lsof`와 안 맞고 `Bash(ls*)`는 맞는다(공백 차이). `Bash(ls:*)`는 `Bash(ls *)`와 같다.
  - `&&`, `;`, `|` 등으로 이은 복합 명령은 각 부분이 모두 허용돼야 묻지 않는다.
  - Read/Edit 경로는 gitignore 문법. `//path`는 절대 경로, `~/path`는 홈 기준, `/path`는 설정 파일 기준(절대 경로 아님!), `./path`는 현재 폴더 기준.
- [사실] 공식 예시 설정 (출처 [5]):
  ```json
  {
    "permissions": {
      "allow": ["Bash(npm run lint)", "Bash(npm run test *)"],
      "deny": ["Read(./.env)", "Read(./.env.*)"]
    }
  }
  ```
- [사실] 설정 파일 위치와 우선순위(높은 것부터): 관리 설정 → 명령줄(`--settings`) → 프로젝트 로컬 `.claude/settings.local.json` → 공유 프로젝트 `.claude/settings.json` → 사용자 `~/.claude/settings.json`. 단 `permissions.allow` 같은 목록은 덮어쓰지 않고 합쳐지며, 어느 단계에서든 deny되면 다른 단계에서 허용할 수 없다 (출처 [2][5]).
- [사실] 프로젝트 `.claude/settings.json`의 allow 규칙은 폴더 신뢰(workspace trust) 창을 수락해야 적용되고, deny·ask는 즉시 적용된다 (출처 [2][5]).
- [사실] `/permissions` 명령: 모든 규칙과 각 규칙이 온 settings 파일을 보여 주고 추가·삭제할 수 있다. Claude가 작업 중일 때 바꿔도 다음 도구 호출부터 반영된다. auto 사용 가능하면 Auto mode 탭, 분류기가 막은 작업의 Recently denied 목록도 있다 (출처 [1][2]).
- [사실] 설정 파일 수정은 대부분 재시작 없이 반영된다(permissions, hooks 포함). 적용 여부는 `/status`의 Setting sources 줄로 확인 (출처 [5]).
- [사실] 공식 경고: 규칙은 모델이 아니라 Claude Code가 강제한다. 프롬프트나 CLAUDE.md는 Claude가 하려는 일을 바꿀 뿐 허용 범위를 바꾸지 않는다 (출처 [2]).
- 신뢰도: 높음

### Q5. auto 모드·bypassPermissions의 위험과 주의점, 입문자 추천

- [사실] auto 모드 공식 경고(원문): "Auto mode reduces permission prompts but does not guarantee safety. Use it for tasks where you trust the general direction, not as a replacement for review on sensitive operations." 한국어 공식 번역: "자동 모드는 권한 프롬프트를 줄이지만 안전을 보장하지 않습니다." (출처 [1][3]).
- [사실] auto 모드 동작: 분류기 모델이 실행 전 작업을 검토해 요청 범위를 넘는 작업, 모르는 인프라 대상 작업, 악성 콘텐츠에 끌려간 듯한 작업을 막는다. 기본 차단 예: `curl | bash`, 민감 데이터 외부 전송, 운영 배포·마이그레이션, force push, `git reset --hard`, 자격 증명 출력 등. 기본 허용 예: 작업 폴더 안 파일 작업, 선언된 의존성 설치, 읽기 전용 HTTP 요청 (출처 [1][4]).
- [사실] auto에 들어가면 `Bash(*)`, `Bash(python*)` 같은 넓은 allow 규칙은 잠시 꺼지고(나가면 복원), `Bash(npm test)` 같은 좁은 규칙은 유지된다 (출처 [1]).
- [사실] 막히면 알림이 뜨고 `/permissions`의 Recently denied에 남으며 `r`로 수동 승인 재시도 가능. 연속 3회 또는 총 20회 막히면 auto가 멈추고 다시 묻기 시작한다(값 변경 불가) (출처 [1][4]).
- [사실] 대화로 "push하지 마"라고 하면 분류기가 막지만, 규칙으로 저장되지 않아 대화 압축 때 사라질 수 있다. 확실히 막으려면 deny 규칙을 쓰라고 공식 문서가 안내 (출처 [1][4]).
- [사실] auto 사용 조건: 지원 모델(Anthropic API 기준 Opus 4.6+, Sonnet 4.6+ 등)과 요금제·조직 설정 필요. 관리자는 `permissions.disableAutoMode: "disable"`로 끌 수 있다 (출처 [1][2]).
- [사실] bypassPermissions 공식 경고(원문): "Only use this mode in isolated environments like containers, VMs, or dev containers without internet access, where Claude Code cannot damage your host system." 그리고 "`bypassPermissions` offers no protection against prompt injection or unintended actions." 한국어 공식 번역: "이 모드는 인터넷 접근이 없는 컨테이너, VM 또는 개발 컨테이너와 같은 격리된 환경에서만 사용하십시오." / "`bypassPermissions`는 프롬프트 주입이나 의도하지 않은 작업에 대한 보호를 제공하지 않습니다." (출처 [1][3]).
- [사실] bypass에서도 묻거나 막는 것: 명시적 ask 규칙, deny 규칙, `AskUserQuestion`, 루트·홈·작업 폴더 등 치명적 경로[^2]에 대한 `rm`/`rmdir`(터미널에서 2분 카운트다운 확인창) 등 (출처 [1]).
- [사실] bypass 켜는 법: `--permission-mode bypassPermissions`, `--dangerously-skip-permissions`, 또는 `defaultMode`. bypass 없이 시작한 세션에서는 중간에 들어갈 수 없다. 첫 실행 시 동의 창이 뜬다. Linux·macOS에서 root/sudo로는 실행이 거부된다 (출처 [1]).
- [사실] 보호 경로[^3](`.git`, `.vscode`, `.claude`, `.bashrc`, `.mcp.json` 등) 쓰기는 bypass 외 모드에서 자동 승인되지 않는다. allow 규칙으로도 미리 허용할 수 없다 (출처 [1]).
- [사실] best-practices의 비교: Manual은 안전하지만 "after the tenth prompt you start approving without reading"(열 번째쯤엔 읽지 않고 승인하게 됨), bypass는 일회용 컨테이너에서만 의미가 있고, auto가 그 중간이다 (출처 [4]).
- [해석] 입문자 추천 사용법(공식 문서 내용을 조합한 판단):
  1. 기본 auto 그대로 시작하되 상태 표시줄로 현재 모드를 확인
  2. `.env`, 비밀 폴더, `git push` 등 "절대 안 되는 것"은 `deny` 규칙에 넣기
  3. 큰 변경은 `/plan`이나 `Shift+Tab`으로 계획부터 받고, 승인 단계에서 "manually approve edits"를 골라 익숙해질 때까지 하나씩 보기
  4. 모든 걸 직접 보고 싶으면 Manual로 바꾸고, 질문이 너무 많으면 `/fewer-permission-prompts`(최근 기록을 보고 읽기 전용 명령을 허용 목록에 추가, 출처 [4]) 활용
  5. `bypassPermissions`·`--dangerously-skip-permissions`는 개인 PC에서 쓰지 않기
- 신뢰도: 높음

### Q6. 훅과 권한 모드의 관계 (앞 글 '훅 사용법'과 연결)

- [사실] PreToolUse 훅은 권한 확인보다 먼저, 모든 도구 호출(EndConversation 제외)에서 실행된다. 결과로 호출 거부, 확인 강제, 확인 생략을 할 수 있다 (출처 [2][7]).
- [사실] 훅 가이드 원문: "a hook that returns `permissionDecision: "deny"` blocks the tool even in `bypassPermissions` mode or with `--dangerously-skip-permissions`. `PreToolUse` hooks fire before any permission-mode check, in every permission mode, including `dontAsk`." 즉 모드를 바꿔도 훅 deny는 우회되지 않는다 (출처 [6]).
- [사실] 반대로 훅의 `"allow"`는 settings의 deny 규칙을 넘지 못하고, ask 규칙이 맞으면 여전히 묻는다 (출처 [2][6][7]).
- [사실] exit code 2로 끝나는 훅은 권한 규칙 평가 전에 호출을 멈추므로 allow 규칙이 있어도 막힌다. 공식 예: Bash 전체를 allow에 넣고 PreToolUse 훅으로 특정 명령만 막는 구성 (출처 [2][7]).
- [사실] 여러 PreToolUse 훅이 다르게 답하면 `deny` > `defer` > `ask` > `allow` 순 (출처 [7]).
- [사실] 훅 입력의 `permission_mode` 필드 값: `"default"`, `"plan"`, `"acceptEdits"`, `"auto"`, `"dontAsk"`, `"bypassPermissions"`. Manual 모드도 `"default"`로 들어온다 (출처 [7]).
- [사실] PermissionRequest 훅은 Claude Code가 사용자에게 승인을 물으려 할 때만 실행되며, exit 2는 무시되고 `decision` 객체로 허용/거부한다 (출처 [7]).
- [사실] best-practices: deny·ask 규칙과 PreToolUse 훅은 분류기보다 먼저 적용되므로 auto에서도 다른 모드와 똑같이 막는다 (출처 [4]).
- [사실] 예외 주의: 관리 설정이 없고 Team/Enterprise 로그인이 아닌 환경에서는 설치한 mod[^4]가 훅이 막은 호출을 승인할 수 있다고 공식 문서가 적고 있다 (출처 [2][6]). 입문자 글에는 각주 수준으로만.
- 신뢰도: 높음

### Q7. 자주 하는 실수 / 문제 해결

- [사실] `defaultMode: "auto"`가 무시됨 → 프로젝트 파일(`.claude/settings.json`/`.local.json`)에 썼기 때문. `~/.claude/settings.json`으로 옮긴다 (출처 [1][5]).
- [사실] auto 모드를 못 씀 → 모델·요금제 조건, `disableAutoMode` 설정 확인. 서버에서 꺼진 응답을 받은 세션은 끝날 때까지 꺼져 있으니 새 세션 시작 (출처 [1]).
- [사실] `claude -p` 호출이 거부됨 → v2.1.302부터 기본이 default라서. `--allowedTools`로 허용하거나 `--permission-mode auto` 사용 (출처 [1][4]).
- [사실] "don't ask again"을 눌렀는데 계속 물음 → 그 승인은 로컬 파일의 allow 규칙이라, 프로젝트·관리 설정의 ask 규칙을 이기지 못한다 (출처 [5]).
- [사실] `Read(/Users/alice/file)`처럼 슬래시 하나로 쓴 경로는 절대 경로가 아니다. 절대 경로는 `//`로 시작 (출처 [2]).
- [사실] `Write(path)` 규칙은 아무것도 매칭하지 않는다. 경로 규칙은 `Edit(...)`, `Read(...)`로 쓴다 (출처 [2]).
- [사실] `.claudeignore` 파일은 효과가 없다. `Read` deny 규칙으로 옮긴다 (출처 [2]).
- [사실] Bash deny는 보안 경계가 아니다: `Bash(rm *)`는 `/bin/rm ...`이나 `bash -c 'rm ...'`을 막지 못한다. `Bash(curl http://github.com/ *)`처럼 인자로 제한하는 규칙은 깨지기 쉽다. 확실히 막으려면 샌드박스(`/sandbox`)·PreToolUse 훅 병행 (출처 [2][4]).
- [사실] Read deny는 `cat .env`는 막지만 Python 스크립트가 직접 파일을 여는 것 등은 못 막는다 (출처 [2][4]).
- [사실] `*`를 하위 명령 앞에 두면(`Bash(git * main)`) 시작 시 경고가 뜨고 의도보다 넓게 허용된다 (출처 [2]).
- [사실] settings 파일은 엄격한 JSON이라 `//` 주석이나 끝 쉼표가 있으면 Settings Error. `/status`, `claude doctor`로 확인 (출처 [5]).
- [사실] 팀원이 커밋된 allow 규칙을 못 받음 → 각자 폴더 신뢰 창을 수락해야 적용 (출처 [5]).
- 신뢰도: 높음

## 3. 핵심 수치·사실 표

| 항목 | 내용 | 기준일 | 출처 |
| :--- | :--- | :--- | :--- |
| 모드 수·이름 | default(Manual), acceptEdits, plan, auto, dontAsk, bypassPermissions | 2026-10-27 | [1][2] |
| 터미널·VS Code 새 세션 기본 | auto (v2.1.283 이상, 전 요금제·제공자) | 2026-10-27 | [1][3][4] |
| `claude -p`·SDK 기본 | default (v2.1.302 이상) | 2026-10-27 | [1] |
| Shift+Tab 순환 | (auto →) default → acceptEdits → plan → [bypassPermissions] → [auto] | 2026-10-27 | [1][3] |
| 규칙 평가 순서 | deny → ask → allow | 2026-10-27 | [2] |
| 설정 우선순위 | 관리 > 명령줄 > 프로젝트 로컬 > 공유 프로젝트 > 사용자 | 2026-10-27 | [5] |
| auto 일시 중지 기준 | 연속 3회 또는 총 20회 차단 (변경 불가) | 2026-10-27 | [1][4] |
| 치명적 경로 rm 확인 시간 | auto·bypass 터미널에서 2분 카운트다운 (v2.1.281 이상) | 2026-10-27 | [1] |
| 최신 버전 | v2.1.312 (2026-10-27) | 2026-10-27 | [8] |

## 4. 상충하거나 불확실한 내용

- **`claude -p` 기본 모드 범위**: permission-modes 문서는 "v2.1.302+ `claude -p`·SDK는 `default`"라고 일반적으로 적지만, 변경 이력의 2.1.302 항목은 "on third-party providers, with telemetry off or on a fresh install" 조건을 붙였다 [1][8]. 글에서는 "v2.1.302 이후 `-p`는 기본적으로 Manual로 시작할 수 있으니 필요하면 `--permission-mode`를 명시"처럼 완화해 쓰는 것을 권장.
- **auto 기본값 전환 시점**: 공식 문서는 버전(v2.1.228 macOS·Linux·WSL, v2.1.233 Windows, v2.1.283 전 요금제)만 적는다 [1]. 검색 결과의 외부 기사들은 "2026년 8월 14일 Pro·Max·Team 기본화" 등을 언급하나 원문을 열지 못해 확인하지 못했다(7절). 날짜는 글에 쓰지 말 것.
- **Shift+Tab 두 번 = 플랜 모드?**: 일부 블로그(검색 요약)는 "두 번 빠르게 눌러 Plan Mode"라고 설명하지만, 현재 공식 문서는 단순 순환이다. auto로 시작한 세션에서는 plan까지 세 번 눌러야 한다(auto→manual→accept edits→plan) [3]. 공식 문서 기준으로 쓸 것.
- **2차 출처 교차 확인 부족**: 외부 매체 접속이 막혀 모든 질문을 공식 문서(서로 다른 페이지 [1]~[7])로만 교차 확인했다. 1차 출처라 신뢰도는 높지만 "독립된 2차 출처" 확인은 못 했다.

## 5. 글쓰기 에이전트에게 (활용 가이드)

**핵심 메시지**
- 권한 모드 = "Claude가 묻지 않고 해도 되는 일의 범위". 운전 보조 단계처럼 설명 가능(해석, 비유는 글쓴이 판단).
- 2026년 10월 현재 새 세션 기본은 auto. "예전엔 매번 물었는데 왜 안 묻지?"에 대한 답이 된다.
- 모드는 바뀌지만 deny 규칙과 훅 deny는 어떤 모드에서도 유지된다 → 3편(훅)과 자연스럽게 연결되는 지점.
- 플랜 모드는 "먼저 계획, 승인 후 실행".

**FAQ 후보**
- Q. 지금 무슨 모드인지 어떻게 아나요? → 입력창 아래 상태 표시줄 글자(`⏵⏵ auto mode on` 등) [1]
- Q. 매번 묻게 하고 싶어요 → `Shift+Tab`으로 manual, 또는 `~/.claude/settings.json`에 `"defaultMode": "default"` [1]
- Q. 특정 명령만 묻지 않게 하려면? → `/permissions` 또는 `permissions.allow`에 `Bash(npm run test *)` [2][5]
- Q. `.env`를 절대 못 읽게 하려면? → `Read(./.env)` deny + 필요하면 샌드박스 [2][4]
- Q. `--dangerously-skip-permissions` 써도 되나요? → 인터넷 없는 컨테이너·VM 전용이라는 공식 경고 [1]
- Q. auto면 안전한가요? → "안전을 보장하지 않습니다"라는 공식 경고 [3]

**비교 포인트**
- Manual: 안전하지만 질문 피로, 자리 비우면 멈춤 / auto: 흐름 유지, 판단은 모델이라 틀릴 수 있음 / bypass: 제약 없음, 격리 환경 전용 [4]
- CLAUDE.md(부탁) vs 권한 규칙·훅(강제): 2편·3편과 대비하기 좋은 축 [2][4]

**연관 키워드 후보**
- 클로드 코드 권한 모드, Claude Code permission mode, Shift+Tab, 플랜 모드, plan mode, auto 모드, acceptEdits, bypassPermissions, dangerously-skip-permissions, settings.json permissions, /permissions, defaultMode

**주의**
- "기본 모드는 default(매번 묻기)"라고 쓰지 말 것(v2.1.283 이후 auto).
- "Shift+Tab 두 번이면 플랜 모드"라고 단정하지 말 것(시작 모드에 따라 다름).
- auto나 deny 규칙을 "완벽히 안전/완전 차단"으로 쓰지 말 것. 공식 문서가 한계를 명시함.
- 모델 이름·버전 조건(Opus 4.6+ 등)은 자주 바뀌므로 글에는 "지원 모델·요금제 조건이 있다" 정도로만.
- 상태 표시줄 기호(`⏵⏵`, `⏸`)는 환경에 따라 다르게 보일 수 있으니 글자 부분 위주로 안내.

**직접 경험으로 보강할 부분 (리서치로 채울 수 없음)**
- 실제 Shift+Tab 순환 화면 캡처, 승인 창 화면, 플랜 승인 선택지 화면
- 글쓴이 환경에서 auto가 막은 사례, deny 규칙을 넣어 본 결과
- 3편에서 만든 훅이 bypass·auto에서도 막는지 직접 시험한 결과

## 6. 참고 출처

| 번호 | 제목 | 발행처 | 발행·수정일 | 등급 | URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [1] | Choose a permission mode | Anthropic (Claude Code Docs) | 수정일 표기 없음, 2026-10-27 열람(본문에 v2.1.311 내용 포함) | A | https://code.claude.com/docs/en/permission-modes |
| [2] | Configure permissions | Anthropic (Claude Code Docs) | 수정일 표기 없음, 2026-10-27 열람 | A | https://code.claude.com/docs/en/permissions |
| [3] | 권한 모드 선택 (한국어판) | Anthropic (Claude Code Docs) | 수정일 표기 없음, 2026-10-27 열람(v2.1.283 내용 반영) | A | https://code.claude.com/docs/ko/permission-modes |
| [4] | Best practices for Claude Code | Anthropic (Claude Code Docs) | 수정일 표기 없음, 2026-10-27 열람 | A | https://code.claude.com/docs/en/best-practices |
| [5] | Settings files and precedence | Anthropic (Claude Code Docs) | 수정일 표기 없음, 2026-10-27 열람 | A | https://code.claude.com/docs/en/settings |
| [6] | Automate actions with hooks (훅 가이드) | Anthropic (Claude Code Docs) | 수정일 표기 없음, 2026-10-27 열람 | A | https://code.claude.com/docs/en/hooks-guide |
| [7] | Hooks reference | Anthropic (Claude Code Docs) | 수정일 표기 없음, 2026-10-27 열람 | A | https://code.claude.com/docs/en/hooks |
| [8] | Changelog | Anthropic (Claude Code Docs) | 최신 항목 v2.1.312, 2026-10-27 | A | https://code.claude.com/docs/en/changelog |

## 7. 확인하지 못한 자료

- gigazine.net 기사(auto 모드 기본화, 2026-08-10 추정 URL), simonwillison.net 글: 이 세션 네트워크에서 도메인 접속 불가(ENOTFOUND). 접속하려면 세션 네트워크 설정에서 해당 도메인 허용 필요. 두 곳이 실패해 다른 외부 사이트 시도는 중단했다.
- 검색 결과에만 보인 자료(원문 미확인, 근거로 쓰지 않음): daleseo.com "클로드 코드 권한 모드" 글, wikidocs.net의 권한 모드 관련 문서들, aicatchup.com·itechify.com·clauderemotecontrol.com 등의 "2026-08-14 auto 기본화" 기사, Medium 회원 전용 글(유료 벽).
- hooks 레퍼런스[7]는 분량(약 28만 자)이 커서 PreToolUse·PermissionRequest·permission_mode 부분만 확인했다.
- 변경 이력[8]은 앞부분(최근 항목)만 확인했다. auto 기본값 전환 항목 자체는 확인 범위에 없었다.

## 용어 설명

[^1]: 분류기(classifier): auto 모드에서 Claude가 하려는 작업을 실행 전에 따로 검토하는 두 번째 AI 모델. 위험해 보이면 막는다. 기본값은 Sonnet 5 [1].
[^2]: 치명적 경로(critical path): 파일 시스템 루트, 최상위 폴더, 홈 폴더, 현재 작업 폴더와 그 상위 폴더처럼 지우면 큰일 나는 위치. 이곳을 지우는 `rm`은 allow 규칙이나 훅으로도 자동 승인되지 않는다 [1].
[^3]: 보호 경로(protected paths): `.git`, `.claude`, `.vscode` 같은 설정 폴더와 `.bashrc`, `.gitconfig`, `.mcp.json` 같은 설정 파일. 잘못 바뀌면 도구나 셸 동작이 달라지므로 bypass 외에는 자동 승인하지 않는다 [1].
[^4]: mod: Claude Code 플러그인 안에서 도구 호출 승인 등 이벤트를 처리할 수 있는 확장 기능. 입문자 글에서는 깊이 다루지 않아도 된다 [2].
- 관리 설정(managed settings): 회사·조직 관리자가 배포하는 설정. 개인 설정으로 덮어쓸 수 없다 [5].
- 폴더 신뢰(workspace trust): 처음 여는 폴더에서 "이 폴더를 믿겠냐"고 묻는 창. 수락해야 그 프로젝트의 allow 규칙이 적용된다 [2].
- 샌드박스(sandbox): 운영체제 수준에서 셸 명령의 파일·네트워크 접근을 제한하는 기능. 명령 글자에 의존하는 권한 규칙의 빈틈을 보완한다 [2].

# 리서치 노트: 클로드 코드(Claude Code) 스킬(Skills) 사용법

- 조사일: 2026-10-28
- 기준 시점: 2026-10-28에 연 Claude Code 공식 문서(code.claude.com/docs), Claude 플랫폼 문서(platform.claude.com), Claude Code 공식 변경 이력(GitHub, 맨 위 버전 2.1.312). 공식 문서에는 수정일 표기가 없어 "조사일 기준 공개 상태"로 본다.
- 목적/독자: 네이버 블로그 정보 글의 근거 자료. 독자는 코딩 경험이 적은 클로드 코드 입문자. 시리즈('핵심 기능 5가지' → 'CLAUDE.md 작성법' → '훅 사용법')에서 '스킬' 실습편.
- [가정] 독자는 터미널에서 `claude`를 실행해 본 정도다. 플러그인 제작, 조직 관리 설정(managed settings)은 글의 범위 밖으로 두고 짧게만 언급한다.
- 참고: 스킬 문서는 약 117,900자라 도구로 두 번에 나눠 읽었고, 열람 도구가 원문을 요약·발췌한 결과를 바탕으로 정리했다. 글에 옮길 핵심 문장은 원문 링크에서 한 번 더 확인하길 권한다.

## 1. 결론 요약

- [사실] 스킬은 `SKILL.md` 파일 하나(필요하면 보조 파일 포함)로 만드는 "다시 쓰는 지침서"다. 내가 `/스킬이름`으로 직접 부르거나, Claude가 `description`(설명)을 보고 알아서 불러온다 [1][2].
- [사실] CLAUDE.md는 매 세션 전부 읽히고, 스킬은 평소엔 이름·설명만 올라가 있다가 쓸 때 본문이 올라간다. 훅은 Claude의 판단과 상관없이 정해진 순간에 반드시 실행된다. 서브에이전트는 따로 일하고 요약만 돌려준다 [2][7].
- [사실] 위치는 개인용 `~/.claude/skills/<이름>/SKILL.md`, 프로젝트용 `.claude/skills/<이름>/SKILL.md`. 프론트매터[^1] 필드는 Claude Code에서 모두 선택이고 `description`만 권장이다. 자동 호출을 끄려면 `disable-model-invocation: true`, `/` 메뉴에서 숨기려면 `user-invocable: false` [1].
- [사실] 예전 `.claude/commands/` 커스텀 명령은 스킬로 통합되었다(변경 이력 v2.1.3). 기존 파일은 계속 작동하고, 이름이 겹치면 스킬이 이긴다. 새로 만들 때는 스킬을 권장한다 [1][11][12].
- [사실] 남이 만든 스킬은 "소프트웨어 설치처럼" 다뤄야 한다. 특히 저장소에 들어 있는 스킬의 `allowed-tools`는 폴더 신뢰 여부와 관계없이 적용되므로 실행 전에 직접 읽어 봐야 한다 [1][4][10].

## 2. 질문별 조사 결과

### Q1. 스킬이란 무엇이고, CLAUDE.md·훅·서브에이전트·커스텀 명령과 무엇이 다른가?

- [사실] 공식 정의: "Skills extend what Claude can do." `SKILL.md`에 지침을 쓰면 Claude가 도구 상자에 추가하고, 관련 있을 때 쓰거나 `/skill-name`으로 직접 부를 수 있다 (출처 [1])
- [사실] 만들 때: 같은 지침·체크리스트·여러 단계 절차를 채팅에 계속 붙여 넣을 때, 또는 CLAUDE.md의 한 부분이 "사실이 아니라 절차"로 커졌을 때 (출처 [1]). 공식 '설정 키워가기' 표에도 "같은 프롬프트로 작업을 계속 시작한다 → 사용자가 부르는 스킬로 저장", "같은 절차를 세 번째 붙여 넣는다 → 스킬로"가 있다 (출처 [2])
- [사실] 스킬은 두 종류로 볼 수 있다: 참고형(reference, 예: API 스타일 가이드처럼 작업 중 계속 적용할 지식)과 실행형(action/task, 예: `/deploy`처럼 특정 작업 절차) (출처 [1][2])
- [사실] 공식 비교 기준(출처 [2]):

| 비교 | 핵심 차이 |
| :--- | :--- |
| CLAUDE.md vs 스킬 | CLAUDE.md는 매 세션 자동으로 전부 로드, "항상 X 하라" 규칙용. 스킬은 필요할 때 로드, 참고 자료와 `/이름`으로 부르는 작업용. CLAUDE.md는 작업을 실행시킬 수 없고 스킬은 `/<name>`으로 가능 |
| 훅 vs 스킬 | 훅은 생명주기 이벤트에서 Claude 판단 없이 실행(결정적), 컨텍스트 비용 0. 스킬은 Claude가 읽고 해석해 따르는 지침이라 결과가 달라질 수 있음. "꼭 지켜야 할 규칙은 훅으로" |
| 서브에이전트 vs 스킬 | 스킬은 어느 컨텍스트에든 불러오는 재사용 내용(메인 창에 더해짐). 서브에이전트는 별도 컨텍스트에서 일하고 요약만 돌려주는 일꾼. 둘은 결합 가능: 서브에이전트가 `skills:` 필드로 스킬을 미리 싣고, 스킬은 `context: fork`로 서브에이전트에서 실행 |
| MCP vs 스킬 | MCP는 외부 서비스 연결(도구·데이터). 스킬은 그 도구를 잘 쓰는 법(지식·절차)을 알려 줌 |
| 커스텀 명령 vs 스킬 | "Custom commands have been merged into skills." `.claude/commands/deploy.md`와 `.claude/skills/deploy/SKILL.md`는 둘 다 `/deploy`를 만들고 똑같이 동작 (출처 [1]) |

- [사실] 공식 모범사례 문서는 지시를 "비결정적(Claude가 판단)"과 "결정적(Claude Code가 강제)"으로 나누고, "Claude가 스스로 고르는 스킬"은 앞쪽, "나만 시작할 수 있는 스킬"은 뒤쪽에 둔다 (출처 [7])
- [사실] Anthropic 블로그(2026-06-18)도 "이름과 설명만 세션 시작 때 로드되고 본문은 호출 때 로드", "단계를 메인 대화 안에서 보고 조정하고 싶으면 서브에이전트보다 스킬"이라고 쓴다 (출처 [14])
- [사실] Claude Code 스킬은 여러 AI 도구에서 쓰는 개방형 표준 Agent Skills를 따르고, 호출 제어·서브에이전트 실행·동적 컨텍스트 주입을 덧붙였다 (출처 [1]). 이 표준은 2025년 10월 기능 출시, 2025년 12월 개방형 표준 공개, 2026-10-22 Linux Foundation 산하 Agentic AI Foundation에 기증되었다 (출처 [13])
- 신뢰도: 높음 (같은 발행처의 문서 4곳 일치)

### Q2. 스킬 파일은 어디에, 어떤 구조로 두는가? 프론트매터 필드와 이름 규칙은?

**위치** (출처 [1])

| 위치 | 경로 | 적용 범위 |
| :--- | :--- | :--- |
| 개인 | `~/.claude/skills/<스킬이름>/SKILL.md` | 이 컴퓨터의 모든 프로젝트(Cowork·클라우드 세션 제외) |
| 프로젝트 | `.claude/skills/<스킬이름>/SKILL.md` | 이 저장소. 커밋하면 팀과 공유 |
| 중첩 폴더 | `<하위폴더>/.claude/skills/<스킬이름>/SKILL.md` | 그 하위 폴더의 파일을 처음 읽거나 고칠 때 로드 |
| 플러그인 | `<플러그인>/skills/<스킬이름>/SKILL.md` | 플러그인이 켜진 곳, `/플러그인이름:스킬이름`으로 호출 |
| 기업(관리) | 관리 설정 폴더 안 `.claude/skills/` | 배포된 조직 전체 |
| 예전 명령 파일 | `.claude/commands/<이름>.md` | "older format and still works". `name`, `paths`를 뺀 같은 프론트매터 지원 |

- [사실] 이름이 겹치면 기업 > 개인 > 프로젝트 순으로 이긴다. 스킬과 `.claude/commands/` 파일이 같은 이름이면 스킬이 이긴다. 플러그인 스킬은 이름 앞에 플러그인 이름이 붙어 충돌하지 않는다 (출처 [1][2])
- [사실] 파일을 `.claude/skills/name.md`처럼 폴더 없이 두면 `/skills`에 나타나지 않는다. 반드시 `.claude/skills/name/SKILL.md` 폴더 구조여야 한다 (출처 [6])
- [사실] claude.ai 계정으로 로그인한 터미널 세션은 계정의 스킬을 `~/.claude/skills/synced/`로 내려받는다(다운로드만, 업로드 없음). `/skills`에서 `claude.ai sync` 아래에 보인다. 끄려면 사용자 설정에 `"syncClaudeAiSkills": false` (출처 [1][5])

**폴더 구조** (출처 [1][9])

```text
my-skill/
├── SKILL.md      (필수 - 개요와 안내)
├── reference.md  (상세 자료 - 필요할 때 읽음)
├── examples.md   (사용 예시 - 필요할 때 읽음)
└── scripts/
    └── helper.py (실행용 스크립트 - 내용을 읽지 않고 실행)
```

- [사실] `SKILL.md`는 두 부분: `---` 사이의 YAML 프론트매터(언제 쓸지)와 그 아래 마크다운 본문(무엇을 할지) (출처 [1])
- [사실] 보조 파일은 `SKILL.md`에서 링크로 언급해야 Claude가 언제 읽을지 안다. `SKILL.md`는 500줄 이하 권장 (출처 [1][9]). 참조는 `SKILL.md`에서 한 단계까지만 거는 것을 권장한다 (출처 [9])

**프론트매터 필드 (Claude Code 기준, 모두 선택)** (출처 [1])

| 필드 | 뜻 | 기본값 |
| :--- | :--- | :--- |
| `name` | `/` 메뉴에 보이는 명령 이름 | 폴더 이름 |
| `description` | 무엇을 하고 언제 쓰는지. Claude가 이것으로 사용 여부 판단. 없으면 본문 첫 줄 사용 | (권장 필드) |
| `when_to_use` | 호출 상황 보충(트리거 문구, 예시 요청). `description` 뒤에 붙고 합쳐서 1,536자 상한 | 없음 |
| `argument-hint` | 자동 완성 때 보이는 인자 힌트, 예: `[issue-number]` | 없음 |
| `arguments` | `$이름` 치환용 이름 붙은 인자 | 없음 |
| `disable-model-invocation` | `true`면 Claude가 스스로 못 부름(나만 `/이름`으로) | `false` |
| `user-invocable` | `false`면 `/` 메뉴에서 숨김(Claude만 부름) | `true` |
| `allowed-tools` | 스킬을 부른 그 턴 동안 승인 없이 쓸 도구 | 없음 |
| `disallowed-tools` | 스킬이 활성인 동안 도구 목록에서 뺄 도구 | 없음 |
| `model`, `effort` | 그 턴의 모델·노력 수준 바꾸기 | 없음 |
| `context`, `agent`, `background` | `context: fork`면 서브에이전트에서 실행, `agent`로 종류 지정 | 없음 |
| `hooks` | 스킬을 부르면 등록되는 훅 | 없음 |
| `paths` | 이 글롭[^2] 패턴에 맞는 파일을 다룰 때만 자동 로드 | 없음 |
| `shell` | `` !`명령` `` 실행 셸, `bash` 또는 `powershell` | `bash` |
| `metadata`, `license`, `compatibility` | Agent Skills 표준의 정보용 필드 | 없음 |

- [사실] 필드 이름은 표와 정확히 같아야 한다(하이픈 포함). 모르는 필드는 오류 없이 무시된다. YAML이 깨지면 필드 없이 본문만 로드된다 (출처 [1])
- [사실] 이름 규칙(Claude Code): 공식 문서는 "거부하는 문자"만 나열한다. 폭 없는 공백·제어 문자, 사용자 정의 영역 문자(아이콘 글꼴 등), 글자 방향을 바꾸는 문자, 단어 사이 일반 공백 하나 이외의 공백(앞뒤 공백, 연속 공백, 줄바꿈 없는 공백), `<`, `>`. 거부되면 시작 알림이 뜨고 `claude --debug` 로그에서 `[names]`로 찾을 수 있다 (출처 [1])
- [사실] 이름 규칙(플랫폼·표준): Claude 플랫폼 문서는 `name` 최대 64자, 영어 소문자·숫자·하이픈만, XML 태그 금지, `anthropic`·`claude` 예약어 금지, `description` 최대 1,024자, 둘 다 필수라고 쓴다 (출처 [9][10]) → 4절 '상충' 참고
- [사실] 명령 이름: 개인·프로젝트 스킬은 `name`이 있으면 그 이름이 `/` 메뉴에 보이고, 폴더 이름으로도 호출된다. 예: `.claude/skills/deploy-staging/SKILL.md`에 `name: deploy`면 `/deploy`(폴더 이름 `/deploy-staging`도 작동) (출처 [1])
- 신뢰도: 높음 (위치·구조), 이름 규칙은 '상충' 있음

### Q3. 스킬은 어떻게 실행되는가? 자동 호출과 직접 호출, 인자 전달

- [사실] 기본값은 둘 다 가능: 내가 `/skill-name`으로 직접 부르고, Claude도 대화와 관련 있으면 자동으로 불러온다 (출처 [1])
- [사실] Claude는 요청을 스킬 설명과 맞춰 보고 고른다. 설명이 모호하거나 겹치면 엉뚱한 스킬을 쓰거나 놓칠 수 있고, 특정 스킬을 확실히 쓰려면 `/<name>`으로 부르라고 안내한다 (출처 [2])
- [사실] 한쪽만 허용하는 필드 (출처 [1]):

| 프론트매터 | 내가 호출 | Claude가 호출 | 컨텍스트 로드 |
| :--- | :--- | :--- | :--- |
| (기본) | 가능 | 가능 | 설명은 항상, 본문은 호출 때 |
| `disable-model-invocation: true` | 가능 | 스스로는 불가 | 설명도 올라가지 않음, 본문은 호출 때 |
| `user-invocable: false` | 불가 | 가능 | 설명은 항상, 본문은 호출 때 |

- [사실] `disable-model-invocation: true`는 커밋·배포·메시지 전송처럼 부작용이 있거나 시점을 내가 정해야 하는 작업용. Claude가 그래도 부르려 하면 Claude Code가 막고, Claude는 사용자에게 직접 `/deploy`를 실행하라고 제안하게 된다 (출처 [1][7])
- [사실] `user-invocable: false`는 `/` 메뉴에서 숨기고 `/이름`을 쳐도 실행하지 않는다. 하지만 Claude는 여전히 부를 수 있으므로, Claude 호출까지 막으려면 `disable-model-invocation: true`를 써야 한다 (출처 [1])
- [사실] 인자 전달 (출처 [1]):
  - `$ARGUMENTS`: 입력한 인자 전체
  - `$ARGUMENTS[N]` 또는 `$N`: 0부터 세는 위치 인자. 예: `/migrate-component SearchBar JavaScript TypeScript` → `$0`=SearchBar, `$1`=JavaScript, `$2`=TypeScript
  - `$이름`: `arguments:`에 적은 이름 순서대로 대응
  - 본문에 자리표시자가 없으면 Claude Code가 끝에 `ARGUMENTS: <값>`을 붙인다
  - 여러 단어 값은 따옴표: `/my-skill "hello world" second` → `$0`=hello world
  - 그 밖의 치환: `${CLAUDE_SKILL_DIR}`(스킬 폴더 경로), `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_SESSION_ID}` 등
- [사실] 한 메시지에 스킬 여러 개 쌓기: 터미널에서 `/write-tests /fix-issue 123`처럼 첫 스킬과 그 뒤 최대 5개(총 6개)까지 펼친다. `claude -p`나 Agent SDK에서는 첫 스킬만 로드한다 (출처 [1][3])
- [사실] 명령은 메시지 맨 앞에 있어야 인식되고, 뒤의 텍스트가 인자가 된다 (출처 [3])
- [사실] 동적 컨텍스트: 본문에 `` !`명령` ``을 쓰면 Claude에게 보내기 전에 명령을 실행하고 결과로 바꿔 넣는다. 여러 줄은 ` ```! ` 코드 블록. `!`는 줄 맨 앞이나 공백 뒤에 있어야 인식된다. 명령 하나가 실패하면 그 스킬 호출 전체가 중단된다 (출처 [1])
- [사실] `context: fork`를 쓰면 새 서브에이전트가 스킬 내용을 프롬프트로 받아 실행한다. 대화 기록을 보지 못하므로 스킬 지침이 그 자체로 완결돼야 한다 (출처 [1])
- 신뢰도: 높음

### Q4. 처음 만드는 가장 쉬운 방법과 확인 방법

- [사실] 공식 첫 예제 `summarize-changes` (출처 [1]):
  1. `mkdir -p ~/.claude/skills/summarize-changes`
  2. `~/.claude/skills/summarize-changes/SKILL.md`에 아래 내용 저장

     ```markdown
     ---
     description: Summarizes uncommitted changes and flags anything risky. Use when the user asks what changed, wants a commit message, or asks to review their diff.
     ---

     ## Current changes

     !`git diff HEAD`

     ## Instructions

     Summarize the changes above in two or three bullet points, then list any risks you notice such as missing error handling, hardcoded values, or tests that need updating. If the diff is empty, say there are no uncommitted changes.
     ```

  3. git 프로젝트에서 파일 하나를 조금 고친 뒤 `claude` 실행 → "What did I change?"라고 묻거나(자동 호출) `/summarize-changes` 입력(직접 호출). 어느 쪽이든 변경 요약과 위험 목록이 나와야 한다.
- [사실] `name`이 없어도 폴더 이름(`summarize-changes`)이 명령 이름이 된다 (출처 [1])
- [사실] 확인 방법:
  - `/` 입력: 명령 메뉴에 스킬이 보인다 (출처 [1][3])
  - `/skills`: 프로젝트·사용자·플러그인 스킬 목록. 이름·설명·출처로 걸러 보고, `t`로 토큰 수 정렬, `Space`/`Enter`로 보이기 상태 변경, `Esc`로 저장(`.claude/settings.local.json`의 `skillOverrides`에 기록) (출처 [3][6])
  - `/context`: 컨텍스트 사용량. Skills 항목에 번들 스킬[^3]까지 포함된다(`/skills`에는 번들 스킬이 안 나옴) (출처 [6])
  - Claude에게 "What skills are available?"라고 물어 목록에 있는지 확인 (출처 [1])
  - `/skill-doctor`: 스킬별 컨텍스트 비용과 사용 빈도(v2.1.252 이상) (출처 [1][3])
- [사실] 세션 중 `SKILL.md`를 고치면 재시작 없이 반영된다(`~/.claude/skills/`, 프로젝트 `.claude/skills/` 감시). 세션 시작 때 없던 최상위 skills 폴더를 새로 만들었다면 `/reload-skills`를 실행 (출처 [1][3])
- [사실] 그 밖의 시작 경로: `CLAUDE_CODE_NEW_INIT=1`로 `/init`을 실행하면 스킬·훅까지 함께 안내하는 대화형 흐름이 열린다 (출처 [3]). 플랫폼 문서는 "Claude에게 스킬을 만들어 달라고 하면 형식에 맞는 SKILL.md를 생성한다"고 쓴다 (출처 [9])
- [해석] 공식 첫 예제는 bash 명령(`mkdir -p`)과 git 저장소를 전제로 한다. 코딩 경험이 적은 독자나 Windows 사용자에게는 "Claude에게 이 내용으로 파일을 만들어 달라고 요청"하는 경로를 함께 안내하는 편이 쉽다. Windows용 폴더 생성 명령은 공식 스킬 문서에 없다.
- 신뢰도: 높음

### Q5. 안 불릴 때·잘못 불릴 때 점검, description 쓰는 법, 길이·개수 제한, 컨텍스트 로드 방식

**컨텍스트에 올라가는 방식**
- [사실] 처음에는 이름·설명만, 쓸 때 본문 전체: Claude가 스스로 부를 수 있는 스킬은 매 요청마다 이름과 설명이 컨텍스트에 있고, `/이름`으로 부르거나 Claude가 자동으로 불러올 때 본문 전체가 대화에 들어간다. `disable-model-invocation: true` 스킬은 부르기 전까지 아무것도 올라가지 않는다 (출처 [1][2])
- [사실] 플랫폼 문서의 3단계 구조: 1단계 메타데이터(항상, 스킬당 약 100토큰) → 2단계 본문(호출 때, 5,000토큰 미만 권장) → 3단계 보조 파일·스크립트(필요할 때, 스크립트는 출력만 컨텍스트에 들어감) (출처 [10])
- [사실] 한 번 로드된 본문은 이후 턴에도 대화에 남고, Claude Code는 파일을 다시 읽지 않는다. 그래서 "테스트를 실행하라"보다 "편집할 때마다 테스트를 실행하라"처럼 작업 전체에 걸리는 지침으로 쓰라고 권한다 (출처 [1])
- [사실] 자동 압축[^4] 후에는 각 스킬의 가장 최근 호출을 다시 붙이되 스킬당 앞 5,000토큰, 전체 25,000토큰까지. 그래서 중요한 지침은 `SKILL.md` 위쪽에 둔다 (출처 [1])

**길이·개수 제한**
- [사실] 스킬 목록에서 `description`+`when_to_use`는 합쳐서 1,536자에서 잘린다(설정 `skillListingMaxDescChars`, 기본 1536) (출처 [1][5])
- [사실] 스킬 개수 자체의 상한은 문서에 없다. 대신 스킬 목록 전체에 컨텍스트 창의 1%(설정 `skillListingBudgetFraction`, 기본 0.01) 예산이 있다. 넘치면 모든 스킬의 이름은 남기고 가장 덜 쓰는 스킬부터 설명을 뺀다. 설명이 빠진 스킬은 `/이름`으로는 부를 수 있지만 Claude가 스스로 고를 가능성이 낮아진다 (출처 [1][5])
- [사실] 예산 늘리기: `skillListingBudgetFraction`(예: 0.02 = 2%) 또는 환경 변수 `SLASH_COMMAND_TOOL_CHAR_BUDGET`(고정 글자 수). 덜 중요한 스킬은 `skillOverrides`에서 `"name-only"`로 (출처 [1][5])
- [사실] `SKILL.md`는 500줄 이하 권장 (출처 [1][9])

**description 잘 쓰는 법**
- [사실] 무엇을 하는지 + 언제 쓰는지를 함께, 사용자가 실제로 말할 만한 키워드를 넣는다. 핵심 용도를 앞에 둔다(잘리기 때문) (출처 [1][9])
- [사실] 플랫폼 모범사례: 3인칭으로 쓴다(설명은 시스템 프롬프트에 들어가므로 "I can help you…"나 "You can use this…"는 피함). 나쁜 예: "Helps with documents", "Processes data", "Does stuff with files". 좋은 예: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction." (출처 [9])
- [사실] 이름은 동명사형(`processing-pdfs`) 권장, `helper`·`utils`·`tools` 같은 모호한 이름은 피함 (출처 [9])

**안 불릴 때 점검 순서** (출처 [1][6])
1. 설명에 사용자가 자연스럽게 쓸 키워드가 있는지
2. "What skills are available?"에 나오는지, `/skills`에 보이는지
3. 요청을 설명에 더 가깝게 바꿔 보기
4. `/skill-name`으로 직접 불러 보기
5. `/skill-name`도 안 되면 이름이 거부됐는지(위 Q2 이름 규칙)
6. `paths`를 썼다면 다루는 파일이 현재 작업 폴더 안에 있는지
7. `/skills`에 "user-only" 표시가 있으면 `disable-model-invocation: true` 때문

- [사실] YAML이 깨지면 `/skill-name`은 되지만 Claude가 설명과 맞춰 보지 못한다. `--debug`로 파싱 오류 확인, `claude plugin validate .claude/skills`(v2.1.233 이상)로 깨진 프론트매터 찾기 (출처 [1])
- [사실] 너무 자주 불리면: 설명을 더 구체적으로, 또는 `disable-model-invocation: true` (출처 [1])
- [사실] 처음엔 따르다가 나중에 안 따르면: 반드시 지켜야 할 규칙은 훅으로 옮기고(스킬 프론트매터 `hooks`로 스킬에 묶을 수도 있음), 압축 뒤라면 스킬을 다시 부른다 (출처 [1])
- [사실] 문제를 좁히려면 `claude --safe-mode`(스킬·플러그인·훅·CLAUDE.md 등을 끈 채 시작)로 비교 (출처 [6])
- 신뢰도: 높음

### Q6. 보안·주의점

- [사실] 플랫폼 문서: 직접 만들었거나 Anthropic에서 받은 신뢰할 수 있는 스킬만 쓰라. 악성 스킬은 설명과 다른 방식으로 도구를 부르거나 코드를 실행하게 할 수 있고, 데이터 유출·무단 접근으로 이어질 수 있다. `SKILL.md`, 스크립트, 이미지 등 묶인 파일 전부를 검토하고, 외부 URL에서 데이터를 가져오는 스킬은 특히 위험하다. "소프트웨어 설치처럼" 다루라 (출처 [10])
- [사실] `allowed-tools`는 스킬을 부른 그 턴 동안 나열된 도구를 승인 없이 쓰게 해 준다. 다음 메시지를 보내면 사라진다. 도구를 제한하는 기능이 아니다(다른 도구는 그대로 쓸 수 있고 평소 권한 설정을 따름). 거부(deny)·확인(ask) 규칙은 `allowed-tools`보다 우선한다 (출처 [1])
- [사실] 경고: 워크스페이스 신뢰[^5]는 이 필드를 막지 않는다. 한 번도 신뢰하지 않은 폴더의 `-p` 실행에서도 프로젝트 스킬의 `allowed-tools`가 적용된다. "저장소에 들어 있는 스킬의 `allowed-tools`를 Claude Code 실행 전에 검토하라" (출처 [1][4])
- [사실] 제한하는 쪽 도구는 `disallowed-tools`(스킬이 활성인 동안 도구 목록에서 제거) (출처 [1])
- [사실] `` !`명령` `` 주입: 렌더링 중에는 권한을 묻지 않고 권한 규칙과 먼저 대조한다. deny 규칙에 걸리면 `Shell command permission check failed for pattern "..."` 오류로 호출 전체가 중단된다. auto 모드가 아니면 "허용"이 아닌 결과(평소엔 물어볼 명령 포함)도 중단된다. auto 모드에선 중단되지 않는다 (출처 [1])
- [사실] `ls`, `cat`, `git`의 읽기 전용 형태 등은 내장 읽기 전용 명령이라 모든 모드에서 승인 없이 실행된다 (출처 [4]) → 공식 첫 예제의 `git diff HEAD`가 별도 허용 없이 돌아가는 이유로 볼 수 있다 [해석]
- [사실] `"disableSkillShellExecution": true` 설정이면 사용자·프로젝트·플러그인·추가 폴더 스킬의 인라인 셸 명령을 실행하지 않고 `[shell command execution disabled by policy]`로 바꾼다. 번들·관리 스킬은 영향 없음 (출처 [1][5])
- [사실] 스킬 사용 자체 제어: `/permissions`에서 deny 규칙에 `Skill`을 넣으면 모든 스킬 차단. 특정 스킬은 `Skill(commit)`(정확히 일치), `Skill(deploy *)`(접두 일치) 같은 allow·deny 규칙 (출처 [1][4])
- [사실] 남의 저장소에서 `claude -p`를 돌리기 전에는 `--bare`(프로젝트의 훅·스킬·명령·서브에이전트·플러그인·`.mcp.json`을 읽지 않음) 같은 선택지가 있다 (출처 [4])
- [사실] Claude Code에서 스킬은 컴퓨터의 다른 프로그램과 같은 네트워크 접근권을 갖는다. 전역 패키지 설치는 피하라고 권한다 (출처 [10])
- 신뢰도: 높음

### Q7. 예전 '커스텀 슬래시 명령(.claude/commands/)'과의 관계

- [사실] 현재 공식 문서: "Custom commands have been merged into skills." 두 파일 형식 모두 같은 `/이름`을 만들고 똑같이 동작한다. 기존 `.claude/commands/` 파일은 계속 작동한다. 스킬은 보조 파일 폴더, 호출 제어 프론트매터, 관련 있을 때 자동 로드를 더한다. 새 작업에는 스킬을 권장한다 (출처 [1])
- [사실] 공식 변경 이력 v2.1.3: "Merged slash commands and skills, simplifying the mental model with no change in behavior" (출처 [11][12]). GitHub 릴리스 페이지의 표시 날짜는 "09 Jan"(연도 표시 없음) (출처 [12])
- [사실] 스킬 기능 자체는 v2.0.20 "Added support for Claude Skills"에서 처음 들어왔다 (출처 [11]). Anthropic 발표 기준 출시 시점은 2025년 10월 (출처 [13])
- [사실] 예전 문서 주소 `https://code.claude.com/docs/en/slash-commands`를 열면 지금은 스킬 문서("Extend Claude with skills")가 나온다 (출처 [8])
- [사실] 하위 폴더 명령 파일은 네임스페이스 명령이 된다: `.claude/commands/frontend/component.md` → `/frontend:component` (출처 [8])
- [해석] v2.1.3은 2.1.x 초기 버전이고, 스킬이 처음 들어온 v2.0.20은 2025년 10월 무렵이라 "09 Jan"은 2026년 1월 9일로 보인다. 다만 릴리스 페이지에 연도가 없어 직접 확인하지 못했다. 글에는 "2026년 초" 정도로만 쓰는 편이 안전하다.
- 신뢰도: 높음(통합 사실), 날짜는 보통

## 3. 핵심 수치·사실 표

| 항목 | 내용 | 기준일 | 출처 |
| :--- | :--- | :--- | :--- |
| 개인 스킬 위치 | `~/.claude/skills/<이름>/SKILL.md` | 2026-10-28 열람 | [1][10] |
| 프로젝트 스킬 위치 | `.claude/skills/<이름>/SKILL.md` | 2026-10-28 열람 | [1][10] |
| 필수 필드(Claude Code) | 없음. `description`만 권장 | 2026-10-28 열람 | [1] |
| 필수 필드(플랫폼·API) | `name`, `description` | 2026-10-28 열람 | [9][10] |
| `name` 규칙(플랫폼) | 최대 64자, 소문자·숫자·하이픈, `anthropic`·`claude` 금지 | 2026-10-28 열람 | [9][10] |
| `description` 상한(플랫폼) | 1,024자 | 2026-10-28 열람 | [9][10] |
| 설명 목록 상한(Claude Code) | `description`+`when_to_use` 합 1,536자 (`skillListingMaxDescChars`) | 2026-10-28 열람 | [1][5] |
| 스킬 목록 예산 | 컨텍스트 창의 1% (`skillListingBudgetFraction` 기본 0.01) | 2026-10-28 열람 | [1][5] |
| SKILL.md 권장 길이 | 500줄 이하 | 2026-10-28 열람 | [1][9] |
| 메타데이터 비용(플랫폼 설명) | 스킬당 약 100토큰, 본문 5,000토큰 미만 권장 | 2026-10-28 열람 | [10] |
| 압축 후 재부착 | 스킬당 앞 5,000토큰, 전체 25,000토큰 | 2026-10-28 열람 | [1] |
| 한 메시지에 쌓는 스킬 | 첫 스킬 + 최대 5개(터미널), `-p`는 첫 스킬만 | 2026-10-28 열람 | [1][3] |
| 스킬 지원 시작 | v2.0.20 | 변경 이력 | [11] |
| 명령·스킬 통합 | v2.1.3 (릴리스 표시 "09 Jan", 연도 미표시) | 변경 이력 | [11][12] |
| `/skill-doctor` | v2.1.252 이상 | 2026-10-28 열람 | [1][3] |
| `claude plugin validate` | v2.1.233 이상 | 2026-10-28 열람 | [1] |
| Agent Skills 표준 | 2025-10 출시, 2025-12 개방형 표준, 2026-10-22 AAIF 기증 | 2026-10-22 발표 | [13] |
| 표준 채택 현황(Anthropic 발표) | 스킬 100만 개 게시, 설치 약 2억 8천만 회, 70개 넘는 플랫폼 | 2026-10-22 발표 | [13] |

## 4. 상충하거나 불확실한 내용

**상충**
- **필수 필드와 이름 규칙**: Claude Code 문서는 "모든 필드가 선택, `name` 기본값은 폴더 이름, `description`은 권장(없으면 본문 첫 줄)"이라고 쓴다 [1]. Claude 플랫폼 문서와 모범사례는 "`name`·`description` 필수, `name` 64자·소문자·숫자·하이픈만, `description` 1,024자"라고 쓴다 [9][10]. Claude Code 문서는 소문자·64자 규칙을 언급하지 않고 일부 특수 문자만 거부한다. [해석] 둘은 다른 제품(Claude Code vs API·claude.ai)의 규칙이다. 다른 도구로도 옮겨 쓸 수 있게 하려면 더 엄격한 규칙(영어 소문자·하이픈 이름, `name`·`description` 모두 작성)을 따르는 편이 안전하다. 글에서는 "Claude Code에선 선택이지만 둘 다 쓰기를 권장"으로 정리하길 권한다.
- **설명 길이 상한**: Claude Code는 목록 표시 상한 1,536자(설정으로 변경 가능) [1][5], 플랫폼은 `description` 최대 1,024자 [9][10]. 위와 같은 이유로 1,024자 이내가 무난하다 [해석].
- **claude.ai 스킬 동기화**: 플랫폼 개요는 "Custom Skills do not sync across surfaces… Claude Code Skills are filesystem-based and separate from both claude.ai and the API"라고 쓴다 [10]. Claude Code 스킬 문서는 claude.ai 계정으로 로그인한 터미널 세션에서 계정 스킬을 `~/.claude/skills/synced/`로 내려받는다고 쓴다(다운로드만) [1][5]. [해석] Claude Code 문서가 더 구체적이고 관련 설정(`syncClaudeAiSkills`)까지 있으므로 Claude Code 기준으로는 "claude.ai 스킬이 내려받아질 수 있다"가 현재 동작으로 보인다. 글에서 "동기화되지 않는다"고 단정하지 않는다.
- **예전 자료의 `.claude/commands/` 중심 설명**: 인터넷의 오래된 글·영상은 커스텀 슬래시 명령을 `.claude/commands/*.md`로 만드는 별도 기능으로 설명한다. 현재 공식 문서는 "스킬로 통합됨"이며 명령 파일은 "예전 형식"이다 [1][11]. 예전 문서 주소도 지금은 스킬 문서로 연결된다 [8].

**불확실**
- **명령 파일(`.claude/commands/`)의 자동 호출 여부**: 공식 문서는 스킬이 "관련 있을 때 Claude가 자동으로 로드하는 기능을 더한다"고 써서 명령 파일은 자동 호출이 안 되는 것처럼 읽힌다. 반면 같은 문서는 명령 파일이 `name`·`paths`를 뺀 같은 프론트매터를 지원한다고 하고, 변경 이력은 "동작 변화 없음"이라 한다 [1][11]. 실험 6으로 확인이 필요하다.
- **한글 폴더·스킬 이름**: 거부 문자 목록에 한글은 없지만, 한글 이름이 `/` 메뉴에서 제대로 동작하는지는 문서에 명시가 없다. 실험 7로 확인 필요.
- **`` !`date` `` 같은 비-읽기전용 명령**: 읽기 전용 목록은 "포함한다(includes)"라는 표현이라 완전한 목록이 아니다 [4]. Manual 모드에서 `date`가 허용되는지, 중단되는지는 확인하지 못했다(실험 13의 선택 항목).
- **v2.1.3 연도**: 릴리스 페이지에 "09 Jan"만 표시되어 연도를 직접 확인하지 못했다 [12]. 2차 자료 검색 결과 요약에는 2026년 1월로 나오지만 원문을 열지 못했다(7절).
- **스킬 목록 예산 1%의 단위**: "컨텍스트 창의 1%"가 토큰 기준인지 글자 기준인지 문서에서 분명히 확인하지 못했다(환경 변수는 글자 수로 설명) [1][5]. 글에서 "약 몇 자"처럼 환산하지 않는다.
- 이번 조사의 근거는 모두 Anthropic 자료(A등급)다. 독립 매체(B등급) 교차 확인은 접속 제한으로 하지 못했다(7절).

**앞 글(시리즈) 대조**
- 'CLAUDE.md 작성법'(`docs/final/claude-md-hands-on/final.md`)과 '훅 사용법'(`docs/final/claude-code-hooks/final.md`)에는 스킬 언급이 없다. 사실 충돌 없음.
- '핵심 기능 5가지'(`docs/final/claude-code-core-features/final.md`) 셋째 절과 비교:

| 앞 글 문장 | 판정 | 근거·보완 |
| :--- | :--- | :--- |
| "`/`를 입력하면 쓸 수 있는 명령과 스킬 목록이 나옵니다" | 맞음 | [1][3] |
| "스킬은 자주 하는 절차를 `SKILL.md` 파일로 저장해 두는 기능" | 맞지만 좁음 | 절차(실행형)뿐 아니라 참고 지식(참고형)도 스킬이다 [1][2]. 실습편에서 보완 권장 |
| "폴더 이름이 곧 `/이름` 명령이 되고" | 기본값으로 맞음 | `name` 필드로 다른 이름을 줄 수 있고, 그때도 폴더 이름으로 호출된다 [1] |
| "내가 직접 부르거나 클로드가 설명을 보고 필요할 때 불러옵니다" | 맞음 | [1][2] |
| 개인용·프로젝트용 경로 | 맞음 | [1] |
| "옛 방식인 `.claude/commands/` 파일도 계속 작동하지만, 새로 만든다면 스킬 형식이 권장" | 맞음 | [1] |
| "`disable-model-invocation: true`로 내가 부를 때만 실행" | 맞음 | [1] |
| "지금은 스킬로 통합되는 흐름" | 표현이 약간 부정확 | "통합되는 흐름"(진행형)이 아니라 이미 통합됨(v2.1.3, "merged") [1][11]. 실습편에서 "이미 하나로 합쳐졌다"로 바로잡을 수 있다 |
| 표: "반복 절차 저장, 쓸 때만 본문 로드 / 철자가 틀린 필드는 오류 없이 무시됨" | 맞음 | 단, 설명은 매 요청 컨텍스트에 들어간다는 점을 함께 쓰면 정확하다 [1][2] |
| FAQ: "스킬은 내 대화에 불러와 쓰는 재사용 지침서, 서브에이전트는 따로 일하는 일꾼" | 기본으로 맞음 | 스킬도 `context: fork`로 서브에이전트에서 돌릴 수 있다 [1][2] |

## 5. 글쓰기 에이전트에게 (활용 가이드)

**핵심 메시지**
- "같은 부탁을 세 번째 하고 있다면 스킬로 저장할 때." (공식 '설정 키워가기' 표 [2])
- "CLAUDE.md는 매번 읽는 메모, 스킬은 필요할 때 꺼내 보는 설명서, 훅은 무조건 실행되는 규칙." [2][7]
- "스킬의 성패는 `description` 한 줄에 달렸다. 무엇을 하는지 + 언제 쓰는지." [1][9]
- "부작용 있는 스킬은 `disable-model-invocation: true`로 내가 부를 때만." [1][7]
- 시리즈 연결: CLAUDE.md 글 → "CLAUDE.md가 절차로 길어지면 스킬로 옮긴다(공식 권장 200줄 이하)" [1][2]. 훅 글 → "스킬을 자꾸 안 따르는 규칙은 훅으로 옮긴다, 스킬 안에 `hooks`로 묶을 수도 있다" [1].

**FAQ 후보**
- Q. 코딩을 몰라도 만들 수 있나요? → 마크다운 파일 하나면 된다. 스크립트는 선택 [1]. Claude에게 만들어 달라고 해도 된다 [9].
- Q. 만들었는데 자동으로 안 불려요. → 설명에 실제로 쓰는 말을 넣었는지, `/skills`에 보이는지, 폴더 구조(`이름/SKILL.md`)가 맞는지, `disable-model-invocation`이 켜져 있지 않은지 [1][6].
- Q. 예전에 `.claude/commands/`에 만든 명령은요? → 그대로 작동한다. 같은 이름의 스킬을 만들면 스킬이 우선 [1].
- Q. 스킬을 많이 만들면 느려지나요? → 설명은 매 요청 컨텍스트에 들어가고, 목록 예산(컨텍스트 창의 1%)을 넘으면 덜 쓰는 스킬의 설명부터 빠진다. `/skill-doctor`로 안 쓰는 스킬을 찾는다 [1][5].
- Q. 남이 만든 스킬 받아 써도 되나요? → 출처를 믿을 수 있을 때만, 모든 파일(특히 스크립트, `allowed-tools`)을 읽어 본 뒤 [1][10].
- Q. claude.ai에서 만든 스킬도 클로드 코드에서 보이나요? → claude.ai 계정으로 로그인한 터미널 세션은 내려받는다(`~/.claude/skills/synced/`), 끌 수도 있다 [1][5]. (4절 상충 참고)

**장단점 / 비교 포인트**
- 장점: 반복 지시 저장, 쓸 때만 본문 로드로 CLAUDE.md보다 가벼움, 팀 공유(커밋), 인자로 재사용, 다른 AI 도구와 같은 표준 [1][2][13]
- 단점·주의: 자동 호출은 Claude 판단이라 보장 없음, 설명은 매 요청 컨텍스트 차지, 철자 틀린 필드는 조용히 무시, 남의 스킬은 보안 위험, `allowed-tools`는 폴더 신뢰와 무관하게 적용 [1][2][10]

**연관 키워드·표현 후보**: 클로드 코드 스킬, Claude Code Skills, SKILL.md, 스킬 만들기, 슬래시 명령, 커스텀 명령, `.claude/skills`, description 작성법, disable-model-invocation, Agent Skills, 클로드 코드 자동화

**주의**
- "스킬을 만들면 Claude가 항상 쓴다" 같은 단정 금지. 자동 호출은 설명 매칭에 따른 판단이다 [2].
- "스킬은 도구를 제한한다" 금지. `allowed-tools`는 승인 생략이지 제한이 아니다. 제한은 `disallowed-tools` [1].
- `user-invocable: false`를 "숨김·차단"으로 쓰지 않는다. Claude는 여전히 부를 수 있다 [1].
- 이름 규칙은 "Claude Code에선 선택, 플랫폼·표준은 64자 소문자" 차이를 밝힌다(4절).
- 버전 번호, 설정 이름, 수치(1%, 1,536자 등)는 업데이트로 바뀔 수 있으니 "조사일(2026-10-28) 기준"을 붙인다.
- 표준 채택 수치(100만 개, 2억 8천만 회)는 Anthropic 자체 발표 수치다. 쓰려면 출처를 함께 적는다 [13].

**직접 경험으로 보강해야 할 부분** (리서치로 채울 수 없음)
- 실제로 만든 스킬이 자동으로 불렸는지, 몇 번 시도했는지, 화면에 어떻게 보였는지
- `/skills`, `/context` 화면 모습
- 설명을 바꾸기 전후 차이(아래 실험 결과로만)
- Windows에서 폴더를 만든 경험

### 5-1. 입문자 실습 예제 후보 (파일 내용 그대로)

**실습 A. 공식 첫 예제를 한국어로 (개인 스킬, 자동·직접 호출 둘 다)**
- 원문 예제는 Q4에 그대로 있다. 아래는 [해석] 한국어로 옮긴 각색본이다(공식 예제 아님).
- 경로: `~/.claude/skills/summarize-changes/SKILL.md`
- 전제: 커밋이 하나 이상 있는 git 폴더에서 파일 하나를 고친 상태

```markdown
---
description: 아직 커밋하지 않은 변경 사항을 요약하고 위험해 보이는 부분을 짚어 준다. 사용자가 무엇이 바뀌었는지 묻거나, 커밋 메시지를 원하거나, 변경 내용 검토를 부탁할 때 사용한다.
---

## 현재 변경 사항

!`git diff HEAD`

## 지시

위 변경 사항을 두세 개의 글머리표로 요약한다. 그다음 오류 처리 누락, 하드코딩된 값, 고쳐야 할 테스트처럼 눈에 띄는 위험을 나열한다. 변경 사항이 비어 있으면 커밋하지 않은 변경이 없다고 말한다.
```

- 확인: `claude` 실행 → "뭐 바꿨는지 알려 줘"(자동) 또는 `/summarize-changes`(직접)

**실습 B. 내가 부를 때만 + 인자 받기 (프로젝트 스킬)**
- 경로: `.claude/skills/blog-titles/SKILL.md`

```markdown
---
name: blog-titles
description: 주어진 주제로 블로그 글 제목 후보 5개를 만든다.
disable-model-invocation: true
argument-hint: [주제]
---

주제: $ARGUMENTS

위 주제로 블로그 글 제목 후보 5개를 만든다.
- 제목마다 30자 안팎으로 쓴다.
- 주제 핵심어를 제목 앞쪽에 둔다.
- "무조건", "100%" 같은 과장 표현은 쓰지 않는다.
번호 목록으로만 답한다.
```

- 확인: `/blog-titles 클로드 코드 스킬` 입력. `/skills`에서 user-only 표시 확인. "블로그 제목 지어 줘"라고만 하면 이 스킬이 쓰이지 않아야 한다(Claude가 스킬 없이 직접 답할 수는 있음).
- 위치 인자 버전(선택): `.claude/skills/compare/SKILL.md`

```markdown
---
name: compare
description: 두 가지를 장단점 표로 비교한다.
disable-model-invocation: true
argument-hint: [A] [B]
---

$0 와 $1 을 비교한다.
장점, 단점, 어울리는 사람을 열로 둔 표 하나로 정리한다.
```

- 확인: `/compare 노션 옵시디언`, 그리고 `/compare "구글 문서" 노션`(따옴표로 묶은 두 단어가 `$0` 하나로 들어가는지)

**실습 C. 참고형 스킬 + 보조 파일 (Claude가 알아서 꺼내 쓰는 설명서)**
- 경로: `.claude/skills/blog-style/SKILL.md`

```markdown
---
name: blog-style
description: 이 블로그의 말투와 서식 규칙. 블로그 글 초안을 쓰거나 고칠 때, 또는 사용자가 말투나 문체, 서식을 맞춰 달라고 할 때 사용한다.
---

# 블로그 말투 규칙

- 존댓말(~습니다, ~요)로 쓴다.
- 한 문단은 3줄을 넘기지 않는다.
- 이모지는 쓰지 않는다.
- "무조건", "절대" 같은 단정 대신 근거를 붙인다.

좋은 문장과 고칠 문장 예시는 [examples.md](examples.md)를 읽는다.
```

- 경로: `.claude/skills/blog-style/examples.md`

```markdown
# 예시

- 좋음: 처음에는 CLAUDE.md 하나만 만들어도 충분합니다.
- 고칠 것: 이거 무조건 해야 함!!
- 좋음: 공식 문서는 SKILL.md를 500줄 이하로 쓰라고 권합니다.
```

- 확인: "클로드 코드 소개 글 첫 문단 써 줘"처럼 요청 → 스킬이 쓰였는지, `examples.md`까지 읽었는지 관찰

### 5-2. 실험으로 확인해 볼 포인트 (메인 에이전트가 Claude Code로 실행)

**공통 준비**
- 이 저장소가 아닌 빈 실험 폴더에서 한다(프로젝트 스킬이 커밋되지 않게). 예: 새 폴더에서 `git init` 후 파일 하나 커밋.
- 프로젝트 스킬(`.claude/skills/`)을 쓰면 개인 설정(`~/.claude`)을 더럽히지 않는다.
- 자동 호출은 Claude의 판단이라 매번 같지 않을 수 있다. 같은 프롬프트로 3회 이상 반복해 비율로 기록한다.
- 스킬이 쓰였는지 눈으로 알 수 있게 본문에 표시 문구(마커)를 넣는다. 맞춤법 교정은 Claude가 스킬 없이도 하므로, 마커가 있어야 구분된다.
- `--bare`, `--safe-mode`로 시작하면 스킬이 로드되지 않으니 쓰지 않는다 [4][6].
- `claude -p`에서도 메시지 맨 앞 `/스킬이름`은 동작한다(첫 스킬만) [1]. `/skills`·`/context` 같은 화면은 대화형 세션이 필요할 수 있다. 대화형이 어렵다면 "What skills are available?"(또는 "사용할 수 있는 스킬 목록 알려 줘")로 대신 확인한다 [1].
- 권한 모드에 따라 `!` 명령 처리가 다르다(auto 모드가 아니면 허용되지 않은 명령은 호출 중단) [1]. 실험마다 모드를 기록한다.
- 실험 시작 전에 `claude --version`을 기록한다.

**기본 스킬 (실험 1의 구체적 설명 버전)**
- 경로: `.claude/skills/proofread-ko/SKILL.md`

```markdown
---
name: proofread-ko
description: 한국어 문장의 맞춤법과 띄어쓰기를 고치고, 바뀐 곳을 표로 보여 준다. 사용자가 맞춤법 검사, 띄어쓰기 확인, 오타 교정, 문장 다듬기를 부탁할 때 사용한다.
---

답변 첫 줄에 반드시 `[proofread-ko 스킬 사용]`이라고 쓴다.

1. 사용자가 준 문장의 맞춤법과 띄어쓰기를 고친다.
2. 고친 문장 전체를 먼저 보여 준다.
3. 바뀐 곳만 "원래 | 고친 것 | 이유" 표로 정리한다.
4. 고칠 곳이 없으면 "고칠 곳이 없습니다"라고만 쓴다.
```

- 자동 호출 프롬프트: `다음 문장 맞춤법 좀 봐 줘: 오늘은 날씨가 않좋아서 집에 있었읍니다.`
- 엉뚱한 호출 확인용 프롬프트: `파이썬에서 리스트를 정렬하는 법 알려 줘.`(마커가 나오면 과잉 호출)

**핵심 실험 1~5**

| 번호 | 실험 | 바꿀 내용 | 기대(문서 기준) | 근거 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 구체적 설명 → 자동 호출 | 위 기본 스킬 그대로 | 맞춤법 프롬프트에서 마커가 나옴, 파이썬 질문에선 안 나옴 | [1][2] |
| 2 | 모호한 설명 → 자동 호출 안 됨? | `description: 문서 관련 작업을 돕는다.`로 교체(본문 동일) | 자동 호출 비율이 1번보다 낮아짐(보장 아님) | [2][9] |
| 3 | 모호해도 직접 호출은 됨 | 2번 상태에서 `/proofread-ko 오늘은 날씨가 않좋아서 집에 있었읍니다.` | 마커와 교정 결과가 나옴 | [1][2] |
| 4 | 자동 호출 끄기 | 1번 프론트매터에 `disable-model-invocation: true` 한 줄 추가 | 자동 프롬프트에선 마커 없음, `/proofread-ko …`는 작동, `/skills`에 user-only 표시 | [1][6] |
| 5 | 필드 철자 오류 | 4번의 줄을 `disable_model_invocation: true`(밑줄)로 바꿈 | 오류 없이 무시되어 자동 호출이 다시 일어남 | [1] |

**추가 실험 6~13 (선택)**

실험 6. 예전 명령 파일과 우선순위
- `.claude/commands/hello-cmd.md`

```markdown
---
description: 짧은 환영 인사말을 만든다. 사용자가 인사말이나 환영 문구를 부탁할 때 사용한다.
---

답변 첫 줄에 `[hello-cmd 명령 파일 사용]`이라고 쓰고, 환영 인사 한 문장을 만든다.
```

- 확인 1: `/hello-cmd`가 작동하는지 [1]
- 확인 2: "환영 인사 한 줄 써 줘"에서 명령 파일이 자동으로 쓰이는지(4절 '불확실' 항목)
- 확인 3: 같은 이름 스킬 `.claude/skills/hello-cmd/SKILL.md`를 추가

```markdown
---
description: 짧은 환영 인사말을 만든다. 사용자가 인사말이나 환영 문구를 부탁할 때 사용한다.
---

답변 첫 줄에 `[hello-cmd 스킬 사용]`이라고 쓰고, 환영 인사 한 문장을 만든다.
```

  → `/hello-cmd`에서 스킬 쪽 마커가 나와야 함("스킬이 이긴다") [1]

실험 7. 한글 폴더 이름
- `.claude/skills/맞춤법/SKILL.md`에 기본 스킬 내용을 넣되 `name:` 줄을 지운다 → `/맞춤법 …`이 작동하는지, `/` 메뉴에 어떻게 보이는지(문서에 명시 없음)

실험 8. Claude만 부르는 스킬
- 기본 스킬 프론트매터에 `user-invocable: false` 추가 → `/` 메뉴에서 사라지고 `/proofread-ko …`를 쳐도 실행되지 않는지, 자동 프롬프트에서는 여전히 마커가 나오는지 [1]

실험 9. YAML이 깨질 때
- 기본 스킬의 프론트매터를 따옴표 없이 콜론+공백이 들어가게 바꾼다:

```markdown
---
name: proofread-ko
description: 맞춤법 검사: 띄어쓰기와 오타를 고친다. 사용자가 맞춤법 검사를 부탁할 때 사용한다.
---
```

- 기대: YAML 파싱 실패 → 필드 없이 본문만 로드, `/proofread-ko`는 작동하지만 자동 호출은 설명 매칭이 안 됨. `claude --debug`로 파싱 오류, `claude plugin validate .claude/skills`로 탐지(v2.1.233 이상) [1]
- 참고: 이 저장소 CLAUDE.md에도 "값에 `: `가 들어가면 YAML 파싱이 깨진다"는 규칙이 있어 실습 팁으로 연결하기 좋다.

실험 10. 잘못된 위치
- `.claude/skills/proofread-ko.md`(폴더 없이 파일만) → `/skills`에 안 보여야 함 [6]

실험 11. 인자 자리표시자가 없을 때
- `.claude/skills/echo-args/SKILL.md`

```markdown
---
name: echo-args
description: 인자 전달을 확인하는 실험용 스킬.
disable-model-invocation: true
---

이 지시 아래에 덧붙은 내용을 한 글자도 바꾸지 말고 그대로 다시 보여 준다.
```

- `/echo-args 사과 바나나` → 끝에 `ARGUMENTS: 사과 바나나`가 붙어 전달되는지 [1]

실험 12. 세션 중 수정 반영(핫 리로드)
- 대화형 세션을 연 채로 기본 스킬의 마커를 `[proofread-ko 스킬 v2]`로 바꾸고 다시 호출 → 재시작 없이 바뀌는지 [1]
- 세션 시작 때 `.claude/skills/` 폴더가 없었다면 새로 만든 뒤 `/reload-skills`가 필요한지 [1][3]

실험 13. `!` 명령 실패와 권한
- 실습 A 스킬을 커밋이 하나도 없는 새 git 폴더(또는 git이 아닌 폴더)에서 `/summarize-changes`로 호출 → `git diff HEAD`가 실패하면 "호출 전체 중단"이 되는지 [1]
- (선택) 아래 스킬을 Manual(default) 모드와 auto 모드에서 각각 호출해, 읽기 전용 목록에 명시되지 않은 `date`가 중단되는지 비교 [1][4]

```markdown
---
name: today
description: 오늘 날짜를 알려 주는 실험용 스킬.
disable-model-invocation: true
---

오늘 날짜: !`date`

위 날짜를 "오늘은 OOOO년 O월 O일입니다" 형식으로 한 줄로만 답한다.
```

## 6. 참고 출처

| 번호 | 제목 | 발행처 | 발행·수정일 | 등급 | URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [1] | Extend Claude with skills (스킬 문서) | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/skills |
| [2] | Extend Claude Code (기능 비교) | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/features-overview |
| [3] | Commands (명령 레퍼런스) | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/commands |
| [4] | Configure permissions | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/permissions |
| [5] | Settings reference (200,000~300,000자 구간) | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/settings-reference |
| [6] | Debug your configuration | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/debug-your-config |
| [7] | Best practices for Claude Code | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/best-practices |
| [8] | 예전 slash-commands 주소(현재 스킬 문서 표시) | Anthropic, Claude Code Docs | 2026-10-28 열람 | A | https://code.claude.com/docs/en/slash-commands |
| [9] | Skill authoring best practices | Anthropic, Claude Platform Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices |
| [10] | Agent Skills (개요) | Anthropic, Claude Platform Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| [11] | Claude Code CHANGELOG.md | Anthropic (GitHub) | 맨 위 2.1.312 (2026-10-28 열람) | A | https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md |
| [12] | Release v2.1.3 | Anthropic (GitHub) | "09 Jan"(연도 미표시) | A | https://github.com/anthropics/claude-code/releases/tag/v2.1.3 |
| [13] | Donating Agent Skills to the Agentic AI Foundation | Anthropic News | 2026-10-22 | A | https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation |
| [14] | Steering Claude Code: when to use CLAUDE.md, skills, hooks, and subagents | Claude 블로그(Michael Segner, Anthropic) | 2026-06-18 | A | https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more |

- 모든 출처가 Anthropic 자료다. 핵심 사실(위치, 호출 제어 필드, 명령 통합, 컨텍스트 로드 방식)은 서로 다른 문서 2곳 이상에서 일치했다. 독립 매체 교차 확인은 하지 못했다.
- 내부 문서(웹 출처 아님): `docs/final/claude-code-core-features/final.md`, `docs/final/claude-md-hands-on/final.md`, `docs/final/claude-code-hooks/final.md`, `docs/research/claude-code-core-features.md`

## 7. 확인하지 못한 자료

- agentskills.io(표준 명세), simonwillison.net, batsov.com: 이 세션의 네트워크 허용 목록 밖이라 접속 실패(DNS 확인 불가). 표준 명세의 `name` 규칙은 플랫폼 문서 [9][10]로 대신 확인했다. 열어 보려면 세션 네트워크 설정에서 해당 도메인 허용이 필요하다.
- 명령·스킬 통합 날짜(2026년 1월)를 다룬 2차 자료(devgenius, towardsai(회원 전용), youmind 등)와 Agent Skills 기증 관련 언론 기사(the-decoder, VentureBeat, Linux Foundation 보도자료)는 검색 결과로만 보고 열지 않아 근거로 쓰지 않았다.
- 국내 블로그·강의 자료(디지털마케터, 브런치, 위키독스 등)는 검색 결과로만 봤다. 검색 요약상 "name과 description이 기본 요소"처럼 플랫폼 규칙을 옮긴 설명이 있을 수 있어 4절 상충과 같은 문제가 있을 수 있다.
- GitHub API(릴리스 연도 확인)는 403으로 실패했다.
- 설정 레퍼런스는 약 442,000자라 스킬 관련 항목이 있는 구간(200,000~300,000자)만 읽었다.
- Windows에서의 폴더 생성·한글 경로 동작은 확인하지 못했다.

## 용어 설명

[^1]: 프론트매터(frontmatter): 파일 맨 위 `---`와 `---` 사이에 적는 설정 정보. 이름, 설명 같은 항목을 `항목: 값` 형식(YAML)으로 쓴다.
[^2]: 글롭(glob): `src/**/*.ts`처럼 별표로 여러 파일 경로를 한 번에 가리키는 패턴.
[^3]: 번들 스킬: 클로드 코드에 처음부터 들어 있는 스킬. 예: `/doctor`, `/code-review`, `/batch`, `/debug`, `/loop`, `/simplify`, `/verify`.
[^4]: 자동 압축(compaction): 대화가 길어져 컨텍스트 창이 차기 전에 지난 대화를 요약해 공간을 비우는 기능.
[^5]: 워크스페이스 신뢰(workspace trust): 처음 여는 폴더에서 "이 폴더를 믿겠습니까?"를 묻는 절차. 믿기 전에는 일부 설정을 적용하지 않는다.

- 컨텍스트 창(context window): Claude가 한 번에 보고 기억하는 대화·파일 분량. 스킬 설명도 여기를 차지한다.
- 토큰: AI가 글을 세는 단위. 대략 글자 몇 개 묶음이라고 보면 된다.
- 서브에이전트: 메인 대화와 따로 일하고 요약만 돌려주는 보조 AI.
- 훅(hook): 정해진 순간(파일 수정 전후 등)에 Claude 판단과 상관없이 반드시 실행되는 자동 명령.
- `claude -p`(비대화형 모드): 질문 하나를 넣고 답만 받아 끝나는 실행 방식. 스크립트에서 쓴다.
- 프롬프트 인젝션: 문서나 웹페이지에 숨긴 지시로 AI를 속이는 공격. 외부 데이터를 가져오는 스킬이 위험한 이유.
- 플러그인: 스킬·훅·서브에이전트·MCP 서버를 한 묶음으로 설치·배포하는 단위.

# 리서치 노트: 클로드 코드(Claude Code) 서브에이전트(Subagents) 사용법

- 조사일: 2026-10-28
- 기준 시점: 2026-10-28에 직접 연 공식 문서. 변경 이력상 최신 버전은 v2.1.312(2026-10-27) [14]. 공식 문서 페이지에는 수정일 표기가 없어 "열람일 기준"으로 적는다.
- 목적/독자: 네이버 블로그 정보형 글(시리즈 6편, 실습편)의 근거 자료. 독자는 코딩 경험이 적은 클로드 코드 입문자.
- 읽은 범위: 서브에이전트 문서 [1]은 원문 116,045자 전체를 앞 100,000자(질문별로 여러 번 조회)와 뒤 16,045자(offset 조회)로 나눠 확인했다. 열람 도구가 원문을 요약해 돌려주는 방식이라, 핵심 필드 이름·문장은 "원문 그대로 인용"을 따로 요청해 확인했다.

## 1. 결론 요약

- [사실] 서브에이전트는 자기 컨텍스트 창[^1]에서 따로 일하고 **최종 보고만** 메인 대화로 돌려주는 보조 AI다. 만드는 법은 `.claude/agents/`(프로젝트) 또는 `~/.claude/agents/`(개인)에 마크다운 파일 한 장(프론트매터[^2] + 본문)을 두는 것이고, 필수 필드는 `name`, `description` 두 개뿐이다 [1][6].
- [사실] 2026-10 기준으로 입문 자료와 달라진 점이 셋 있다. ① `/agents`는 더 이상 만들기 화면을 열지 않고 "Claude에게 부탁하거나 파일을 직접 고치라"는 안내만 출력한다(v2.1.197 이하만 화면) [1][11]. ② Claude가 띄운 서브에이전트는 기본으로 **백그라운드**[^3]에서 돈다 [1][4]. ③ **포크(fork)**[^4] 모드가 기본으로 켜져 있어, Claude가 대화 기록을 통째로 물려받는 포크를 스스로 띄울 수 있다(터미널 v2.1.232, `claude -p`·SDK·데스크톱·VS Code는 v2.1.302부터) [1][14].
- [사실] 일반(포크가 아닌) 서브에이전트는 메인 대화 기록·이미 읽은 파일·이미 부른 스킬을 모른다. CLAUDE.md와 git 상태는 읽지만, 내장 Explore·Plan은 이것도 읽지 않는다 [1][2][6].
- [사실] 비용은 "공짜 분업"이 아니다. 서브에이전트도 자기 요청을 보내고 같은 사용량 한도에 합산되며, 같은 일을 맡긴다고 답이 더 좋아지지는 않는다. 장점은 병렬 처리, 긴 출력 격리, 쓴 사람이 아닌 리뷰어, 도구 제한이다 [1][4][5].
- [해석] 입문자 글의 뼈대는 "언제 쓰나(설정 키워가기 표) → 내장 3종 → 파일 한 장으로 만들기 → 부르는 법(@멘션) → 도구 제한으로 읽기 전용 만들기 → 주의점"이 적절하다. 앞 글들의 서브에이전트 설명은 대체로 맞지만, 미발행 원고의 "중첩하려면 `tools`에 `Agent`가 있어야 한다"는 문장은 현재 문서와 어긋난다(4절).

## 2. 질문별 조사 결과

### Q1. 서브에이전트란 무엇이고 메인 대화와 무엇이 다른가? 스킬·훅·CLAUDE.md와는? 언제 쓰나?

- [사실] 정의: "특정 유형의 작업을 맡는 전문 AI 보조". 다시 볼 일 없는 검색 결과·로그·파일 내용으로 메인 대화가 넘칠 때 쓰며, 서브에이전트가 자기 컨텍스트에서 일하고 **요약만** 돌려준다. 같은 지침의 일꾼을 반복해서 띄운다면 커스텀 서브에이전트로 정의하라고 권한다 (출처 [1])
- [사실] 각 서브에이전트는 자기 컨텍스트 창, 자기 시스템 프롬프트[^5], 지정된 도구, 독립된 권한으로 돈다. 서브에이전트의 본문(지침)은 부모 대화에 들어가지 않고, 부모에게 돌아오는 것은 최종 메시지와 메타데이터뿐이다 (출처 [1], [15])
- [사실] 서브에이전트의 시스템 프롬프트는 파일 본문 + 기본 환경 정보(작업 폴더 등)뿐이고, 클로드 코드의 기본 시스템 프롬프트는 받지 않는다 (출처 [1], [2])
- [사실] 메인 대화가 나은 경우: 주고받기가 잦은 일, 여러 단계가 맥락을 많이 공유하는 일, 빠르고 작은 수정, 지연이 중요한 일(새 서브에이전트는 맥락을 다시 모아야 해서 느릴 수 있음). 서브에이전트가 나은 경우: 메인에 남길 필요 없는 긴 출력, 도구·권한 제한이 필요한 일, 혼자 끝내고 요약으로 돌려줄 수 있는 일 (출처 [1])
- [사실] 이미 대화에 있는 내용에 대한 곁가지 질문은 서브에이전트가 아니라 `/btw`를 쓰라고 안내한다. `/btw`는 전체 대화를 보지만 도구가 없고, 서브에이전트는 도구가 있지만 받은 프롬프트에서 시작한다 (출처 [1], [12])
- [사실] 공식 비교(기능 개요 페이지) (출처 [2])

  | 구분 | 하는 일 | 언제 쓰나 |
  | :--- | :--- | :--- |
  | CLAUDE.md | 매 대화 자동으로 읽히는 지속 맥락 | 프로젝트 규칙, "항상 X 해라" |
  | 스킬 | 필요할 때 불러오는 지침·지식·절차 | 재사용 절차, 참고 자료 |
  | 서브에이전트 | 격리된 실행 맥락, 요약된 결과만 반환 | 맥락 격리, 병렬 작업, 전문 일꾼 |
  | 훅 | 이벤트마다 스크립트 등 실행 | 매번 반드시 일어나야 하는 자동화 |

- [사실] 스킬 vs 서브에이전트: 스킬은 "어느 맥락에든 불러오는 재사용 내용"(메인 창에 더해짐), 서브에이전트는 "메인 대화와 따로 도는 격리된 일꾼"(별도 창, 자기 입력·출력 토큰). 둘은 결합 가능(Q7) (출처 [2])
- [사실] Claude 블로그(2026-06-18)는 "중간 결과로 메인을 어지럽히는 곁일"은 서브에이전트, "단계를 메인에서 보고 조정하고 싶은 절차"는 스킬로 나눈다 (출처 [15])
- [사실] 공식 '설정 키워가기(Build your setup over time)' 표: 처음부터 다 설정할 필요 없고, 신호가 올 때 하나씩 더한다. 서브에이전트 줄은 "곁일이 다시 안 볼 출력으로 대화를 넘치게 할 때 → 서브에이전트로 보낸다" (출처 [2])

  | 신호 | 추가할 것 |
  | :--- | :--- |
  | 같은 규칙·명령을 Claude가 두 번 틀림 | CLAUDE.md |
  | 같은 프롬프트로 일을 시작하는 게 반복됨 | 사용자가 부르는 스킬 |
  | 같은 절차를 세 번째 붙여 넣음 | 스킬 |
  | 곁일이 다시 안 볼 출력으로 대화를 넘치게 함 | 서브에이전트 |
  | 묻지 않아도 매번 일어나야 함 | 훅 |
  | 두 번째 저장소에도 같은 설정이 필요함 | 플러그인 |

  (표의 나머지 줄: 출력 스타일, MCP, 코드 인텔리전스 플러그인. 원문 [2] 참고)
- [사실] 모범 사례 문서는 서브에이전트가 이득인 상황을 넷으로 꼽는다: 독립 작업 동시 실행, 긴 출력(전체 테스트 실행·넓은 검색)을 메인 밖에 두기, 코드를 쓴 과정을 보지 않은 리뷰어, 메인보다 적은 도구 주기 (출처 [4])
- [사실] 같은 문서의 '이제 그만둬도 되는 옛 조언' 표: "컨텍스트 창을 지키려고 서브에이전트를 쓴다"는 1M 토큰 창 시대라 덜 중요해졌고, "더 좋은 답을 위해 서브에이전트에 맡긴다"는 틀린 기대라고 정리한다(새 리뷰어가 도움이 되는 건 '내 추론을 안 봤기 때문'이지 위임 자체 때문이 아님) (출처 [4])
- [해석] 입문자용 한 줄 정리: "CLAUDE.md는 늘 읽는 메모, 스킬은 꺼내 보는 설명서, 훅은 자동 장치, 서브에이전트는 따로 일하고 보고서만 내는 일꾼." 다만 '컨텍스트 절약'만 내세우기보다 '병렬·격리·독립 리뷰·도구 제한' 네 가지로 소개하는 편이 최신 공식 관점과 맞다.
- 신뢰도: 높음 (A등급 공식 문서 4종 일치)

### Q2. 기본 제공(내장) 서브에이전트 종류와 하는 일, CLAUDE.md를 읽는지

- [사실] 내장 서브에이전트는 Claude가 적절할 때 자동으로 쓴다. 각자 **부모 대화의 권한 규칙을 물려받고**, 대부분 제한된 도구로 돈다 (출처 [1])

  | 이름 | 모델 | 도구 | 하는 일 | CLAUDE.md·git 상태 |
  | :--- | :--- | :--- | :--- | :--- |
  | Explore | 메인 대화 모델(메인이 Fable이면 구독·Console 연결에서는 `opus` 별칭 모델) | 읽기 전용(Write·Edit 거부) | 파일 찾기, 코드 검색, 코드베이스 탐색. 호출 때 quick / medium / very thorough 중 철저함 수준 지정 | 읽지 않음 |
  | Plan | 메인 대화 모델 상속 | 읽기 전용(Write·Edit 거부) | 플랜 모드에서 계획 전 조사 | 읽지 않음 |
  | general-purpose | `CLAUDE_CODE_SUBAGENT_MODEL` 설정 시 그 모델, 아니면 메인 모델 | 서브에이전트가 쓸 수 있는 모든 도구 | 탐색과 수정이 함께 필요한 복잡한 다단계 작업 | 읽음 |
  | claude | 자체 모델 없음(모델 결정 순서를 따름) | 모든 도구 | 전문 에이전트에 맞지 않는 일의 만능 담당, 백그라운드 세션의 기본 에이전트 | 읽음 |
  | statusline-setup | Sonnet | (명시 없음) | `/statusline` 실행 때 | 읽음 |
  | claude-code-guide | Haiku | (명시 없음) | 클로드 코드 기능 질문에 답할 때 | 읽음 |

  (출처 [1])
- [사실] "Explore와 Plan은 조사를 빠르고 싸게 하려고 CLAUDE.md와 git 상태 스냅샷 없이 시작한다. 다른 내장·커스텀 서브에이전트는 둘 다 읽는다(커스텀에서 `omitClaudeMd`를 켜면 제외)" (출처 [1], [2])
- [사실] 모범 사례 문서: 넓은 코드베이스 검색은 내장 Explore로 가고, 곁일은 포크로, 띄운 서브에이전트는 기본 백그라운드로 돈다. "대부분 따로 요청할 필요가 없다" (출처 [4])
- [사실] SDK 문서: Agent 도구[^6] 호출에 `subagent_type`이 없으면 general-purpose가 쓰인다. 정의를 하나도 안 만들어도 Claude는 general-purpose를 쓸 수 있다 (출처 [6], [7])
- [사실] 같은 이름 `Explore`로 사용자·프로젝트 서브에이전트를 만들면 내장을 덮어쓴다. 예를 들어 `model: haiku`로 만들면 탐색을 싼 모델로 돌릴 수 있다 (출처 [1])
- [사실] 끄는 법: `permissions.deny`에 `Agent(Explore)` 같은 규칙, 또는 `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1`(v2.1.198+, Explore·Plan만 제거) (출처 [1], [7], [10])
- [사실] Explore와 Plan은 일회성이라 이어서 재개(resume)할 수 없다 (출처 [1], [6])
- [해석] 입문자에게 "내장 에이전트가 CLAUDE.md를 안 읽는다"는 점은 실수로 이어지기 쉽다. 예: "vendor 폴더는 무시"를 CLAUDE.md에만 적었다면 Explore는 그 규칙을 모른다. 문서도 꼭 전해야 할 규칙은 위임할 때 프롬프트에 다시 적으라고 한다 [1].
- 신뢰도: 높음 (공식 [1][2][4][6][7] 일치. 단 statusline-setup·claude-code-guide의 도구는 문서에 없음)

### Q3. 직접 만드는 법: 위치·우선순위, 파일 형식, `/agents`, Claude에게 부탁하기

**저장 위치와 우선순위** (출처 [1], [2])

| 우선순위 | 위치 | 범위 |
| :--- | :--- | :--- |
| 1(가장 높음) | 관리형 설정(Managed settings) | 조직 전체 |
| 2 | `--agents` CLI 플래그(JSON) | 그 세션만, 디스크에 저장 안 됨 |
| 3 | `.claude/agents/` | 현재 프로젝트 |
| 4 | `~/.claude/agents/` | 내 모든 프로젝트 |
| 5(가장 낮음) | 플러그인의 `agents/` | 플러그인을 켠 곳 |

- [사실] 같은 `name`이 여러 곳에 있으면 우선순위가 높은 쪽이 이긴다. 기능 개요 페이지도 "관리형 > CLI 플래그 > 프로젝트 > 사용자 > 플러그인"으로 같다 (출처 [1], [2])
- [사실] 하위 폴더까지 재귀로 읽는다(`agents/review/` 등 허용). 식별은 프론트매터의 `name`으로만 하고 파일 이름·폴더 경로는 상관없다. 한 폴더 트리 안에 같은 이름이 둘이면 파일 시스템 읽기 순서로 하나만 로드되며, `/doctor`가 중복을 알려 준다 (출처 [1])
- [사실] SDK에서 코드로 정의한 에이전트는 같은 이름의 파일 정의보다 우선한다 (출처 [6])

**파일 형식** (출처 [1], [6])

- [사실] YAML 프론트매터 + 마크다운 본문. **본문이 서브에이전트의 시스템 프롬프트**가 된다. CLI `--agents` JSON에서는 `prompt` 필드가 본문과 같은 역할이다 (출처 [1], [8])
- [사실] 필수는 `name`, `description`. 필드 이름은 camelCase[^7]로 정확히 써야 하고, 모르는 필드는 오류 없이 무시된다 (출처 [1])

| 필드 | 필수 | 값과 동작 |
| :--- | :--- | :--- |
| `name` | 예 | 고유 식별자. 256자 이하, `:` 불가(플러그인 이름용 예약), `-`로 시작 불가. 문서 예시는 소문자+하이픈 |
| `description` | 예 | Claude가 언제 맡길지 판단하는 기준 |
| `tools` | 아니요 | 쉼표 문자열 또는 YAML 목록. **생략하면 서브에이전트가 쓸 수 있는 모든 도구 상속** |
| `disallowedTools` | 아니요 | 금지 목록. 먼저 적용된 뒤 `tools`가 나머지에서 결정됨 |
| `model` | 아니요 | `sonnet`, `opus`, `haiku`, `fable`, 전체 모델 ID(예: `claude-opus-5-5`), `inherit` |
| `permissionMode` | 아니요 | `default`(=`manual`), `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | 아니요 | 최대 턴 수. 도달하면 결과를 '부분'으로 표시해 반환, 재개 가능 |
| `skills` | 아니요 | 시작할 때 본문 전체를 미리 넣을 스킬(최대 32개) |
| `mcpServers` | 아니요 | 이 서브에이전트만 쓸 MCP 서버 |
| `hooks` | 아니요 | 이 서브에이전트가 도는 동안만 작동하는 훅(`Stop`은 `SubagentStop`으로 바뀜) |
| `memory` | 아니요 | `user` / `project` / `local` 영구 메모리 폴더 |
| `background` | 아니요 | `true`면 Claude가 기다리려 해도 백그라운드 유지 |
| `effort` | 아니요 | `low`~`max` |
| `isolation` | 아니요 | `worktree`면 임시 git 워크트리[^8]에서 실행 |
| `color` | 아니요 | `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan` |
| `omitClaudeMd` | 아니요 | `true`면 사용자·프로젝트·로컬 CLAUDE.md 제외(v2.1.271+) |
| `initialPrompt` | 아니요 | `--agent`로 세션 전체를 이 에이전트로 돌릴 때 첫 턴 자동 입력 |
| `autoCompactWindow` | 아니요 | 100000~1000000 정수(v2.1.296+). `200k`라고 쓰면 200으로 읽혀 무시됨 |

(출처 [1]. `experimental` 필드도 있으나 입문 글 범위 밖)

- [사실] 문서의 기본 예시 (출처 [1])

  ```markdown
  ---
  name: code-reviewer
  description: Reviews code for quality and best practices. Use proactively after code changes.
  tools: Read, Glob, Grep
  model: sonnet
  ---

  You are a code reviewer. When invoked, analyze the code and provide
  specific, actionable feedback on quality, security, and best practices.
  ```

**잘못된 파일은 대개 조용히 건너뜀** (출처 [1], [6])

- [사실] `name` 없음, 여는 `---`가 첫 줄이 아님 → 문서 파일로 취급되어 조용히 건너뜀. `name` 형식 오류(`-` 시작, `:` 포함, 256자 초과), `description` 없음, YAML 파싱 실패 → 건너뛰고 디버그 로그에만 기록. 모르는 필드 → 오류 없이 무시 (출처 [1])
- [사실] 진단: `claude --debug` 후 `~/.claude/debug/<session-id>.txt`에서 `does not recognize or apply` 검색(모르는 필드와 의도했을 법한 이름을 알려 줌, v2.1.296+). 세션 전에 YAML만 확인하려면 `claude plugin validate .claude/agents`(v2.1.233+) (출처 [1])

**`/agents` 명령** (출처 [1], [11])

- [사실] 현재: "`/agents`를 실행하면 Claude에게 부탁하거나 `.claude/agents/`, `~/.claude/agents/`를 직접 고치라는 안내를 출력한다." v2.1.197 이하에서만 Running 탭·Library 탭이 있는 대화형 마법사가 열렸다 (출처 [1], [11])
- [사실] 지금 쓸 수 있는 목록 확인 수단: `@`를 입력하면 나오는 자동 완성 목록(파일 @멘션과 같은 방식), 실행 중·완료된 서브에이전트는 `/tasks`, 프롬프트 아래 서브에이전트 패널. 별도 '목록 명령'은 문서에 없다 (출처 [1], [11], [12])
- [사실] `claude agents`(터미널 명령)는 서브에이전트 관리가 아니라 백그라운드 세션을 보는 '에이전트 뷰'를 연다 (출처 [8], [7])

**Claude에게 만들어 달라고 하기** (출처 [1])

- [사실] 공식 퀵스타트 순서: ① 원하는 서브에이전트와 저장 위치를 말로 설명("~/.claude/agents/에 개인용 code-improver 서브에이전트를 만들어 줘 ... 읽기 전용으로, Sonnet을 쓰게") ② 만들어진 파일을 열어 프론트매터가 요청과 맞는지 확인 ③ "Use the code-improver agent to suggest improvements in this project"로 시험. Claude가 새 서브에이전트를 못 찾으면 재시작(세션 시작 때 `~/.claude/agents/` 폴더가 없었던 경우에만 생김) (출처 [1])
- [사실] SDK 문서의 세 가지 생성 방식: 코드로 정의(`agents` 옵션), 파일로 정의(`.claude/agents/`), 내장 general-purpose (출처 [6])
- [해석] 입문자에게는 "Claude에게 부탁 → 파일 열어 확인"이 가장 쉽다. 단 Claude가 만든 `tools` 줄을 반드시 확인하라고 강조할 것(읽기 전용을 부탁했는데 `tools`가 비어 있으면 모든 도구를 상속한다).
- 신뢰도: 높음

### Q4. 호출 방식: 자동 위임, 이름 부르기, @멘션, description 작성 요령

- [사실] 자동 위임: Claude는 요청 내용, 각 서브에이전트의 `description`, 현재 맥락을 보고 맡긴다. 적극적인 위임을 원하면 description에 "use proactively" 같은 문구를 넣으라고 한다 (출처 [1])
- [사실] 문서 예시 description: "Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code." (출처 [1])
- [사실] 이름 부르기(자연어): `Use the test-runner subagent to fix failing tests` 처럼 이름을 넣으면 **대개** 위임하지만 결정은 Claude가 한다 (출처 [1])
- [사실] @멘션: 특정 서브에이전트 실행을 **보장**한다. `@`를 치고 자동 완성에서 고르거나 전체를 직접 쓴다. 정확한 문법: `@"code-reviewer (agent)" look at the auth changes`. 직접 `@agent-<name>`으로 쳐도 된다. 플러그인 에이전트는 `@agent-my-plugin:code-reviewer`처럼 범위 이름. @멘션은 "어느 서브에이전트가 도는지"를 정할 뿐, 서브에이전트에게 갈 작업 프롬프트는 여전히 Claude가 쓴다 (출처 [1])
- [사실] 세션 전체를 서브에이전트로: `claude --agent code-reviewer`(그 에이전트의 프롬프트가 기본 시스템 프롬프트를 대체), 또는 프로젝트 설정 `{"agent": "code-reviewer"}` (출처 [1], [8])
- [사실] 이어 쓰기(체이닝): `Use the code-reviewer subagent to find performance issues, then use the optimizer subagent to fix them` 처럼 한 요청에 순서를 말하면, 각 결과가 메인으로 돌아오고 메인이 다음 단계로 필요한 맥락을 넘긴다 (출처 [1])
- [사실] 병렬 조사 예: `Research the authentication, database, and API modules in parallel using separate subagents`. 다만 상세한 결과가 많이 돌아오면 그만큼 메인 맥락을 차지한다고 경고한다 (출처 [1])
- [사실] description 요령: 언제 쓰는지 분명히, "use proactively" 같은 문구, **하나의 서브에이전트만 골라지도록 구체적으로**, 짧게. 내장을 뺀 서브에이전트 description 합계가 15,000 토큰을 넘으면 시작할 때 경고(모두 로드는 됨). 자세한 내용은 본문으로 옮기라(본문은 실행 때만 로드) (출처 [1])
- [사실] SDK 문서도 "description이 Claude에게 언제 쓸지 알려 준다, 분명하고 구체적으로 써라", 안 불리면 "이름을 명시하라"를 해결책으로 든다 (출처 [6])
- [사실] Claude 블로그 표: 서브에이전트는 이름·설명·도구 목록만 세션 시작 때 올라가고 본문은 Agent 도구로 불릴 때만 로드된다 (출처 [15])
- [해석] 한국어로 써도 되지만, 공식 예시가 영어 "use proactively"라 한국어 description 끝에 영어 한 문장을 덧붙이는 방법도 소개할 만하다(효과 차이는 문서에 없음 → 실험 후보).
- 신뢰도: 높음 (단, @멘션 문법은 [1] 단일 출처. 이름 부르기의 '보장' 여부는 [1]과 [6]이 다르게 말함 → 4절)

### Q5. 도구 제한, 모델 지정, 권한 모드와의 관계

**도구** (출처 [1], [4], [6])

- [사실] `tools`를 생략하면 메인 대화에서 쓸 수 있는 내장 도구·MCP 도구를 상속한다. 단 두 단계 필터가 있다: ① 모든 서브에이전트에서 빠지는 도구(`AskUserQuestion`, `EnterPlanMode`, `ExitPlanMode`(plan 모드 제외) 등, 깊이 한도에 닿으면 `Agent`) ② 백그라운드 서브에이전트는 내장 도구가 `Read`, `Grep`, `Glob`, `Bash`, `Edit`, `Write`, `WebFetch`, `WebSearch`, `Skill` 등 정해진 목록으로 줄어든다(MCP 도구는 유지). 그래서 같은 정의도 포그라운드와 백그라운드에서 도구가 다를 수 있다 (출처 [1])
- [사실] 읽기 전용 만들기: 허용 목록 `tools: Read, Grep, Glob`. 모범 사례 문서는 이렇게 하면 "프롬프트로 부탁하는 게 아니라 클로드 코드가 강제하는" 수정 불가 리뷰어가 된다고 쓴다 (출처 [4], [6])
- [사실] 금지 목록 방식: `disallowedTools: Write, Edit`(나머지 도구와 MCP 도구는 상속). `Bash(git push *)`처럼 범위를 붙인 항목은 `disallowedTools`에서 Bash 전체를 지운다. Bash는 두고 특정 명령만 막으려면 설정의 `permissions.deny`에 Bash 규칙을 넣는다(메인과 서브에이전트 모두 적용) (출처 [1])
- [사실] SDK 문서: 빼 버린 도구는 서브에이전트 세션에 아예 없으므로, 권한 요청이나 오류 없이 그 도구 없이 일한다 (출처 [6])
- [사실] 자주 쓰는 조합(SDK 문서): 읽기 분석 `Read, Grep, Glob` / 테스트 실행 `Bash, Read, Grep` / 코드 수정 `Read, Edit, Write, Grep, Glob` / 전체 `tools` 생략 (출처 [6])
- [사실] 문서 예시 중 code-reviewer는 `tools: Read, Grep, Glob, Bash`(git diff를 보려고 Bash 포함), debugger는 Edit 포함 (출처 [1])
- [해석] `Bash`를 주면 셸 명령으로 파일을 바꿀 수 있으므로 "완전한 읽기 전용"은 `Read, Grep, Glob`만 주는 쪽이다. 문서도 Bash를 주되 SQL 쓰기를 막는 예는 `PreToolUse` 훅으로 보강한다 [1].
- [해석] `tools`는 **그 서브에이전트**만 제한한다. 서브에이전트가 못 고치면 메인 대화가 직접 고칠 수 있다(메인은 여전히 Edit 보유). 세션 전체에서 막으려면 권한 규칙·훅이 필요하다 → 실험 2로 확인 권장.

**모델** (출처 [1], [7], [4], [5])

- [사실] 결정 순서: ① Claude가 Agent 도구 호출 때 넘기는 `model`(별칭만) ② 정의의 `model`(`inherit`=메인 모델) ③ `CLAUDE_CODE_SUBAGENT_MODEL` 환경 변수 ④ 메인 대화 모델. 모든 서브에이전트를 한 모델로 강제하려면 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`(v2.1.257+) (출처 [1], [7])
- [사실] 단순한 일(모듈을 import하는 파일 모으기, 문서 링크 확인)은 `model: haiku`가 훨씬 싸다고 권한다. `/model`로 메인을 Opus로 바꾸면 메인 모델을 상속하는 서브에이전트에도 적용된다 (출처 [4], [5])

**권한 모드와의 관계** (출처 [1], [10], [9])

- [사실] `permissionMode`를 비우면 메인 대화의 권한 모드를 상속한다 (출처 [1])
- [사실] 메인이 `bypassPermissions`, `acceptEdits`, `auto`면 서브에이전트도 그 모드로 돌고 정의의 `permissionMode`는 무시된다. auto 모드에서는 분류기가 메인의 규칙으로 서브에이전트 도구 호출을 평가하고, 끝난 뒤 작업과 최종 보고도 검토한다 (출처 [1])
- [사실] 메인이 `plan`이면 서브에이전트도 plan 모드에 머문다 (출처 [1])
- [사실] 메인이 `default`·`dontAsk`면 서브에이전트는 정의한 모드로 돈다. 단 정의에 `bypassPermissions`를 써도 메인 모드를 유지한다(v2.1.267+). 즉 서브에이전트가 혼자 권한을 높일 수 없다 (출처 [1])
- [사실] 포그라운드 서브에이전트의 권한 요청은 그대로 사용자에게 오고, 백그라운드 서브에이전트의 권한 요청은 메인 세션에 "어느 서브에이전트가 묻는지"와 함께 뜬다. Esc는 그 도구 호출만 거부하고 서브에이전트는 계속 돈다 (출처 [1])
- [사실] 내장 서브에이전트는 부모의 권한 규칙을 물려받는다. 한 번 '세션 동안 허용'으로 답하면 메인 대화를 포함한 세션 전체에 적용된다 (출처 [1])
- [사실] 특정 서브에이전트 금지: `permissions.deny`에 `Agent(이름)`, 또는 `claude --disallowedTools "Agent(Explore)"` (출처 [1], [10])
- [사실] `claude -p`는 v2.1.302부터 아무것도 지정하지 않으면 Manual 모드로 시작하고, 승인이 필요한 호출은 허용 규칙 등이 없으면 거부된다 (출처 [9])
- 신뢰도: 높음

### Q6. 주의점·한계

**메인 대화 기록을 못 본다(포크 제외)** (출처 [1], [6], [2])

- [사실] 일반 서브에이전트의 시작 맥락: 자기 시스템 프롬프트 + 환경 정보, Claude가 쓴 위임 메시지, CLAUDE.md(Explore·Plan 제외), git 상태(Explore·Plan 제외), `skills`에 적은 스킬 본문. 보지 못하는 것: 대화 기록, 메인이 이미 읽은 파일, 이미 부른 스킬, 출력 스타일, 메인의 자동 메모리 (출처 [1], [2])
- [사실] SDK 문서: 부모가 넘기는 유일한 내용은 Agent 도구의 프롬프트 문자열이니, 파일 경로·오류 메시지·결정 사항을 그 안에 직접 넣어라 (출처 [6])
- [사실] 포크는 예외로, 지금까지의 대화 전체·시스템 프롬프트·도구·모델을 그대로 물려받는다. 그래도 포크 자신의 도구 호출은 메인에 쌓이지 않고 최종 결과만 돌아온다. 포크는 프롬프트 캐시[^9]를 메인과 공유해 같은 맥락이 필요한 일에는 새 서브에이전트보다 싸다. 포크는 또 포크를 띄울 수 없다 (출처 [1])
- [사실] 포크 모드는 기본으로 켜져 있어 Claude가 스스로 포크를 띄울 수 있다. 직접 띄우려면 `/subtask <작업>`. 끄려면 `CLAUDE_CODE_FORK_SUBAGENT=0`, 포크만 막으려면 `permissions.deny`에 `Agent(fork)` (출처 [1], [6], [7])
- [사실] 포크 모드가 켜져 있는 동안 터미널·VS Code·데스크톱 대화형 세션에서는 Claude가 서브에이전트를 기다릴 수 없다(백그라운드로 돌고 끝나면 결과가 도착). 기다리게 하려면 포크 모드를 끄고 재시작한 뒤 "리뷰어를 돌리고 보고를 기다려"처럼 요청 (출처 [1], [7])

**중첩(서브에이전트가 서브에이전트를 부르기)** (출처 [1], [7], [6])

- [사실] 기본으로 가능하며, 메인 아래 **3계층**까지. 한도에 닿으면 Agent 도구가 빠져 그 층은 스스로 일하고 요약 하나를 돌려준다. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`로 조정(`1`이면 중첩 끔). v2.1.217~218은 기본 1, v2.1.219부터 기본 3 (출처 [1], [7])
- [사실] 특정 서브에이전트만 못 부르게 하려면 `tools` 목록에서 `Agent`를 빼거나 `disallowedTools`에 넣는다. 즉 `tools`를 생략한 에이전트는 Agent를 상속해 중첩이 가능하고, `tools` 목록을 쓴 에이전트는 `Agent`를 적어야 중첩 가능 (출처 [1])
- [사실] 동시 실행 기본 20개(`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, v2.1.217+). 세션 전체 생성 수 제한은 없다(`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`은 v2.1.224에서 제거) (출처 [1], [7], [6])

**비용·토큰** (출처 [1], [4], [5], [13])

- [사실] 서브에이전트마다 자기 요청을 보내고, 메인 대화와 같은 사용량 한도에 합산된다. 결과 보고도 메인 맥락에 들어가므로 상세한 보고가 많으면 맥락을 차지한다 (출처 [1], [5])
- [사실] 비용은 주로 토큰이고, 때로는 시간도 든다: 새 서브에이전트는 메인이 이미 가진 맥락을 다시 모아야 해서 그 자리에서 하는 것보다 느릴 수 있다. 기본은 같은(또는 더 작은) 모델이 같은 일을 하는 것이라 "더 똑똑한 답"은 아니다 (출처 [4])
- [사실] 절약법: 단순 작업은 `model: haiku`, 짧은 요약으로 돌려받기, `/usage`에서 서브에이전트별 사용 비중 확인(Pro·Max·Team·Enterprise) (출처 [4], [5])
- [사실] 서브에이전트 프롬프트 캐시는 따로 바꾸지 않으면 5분이다(구독 메인 대화는 약 1시간) (출처 [4], [13])
- [사실] 측정 시: `claude -p --output-format json` 결과의 `total_cost_usd`와 모델별 내역은 서브에이전트 사용분을 **포함**하고, 결과의 `usage`는 최상위(메인) 루프만 센다 (출처 [9], [13])

**새 파일 인식 시점** (출처 [1], [6], [10])

- [사실] `~/.claude/agents/`와 `.claude/agents/`를 감시해, 파일 추가·수정이 몇 초 안에 반영되고 다음 위임부터 새 정의를 쓴다. 재시작이 필요한 경우: ① 세션 시작 때 없던 범위의 `agents` 폴더에 첫 파일을 만든 경우(가장 흔한 원인) ② `--add-dir`·`/add-dir`로 추가한 폴더의 에이전트(감시 안 함) ③ `--disable-slash-commands`로 시작한 세션 (출처 [1], [6], [10])

**보안(남의 저장소)** (출처 [1], [10], [9], [8])

- [사실] 저장소의 `.claude/agents/` 파일에 있는 프론트매터 훅과 인라인 `mcpServers`는 그 폴더를 신뢰(trust)하기 전에는 쓰이지 않는다(부모 폴더만 신뢰한 경우·`claude -p` 포함). 인라인 MCP 서버 신뢰 확인은 v2.1.238부터, 그 전에는 확인 없이 로드했다 (출처 [1], [10])
- [사실] 신뢰 전에도 서브에이전트 자체는 돈다(훅만 건너뜀) (출처 [1])
- [사실] 플러그인 서브에이전트는 "보안상" `hooks`, `mcpServers`, `permissionMode`를 지원하지 않고 무시한다 (출처 [1])
- [사실] 남의 저장소에서 `claude -p`를 돌리기 전 선택지: `--bare`(프로젝트의 훅·스킬·명령·서브에이전트·플러그인·`.mcp.json`을 읽지 않음), `--setting-sources user` 등 (출처 [10], [9], [8])
- [사실] 서브에이전트 최종 보고는 메인이 읽기 전에 지시처럼 보이는 패턴(가짜 시스템 태그, `Human:` 줄 등)을 검사해 무력화 표시를 붙인다(v2.1.210+). 단 문서는 이것이 "서브에이전트가 닿을 수 있는 범위를 제한하는 것의 대체물이 아니다"라고 한다 (출처 [1], [6])
- [사실] 다른 에이전트의 메시지는 권한 승인으로 인정되지 않고, 서브에이전트의 권한 설정·CLAUDE.md·설정을 바꿀 수 없다 (출처 [1])
- [해석] 에이전트 파일의 본문은 곧 시스템 프롬프트라, 남의 저장소의 에이전트는 "지시문 묶음"이다. `tools`가 비어 있으면 모든 도구를 상속하므로, 스킬 글에서와 같이 "남이 만든 것은 열어 읽어 보고 쓰라"는 주의를 그대로 적용할 수 있다.

**기타** (출처 [1])

- [사실] 서브에이전트 기록은 `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`에 따로 저장되고, `cleanupPeriodDays`(기본 30일)가 지나면 지워진다 (출처 [1])
- [사실] v2.1.63에서 Task 도구 이름이 Agent로 바뀌었다. 설정의 `Task(...)`는 별칭으로 계속 동작한다 (출처 [1], [6])
- 신뢰도: 높음

### Q7. 스킬과 결합: 스킬의 `context: fork`, 에이전트의 `skills:` 필드

- [사실] 두 방향이 있다. 서브에이전트가 `skills:` 필드로 스킬을 미리 싣거나, 스킬이 `context: fork`로 격리된 맥락에서 돈다 (출처 [2], [3])
- [사실] 스킬 쪽 `context: fork`: 새 서브에이전트(종류는 `agent` 필드)가 스킬 본문을 프롬프트로 받아 실행한다. 대화 기록을 못 보므로 지침이 그 자체로 완결돼야 한다. `agent`에는 내장(`Explore`, `Plan`, `general-purpose`)이나 `.claude/agents/`의 커스텀 에이전트를 쓸 수 있고, 생략하면 general-purpose (출처 [3])
- [사실] 이름과 달리 `context: fork` 스킬은 "대화 포크"가 아니다(대화 기록을 넘기지 않음). 기록이 필요하면 대화 포크를 쓰라고 문서가 구분한다 (출처 [3])
- [사실] `context: fork` 스킬은 기본 백그라운드로 돌고 결과가 끝나면 대화에 도착한다. `background: false`면 그 턴에서 기다린다. `-p`·SDK에서는 항상 기다린다. 백그라운드 실행은 축소된 도구 목록을 쓰므로 그 밖의 도구가 필요하면 `background: false` (출처 [3])
- [사실] 경고: "이 API 규칙을 따르라" 같은 지침만 있고 할 일이 없는 스킬에 `context: fork`를 쓰면, 서브에이전트가 실행할 지시가 없어 의미 있는 결과 없이 돌아온다 (출처 [3])
- [사실] 문서 예시 (출처 [3])

  ```yaml
  ---
  name: deep-research
  description: Research a topic thoroughly
  context: fork
  agent: Explore
  ---

  Research $ARGUMENTS thoroughly:

  1. Find relevant files using Glob and Grep
  2. Read and analyze the code
  3. Summarize findings with specific file references
  ```

- [사실] 비교표 (출처 [3])

  | 방식 | 시스템 프롬프트 | 할 일(Task) | 함께 로드 |
  | :--- | :--- | :--- | :--- |
  | 스킬 + `context: fork` | 에이전트 종류의 것 | SKILL.md 내용 | CLAUDE.md(에이전트 규칙대로) |
  | 서브에이전트 + `skills` 필드 | 서브에이전트 본문 | Claude의 위임 메시지 | 미리 실은 스킬 + CLAUDE.md |

- [사실] 에이전트 쪽 `skills:` 필드: 나열한 스킬의 **본문 전체**가 시작할 때 주입된다(최대 32개). 이 필드는 "미리 싣는 것"을 정할 뿐, 서브에이전트가 접근 가능한 스킬을 제한하지 않는다(목록에 없는 스킬도 Skill 도구로 발견·사용 가능). `disable-model-invocation: true` 스킬은 미리 실을 수 없다. 내장 에이전트는 스킬을 미리 싣지 않는다 (출처 [1], [2], [6])
- [사실] 문서 예시 (출처 [1])

  ```yaml
  ---
  name: api-developer
  description: Implement API endpoints following team conventions
  skills:
    - api-conventions
    - error-handling-patterns
  ---

  Implement API endpoints. Follow the conventions and patterns from the preloaded skills.
  ```

- [사실] 기능 개요의 결합 패턴: "스킬 + 서브에이전트 = 스킬이 병렬 작업용 서브에이전트를 띄움"(예: `/audit` 스킬이 보안·성능·스타일 서브에이전트를 격리 맥락에서 실행) (출처 [2])
- [해석] 시리즈 연결 포인트: 5편의 `blog-titles` 스킬은 `disable-model-invocation: true`라 `skills:`로 미리 실을 수 없고, 실험에 쓴 `proofread-ko`(자동 호출 허용)는 실을 수 있다. 앞 글 독자에게 바로 와닿는 예다.
- 신뢰도: 높음 (공식 [1][2][3][6] 일치)

## 3. 핵심 수치·사실 표

| 항목 | 내용 | 기준일 | 출처 |
| :--- | :--- | :--- | :--- |
| 최신 버전 | v2.1.312 (2026-10-27) | 2026-10-28 열람 | [14] |
| 필수 필드 | `name`, `description` | 2026-10-28 | [1][6] |
| `name` 규칙 | 256자 이하, `:` 불가, `-`로 시작 불가 | 2026-10-28 | [1] |
| description 합계 경고 | 내장 제외 합계 15,000 토큰 초과 시 시작 경고 | 2026-10-28 | [1] |
| 우선순위 | 관리형 > `--agents` > 프로젝트 > 사용자 > 플러그인 | 2026-10-28 | [1][2] |
| `/agents` 마법사 | v2.1.197 이하만. 이후는 안내 문구만 출력 | 2026-10-28 | [1][11] |
| 중첩 깊이 | 기본 3계층(v2.1.219부터, v2.1.217~218은 1) | 2026-10-28 | [1][7] |
| 동시 실행 | 기본 20개(v2.1.217+) | 2026-10-28 | [1][6][7] |
| 세션당 총 생성 수 | 제한 없음(옛 상한 200은 v2.1.224에서 제거) | 2026-10-28 | [1][7] |
| `skills` 미리 싣기 | 최대 32개 | 2026-10-28 | [1][6] |
| 포크 모드 기본 켜짐 | 대화형 터미널 v2.1.232, `-p`·SDK·데스크톱·VS Code v2.1.302(2026-10-16) | 2026-10-28 | [1][14] |
| `claude -p` 기본 권한 모드 | 지정 없으면 Manual(v2.1.302+) | 2026-10-28 | [9] |
| Task → Agent 이름 변경 | v2.1.63 (`Task(...)` 별칭 유지) | 2026-10-28 | [1][6] |
| 서브에이전트 기록 보관 | `~/.claude/projects/.../subagents/agent-<id>.jsonl`, 기본 30일 | 2026-10-28 | [1] |
| 서브에이전트 프롬프트 캐시 | 따로 바꾸지 않으면 5분 | 2026-10-28 | [4] |
| 영구 메모리 로드 양 | `MEMORY.md` 첫 200줄 또는 25KB 중 먼저 닿는 쪽 | 2026-10-28 | [1] |
| 결과 필드 범위 | `usage`=메인 루프만, `total_cost_usd`·`modelUsage`=서브에이전트 포함 | 2026-10-28 | [13] |
| `-p` 백그라운드 대기 | 백그라운드 서브에이전트가 끝날 때까지 실행이 열려 있음 | 2026-10-28 | [9] |
| 에이전트 팀(참고) | 플랜 모드 팀원 기준 일반 세션의 약 7배 토큰 | 2026-10-28 | [5] |

## 4. 상충하거나 불확실한 내용

### 4-1. 앞 글(발행본)과 공식 문서 대조

| 글 | 앞 글의 서술 | 현재 문서 기준 판정 | 근거 |
| :--- | :--- | :--- | :--- |
| 1편 핵심 기능 | "독립된 컨텍스트 창과 별도 지침, 제한된 도구를 가지고, 끝나면 결과 요약만 돌려줍니다" | 대체로 맞음. 보완: 도구는 `tools`로 좁힐 때만 제한되고 생략하면 전부 상속. 포크는 대화 기록을 물려받음(포크 모드 기본 켜짐) | [1][6] |
| 1편 | 필수 항목은 `name`과 `description` | 맞음 | [1] |
| 1편 | 최신 `/agents`는 마법사 대신 "요청하거나 파일을 직접 편집하라는 안내" | 맞음(v2.1.198+) | [1][11] |
| 1편 | 장단점 표 "토큰 사용량이 합산됨" | 맞음(같은 사용량 한도에 합산) | [1][5] |
| 1편 | "읽을 양이 많은 작업은 서브에이전트에 맡깁니다" | 공식 '설정 키워가기' 표와 일치. 단 모범 사례 문서는 "컨텍스트 보호용 서브에이전트"를 옛 조언으로 분류 → 관점 차이로 보완 설명 권장 | [2][4] |
| 1편 | 조사 담당에게 웹 검색·읽기·쓰기 도구만 줌 | 저장소 `researcher.md`의 `tools: WebSearch, WebFetch, Read, Glob, Grep, Write`와 일치 | 저장소 |
| 5편 스킬 | "스킬은 지금 대화에 불러오는 설명서, 서브에이전트는 따로 일한 뒤 요약만 돌려주는 일꾼" | 맞음. 보완: 둘은 `context: fork`·`skills:`로 결합 가능 | [2][3] |
| 4편 권한 모드 | 서브에이전트 언급 없음 | 이번 글에서 보완할 만함: 서브에이전트는 메인 권한 모드를 대부분 따르고 스스로 권한을 높일 수 없음, 백그라운드 서브에이전트의 권한 요청은 메인에 뜸 | [1] |

### 4-2. 미발행 원고(`docs/research/claude-code-subagent-team.md`, `docs/final/claude-code-subagent-team/final.md`)와 대조

- **상충 1 (중첩 조건)**: 미발행 최종본 팁 "서브에이전트가 또 다른 서브에이전트를 부르려면 `tools`에 `Agent`가 있어야 하고, 기본 최대 3단계" / 노트 "중첩: … `tools`에 `Agent`가 있어야 하고". 현재 문서는 "기본으로 서브에이전트는 자기 서브에이전트를 띄울 수 있다(3계층)"이고, `tools`를 생략하면 Agent를 상속한다. `Agent`를 적어야 하는 것은 `tools` 허용 목록을 쓴 경우뿐이다 [1][7]. → "목록을 직접 쓴 경우에는 `Agent`를 넣어야 한다"로 고쳐 써야 정확하다. (저장소 기준으로 `tools`를 생략한 backend-developer·qa-engineer·code-reviewer는 중첩 가능, 목록을 쓴 researcher·writer 등은 불가 [해석])
- **상충 2 (인식 시점)**: 저장소 `CLAUDE.md`의 "새로 추가하거나 고친 에이전트는 새 세션부터 인식된다"는 현재 문서와 다르다. 문서는 몇 초 안에 반영, 예외 세 가지(새 `agents` 폴더, `--add-dir` 폴더, `--disable-slash-commands`)에만 재시작 [1][6]. 미발행 원고는 이미 이 점을 반영했으나, 저장소 `CLAUDE.md` 문장은 그대로다(파일은 수정하지 않음, 판단은 사용자 몫).
- **누락(최신화 필요)**: 미발행 원고에는 ① 포크 모드 기본 켜짐과 서브에이전트 기본 백그라운드 [1][4][14] ② `model` 값의 `fable`·전체 모델 ID [1] ③ `claude plugin validate .claude/agents`(v2.1.233+)와 디버그 로그의 `does not recognize or apply`(v2.1.296+) [1] ④ `omitClaudeMd`(v2.1.271+) [1] ⑤ 내장 에이전트(Explore·Plan·general-purpose 등) 소개가 없다.
- **그대로 맞는 부분**: 필수 필드 2개, 프로젝트가 사용자보다 우선, 프론트매터 오류 시 조용히 건너뜀, `@"이름 (agent)"` 문법, description 15,000 토큰 경고, 동시 20개, "대화 기록을 모름(포크 예외)", "읽기 전용을 지침으로만 두면 강제가 아님 → `tools: Read, Glob, Grep`로 좁혀라"(모범 사례 문서 [4]와 일치).

### 4-3. 출처끼리 다른 부분

- **중첩 깊이**: 공식 문서는 기본 3계층(조정 가능) [1][7]. Claude 블로그(2026-06-18)는 "subagents can nest up to five levels deep"라고 썼다 [15]. 블로그 문맥이 동적 워크플로(수십~수백 에이전트 조율) 설명 부분이고 발행 시점도 앞선다. **글에는 문서 기준 3계층으로 쓴다.**
- **이름을 부르면 보장되나**: 서브에이전트 문서는 "자연어로 이름을 부르면 대개 위임하지만 Claude가 결정한다, @멘션은 보장한다" [1]. SDK 문서는 "이름을 언급하면 자동 매칭을 건너뛰고 그 에이전트를 직접 부른다(보장)" [6]. **CLI 독자 대상 글에서는 [1] 기준으로 "확실히 하려면 @멘션"**으로 쓴다.
- **자동 위임이 얼마나 일어나나**: 모범 사례 문서는 "Claude가 스스로 위임한다(넓은 검색은 Explore, 곁일은 포크)" [4]. 반면 SDK 문서·Opus 5 프롬프트 가이드는 "모델이 Opus 5이고 `claude_code` 시스템 프롬프트 프리셋을 쓰면, 요청받지 않으면 Agent 도구를 부르지 말라는 줄을 클로드 코드가 넣는다" [6][16]. 현재 기본 모델이 Opus 5.5라는 서술은 [4]에 있으나, 이 지시가 Opus 5.5에도 적용되는지는 **문서에서 확인하지 못했다**. [해석] 커스텀 에이전트 자동 위임 실험 결과가 모델에 따라 달라질 수 있으므로 실험마다 모델을 기록해야 한다.
- **'컨텍스트 절약'의 비중**: 기능 개요는 "컨텍스트가 차고 있을 때 서브에이전트"를 권하고 [2], 모범 사례는 "1M 창이라 컨텍스트 부족은 드물다, 그래도 병렬·출력 격리·독립 리뷰에는 좋다(대신 토큰 추가)"라고 한다 [4]. 둘 다 공식이므로 양쪽을 함께 적는다.
- **버전 정보(제3자)**: 검색 결과 요약에는 "백그라운드 기본은 v2.1.198", "포크 기본이 v2.1.161부터"라는 제3자 서술이 보였지만 원문을 열지 못했고(접속 차단) 공식 문서와도 맞춰 보지 못했다. **쓰지 않는다.** 공식 문서가 밝힌 버전(포크: 터미널 v2.1.232, 그 외 v2.1.302)만 쓴다 [1][14].

### 4-4. 확인하지 못한 부분

- statusline-setup·claude-code-guide의 도구 구성(문서에 없음).
- `claude -p` 프롬프트 안에 `@"이름 (agent)"`를 넣었을 때도 @멘션으로 처리되는지(문서에 명시 없음 → 실험 후보).
- 한국어 description에 영어 "use proactively"를 덧붙이는 효과(문서에 없음 → 실험 후보).
- CLI `--output-format json`·`stream-json`의 필드 경로(`modelUsage`, 메시지별 `message.usage`)는 SDK 문서 [13] 기준으로 적었다. CLI 출력에서 실제 이름을 한 번 확인할 것.
- 변경 이력 [14]은 112만 자라 앞 10만 자(v2.1.299~v2.1.312)만 읽었다. `/agents` 마법사 제거·중첩 기본값 변경 항목은 변경 이력 원문이 아니라 문서 [1][7]의 버전 서술로 확인했다.

## 5. 글쓰기 에이전트에게 (활용 가이드)

### 글에 바로 쓸 수 있는 핵심 메시지

- 서브에이전트 = "따로 일하고 보고서만 내는 일꾼". 장점 넷: 병렬, 긴 출력 격리, 쓴 과정을 안 본 리뷰어, 도구 제한 [4].
- 만드는 법은 파일 한 장, 필수는 `name`·`description` 둘, 본문이 지침(시스템 프롬프트) [1].
- 가장 쉬운 시작은 "Claude에게 만들어 달라고 부탁 → 파일을 열어 `tools` 줄 확인" [1].
- 확실히 부르려면 `@"이름 (agent)"` [1].
- "읽기 전용"은 지침이 아니라 `tools: Read, Grep, Glob`로 [4].
- 2026-10 기준 달라진 점: `/agents`는 안내만, 서브에이전트는 기본 백그라운드, 포크 모드 기본 켜짐 [1][14].
- 공짜 아님: 서브에이전트도 같은 사용량 한도를 쓴다. 단순한 일은 `model: haiku` [4][5].

### FAQ 후보

- **Q. `/agents`를 쳤는데 만들기 화면이 안 나와요.** v2.1.198부터는 안내 문구만 나온다. Claude에게 부탁하거나 `.claude/agents/`에 파일을 직접 만든다 [1][11].
- **Q. 만든 서브에이전트가 목록에 없어요.** `@`를 쳐서 자동 완성에 나오는지 본다. 없으면 ① 첫 줄이 `---`인지 ② `name`·`description`이 있는지 ③ description 값에 `: `(콜론+공백)이 있어 YAML이 깨졌는지 ④ 세션 시작 후 `agents` 폴더를 새로 만들었는지(재시작 필요) 순서로 확인. `claude plugin validate .claude/agents`로 YAML 검사 [1][6].
- **Q. 서브에이전트가 우리 대화 내용을 아나요?** 일반 서브에이전트는 모른다. Claude가 쓴 위임 메시지와 CLAUDE.md만 보고 시작한다(Explore·Plan은 CLAUDE.md도 안 봄). 포크만 대화를 물려받는다 [1][6].
- **Q. 서브에이전트를 쓰면 더 좋은 답이 나오나요?** 아니다. 같은(또는 작은) 모델이 같은 일을 하는 것이라, 얻는 건 병렬성과 '새 눈'이다 [4].
- **Q. 비용이 더 드나요?** 서브에이전트마다 따로 요청을 보내 같은 한도에 합산된다. 새로 맥락을 모으느라 더 느릴 수도 있다 [1][4][5].
- **Q. `claude agents` 명령은 서브에이전트 목록인가요?** 아니다. 백그라운드 세션을 보는 에이전트 뷰다 [8].
- **Q. 스킬과 서브에이전트, 뭘 만들어야 하죠?** 단계를 메인에서 보며 조정하고 싶으면 스킬, 중간 결과를 볼 필요 없는 곁일이면 서브에이전트 [2][15]. 둘을 합칠 수도 있다(`context: fork`, `skills:`) [3].
- **Q. 서브에이전트가 결과를 늦게 줘요/기다리질 않아요.** 대화형 세션에서는 기본 백그라운드라 결과가 끝나면 도착한다. 기다리게 하려면 `CLAUDE_CODE_FORK_SUBAGENT=0` 후 재시작하고 "기다려"라고 요청 [1].
- **Q. 남이 만든 에이전트 파일을 받아 써도 되나요?** 본문이 곧 지시문이고 `tools`를 비우면 모든 도구를 쓴다. 열어서 읽어 보고 쓴다. 저장소 에이전트의 훅·인라인 MCP는 폴더 신뢰 전에는 작동하지 않는다 [1][10].

### 장단점·비교 포인트

| 방식 | 장점 | 단점·주의 |
| :--- | :--- | :--- |
| 메인 대화에서 직접 | 맥락 공유, 빠른 주고받기, 지연 적음 | 긴 출력이 대화에 계속 남음 |
| 서브에이전트(일반) | 출력 격리, 도구 제한, 병렬 | 맥락을 다시 모음(느릴 수 있음), 토큰 추가, 대화 기록 모름 |
| 포크 | 설명 없이 바로 곁일 시작, 캐시 공유로 상대적으로 쌈 | 입력 격리가 없음(대화 전체를 봄), 포크는 또 포크 못 함 |
| 스킬 `context: fork` | 반복 절차를 격리 실행 | 지침만 있는 스킬엔 무의미, 대화 기록 못 봄 |
| `tools` 허용 목록 | 클로드 코드가 강제 | 필요한 도구까지 빠질 수 있음, Agent를 빼면 중첩 불가 |
| 지침으로만 제한 | 유연함 | 강제 아님 |

### 연관 키워드·표현 후보

클로드 코드 서브에이전트(메인), 서브에이전트 사용법, 서브에이전트 만들기, Claude Code subagents, `.claude/agents`, Explore 에이전트, `@멘션` 호출, 읽기 전용 에이전트, description 작성법, use proactively, 포크(fork), 백그라운드 에이전트, 클로드 코드 에이전트 차이.

### 주의: 쓰면 안 되는 단정 표현

- "`/agents`로 만들기 화면을 연다" (v2.1.197 이하 이야기) [1].
- "서브에이전트는 대화 기록을 절대 못 본다" → "일반 서브에이전트는 못 본다, 포크는 본다" [1].
- "서브에이전트를 쓰면 비용이 절약된다/답이 좋아진다" (조건부. 토큰은 추가로 든다) [4].
- "description만 잘 쓰면 반드시 자동으로 불린다" (Claude 판단, 모델·프롬프트에 따라 다름) [1][6].
- "최대 5단계 중첩" (블로그 표현. 문서는 기본 3계층) [1][15].
- "중첩하려면 `tools`에 `Agent`가 필요하다" (목록을 쓴 경우에만) [1].
- "새 에이전트는 재시작해야 인식된다" (대부분 몇 초 안 반영) [1].
- 버전 숫자는 모두 "조사일(2026-10-28), v2.1.312 기준"으로 적는다. 빠르게 바뀌는 기능이다 [14].

### 직접 경험으로 보강해야 할 부분 (리서치로는 채울 수 없음)

- `/agents` 실행 화면(안내 문구) 캡처, `@` 자동 완성에 내 에이전트가 뜨는 화면, 서브에이전트 패널·`/tasks` 화면.
- 아래 실험의 실제 수치(메인 맥락 크기, 비용, 걸린 시간, 자동 위임 비율). 결과가 문서 기대와 다르면 그대로 적는다.
- 내 저장소 에이전트(researcher·writer 등)를 실제로 이 시리즈 제작에 쓴 경험. 단 git 기록 등으로 확인 가능한 사실만.

### 5-1. 입문자 실습 예제 후보 (파일 내용 그대로)

공통 주의: 이 저장소 `CLAUDE.md` 규칙대로 description 값에 `: `(콜론+공백)를 넣지 않았다. 파일 이름과 `name`을 같게 맞췄다(문서상 필수는 아님 [1]).

**예제 A. 찾아서 요약만 돌려주는 조사 담당 (읽기 전용 + 싼 모델)**

- 경로: `.claude/agents/doc-finder.md`
- 보여 줄 포인트: 맥락 격리(요약만 돌아옴), `tools`로 읽기 전용, 단순 작업에 `model: haiku` [1][4]

```markdown
---
name: doc-finder
description: 프로젝트 폴더에서 원하는 내용이 어느 파일 어디에 있는지 찾아, 근거 파일 경로와 함께 5줄 이내로 요약해 돌려주는 읽기 전용 조사 담당. 사용자가 프로젝트 안에서 무언가를 찾아 달라고 하거나 어디에 있는지 물을 때 사용한다. Use proactively for project-wide searches.
tools: Read, Grep, Glob
model: haiku
color: cyan
---

당신은 프로젝트 안에서 자료를 찾아 주는 조사 담당이다.

1. Glob과 Grep으로 관련 파일을 찾는다.
2. 필요한 부분만 Read로 읽는다.
3. 결과를 5줄 이내로 요약하고, 줄마다 근거 파일 경로를 붙인다.
4. 파일을 고치거나 새로 만들지 않는다.
5. 찾지 못했으면 "찾지 못했습니다"와 찾아본 위치만 쓴다.

보고 첫 줄에 [doc-finder 보고]라고 쓴다.
```

- 부르는 법: `@"doc-finder (agent)" 로그인 처리가 어디 있는지 찾아 줘` 또는 "doc-finder 서브에이전트로 … 찾아 줘" [1]

**예제 B. 고치지 못하는 코드 리뷰어 (공식 예시를 한국어로)**

- 경로: `.claude/agents/code-reviewer.md`
- 보여 줄 포인트: "읽기 전용"을 지침이 아니라 도구로 강제, 우선순위별 보고 형식 [1][4]

```markdown
---
name: code-reviewer
description: 바뀐 코드를 읽고 버그와 위험한 부분을 찾아 우선순위별로 보고하는 읽기 전용 리뷰어. 코드를 작성하거나 고친 직후, 또는 사용자가 코드 검토를 부탁할 때 사용한다. Use proactively after code changes.
tools: Read, Grep, Glob
model: inherit
color: red
---

당신은 꼼꼼한 코드 리뷰어다. 코드를 고치지 않고 문제와 근거만 보고한다.

검토할 파일은 위임 메시지에 적힌 것만 본다.

확인할 것:
- 읽기 쉬운가, 이름이 알맞은가
- 오류 처리가 빠진 곳이 있는가
- 비밀번호나 키가 코드에 그대로 들어 있지 않은가
- 입력값을 검사하는가

보고 형식:
1. 꼭 고칠 것
2. 고치면 좋은 것
3. 참고 사항

항목마다 파일 경로와 줄 번호, 고치는 방법 예시를 붙인다. 문제가 없으면 "발견한 문제가 없습니다"라고만 쓴다.
```

- 비교 실습: 같은 파일에서 `tools:` 줄을 지우면(전부 상속) 수정 요청에 실제로 고칠 수 있게 된다 → 실험 2

**예제 C. 5편 스킬과 합치기 (`skills:` 미리 싣기 / `context: fork`)**

- 전제: 5편 실험의 `proofread-ko` 스킬이 `.claude/skills/proofread-ko/SKILL.md`에 있음(자동 호출 허용 스킬이어야 미리 실을 수 있음) [1]
- C-1 경로: `.claude/agents/blog-proofreader.md`

```markdown
---
name: blog-proofreader
description: 블로그 초안 파일을 읽고 맞춤법과 띄어쓰기 문제를 표로 정리해 돌려주는 읽기 전용 교정 담당. 사용자가 초안 파일의 맞춤법 점검이나 교정을 부탁할 때 사용한다.
tools: Read, Grep, Glob
model: inherit
skills:
  - proofread-ko
---

위임 메시지로 받은 파일만 읽는다.
미리 불러온 proofread-ko 스킬의 규칙대로 고칠 곳을 찾되, 파일은 고치지 않는다.
결과는 "원래 | 고친 것 | 이유" 표와 고칠 곳 개수만 돌려준다.
```

- 함정 포인트: 5편의 `blog-titles`처럼 `disable-model-invocation: true`인 스킬은 `skills:`에 넣어도 미리 실리지 않는다 [1].
- C-2 (스킬 쪽에서 서브에이전트로 보내기) 경로: `.claude/skills/find-in-project/SKILL.md`

```markdown
---
name: find-in-project
description: 프로젝트 안에서 주제를 찾아 근거 파일 경로와 함께 요약한다. 사용자가 프로젝트에서 무언가를 찾아 정리해 달라고 할 때 사용한다.
context: fork
agent: doc-finder
---

다음 주제를 이 프로젝트에서 조사한다. 주제는 $ARGUMENTS

1. 관련 파일을 찾는다.
2. 핵심 내용을 5줄 이내로 요약한다.
3. 줄마다 근거 파일 경로를 붙인다.
```

- 부르는 법: `/find-in-project 로그인 처리`. 대화형에서는 기본 백그라운드로 돌고 끝나면 결과가 도착, `-p`에서는 기다린다 [3]. 이름과 달리 대화 포크가 아니라 대화 기록을 못 본다는 점도 함께 설명 [3].

### 5-2. 메인 에이전트가 `claude -p`로 돌릴 실험 포인트 (측정 방법 포함)

**공통 준비**

- 이 저장소가 아닌 빈 실험 폴더에서 한다. 이 저장소에는 프로젝트 에이전트 8개와 CLAUDE.md가 있어 자동 위임 결과가 섞인다. 예:
  - `mkdir -p ~/sa-lab && cd ~/sa-lab && git init`
  - 조사 대상 복사: `cp -r /home/user/claude-code-version/backend ~/sa-lab/backend` 후 `rm -rf ~/sa-lab/backend/.venv` (Idempotency-Key 처리 코드가 있음)
  - `~/.claude/agents/`에 개인 에이전트가 있으면 결과가 섞이니 목록을 기록해 둔다.
- `.claude/agents/` 폴더는 실험 전에 만든다(매 `-p` 실행이 새 세션이라 재시작 문제는 없지만, 대화형으로 볼 때를 대비) [1].
- 매 실험 전에 `claude --version` 기록. 모델도 기록한다(결과의 모델별 내역 키로 확인). 4-3의 Opus 5 위임 억제 지시 때문에 모델별로 자동 위임이 다를 수 있다 [6][16].
- `-p`는 v2.1.302부터 Manual 모드로 시작해 승인이 필요한 호출은 거부된다. 읽기는 작업 폴더 안에서 승인 불필요 [9][10]. 수정이 필요한 실험만 `--permission-mode acceptEdits`를 준다.
- `-p`에서도 포크 모드가 기본 켜짐(v2.1.302+)이라 Claude가 커스텀 에이전트 대신 포크를 쓸 수 있다. Agent 도구 입력의 `subagent_type`을 꼭 기록하고, 깨끗한 비교가 필요하면 `CLAUDE_CODE_FORK_SUBAGENT=0`을 붙인 조건을 따로 돌린다 [1][6].
- `--bare`는 서브에이전트를 읽지 않으므로 쓰지 않는다 [9].
- 자동 위임 실험은 같은 조건을 3~5회 반복해 비율로 기록한다(Claude 판단이라 매번 같지 않음).
- 기록 방식: `claude -p "<프롬프트>" --output-format stream-json --verbose > run.jsonl` (서브에이전트 메시지는 `parent_tool_use_id`가 채워져 나오고, 메인 메시지는 `null`) [9]. 서브에이전트의 글까지 보려면 `--forward-subagent-text` 추가(v2.1.211+) [8][9].

**측정용 jq 명령 (필드 경로는 첫 실행에서 실제 출력과 맞는지 확인)** [9][13]

```bash
# 1) Agent 도구 호출과 서브에이전트 종류
jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and (.name=="Agent" or .name=="Task")) | {id, subagent_type: .input.subagent_type}' run.jsonl

# 2) 메인 루프의 도구 호출 수 (이름별)
jq -r 'select(.type=="assistant" and .parent_tool_use_id==null) | .message.content[]? | select(.type=="tool_use") | .name' run.jsonl | sort | uniq -c

# 3) 서브에이전트 안의 도구 호출 수 (이름별)
jq -r 'select(.type=="assistant" and .parent_tool_use_id!=null) | .message.content[]? | select(.type=="tool_use") | .name' run.jsonl | sort | uniq -c

# 4) 메인 대화 맥락 크기(마지막 메인 단계의 입력 토큰 합)
jq -s '[.[] | select(.type=="assistant" and .parent_tool_use_id==null) | .message.usage] | last | (.input_tokens + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0))' run.jsonl

# 5) 메인으로 돌아온 도구 결과 길이(글자 수). 1)의 Agent id와 맞춰 서브에이전트 보고 분량을 본다
jq -r 'select(.type=="user" and .parent_tool_use_id==null) | .message.content[]? | select(.type=="tool_result") | [.tool_use_id, (.content | if type=="array" then (map(.text // "") | join("")) else tostring end | length)] | @tsv' run.jsonl

# 6) 최종 결과: usage(메인만) vs modelUsage·total_cost_usd(서브에이전트 포함)
jq 'select(.type=="result") | {usage, total_cost_usd, modelUsage}' run.jsonl
```

- 걸린 시간은 `time claude -p ...`로 잰다.
- 수정 여부는 실험 폴더의 `git diff --stat`으로 확인(실험 전 `git add -A && git commit -m base`).

**실험 1. 같은 조사를 직접 vs 서브에이전트 (메인으로 돌아오는 분량 비교)**

- 준비: 예제 A의 `doc-finder.md`를 `~/sa-lab/.claude/agents/`에 둔다(공정 비교를 위해 `model: inherit`로 바꾼 버전도 준비).
- A(직접, 위임 금지):
  `claude -p "backend 폴더에서 Idempotency-Key가 처리되는 흐름을 찾아, 근거 파일 경로와 함께 5줄 이내로 요약해 줘." --disallowedTools "Agent" --output-format stream-json --verbose > A1.jsonl`
  (`--disallowedTools`에 도구 이름만 쓰면 그 도구가 Claude 맥락에서 빠진다 [8])
- B(커스텀 서브에이전트): 같은 요청 앞에 "doc-finder 서브에이전트를 써서"를 붙여 실행 → `B1.jsonl`
- C(내장 Explore): "Explore 서브에이전트를 써서"를 붙여 실행 → `C1.jsonl`
- 측정: jq 2)~6), 시간. 핵심 지표는 "메인 맥락 크기(4)", "메인의 Read 호출 수(2) vs 서브에이전트 안 Read 호출 수(3)", "Agent 결과 글자 수(5)", "`usage` vs `modelUsage` 차이(6)", "총비용·시간".
- 문서 기준 기대: B·C에서 파일 읽기는 서브에이전트 안에서 일어나고 메인에는 요약만 돌아와 메인 맥락이 A보다 작다 [1][2]. 대신 총 토큰·비용은 줄지 않거나 늘 수 있고, 시간도 더 걸릴 수 있다 [4]. 결과가 다르면 그대로 기록한다.
- 반복: 조건별 3회.

**실험 2. 읽기 전용 에이전트에 수정 요청**

- 준비: 예제 B의 `code-reviewer.md`(tools: Read, Grep, Glob). 실험 전 커밋.
- 실행: `claude -p "code-reviewer 서브에이전트를 써서 backend/app/main.py 맨 위에 '# reviewed' 주석 한 줄을 추가해 줘." --permission-mode acceptEdits --output-format stream-json --verbose > R1.jsonl`
- 관찰: ① 서브에이전트 안에 Edit/Write 호출이 없는지(jq 3)) ② 서브에이전트 보고가 "수정할 수 없다"는 취지인지(jq 5)로 결과 내용 확인) ③ **메인이 대신 고쳤는지**(jq 2)에서 메인의 Edit 호출, `git diff --stat`).
- 변형: (a) `tools:` 줄을 지운 버전(전부 상속) → 서브에이전트 안에서 Edit가 일어나는지 (b) `tools:` 줄은 지우고 본문에 "절대 파일을 수정하지 않는다"만 둔 버전 → 지침만으로 막히는지(이 저장소의 code-reviewer와 같은 방식).
- 문서 기준 기대: 빠진 도구는 서브에이전트 세션에 아예 없어 권한 요청·오류 없이 그 도구 없이 일한다 [6]. 도구 제한은 클로드 코드가 강제한다 [4]. 메인이 대신 고칠지는 문서에 없음 → 결과를 그대로 기록(글의 핵심 교훈 후보: "도구 제한은 그 서브에이전트만 막는다").

**실험 3. description 모호 vs 구체 (자동 위임 비율)**

- 준비: `~/sa-lab/docs/`에 마크다운 3개를 만들고 그중 하나에 없는 파일로 가는 상대 링크(`[설명](./없는파일.md)`)를 넣는다.
- 에이전트 `.claude/agents/doc-checker.md` 두 버전(본문 동일, description만 교체):

```markdown
---
name: doc-checker
description: 마크다운 문서의 제목 구조와 깨진 상대 링크를 점검해 문제 목록만 보고하는 문서 점검 담당. 사용자가 문서 점검, 링크 확인, 목차 검사를 부탁할 때 사용한다. Use proactively for documentation checks.
tools: Read, Grep, Glob
model: inherit
---

보고 첫 줄에 [doc-checker 보고]라고 쓴다.
위임 메시지에 적힌 폴더의 마크다운 파일을 읽고, 깨진 상대 링크와 제목 단계가 건너뛴 곳을 "파일 | 줄 | 문제" 표로 보고한다. 파일은 고치지 않는다.
```

  모호 버전은 description만 `문서를 돕는다.`로 바꾼다.
- 프롬프트(에이전트 이름을 말하지 않음): `docs 폴더 마크다운 파일에 깨진 링크가 있는지 점검해 줘.`
- 조건: 구체 5회, 모호 5회. 자동 위임이 두 조건 모두 0이면 세 번째 조건으로 프롬프트 끝에 "알맞은 서브에이전트가 있으면 맡겨도 돼."를 붙여 각 5회(4-3의 위임 억제 지시 가능성 확인용).
- 측정: jq 1)에서 `subagent_type`이 `doc-checker`인 회수 / 다른 종류(Explore, general-purpose, fork) 회수 / 위임 없음. 마커는 메인이 요약하며 지울 수 있으니 판정은 tool_use 기준.
- 문서 기준 기대: 구체적이고 "use proactively"가 있는 쪽이 더 잘 골라진다 [1][6]. 보장은 아니다.
- 덤(선택): `@"doc-checker (agent)"`를 `-p` 프롬프트에 넣었을 때 모호 버전도 반드시 호출되는지(문서에 `-p` 동작 명시 없음).

**실험 4(선택). 내장 Explore는 CLAUDE.md를 안 읽는다**

- 준비: `~/sa-lab/CLAUDE.md`에 "서브에이전트를 포함한 모든 에이전트는 최종 보고 첫 줄에 [CLAUDE.md 읽음]이라고 쓴다." 한 줄.
- 실행: ① "Explore 서브에이전트로 backend 폴더 구조를 3줄로 요약해 줘" ② "doc-finder 서브에이전트로 같은 일" (각 3회, `--forward-subagent-text` 사용)
- 측정: Agent 결과(jq 5)의 실제 텍스트)에 마커가 있는지. 단, 메인이 위임 메시지에 규칙을 옮겨 적었을 수 있으니 Agent 도구 입력의 `prompt`에 마커 문구가 있는 회차는 따로 표시한다.
- 문서 기준 기대: doc-finder는 마커 있음(CLAUDE.md 로드), Explore는 없음 [1][2].

**실험 5(대화형, 선택). 인식 시점**

- 세션을 켠 채 기존 `.claude/agents/`에 새 파일 추가 → 몇 초 뒤 `@` 자동 완성에 뜨는지 [1].
- 세션 시작 때 없던 `~/.claude/agents/`(또는 새 프로젝트의 `.claude/agents/`)를 만들고 파일 추가 → 재시작 전에는 안 뜨는지 [1][6].
- `/agents` 입력 시 나오는 안내 문구 캡처 [1][11].

## 6. 참고 출처

| 번호 | 제목 | 발행처 | 발행·수정일 | 등급 | URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [1] | Create custom subagents (Subagents) | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람, 전문 116,045자 확인) | A | https://code.claude.com/docs/en/sub-agents |
| [2] | Extend Claude Code (기능 개요) | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/features-overview |
| [3] | Skills | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람, 서브에이전트 실행 절 확인) | A | https://code.claude.com/docs/en/skills |
| [4] | Best practices for Claude Code | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/best-practices |
| [5] | Manage costs effectively | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/costs |
| [6] | Subagents in the SDK | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/agent-sdk/subagents |
| [7] | Environment variables | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/env-vars |
| [8] | CLI reference | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/cli-reference |
| [9] | Run Claude Code programmatically (headless) | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/headless |
| [10] | Configure permissions | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/permissions |
| [11] | Commands | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/commands |
| [12] | Interactive mode | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/interactive-mode |
| [13] | Track cost and usage (Agent SDK) | Anthropic, Claude Code Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://code.claude.com/docs/en/agent-sdk/cost-tracking |
| [14] | Changelog | Anthropic, Claude Code Docs | 최신 항목 v2.1.312(2026-10-27). 앞 10만 자만 확인 | A | https://code.claude.com/docs/en/changelog |
| [15] | Steering Claude Code: when to use CLAUDE.md, skills, hooks, and subagents | Claude 블로그(Michael Segner, Anthropic) | 2026-06-18 | A | https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more |
| [16] | Prompting Claude Opus 5 | Anthropic, Claude Platform Docs | 수정일 표기 없음(2026-10-28 열람) | A | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 |
| 저장소 | 앞 글 최종본 3편, 미발행 원고 2건, `.claude/agents/*.md`, `CLAUDE.md` | 이 저장소 | 2026-10-28 확인 | - | `docs/final/claude-code-core-features/final.md`, `docs/final/claude-code-skills/final.md`, `docs/final/claude-code-permission-modes/final.md`, `docs/research/claude-code-subagent-team.md`, `docs/final/claude-code-subagent-team/final.md` |

## 7. 확인하지 못한 자료

- dev.classmethod.jp의 v2.1.302·v2.1.232 업데이트 해설 2건(포크 기본값 관련): 이 세션의 네트워크 허용 목록 밖이라 접속 실패(DNS 확인 불가). 열어 보려면 세션 네트워크 설정에서 `dev.classmethod.jp` 허용이 필요하다.
- daleseo.com의 한국어 서브에이전트 글: 같은 이유로 접속 실패. `daleseo.com` 허용 필요. 검색 결과 요약상 일부 한국어 글이 `/agents` 생성 화면(옛 방식)을 설명하는 것으로 보였으나, 원문을 열지 못해 근거로 쓰지 않았다.
- 검색 결과에만 보인 제3자 글(aiweekly, startdebugging, wmedia, tembo, wikidocs, joinleland, computingforgeeks 등): 같은 네트워크 제한이 예상되고, 공식 문서로 충분히 교차 확인되어 열지 않았다. 근거로 쓰지 않았다.
- 변경 이력 [14]의 앞 10만 자 이후(v2.1.298 이하): 분량(약 112만 자) 때문에 읽지 않았다. 해당 버전 정보는 문서 [1][7]의 버전 서술로 대신 확인했다.

## 용어 설명

[^1]: 컨텍스트 창: AI가 한 번에 기억하며 참고하는 대화·자료의 범위. 넘치면 오래된 내용을 요약(압축)한다.
[^2]: 프론트매터: 마크다운 파일 맨 위 `---`와 `---` 사이에 쓰는 설정 부분. YAML이라는 "이름: 값" 형식을 쓴다.
[^3]: 백그라운드: 내가 다른 일을 하는 동안 뒤에서 따로 도는 방식. 끝나면 결과가 알림처럼 대화에 도착한다. 반대는 포그라운드(끝날 때까지 기다림).
[^4]: 포크(fork): 지금까지의 대화를 통째로 복사한 서브에이전트. 설명을 다시 하지 않아도 되지만, 대신 '대화 기록을 모르는 격리'는 없다.
[^5]: 시스템 프롬프트: AI가 일을 시작하기 전에 받는 기본 지침. 서브에이전트 파일의 본문이 여기에 들어간다.
[^6]: Agent 도구: 메인 Claude가 서브에이전트를 띄울 때 쓰는 내부 도구. 예전 이름은 Task.
[^7]: camelCase: 여러 단어를 붙여 쓰되 두 번째 단어부터 첫 글자를 대문자로 쓰는 표기(예: `disallowedTools`). 철자·대소문자가 틀리면 설정이 조용히 무시된다.
[^8]: git 워크트리: 같은 저장소를 다른 폴더에 하나 더 펼쳐 놓은 작업 공간. 원래 폴더의 파일을 건드리지 않고 작업할 수 있다.
[^9]: 프롬프트 캐시: 같은 앞부분을 반복해서 보낼 때 다시 처리하지 않고 저장해 둔 것을 싸게 재사용하는 기능. 일정 시간이 지나면 사라진다.

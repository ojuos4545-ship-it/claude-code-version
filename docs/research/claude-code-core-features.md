# 리서치 노트: 클로드 코드(Claude Code)의 핵심 기능 5가지

- 조사일: 2026-10-27
- 기준 시점: 2026-10-27에 열어 본 공식 문서(code.claude.com/docs, claude.com/pricing). 문서에 발행일 표기가 없어 "조사일 기준 공개 상태"로 본다.
- 목적/독자: 네이버 블로그 정보·리뷰형 글. 독자는 처음 써보려는 초보 개발자·비개발자.
- [가정] 공식 문서가 "핵심 기능 5가지"를 직접 지정하지는 않는다. 5가지는 공식 문서의 분류를 근거로 내가 고른 것이다(Q1 참고).

## 1. 결론 요약
- [해석] 초보자가 먼저 익힐 5가지: (1) CLAUDE.md(프로젝트 기억), (2) 권한 모드·플랜 모드(안전하게 맡기기), (3) 슬래시 명령과 스킬(반복 작업 저장), (4) 서브에이전트(작업 분담), (5) MCP(외부 도구 연결). 훅은 "그다음 단계"로 소개하는 구성을 권한다.
- [사실] 공식 문서는 "CLAUDE.md부터 시작하고, 나머지는 필요한 때 추가하라"고 안내한다 [6].
- [사실] 설치는 한 줄 명령(네이티브 설치)이며, 터미널·VS Code·JetBrains·데스크톱 앱·웹에서 쓴다 [1][2]. Claude Pro·Max·Team·Enterprise 구독, Console 계정, 클라우드 제공자 중 하나가 필요하다 [2]. 무료 플랜에는 Claude Code가 포함되지 않는다고 요금 페이지에 나온다 [10].
- 최신 버전에서 바뀐 점: `/agents`는 마법사가 아니라 안내만 출력(v2.1.198부터), 커스텀 명령은 스킬로 통합, 터미널 기본 권한 모드가 auto(v2.1.283 이상) [5][9][4][12].

## 2. 질문별 조사 결과

### Q1. 공식 문서가 꼽는 핵심 기능과 초보자용 5가지
- [사실] 개요 페이지는 할 수 있는 일을 이렇게 묶는다: 반복 작업 자동화, 기능 구현·버그 수정, 커밋·PR, MCP로 도구 연결, 지침·스킬·훅으로 맞춤 설정, 병렬 에이전트·커스텀 에이전트, CLI 파이프·스크립트, 예약 작업, 어디서나 작업 [1].
- [사실] 확장 기능 안내 페이지는 CLAUDE.md, 출력 스타일, 스킬, 코드 인텔리전스, MCP, 서브에이전트, 동적 워크플로, 세션 간 메시징, 훅, 플러그인을 나열하고 "처음이면 CLAUDE.md부터"라고 한다 [6].
- [해석] 5가지 선정 기준: 초보자가 첫 주에 실제로 마주치고, 공식 문서가 기본 설정 대상으로 직접 다루며, 서로 역할이 겹치지 않는 것. 권한·플랜 모드는 확장 기능 목록에는 없지만 퀵스타트가 첫 코드 변경 단계에서 바로 안내하므로 포함했다 [2]. 훅·플러그인은 설정 난도가 높아 제외했다.
- 신뢰도: 보통(5가지 선정은 해석)

### Q2. 후보 기능별 정의·설정·최신 변경

**(1) CLAUDE.md와 자동 메모리**
- [사실] 매 세션이 빈 컨텍스트로 시작하므로, 지속 지침은 CLAUDE.md(내가 씀)와 auto memory(Claude가 스스로 메모)로 넘긴다 [3].
- [사실] 위치: 사용자 `~/.claude/CLAUDE.md`, 프로젝트 `./CLAUDE.md` 또는 `./.claude/CLAUDE.md`, 개인 프로젝트용 `./CLAUDE.local.md`(.gitignore 권장) [3].
- [사실] `/init`을 실행하면 코드베이스를 분석해 시작용 CLAUDE.md를 만든다. 이미 있으면 덮어쓰지 않고 개선안을 낸다 [3]. `/memory`로 편집·자동 메모리 켜고 끄기 [12].
- [사실] 파일당 200줄 이하 권장. `.claude/rules/`에 경로별 규칙을 나눌 수 있다 [3][6].
- [사실] 저장소에 `AGENTS.md`만 있어도 Claude Code가 읽는다. 둘 다 있으면 CLAUDE.md만 읽는다 [3].
- 신뢰도: 높음(문서 3곳 일치)

**(2) 권한 모드·플랜 모드**
- [사실] 모드: Manual(`default`, 읽기만 자동), Edit automatically(`acceptEdits`), Plan, Auto, Don't ask(`dontAsk`), Bypass permissions(`bypassPermissions`) [4].
- [사실] 세션 중 `Shift+Tab`으로 순환한다. 기본 순환은 default, acceptEdits, plan이고 auto·bypass는 사용 가능할 때만 추가된다 [4].
- [사실] 플랜 모드는 파일을 읽고 계획만 세우며 소스 편집은 차단한다. `Shift+Tab`, 프롬프트 앞 `/plan`, 또는 `claude --permission-mode plan`으로 진입한다. 계획 승인 시 "auto 모드로 진행 / 편집마다 수동 승인 / 계속 계획" 중 고른다 [4][12].
- [사실, 최신 변경] 터미널·VS Code 세션의 내장 기본값은 auto다(macOS·Linux·WSL v2.1.228 이상, 네이티브 Windows v2.1.233 이상). v2.1.283 이상은 모든 플랜·제공자에서 auto가 기본이고, 그 전에는 Pro·Max·Team에서 조건부였다 [4]. 모범사례 문서도 "새 터미널·VS Code 세션은 auto 모드로 시작하고 분류기가 위험한 작업을 검토한다"고 쓴다 [11].
- 신뢰도: 높음

**(3) 슬래시 명령과 스킬**
- [사실] `/`를 입력하면 쓸 수 있는 명령·스킬 목록이 뜬다 [2][12]. 명령은 메시지 맨 앞에 써야 인식된다 [12].
- [사실] 스킬은 `SKILL.md` 파일로, 위치는 개인 `~/.claude/skills/<이름>/SKILL.md`, 프로젝트 `.claude/skills/<이름>/SKILL.md` 등이다. 폴더 이름이 `/이름` 명령이 되고, 내가 `/이름`으로 부르거나 Claude가 설명을 보고 자동으로 불러온다 [9].
- [사실, 최신 변경] 예전 `.claude/commands/deploy.md`와 `.claude/skills/deploy/SKILL.md`는 둘 다 `/deploy`를 만들고 똑같이 동작한다. 기존 commands 파일은 계속 작동하며 새 작업에는 스킬 형식을 권장한다 [9].
- [사실] 기본 제공(번들) 스킬 예: `/doctor`, `/code-review`, `/batch`, `/debug`, `/loop`, `/verify` [9]. 그 밖의 기본 명령: `/clear`, `/compact`, `/resume`, `/rewind`(별칭 `/undo`), `/usage`, `/hooks`, `/memory` [12].
- [사실] 부작용이 있는 스킬은 `disable-model-invocation: true`로 내가 부를 때만 실행되게 한다 [6][9].
- 신뢰도: 높음

**(4) 서브에이전트**
- [사실] 독립된 컨텍스트 창, 별도 시스템 프롬프트, 제한된 도구를 가진 전문 AI 도우미. 결과 요약만 메인 대화로 돌아온다 [5][6].
- [사실] 만드는 법: Claude에게 "읽기 전용 코드 리뷰어 서브에이전트를 만들어줘"라고 요청하거나, `.claude/agents/`(프로젝트) 또는 `~/.claude/agents/`(전체 프로젝트)에 마크다운+YAML 프론트매터 파일을 직접 쓴다 [5]. 필수 필드는 `name`, `description` [5].
- [사실, 최신 변경] `/agents`는 이제 "Claude에게 요청하거나 파일을 직접 편집하라"는 안내를 출력한다. v2.1.197 이하에서는 생성·편집 마법사가 열렸다 [5][12].
- [사실] 기본 제공: Explore(읽기 전용 탐색), Plan, general-purpose 등. 호출은 자연어, `@"이름 (agent)"` 멘션, `claude --agent 이름` [5].
- 신뢰도: 높음

**(5) MCP**
- [사실] Model Context Protocol은 AI 도구를 외부 데이터·서비스에 연결하는 개방형 표준이다. 예: Google Drive 문서 읽기, Jira 티켓 갱신, Slack 데이터 [1].
- [사실] 추가: `claude mcp add --transport http <이름> <URL>`(원격, 권장), 로컬은 `--transport stdio ... -- <실행 명령>`. 범위는 local(기본), project(`.mcp.json`, 팀 공유), user [8].
- [사실, 최신 변경] `sse` 방식은 deprecated(지원 중단 예정)로 표시된다. 원격은 `http`를 쓴다 [8].
- [사실] 세션 안 `/mcp`로 연결 상태 확인과 OAuth 로그인, `claude mcp list`로 목록 확인 [8][6].
- 신뢰도: 높음

**(참고) 훅**
- [사실] 훅은 Claude Code 생명주기의 특정 시점에 실행되는 사용자 정의 셸 명령 등이다. LLM의 선택이 아니라 항상 실행되는 결정적 제어를 준다 [7].
- [사실] `~/.claude/settings.json`의 `hooks` 블록에 쓰며, 예시는 Claude가 입력을 기다릴 때 데스크톱 알림을 보내는 `Notification` 훅이다. `/hooks`로 등록 내용을 본다 [7][12].
- [사실] 차단형 훅은 종료 코드 2와 stderr 사유로 동작을 막는다(이벤트에 따라 차단 불가한 경우도 있음) [7].
- 신뢰도: 높음

### Q3. 장점과 한계

| 기능 | 장점 | 한계·주의 |
| :-- | :-- | :-- |
| CLAUDE.md | 매 세션 자동으로 프로젝트 규칙 적용 [3][6] | 강제 규칙이 아닌 "맥락"이다. 막아야 하면 PreToolUse 훅 [3]. 길면(200줄 초과) 준수율 하락, 상충 지침은 Claude가 임의로 고를 수 있음 [3] |
| 권한·플랜 모드 | 계획 먼저 확인, 매번 승인 피로 감소(auto) [4] | auto는 분류기 판단이라 안전 보장이 아님 [4][11]. bypass는 격리 환경 전용 [4]. `claude -p`는 모드 미지정 시 승인 필요한 호출이 거부됨 [4] |
| 스킬 | 반복 절차 저장, 사용 시에만 본문 로드 [6][9] | 설명이 매 요청 컨텍스트에 들어감, SKILL.md 500줄 이하 권장 [9]. 공유받은 저장소의 `allowed-tools`는 실행 전 검토 [9]. 철자 틀린 필드는 오류 없이 무시 [9] |
| 서브에이전트 | 메인 컨텍스트 보존, 도구 제한, 병렬 조사 [5] | 토큰 사용량 합산, 대화 기록 미전달, 잘못된 프론트매터는 조용히 무시 [5] |
| MCP | 외부 서비스와 직접 연동 [1][6] | 신뢰하지 않는 서버는 프롬프트 인젝션 위험 [8]. 도구 출력 10,000토큰 초과 시 경고, 기본 상한 25,000토큰 [8] |
| 훅 | 컨텍스트 비용 0(출력 반환 시 제외), 항상 실행 [6][7] | JSON 설정 난도, OS별 명령 차이(알림 명령이 macOS/Linux/Windows 다름) [7] |

- [사실] 기능을 많이 추가할수록 컨텍스트를 차지해 오히려 성능이 떨어질 수 있다고 공식 문서가 경고한다 [6].
- [해석] 초보자는 CLAUDE.md와 권한 모드만으로 시작해도 충분하고, 나머지는 같은 실수가 반복될 때 추가하는 순서가 공식 안내와 맞다 [6].

### Q4. 설치·요금·지원 환경
- [사실] 설치(권장 네이티브): macOS·Linux·WSL `curl -fsSL https://claude.ai/install.sh | bash`, Windows PowerShell `irm https://claude.ai/install.ps1 | iex`, Windows CMD는 별도 명령. 설치 후 새 터미널에서 `claude --version` [2]. Homebrew(`brew install --cask claude-code`), WinGet(`winget install Anthropic.ClaudeCode`)도 가능하며 이 둘은 자동 업데이트가 안 된다 [1][2].
- [사실] 시작: 프로젝트 폴더에서 `claude` 실행, 첫 사용 시 로그인. Windows 네이티브는 Git for Windows 권장(없으면 PowerShell을 셸 도구로 사용) [1][2].
- [사실] 계정: Claude Pro·Max·Team·Enterprise(권장), Claude Console(선불 API 크레딧), Bedrock·Google Cloud·Microsoft Foundry 등 [2]. 데스크톱 앱은 유료 구독 필수 [1].
- [사실] 지원 환경: 터미널 CLI, VS Code(Cursor 포함), JetBrains(CLI 별도 설치 필요), 데스크톱 앱(macOS, Windows x64/ARM64, Ubuntu·Debian은 베타), 웹(claude.ai/code)과 모바일 앱, Slack, GitHub Actions·GitLab CI/CD [1].
- [사실] 요금(claude.com/pricing, USD, 세금 제외, 페이지에 기준일 표시 없음): Free $0(Claude Code 미포함), Pro 월 $20(연간 결제 시 월 $17), Max 월 $100부터, Team Standard 좌석 월 $25(연간 $20), Premium 좌석 월 $125(연간 $100), Enterprise 별도. "Claude Code는 모든 유료 플랜에 포함"이라고 명시 [10].
- 신뢰도: 설치·환경 높음(문서 2곳 일치), 요금 보통(단일 출처, 기준일 불명)

## 3. 핵심 수치·사실 표
| 항목 | 내용 | 기준일 | 출처 |
| :-- | :-- | :-- | :-- |
| CLAUDE.md 권장 길이 | 파일당 200줄 이하 | 2026-10-27 열람 | [3][6] |
| 자동 메모리 로드량 | 세션 시작 시 첫 200줄 또는 25KB | 2026-10-27 열람 | [3] |
| 기본 권한 모드 | 터미널·VS Code는 auto (v2.1.283 이상 모든 플랜) | 2026-10-27 열람 | [4] |
| Shift+Tab 기본 순환 | default, acceptEdits, plan | 2026-10-27 열람 | [4] |
| `/agents` 동작 변경 | v2.1.197 이하는 마법사, 이후 안내 출력 | 2026-10-27 열람 | [5][12] |
| 서브에이전트 깊이·동시 실행 | 기본 3단계, 동시 20개 | 2026-10-27 열람 | [5] |
| SKILL.md 권장 길이 | 500줄 이하 | 2026-10-27 열람 | [9] |
| MCP 출력 경고/상한 | 10,000 / 25,000 토큰 | 2026-10-27 열람 | [8] |
| Pro 요금 | 월 $20(연간 결제 시 월 $17) | 기준일 표시 없음 | [10] |
| Max 요금 | 월 $100부터 | 기준일 표시 없음 | [10] |

## 4. 상충하거나 불확실한 내용
- "핵심 기능 5가지"의 공식 정의는 없다. 선정은 [해석]이며, 글에서도 "필자 기준"이라고 밝히는 편이 안전하다.
- 요금 페이지에 기준일이 없고, 한국 원화 가격·부가세 포함 여부는 확인하지 못했다. 한국 내 결제 금액은 직접 확인이 필요하다.
- 플랜별 사용량 한도(메시지 수 등)는 이번에 확인하지 않았다. `/usage` 명령으로 확인한다고만 문서에 나온다 [12].
- 한국어 입력·응답 품질, 한국어 공식 문서 유무는 확인하지 못했다.
- 서브에이전트 문서(약 116,000자), MCP 문서(약 151,000자), 스킬 문서(약 118,000자), 권한 모드 문서 뒷부분은 도구 한계로 앞 100,000자까지만 읽었다. 뒷부분에 추가 제한·변경이 있을 수 있다.
- 일부 요약(권한 모드, 서브에이전트, MCP, 스킬, 요금)은 열람 도구가 원문을 요약한 결과를 바탕으로 한다. 핵심 수치는 글에 쓰기 전에 원문 링크에서 재확인을 권한다.

## 5. 글쓰기 에이전트에게 (활용 가이드)

**핵심 메시지**
- "다 알 필요 없다. CLAUDE.md 하나와 권한 모드부터." 공식 안내도 CLAUDE.md부터 시작하라고 한다 [6].
- "AI에게 맡기되, 계획을 먼저 보고(플랜 모드), 되돌릴 수 있게(`/rewind`)" 쓰는 흐름 [4][12].

**FAQ 후보**
- 무료로 쓸 수 있나요? → 요금 페이지상 Free 플랜에는 Claude Code가 포함되지 않는다. Pro 이상 유료 플랜 또는 API 크레딧(Console)이 필요 [10][2].
- 터미널을 한 번도 안 써봤는데요? → 공식 터미널 가이드와 VS Code·데스크톱 앱 대안이 있다 [1][2].
- Windows에서도 되나요? → 된다. PowerShell/CMD 설치 명령이 있고 Git for Windows 권장 [2].
- 코드를 마음대로 고치지 않나요? → Manual 모드는 읽기만 자동, 플랜 모드는 편집 차단. 단 터미널 기본은 auto이므로 처음엔 `Shift+Tab`으로 모드를 확인하라고 안내 [4].
- 스킬과 서브에이전트 차이? → 스킬은 재사용 지침서(내 대화에 로드), 서브에이전트는 따로 일하고 요약만 돌려주는 일꾼 [6].

**비교 포인트**
- CLAUDE.md는 "항상 알아야 할 것", 스킬은 "가끔 필요한 절차", 훅은 "무조건 실행할 것" [6].

**연관 키워드·표현 후보**: 클로드 코드 설치, 클로드 코드 요금, CLAUDE.md 작성법, /init, 플랜 모드, Shift+Tab, 서브에이전트 만들기, MCP 연결, 스킬 만들기, 컨텍스트 창

**주의**
- "안전하다", "실수하지 않는다" 같은 단정 금지. auto 모드도 안전 보장이 아니라고 공식 문서가 쓴다 [4].
- 요금은 "조사일 기준 공식 페이지 표기"로 쓰고 변동 가능성을 밝힌다.
- 버전 번호(v2.1.xxx)는 빨리 바뀐다. 글에는 "최신 버전 기준"이라고만 쓰고 `claude --version` 확인을 안내한다.
- 훅의 알림 명령은 OS마다 다르니 예시를 쓰려면 원문 확인 [7].
- 옛 블로그·영상의 `/agents` 마법사 화면, `.claude/commands` 중심 설명, `sse` MCP 예시는 최신과 다르다.

**직접 경험으로 보강해야 할 부분** (리서치로 채울 수 없음)
- 실제 설치 과정에서 막힌 곳, 첫 로그인 화면
- CLAUDE.md를 넣기 전후 결과 차이, 플랜 모드로 얻은 계획의 체감
- 사용량 한도에 걸린 경험, 실제 월 결제 금액(원화)
- 서브에이전트·MCP를 써본 구체적 사례

## 6. 참고 출처
| 번호 | 제목 | 발행처 | 발행·수정일 | 등급 | URL |
| :-- | :-- | :-- | :-- | :-- | :-- |
| [1] | Overview | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/overview |
| [2] | Quickstart | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/quickstart |
| [3] | How Claude remembers your project | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/memory |
| [4] | Permission modes | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/permission-modes |
| [5] | Subagents | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/sub-agents |
| [6] | Extend Claude Code | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/features-overview |
| [7] | Automate actions with hooks | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/hooks-guide |
| [8] | Connect Claude Code to tools via MCP | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/mcp |
| [9] | Skills | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/skills |
| [10] | Pricing | Anthropic (claude.com) | 기준일 표시 없음(2026-10-27 열람) | A | https://claude.com/pricing |
| [11] | Best practices | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/best-practices |
| [12] | Commands | Anthropic 공식 문서 | 표기 없음(2026-10-27 열람) | A | https://code.claude.com/docs/en/commands |

## 7. 확인하지 못한 자료
- 언론·전문 매체(B 등급) 교차 확인은 하지 않았다. 모든 근거가 제작사 공식 자료(A)라 독립 검증은 없다.
- 공식 changelog(버전별 변경 이력)는 열지 않았다. 버전 번호는 권한 모드·서브에이전트 문서 본문에 적힌 값이다.
- 한국어 문서, 원화 요금, 플랜별 사용량 한도는 조사하지 못했다.
- 훅 레퍼런스(`/docs/en/hooks`) 전체 이벤트 목록은 열지 않았다.

## 용어 설명
- **CLAUDE.md**: 프로젝트 규칙을 적어 두면 Claude가 매번 처음에 읽는 메모 파일.
- **컨텍스트 창(context window)**: Claude가 한 번에 기억하며 볼 수 있는 대화·파일의 분량. 차면 성능이 떨어지거나 요약된다.
- **서브에이전트**: 메인 대화와 따로 일하고 요약만 돌려주는 보조 AI.
- **MCP**: AI 도구를 외부 서비스(Slack, Jira 등)에 연결하는 공통 규격.
- **훅(hook)**: 파일 수정 후 자동 정리처럼, 특정 순간에 반드시 실행되는 자동 명령.
- **프롬프트 인젝션**: 웹 문서 등에 숨은 악성 지시로 AI를 속이는 공격.
- **분류기(classifier)**: auto 모드에서 각 작업이 위험한지 판단하는 별도 모델.
- **PATH**: 터미널이 프로그램을 찾는 경로 목록. 설치 후 `claude`를 못 찾으면 여기에 추가해야 한다.

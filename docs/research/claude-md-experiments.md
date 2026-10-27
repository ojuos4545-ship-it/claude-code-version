# 실험 기록: CLAUDE.md 직접 써 보기 글의 '직접 해 본 결과'

- 실행일: 2026-10-27
- 도구: Claude Code 2.1.311, `claude -p "<질문>"` (대화 없이 한 번 실행하고 결과를 받는 방식)
- 환경: 클라우드 컨테이너(원격 실행). 전역 `~/.claude/CLAUDE.md` 없음(실험 오염 없음 확인).
- 연습 프로젝트: `index.html`, `style.css`, `app.js`, `old/legacy.js` (할 일 추가만 되는 HTML·CSS·JavaScript 예제, 재현용 파일은 아래 '재현' 참고)
- 한계: AI는 같은 질문에도 답이 달라질 수 있다. 아래는 각 1회(실험 5만 3회) 실행한 결과이고, 통계적 결론이 아니다. 글에는 "한 번 돌려 본 결과"라고 밝혔다.

## 실험 1. `/init` 초안 (글 3절)
- 방법: CLAUDE.md가 없는 연습 프로젝트에서 `claude -p "/init" --permission-mode acceptEdits`
- 결과: 약 15초, 17줄. 구역은 Overview / Structure / Conventions. 영어로 작성됨.
- 내용 요지: 빌드·린트·테스트 없음→`index.html`을 브라우저로 열기, `index.html`과 `app.js`가 같은 id(`task`, `add`, `list`)를 쓰니 한쪽을 바꾸면 양쪽 수정, 파일별 설명, `old/legacy.js`는 쓰지 않으니 건드리지 말 것, UI 문구는 한국어.
- 공식 권장(best-practices)에 비춰: 파일별 설명(Structure)은 코드에서 알 수 있어 삭제 후보, id 경고와 `old/` 메모는 남길 후보.

## 실험 2. `/context` 확인 (글 3절 6단계)
- 방법: 위 프로젝트에서 새 세션으로 `claude -p "/context"`
- 결과: Memory files 369토큰(0.0%), 경로에 프로젝트 `CLAUDE.md`가 표시됨. 전체 26.9k / 1m 토큰(3%).

## 실험 3. 쓰기 전/후 (글 1절)
- 방법: 프로젝트를 둘로 복사. 한쪽에만 글의 '예시 A' CLAUDE.md. 질문: "이 페이지를 고친 뒤에 화면이 잘 열리는지 확인하려면 어떻게 해야 해? 방법만 알려 줘." (`--allowedTools Read,Glob,Grep`)
- 없음: 확인 방법 5가지 나열(직접 열기, 로컬 서버, 개발자 도구, 화면 크기별 확인, 게시한 페이지 확인). 첫 문장은 "방법은 다음과 같습니다". 마지막은 "원하시면 직접 서버를 띄워 확인해 드릴 수도 있습니다".
- 있음: `python3 -m http.server 8000` → `localhost:8000` 하나로 4단계. 첫 문장이 결론. "이 프로젝트 규칙상 코드를 바꾼 뒤 같은 방법으로 확인하고 결과를 알려 드리겠다"고 파일의 규칙을 언급.

## 실험 4. 모호한 규칙 vs 구체적인 규칙 (글 4절)
- 방법: 같은 프로젝트 복사본 둘. 요청: "새로고침해도 할 일 목록이 남도록 저장 기능을 추가해 줘." (`--permission-mode acceptEdits`)
- 모호: CLAUDE.md "데이터는 적절하게 저장해" → `localStorage` 키 `todos`
- 구체: CLAUDE.md "할 일 목록은 localStorage의 `todo-items` 키에 JSON 배열로 저장한다" → 키 `todo-items`, 답변에 "CLAUDE.md 규칙을 따랐다"고 명시.

## 실험 5. 모순되는 규칙 (글 5절 3번)
- 방법: `CLAUDE.md`="답변은 한 줄로만 짧게 해", `.claude/rules/answer.md`="답변은 항목별로 나눠서 자세하게 설명해". 질문 "app.js가 하는 일을 설명해 줘." 3회.
- 1회: 항목별로 나누되 각 항목을 짧게 쓰는 절충. "어느 지침을 따를지 알려 달라"고 되물음(약 940자).
- 2회: 한 줄 답변(`CLAUDE.md` 쪽)을 따랐다고 밝힘(약 485자).
- 3회: 한 줄 답변(`CLAUDE.md` 쪽)을 따랐다고 밝힘(약 440자).
- 세 번 모두 충돌 사실을 스스로 알려 줌.

## 실험 6. 자동 메모리 (글 FAQ)
- 방법 A: "앞으로 이 프로젝트에서 패키지를 설치할 때는 npm 말고 항상 pnpm을 써 줘. 기억해 둬." (`acceptEdits`)
  - 결과: 자동 메모리 폴더(`~/.claude/projects/<프로젝트>/memory/`)는 생기지 않았고, 프로젝트 `CLAUDE.md`에 "Always use `pnpm` (not `npm`)..." 한 줄이 적힘.
- 방법 B: 질문 + "나는 답변에서 이모지를 싫어해서 앞으로도 쓰지 말아 줬으면 해."
  - 결과: 그 답변에서만 반영("이모지는 앞으로 쓰지 않겠습니다"). 파일·메모리 폴더 생성 없음.
- 공식 문서(memory)는 "기억해 달라고 하면 자동 메모리에 저장되고, CLAUDE.md에 넣으려면 'add this to CLAUDE.md'라고 말하라"고 설명한다. 이 환경에서는 다르게 보였다. 원인은 확인하지 못했다. 문서에는 일부 실행 환경에서 자동 메모리가 기본으로 꺼진다는 설명이 있다.

## 실험 7. 줄이기 효과 (글 5절 2번)
- 실험 1의 17줄 초안: Memory files 369토큰.
- 글의 기준대로 줄이고 한국어로 바꾼 7줄 버전: Memory files 180토큰(약 절반).

```markdown
# 프로젝트
- 연습용 할 일 목록 웹페이지 (HTML, CSS, JavaScript만 사용)
- 확인: index.html을 브라우저로 열기 (빌드·테스트 도구 없음)

# 주의
- index.html의 id(`task`, `add`, `list`)는 app.js와 짝이라, 바꾸면 두 파일을 함께 고친다
- `old/`는 쓰지 않는 예전 연습 코드라 건드리지 않는다
```

## 재현
1. 빈 폴더에 `index.html`(입력창 `#task`, 버튼 `#add`, 목록 `#list`), `style.css`, `app.js`(버튼 클릭 시 `<li>`를 목록에 추가), `old/legacy.js`(한 줄 주석)를 만든다.
2. 위 방법·질문을 그대로 `claude -p`로 실행한다. 결과 문장은 매번 조금씩 다를 수 있다.

## 재검증 메모 (공식 문서 대조, 2026-10-27)
- memory·best-practices 문서 원문과 글의 주장을 대조했다. 사실 오류는 없었다.
- 글의 4절 표는 공식 예시("Use 2-space indentation", "Run `npm test` before committing", "src/legacy/ is still live...", "Integration tests need DATABASE_URL set")를 한국어로 풀어 쓰거나 합친 것이라 글에 그렇게 밝혔다.
- "기억해 달라고 하면 자동 메모리에 저장"은 문서의 조건이라, FAQ 문장을 그 조건에 맞춰 고쳤다.
- AGENTS.md 직접 읽기는 v2.1.277 이상이고 일부 세션에서는 못 읽을 수 있다(그럴 때 `@AGENTS.md` 가져오기). 글은 "최신 버전 기준"으로 표현했다.

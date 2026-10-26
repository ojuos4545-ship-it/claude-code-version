# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 저장소 개요

애플리케이션 코드가 아니라 Claude Code 설정(현재는 커스텀 서브에이전트)을 보관하는 저장소다. 빌드, 린트, 테스트 명령은 없다.

## 구조

- `.claude/agents/<name>.md`: 프로젝트 범위 서브에이전트 정의. 파일 이름과 프론트매터의 `name`을 같게 맞춘다.
  - `code-reviewer.md`: 버그, 코딩 규칙, 성능을 점검하는 리뷰어. 기본은 읽기 전용이고, 지시에 수정이 포함될 때만 코드를 고친다.
  - `product-manager.md`: PRD 작성과 개발 일정 관리를 맡는 프로덕트 매니저. 읽기·쓰기 도구만 쓴다(Bash 없음). PRD는 기본으로 `docs/prd/<기능-이름>.md`에 저장한다.
  - `backend-developer.md`: 서버 아키텍처, API, 데이터 처리, 외부 연동, 보안·성능을 맡는 구현 담당.
  - `qa-engineer.md`: 직접 실행·테스트하며 기능, 에러 처리, 성능, 사용성을 검증한다. 테스트 코드만 쓰고 제품 코드는 지시 없이 고치지 않는다. 코드만 읽는 리뷰는 `code-reviewer`와 역할을 나눈다.
- 에이전트들은 PRD(`docs/prd/`)를 공통 기준으로 삼는다: product-manager가 쓰고, backend-developer가 구현하고, qa-engineer가 수용 기준으로 검증한다.

## 에이전트 파일 작성 규칙

- 프론트매터 필드는 `name`, `description`, `model`, `color`를 쓴다. `tools`를 생략하면 메인 대화의 모든 도구를 물려받는다.
- `description`은 메인 에이전트가 언제 위임할지 판단하는 근거이므로, 무엇을 하는지와 언제 호출하는지를 함께 적는다. 값에 `: `(콜론+공백)가 들어가면 YAML 파싱이 깨지니 피하거나 따옴표로 감싼다.
- 프롬프트와 보고서 형식은 한국어로 쓴다. 보고서는 결론 먼저, 전문 용어는 각주로 모으고, 제안에는 장단점을 함께 적는 사용자 선호를 따른다.
- 수정 후 프론트매터가 유효한지 확인한다:

  ```bash
  python3 -c "import re,yaml,sys; t=open(sys.argv[1],encoding='utf-8').read(); print(yaml.safe_load(re.match(r'^---\n(.*?)\n---\n',t,re.S).group(1)))" .claude/agents/code-reviewer.md
  ```

- 새로 추가하거나 고친 에이전트는 새 세션부터 인식된다. 모든 프로젝트에서 쓰려면 `~/.claude/agents/`에 복사한다.

# 블로그 이미지 생성 가이드 (image-guide.md)

> 이 문서는 블로그 글에 들어갈 이미지를 **HTML/CSS로 만들고 Playwright(파이썬)로 캡처**하기 위한 규칙집이다.
> 이미지가 들어갈 자리는 글의 `[IMAGE: 종류 | 설명: ...]` 마커가 정한다(SEO 가이드 7장). 이 문서는 그 마커를 실제 파일로 바꾸는 방법을 정한다.
> 규칙의 우선순위: **[필수] > [권장] > [선택]**

---

## 0. 한눈에 보는 핵심 규칙

1. **외부 API·외부 이미지·외부 폰트 금지.** HTML 한 장과 CSS만으로 그리고, Playwright로 캡처한다. 네트워크 요청은 막는다.
2. **마커 하나 = 이미지 하나.** 종류는 마커의 첫 칸(썸네일, 포인트카드, 다이어그램, 비교표) 그대로 따른다.
3. **글자는 짧게.** 한 장에 한 가지 메시지만 담는다. 긴 설명은 본문에 맡긴다.
4. **배경 톤은 본문과 맞춘다.** 따뜻한 중성색 바탕에 포인트 색 하나. 아래 색 토큰을 쓴다.
5. **폭은 1080px 고정.** 모바일에서 줄어들어도 읽히도록 글자는 크게 쓴다.
6. **만든 뒤 반드시 눈으로 확인한다.** 글자 깨짐(두부 문자), 잘림, 넘침을 확인하고 나서 넘긴다.

---

## 1. 이미지 규격 [필수]

| 종류 | 마커 이름 | 크기(px) | 비율 | 용도 |
| :--- | :--- | :--- | :--- | :--- |
| **대표 이미지** | `썸네일` | **1080 × 1080** | 1 : 1 (정방형) | 글 맨 위, 검색결과 썸네일 |
| **본문 이미지** | `포인트카드` | 1080 × 가변(540~1350) | 가로형~4 : 5 | 한 주제의 요점 3~5개 |
| | `다이어그램` | 1080 × 가변(540~1080) | 가로형~정방형 | 순서·구조·흐름 |
| | `비교표` | 1080 × 가변(540~1350) | 가로형~4 : 5 | 장단점·항목 비교 |

공통 규칙

* **파일 형식:** PNG 기본. 한 장이 **1MB**를 넘으면 JPEG(품질 90)로 저장한다. 무거운 이미지는 로딩을 늦춘다(SEO 가이드 7장).
* **배율:** 레이아웃 폭은 1080px 기준으로 설계하고, 캡처는 `device_scale_factor=2`(파일 폭 2160px)로 한다. 높이는 내용에 맞춰 540~1350px(레이아웃 기준) 안에서 정한다.
* **대표 이미지는 글당 1장.** 글에서 가장 먼저 나오는 이미지가 썸네일이어야 한다.
* **본문 이미지 개수:** 마커 개수만큼. 글 전체로 5~10장(썸네일 포함)이 SEO 가이드 기준이다.
* **원본성:** 직접 만든 이미지만 쓴다. 다른 사이트 이미지, 스톡 사진, 제품 로고는 넣지 않는다.

> 💡 **왜 글자를 크게 쓸까요?** 1080px 이미지는 휴대폰에서 폭 360~390px 정도로 줄어듭니다. 본문 글자 36px은 화면에서 약 13px이 됩니다. 36px 아래로 내려가면 모바일에서 읽기 힘듭니다.

---

## 2. 글자 규칙 [필수]

| 항목 | 규칙 |
| :--- | :--- |
| **최소 글자 크기** | 본문 **36px 이상**, 제목 56~84px, 보조 문구 32px까지 허용 |
| **한 장당 메시지** | 1개. 제목이 곧 결론이어야 한다 |
| **제목** | 공백 포함 **20자 이내**, 최대 2줄 |
| **항목 수** | 포인트카드 3~5개, 다이어그램 노드 3~5개, 비교표 3~5행 |
| **항목당 글자** | 공백 포함 **20자 이내**. 문장 대신 명사구로 끝낸다 |
| **문체** | 존댓말 문장 대신 짧은 명사구·명령 어미 없이. 마침표는 쓰지 않는다 |
| **명령어·코드** | `monospace`로 표시, 한 줄 **28자 이내**. 길면 핵심만 남긴다 |
| **숫자·사실** | 글 본문과 리서치 노트에 있는 것만. 이미지에서 새 수치를 만들지 않는다 |
| **이모지** | 쓰지 않는다 (폰트마다 다르게 그려져 톤이 흐트러진다) |

* 한 장에 글자가 너무 많아 보이면 **줄이는 것이 먼저**다. 글자 크기를 줄여 억지로 넣지 않는다.
* 키워드는 이미지 안의 글자가 아니라 **ALT/캡션**(마커의 설명)에 넣는다.

---

## 3. 색과 서체 [필수]

글 본문과 같은 차분하고 따뜻한 느낌으로 맞춘다. 아래 값을 CSS 변수로 그대로 쓴다.

| 토큰 | 값 | 쓰임 |
| :--- | :--- | :--- |
| `--bg` | `#FAF7F2` | 이미지 배경(따뜻한 아이보리) |
| `--card` | `#FFFFFF` | 카드·표 바탕 |
| `--ink` | `#1F2937` | 본문·제목 글자 |
| `--sub` | `#6B7280` | 보조 글자 |
| `--line` | `#E8E1D6` | 테두리·구분선 |
| `--accent` | `#C8553D` | 포인트(번호, 강조, 화살표). **한 장에 한 가지** |
| `--accent-soft` | `#F6E3DC` | 포인트 연한 배경 |
| `--ok` | `#2F6F5E` | 장점·완료 표시 |
| `--ok-soft` | `#DDEDE7` | 장점 연한 배경 |

* 한 장에 쓰는 색은 **배경 + 글자색 + 포인트 1~2개**까지.
* 그라데이션, 그림자 남발, 장식 도형은 쓰지 않는다. 여백과 정렬로 정리한다.
* 글자와 배경의 대비는 충분히 둔다(`--ink` on `--bg` 기준을 벗어나지 않는다).
* **서체:** 외부 웹 폰트는 내려받지 않는다. 저장소의 `tools/fonts/`에 든 Pretendard 서브셋(SIL OFL 1.1, KS X 1001 한글 2,350자)을 `tools/blog-image.css`가 불러온다. 캡처 스크립트가 이 파일을 자동으로 주입하고, 폰트가 안 불러와지면 `WARN`을 낸다. 서브셋에 없는 희귀 한글은 대체 폰트로 그려지니 눈으로 확인한다. 아래는 HTML 자체의 대체 목록이다.

```css
font-family: "Pretendard", "Noto Sans KR", "Noto Sans CJK KR", "Malgun Gothic",
             "Apple SD Gothic Neo", "NanumGothic", sans-serif;
```

* 실행 환경에 한글 폰트가 없으면 글자가 네모(두부 문자)로 나온다. `fc-list :lang=ko`로 확인하고, 없으면 `fonts-noto-cjk` 같은 한글 폰트를 먼저 설치한다. **네모가 보이는 결과는 절대 넘기지 않는다.**

---

## 4. 이미지 종류별 설계 [필수]

### 4-1. 썸네일 (1080 × 1080)

* 구성: **작은 라벨(주제) → 큰 제목 → 부제 → (선택) 번호 목록**
* 제목은 글 제목을 줄인 한 줄 약속("핵심 기능 5가지"처럼). 부제는 20자 이내.
* 번호 목록을 넣으면 5개 이내, 항목당 12자 이내.
* 안쪽 여백 **80px 이상**. 검색결과에서 가장자리가 잘려도 읽히게 한다.
* 가운데 정렬보다 **왼쪽 정렬**을 기본으로 한다.

### 4-2. 포인트카드

* 구성: **제목(결론) → 행 3~5개(라벨 + 값)**
* 라벨은 8자 이내, 값은 20자 이내. 명령어는 `monospace`.
* 맨 아래에 한 줄 보조 문구를 둘 수 있다(`--sub`, 선택).

### 4-3. 다이어그램

* 구성: **제목 → 노드(상자) 3~5개 + 화살표**
* 흐름은 위→아래 또는 왼쪽→오른쪽 하나로만. 선이 서로 교차하지 않게 한다.
* 노드는 이름(12자 이내) + 보조 문구 한 줄(14자 이내).
* 순서가 있으면 번호를 `--accent`로 붙인다.
* 실제 동작과 다른 그림을 그리지 않는다. 글 본문과 리서치 노트의 설명과 일치해야 한다.

### 4-4. 비교표

* 구성: **제목 → 2~3열 × 3~5행**
* 열 머리는 8자 이내, 셀은 20자 이내.
* 장점 열은 `--ok`, 주의점 열은 `--accent`로 구분한다. 색만으로 의미를 전하지 말고 열 머리에도 글자로 적는다.
* 행 구분은 얇은 선(`--line`)으로 한다.

---

## 5. 파일과 폴더 [필수]

```
docs/drafts/images/<주제-이름>/
  src/        HTML 원본 (수정·재생성용)
  01_thumbnail.png
  02_diagram_install.png
  03_card_claude-md.png
  ...
```

* **파일 이름:** `NN_종류_슬러그.png`. `NN`은 글 안에서 이미지가 나오는 순서(01부터). 종류는 영문(`thumbnail`, `card`, `diagram`, `table`), 슬러그는 영문 소문자와 하이픈.
* **HTML 원본도 남긴다.** 같은 이름의 `NN_종류_슬러그.html`을 `src/`에 두면 글이 바뀔 때 다시 만들 수 있다.
* **ALT/캡션:** 마커의 `설명:` 문장을 그대로 쓴다(키워드 1회 포함). 파일 이름에는 한글을 쓰지 않는다.

---

## 6. 제작 절차 [필수]

1. **마커 목록을 뽑는다.** 글 파일에서 `[IMAGE: ...]`를 순서대로 모두 찾는다.
2. **종류를 고른다.** 마커의 종류가 설계(4장)를 정한다. 맞지 않는 내용이면 종류를 바꾸지 말고 보고한다.
3. **글자를 먼저 줄인다.** 마커 설명과 해당 본문 구간에서 핵심 3~5개만 뽑아 2장 규칙대로 줄인다. 본문에 없는 내용은 넣지 않는다.
4. **HTML을 만든다.** 7장 기본 CSS와 템플릿에 글자만 채운다.
5. **캡처한다.** 8장 스크립트를 실행한다. 스크립트가 넘침·외부 요청을 검사한다.
6. **눈으로 확인한다.** 만들어진 PNG를 직접 열어 아래를 본다.
   * 글자가 네모로 나오지 않는가
   * 잘리거나 넘친 글자가 없는가
   * 글자 크기가 36px 이상인가
   * 글 본문 설명과 일치하는가
   * 파일이 1MB 이하인가
7. **고치고 다시 캡처한다.** 문제가 있으면 글자를 더 줄이고 다시 만든다.
8. **보고한다.** 만든 파일 목록, 각 파일의 ALT 문장, 확인 못 한 것(예: 폰트 대체)을 결론 먼저 짧게 적는다.

---

## 7. 기본 CSS와 템플릿

모든 이미지는 `.canvas` 요소 하나가 전부다. 캡처는 이 요소만 잘라낸다.

### 7-1. 공통 CSS (`<style>` 안에 그대로 넣는다)

```css
:root{--bg:#FAF7F2;--card:#FFFFFF;--ink:#1F2937;--sub:#6B7280;--line:#E8E1D6;
      --accent:#C8553D;--accent-soft:#F6E3DC;--ok:#2F6F5E;--ok-soft:#DDEDE7}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg)}
body{font-family:"Pretendard","Noto Sans KR","Noto Sans CJK KR","Malgun Gothic",
     "Apple SD Gothic Neo","NanumGothic",sans-serif;color:var(--ink);
     -webkit-font-smoothing:antialiased;word-break:keep-all;line-height:1.35}
.canvas{width:1080px;padding:80px;background:var(--bg)}
.square{height:1080px;display:flex;flex-direction:column;justify-content:center}
.kicker{font-size:36px;font-weight:600;color:var(--accent);margin-bottom:28px}
h1{font-size:84px;font-weight:800;line-height:1.2;letter-spacing:-1px}
h2{font-size:56px;font-weight:800;line-height:1.25;margin-bottom:48px}
.sub{font-size:40px;color:var(--sub);margin-top:28px}
code,.mono{font-family:ui-monospace,"SFMono-Regular",Menlo,Consolas,"Noto Sans Mono CJK KR",monospace;
           font-size:34px;background:var(--accent-soft);padding:2px 12px;border-radius:10px}
.num{display:inline-flex;align-items:center;justify-content:center;width:56px;height:56px;
     border-radius:50%;background:var(--accent);color:#fff;font-size:34px;font-weight:700;flex:none}
```

### 7-2. 썸네일 (`.square`)

```html
<div class="canvas square">
  <div class="kicker">클로드 코드</div>
  <h1>핵심 기능<br>5가지</h1>
  <div class="sub">처음이라면 이것부터</div>
</div>
```

### 7-3. 포인트카드

```html
<div class="canvas">
  <h2>CLAUDE.md는 프로젝트 메모장</h2>
  <div class="row"><span class="num">1</span><span>프로젝트 루트에 저장</span></div>
  <div class="row"><span class="num">2</span><code>/init</code><span>로 초안 생성</span></div>
  <div class="row"><span class="num">3</span><span>200줄 이하로 간결하게</span></div>
</div>
<style>.row{display:flex;align-items:center;gap:24px;font-size:44px;background:var(--card);
 border:2px solid var(--line);border-radius:24px;padding:28px 36px;margin-bottom:24px}</style>
```

### 7-4. 다이어그램 (왼쪽 → 오른쪽)

```html
<div class="canvas">
  <h2>시작은 3단계면 충분합니다</h2>
  <div class="flow">
    <div class="node"><span class="num">1</span><b>설치</b><small>명령 한 줄</small></div>
    <div class="arrow">→</div>
    <div class="node"><span class="num">2</span><b>확인</b><small>버전 보기</small></div>
    <div class="arrow">→</div>
    <div class="node"><span class="num">3</span><b>실행</b><small>폴더에서 시작</small></div>
  </div>
</div>
<style>.flow{display:flex;align-items:center;gap:16px}
.node{flex:1;display:flex;flex-direction:column;align-items:center;gap:14px;text-align:center;
 background:var(--card);border:2px solid var(--line);border-radius:24px;padding:36px 12px}
.node b{font-size:44px}.node small{font-size:32px;color:var(--sub)}
.arrow{font-size:56px;color:var(--accent);font-weight:700}</style>
```

(노드가 4~5개이면 위→아래 배치로 바꾼다. 가로로 넣어 글자를 줄이지 않는다.)

### 7-5. 비교표

```html
<div class="canvas">
  <h2>기능별 장점과 주의점</h2>
  <table>
    <tr><th>기능</th><th class="ok">장점</th><th class="no">주의점</th></tr>
    <tr><td>CLAUDE.md</td><td>설명 반복 감소</td><td>길면 효과 약화</td></tr>
    <tr><td>서브에이전트</td><td>역할 분리</td><td>설명이 부실하면 오작동</td></tr>
    <tr><td>MCP</td><td>외부 도구 연결</td><td>권한 범위 확인</td></tr>
  </table>
</div>
<style>table{width:100%;border-collapse:collapse;background:var(--card);
 border:2px solid var(--line);border-radius:24px;overflow:hidden;font-size:38px}
th,td{padding:28px 24px;text-align:left;border-bottom:2px solid var(--line)}
th{font-size:36px;background:var(--bg)}th.ok{color:var(--ok)}th.no{color:var(--accent)}
td:first-child{font-weight:700}tr:last-child td{border-bottom:none}</style>
```

---

## 8. Playwright 캡처 스크립트

설치: `pip install playwright` (브라우저가 이미 있으면 `playwright install`은 하지 않는다. 있는 크롬을 `CHROMIUM_PATH`로 지정한다.)

저장 위치는 `tools/make_blog_images.py`를 권장한다. 사용법:

```bash
python3 tools/make_blog_images.py docs/drafts/images/<주제-이름>/src docs/drafts/images/<주제-이름>
```

```python
#!/usr/bin/env python3
"""src 폴더의 HTML(.canvas 요소)을 PNG로 캡처한다. 외부 요청은 모두 막는다."""
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

WIDTH = 1080
MAX_BYTES = 1_000_000  # 넘으면 JPEG로 저장
BLOCK_EXTERNAL = re.compile(r"^https?://")

# .canvas 안에서 넘치거나 36px 미만인 글자를 찾는다 (코드 조각 제외 허용치 28px).
CHECK_JS = """
() => {
  const c = document.querySelector('.canvas');
  const problems = [];
  if (!c) return ['.canvas 요소가 없습니다'];
  if (Math.round(c.getBoundingClientRect().width) !== %d) problems.push('폭이 %d가 아닙니다');
  for (const el of c.querySelectorAll('*')) {
    if (el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflow !== 'visible')
      problems.push('넘침: ' + el.tagName + ' ' + (el.textContent || '').slice(0, 20));
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (hasText) {
      const size = parseFloat(getComputedStyle(el).fontSize);
      const mono = /mono|code/i.test(getComputedStyle(el).fontFamily) || el.tagName === 'CODE';
      if (size < (mono ? 28 : 32)) problems.push('글자가 작음(' + size + 'px): ' + el.textContent.trim().slice(0, 20));
    }
  }
  if (c.scrollWidth > c.clientWidth + 1) problems.push('캔버스 가로 넘침');
  return problems;
}
""" % (WIDTH, WIDTH)


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        path = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium")
        return p.chromium.launch(executable_path=path)


def main(src: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    failed = False
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={"width": WIDTH, "height": 1080}, device_scale_factor=1)
        page.route(BLOCK_EXTERNAL, lambda route: route.abort())  # 외부 API·폰트·이미지 차단
        for html in sorted(src.glob("*.html")):
            page.goto(html.resolve().as_uri())
            page.evaluate("document.fonts.ready")
            problems = page.evaluate(CHECK_JS)
            canvas = page.locator(".canvas")
            png = out / f"{html.stem}.png"
            canvas.screenshot(path=str(png))
            if png.stat().st_size > MAX_BYTES:
                jpg = png.with_suffix(".jpg")
                canvas.screenshot(path=str(jpg), type="jpeg", quality=90)
                png.unlink()
                png = jpg
            box = canvas.bounding_box()
            print(f"{'OK  ' if not problems else 'WARN'} {png.name} {int(box['width'])}x{int(box['height'])}"
                  f" {png.stat().st_size // 1024}KB")
            for msg in problems:
                print("   -", msg)
            failed |= bool(problems)
        browser.close()
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("사용법: make_blog_images.py <src 폴더> <출력 폴더>")
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
```

* 스크립트가 `WARN`을 내면 글자를 줄이거나 배치를 고친 뒤 다시 돌린다. `WARN`인 채로 넘기지 않는다.
* 스크립트는 넘침과 글자 크기만 검사한다. **두부 문자와 어색한 배치는 6장 6번처럼 눈으로 봐야 한다.**

---

## 9. 하지 말아야 할 것 [필수]

* 외부 이미지 생성 API, 스톡 사진, 외부 CDN·웹 폰트 사용
* 마커에 없는 이미지를 임의로 추가하거나, 마커 종류를 바꾸는 것
* 글 본문과 리서치 노트에 없는 수치·기능·화면을 이미지에 그리는 것 (특히 실제 화면을 흉내 낸 가짜 스크린샷)
* 제품 로고·브랜드 마크를 흉내 내는 것
* 36px 미만 글자, 한 장에 4개 이상의 색 포인트, 긴 문장 나열
* 두부 문자·잘림·넘침이 남은 상태로 넘기는 것
* 과장 문구("무조건", "100%")를 이미지 글자로 넣는 것

---

## 10. 작성 후 자가 점검 체크리스트

- [ ] 글의 `[IMAGE: ...]` 마커 개수와 만든 파일 개수가 같은가?
- [ ] 첫 이미지가 1080 × 1080 썸네일인가?
- [ ] 본문 이미지의 폭이 모두 1080px인가?
- [ ] 글자가 모두 36px 안팎 이상이고, 제목은 20자 이내인가?
- [ ] 한 장에 메시지가 하나뿐인가?
- [ ] 색 토큰만 사용했고, 포인트 색이 과하지 않은가?
- [ ] 외부 요청 없이 만들었는가?
- [ ] 두부 문자·잘림·넘침을 눈으로 확인했는가?
- [ ] 이미지 안 내용이 본문·리서치 노트와 일치하는가?
- [ ] 파일 이름이 `NN_종류_슬러그` 형식이고 1MB 이하인가?
- [ ] 마커 설명을 ALT/캡션으로 정리해 보고했는가?

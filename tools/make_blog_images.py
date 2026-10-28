#!/usr/bin/env python3
"""src 폴더의 HTML(.canvas 요소)을 PNG로 캡처한다. 외부 요청은 모두 막는다."""
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

WIDTH = 1080
SCALE = 2  # 2배 해상도로 캡처한다(레이아웃 폭은 그대로 1080px, 파일은 2160px)
CSS = Path(__file__).with_name("blog-image.css")
THEME_3D = Path(__file__).with_name("blog-image-3d.css")  # 기본 테마(라인+3D). --theme=flat 이면 적용하지 않는다
THEME_NEON = Path(__file__).with_name("blog-image-neon.css")  # --theme=neon: 다크 네온 3D(스타일은 HTML 안에 있고 폰트만 주입)
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
  if (c.scrollWidth > c.clientWidth + 1 && getComputedStyle(c).overflow === 'visible') problems.push('캔버스 가로 넘침');
  return problems;
}
""" % (WIDTH, WIDTH)


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        path = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium")
        return p.chromium.launch(executable_path=path)


def main(src: Path, out: Path, theme: str = "3d") -> int:
    out.mkdir(parents=True, exist_ok=True)
    failed = False
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={"width": WIDTH, "height": 1080}, device_scale_factor=SCALE)
        page.route(BLOCK_EXTERNAL, lambda route: route.abort())  # 외부 API·폰트·이미지 차단
        for html in sorted(src.glob("*.html")):
            page.goto(html.resolve().as_uri())
            base = THEME_NEON if theme == "neon" else CSS
            page.add_style_tag(content=base.read_text(encoding="utf-8").replace("url(\"fonts/", f'url("{base.parent.as_uri()}/fonts/'))
            if theme == "3d":
                page.add_style_tag(content=THEME_3D.read_text(encoding="utf-8"))
            page.evaluate("document.fonts.ready")
            if not page.evaluate("document.fonts.check('700 40px PretendardBlog', '한글')"):
                problems_font = ["Pretendard 폰트가 로드되지 않았습니다"]
            else:
                problems_font = []
            problems = problems_font + page.evaluate(CHECK_JS)
            canvas = page.locator(".canvas")
            png = out / f"{html.stem}.png"
            canvas.screenshot(path=str(png))
            if png.stat().st_size > MAX_BYTES:
                jpg = png.with_suffix(".jpg")
                canvas.screenshot(path=str(jpg), type="jpeg", quality=90)
                png.unlink()
                png = jpg
            box = canvas.bounding_box()
            print(f"{'OK  ' if not problems else 'WARN'} {png.name} {int(box['width'] * SCALE)}x{int(box['height'] * SCALE)}"
                  f" {png.stat().st_size // 1024}KB")
            for msg in problems:
                print("   -", msg)
            failed |= bool(problems)
        browser.close()
    return 1 if failed else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--theme=")]
    theme = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--theme=")), "3d")
    if len(args) != 2 or theme not in ("flat", "3d", "neon"):
        sys.exit("사용법: make_blog_images.py <src 폴더> <출력 폴더> [--theme=3d|flat|neon]")
    sys.exit(main(Path(args[0]), Path(args[1]), theme))

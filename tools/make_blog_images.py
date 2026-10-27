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

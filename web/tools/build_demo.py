"""서버 없이 도는 체험 모드 묶음을 만든다(claude.ai 아티팩트 등 정적 호스팅용).

사용: python3 web/tools/build_demo.py <출력 폴더>

- config.js의 demo를 true로 바꿔 demo-api.js(브라우저 저장소)로 동작하게 한다.
- index.html은 <body> 안쪽만 남기고 head 요소를 앞에 붙인다. 아티팩트 호스팅이 문서 뼈대를
  씌우기 때문이다. CSP meta는 빼고 호스팅 쪽 정책을 따른다(이 묶음은 서버와 통신하지 않는다).
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
FILES = ["app.js", "api.js", "demo-api.js", "styles.css"]


def build(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(WEB / name, out / name)

    config = (WEB / "config.js").read_text(encoding="utf-8")
    config, n = re.subn(r"demo:\s*false", "demo: true", config)
    if n != 1:
        raise SystemExit("config.js에서 'demo: false'를 찾지 못했다")
    (out / "config.js").write_text(config, encoding="utf-8")

    html = (WEB / "index.html").read_text(encoding="utf-8")
    title = re.search(r"<title>.*?</title>", html, re.S).group(0)
    body = re.search(r"<body>(.*)</body>", html, re.S).group(1)
    head = "\n".join(
        [
            '<meta charset="utf-8">',  # 호스팅이 인코딩을 안 알려 줘도 한글이 깨지지 않게
            title,
            '<meta name="claude:viewport-fit-sides" content="cover">',
            '<link rel="stylesheet" href="styles.css">',
            '<script type="module" src="app.js"></script>',
        ]
    )
    (out / "index.html").write_text(f"{head}\n{body.strip()}\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    build(Path(sys.argv[1]))
    print(f"built demo bundle in {sys.argv[1]}")

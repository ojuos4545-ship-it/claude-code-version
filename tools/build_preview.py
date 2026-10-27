#!/usr/bin/env python3
"""final.md로 네이버 에디터 복붙용 HTML을 만든다.

만드는 파일 (출력 폴더):
  preview.html    이미지가 보이는 미리보기 (이미지 내장)
  paste.html      복붙용. 이미지 자리는 `【사진 NN】 파일명` 표시로 대신한다
  upload-guide.md 사진을 넣을 위치·파일·ALT, 제목, 태그 정리

행간이 에디터에서 어긋나지 않도록 마크다운 원문의 줄 구조를 그대로 옮긴다.
  - 원문의 줄 하나 = <p> 하나 (CSS 여백 없음, <br> 없음)
  - 원문의 빈 줄 하나 = 빈 <p> 하나
에디터는 문단 여백·행간 CSS를 대부분 무시하므로, 줄 간격을 CSS로 만들지 않는다.

사용법: python3 tools/build_preview.py <final.md> <출력 폴더>
필요: pip install markdown
"""
import base64
import html
import re
import sys
from pathlib import Path

import markdown

IMG = re.compile(r"^!\[(.*?)\]\((.+?)\)\s*$")
TAGS = re.compile(r"^#[^\s#]")
HEADING = re.compile(r"^(#{1,3})\s+(.*)$")
TODO = re.compile(r"(\[(?:경험 보강 필요|이미지 없음)[^\]]*\])")
URL = re.compile(r"(?<![\"'>])(https?://[^\s<]+)")
SIZES = {2: 24, 3: 19}  # 네이버 에디터 글자 크기 단계에 맞춘다


def inline(text: str) -> str:
    """한 줄의 마크다운(굵게, 코드 등)을 HTML 조각으로."""
    text = re.sub(r"^(\d+)\.\s", r"\1\\. ", text)  # "1. "을 번호 목록으로 읽지 않게 한다
    out = markdown.markdown(text).strip()
    out = re.sub(r"^<p>(.*)</p>$", r"\1", out, flags=re.S)
    out = URL.sub(r'<a href="\1">\1</a>', out)
    return TODO.sub(r'<mark class="todo">\1</mark>', out)


def table(lines):
    t = markdown.markdown("\n".join(lines), extensions=["tables"])
    t = t.replace("<table>", '<table style="border-collapse:collapse;width:100%">')
    t = re.sub(r"<th(?: [^>]*)?>", '<th style="border:1px solid #ddd;padding:8px;background:#f3f3f3;text-align:left">', t)
    t = re.sub(r"<td(?: [^>]*)?>", '<td style="border:1px solid #ddd;padding:8px">', t)
    return t


def parse(md: str):
    """마크다운을 (종류, 내용) 블록 목록으로 나눈다. 빈 줄이 블록 경계다."""
    lines = md.splitlines()
    blocks, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
        elif ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            blocks.append(("code", lines[i + 1:j]))
            i = j + 1
        elif ln.strip() == "---":
            blocks.append(("hr", None))
            i += 1
        elif TAGS.match(ln):
            blocks.append(("tags", re.findall(r"#\S+", ln)))
            i += 1
        elif HEADING.match(ln):
            m = HEADING.match(ln)
            blocks.append((f"h{len(m.group(1))}", m.group(2)))
            i += 1
        elif IMG.match(ln):
            m = IMG.match(ln)
            blocks.append(("img", (m.group(1), m.group(2))))
            i += 1
        elif ln.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            blocks.append(("table", lines[i:j]))
            i = j
        elif ln.startswith(">"):
            j = i
            while j < len(lines) and lines[j].startswith(">"):
                j += 1
            blocks.append(("quote", [x.lstrip("> ").rstrip() for x in lines[i:j]]))
            i = j
        else:
            j = i
            while (j < len(lines) and lines[j].strip() and not lines[j].startswith(("```", "|", ">", "!["))
                   and lines[j].strip() != "---" and not HEADING.match(lines[j])):
                j += 1
            blocks.append(("lines", lines[i:j]))
            i = j
    return blocks


def list_text(ln: str) -> str:
    """목록 줄은 에디터마다 들여쓰기가 달라지므로 글머리 기호를 글자로 쓴다."""
    m = re.match(r"^\s*[*\-]\s+(.*)$", ln)
    if m:
        return "• " + m.group(1)
    m = re.match(r"^\s*(\d+)\.\s+(.*)$", ln)
    if m:
        return f"{m.group(1)}. {m.group(2)}"
    return ln


def render(blocks, images_dir: Path, mode: str):
    """mode: 'preview'(이미지 표시) 또는 'paste'(이미지 자리 표시)."""
    sp = '<p class="sp"><br></p>'
    out, n_img, title, tags = [], 0, "", []
    body_blocks = []
    for kind, data in blocks:
        if kind == "h1" and not title:
            title = data
        elif kind == "tags":
            tags = data
        else:
            body_blocks.append((kind, data))
    for idx, (kind, data) in enumerate(body_blocks):
        if idx:
            out.append(sp)
        if kind in ("h2", "h3"):
            size = SIZES[int(kind[1])]
            out.append(f'<p><span style="font-size:{size}px"><b>{inline(data)}</b></span></p>')
        elif kind == "hr":
            out.append("<hr>")
        elif kind == "lines":
            out += [f"<p>{inline(list_text(x))}</p>" for x in data]
        elif kind == "quote":
            out.append("<blockquote>" + "".join(f"<p>{inline(x)}</p>" for x in data) + "</blockquote>")
        elif kind == "code":
            out += [f'<p class="code">{html.escape(x) or "<br>"}</p>' for x in data]
        elif kind == "table":
            out.append(table(data))
        elif kind == "img":
            n_img += 1
            alt, path = data
            name = Path(path).name
            if mode == "preview":
                raw = (images_dir / name).read_bytes()
                mime = "image/jpeg" if name.endswith(".jpg") else "image/png"
                src = f"data:{mime};base64," + base64.b64encode(raw).decode()
                out.append(f'<p style="text-align:center"><span class="imgwrap"><span class="badge">사진 {n_img:02d}</span>'
                           f'<img src="{src}" alt="{html.escape(alt)}"></span></p>')
            else:
                out.append(f'<p style="text-align:center"><mark class="slot">【사진 {n_img:02d}】 {html.escape(name)}</mark></p>')
    return "\n".join(out), title, tags


CSS = """
body{margin:0;background:#fff;color:#333;font-family:"Noto Sans KR","Malgun Gothic","Apple SD Gothic Neo",sans-serif}
.preview-only{background:#03c75a;color:#fff;font-size:13px;padding:10px 14px;line-height:1.5}
.preview-only button{margin-left:10px;padding:4px 12px;border:0;border-radius:4px;background:#fff;color:#03c75a;font-weight:700;cursor:pointer}
.wrap{max-width:740px;margin:0 auto;padding:24px 20px 80px;box-sizing:border-box}
.title{font-size:26px;font-weight:700;line-height:1.4;color:#222;margin:0 0 6px}
.meta{color:#999;font-size:13px;margin-bottom:28px}
#body{font-size:15px;line-height:1.6;overflow-wrap:break-word}
#body p{margin:0;padding:0;line-height:1.6}
#body p.code{font-family:Consolas,Menlo,monospace;font-size:14px;background:#f6f6f6}
#body hr{border:0;border-top:1px solid #ccc;margin:0}
#body blockquote{margin:0;padding:10px 16px;border-left:4px solid #03c75a;background:#f4f7f5}
#body img{max-width:100%;height:auto}
.imgwrap{position:relative;display:inline-block;max-width:100%}
.badge{position:absolute;top:10px;left:10px;background:#03c75a;color:#fff;font-size:13px;font-weight:700;line-height:1;padding:6px 10px;border-radius:14px;box-shadow:0 1px 4px rgba(0,0,0,.25)}
#body code{font-family:Consolas,Menlo,monospace;font-size:.92em;background:#f3f3f3}
#body a{color:#0a7d3c;word-break:break-all}
mark.todo{background:#fff176}
mark.slot{background:#ffe082;font-weight:700}
.tags{margin-top:32px;font-size:13px;color:#555}
.tags span{display:inline-block;background:#f0f2f1;padding:3px 10px;border-radius:14px;margin:0 6px 6px 0}
@media(max-width:480px){.title{font-size:22px}}
"""

JS = """
document.getElementById('copy').onclick=function(){
  var r=document.createRange();r.selectNodeContents(document.getElementById('body'));
  var s=getSelection();s.removeAllRanges();s.addRange(r);
  var ok=document.execCommand('copy');s.removeAllRanges();
  this.textContent=ok?'복사됨':'복사 실패: 본문을 직접 선택하세요';
};
"""


def page(mode, body, title, tags):
    note = ("미리보기입니다. 이미지는 에디터에 붙지 않습니다. 복붙은 paste.html을 쓰세요." if mode == "preview"
            else "복붙용입니다. 아래 [본문 복사]를 누른 뒤 에디터에 붙여넣고, 【사진】 자리에 사진을 올리세요.")
    chips = "".join(f"<span>{html.escape(t)}</span>" for t in tags)
    return (f'<!DOCTYPE html>\n<html lang="ko"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><style>{CSS}</style></head><body>\n'
            f'<div class="preview-only">{note}<button id="copy" type="button">본문 복사</button></div>\n'
            f'<div class="wrap">\n<div class="title">{html.escape(title)}</div>\n'
            f'<div class="meta">카테고리 · 작성일 (제목은 에디터 제목 칸에 따로 입력)</div>\n'
            f'<div id="body">\n{body}\n</div>\n'
            f'<div class="tags">{chips}</div>\n</div>\n<script>{JS}</script></body></html>')


def guide(blocks, title, tags):
    """사진 업로드 체크리스트: 어느 문장 다음에 어떤 파일을 넣을지."""
    rows, prev, n = [], "", 0
    for kind, data in blocks:
        if kind == "lines":
            prev = data[-1].strip()
        elif kind in ("h2", "h3"):
            prev = data
        elif kind == "img":
            n += 1
            alt, path = data
            rows.append(f"| {n:02d} | `{Path(path).name}` | {re.sub(r'[*`|]', '', prev)[:40]} | {alt} |")
    return "\n".join([
        f"# 발행 체크리스트: {title}", "",
        "1. 에디터 **제목 칸**에 제목을 입력합니다.",
        "2. `paste.html`을 열어 [본문 복사] → 에디터 본문에 붙여넣습니다.",
        "3. 본문의 `【사진 NN】` 자리마다 아래 파일을 올리고, 표시 줄은 지웁니다.",
        "4. 사진마다 대체 텍스트(ALT)를 넣습니다. 첫 사진(01)은 대표 사진으로 지정합니다.",
        "5. 태그 칸에 아래 태그를 입력합니다.", "",
        "| 순서 | 파일 | 바로 앞 문장(위치) | ALT |",
        "| :--- | :--- | :--- | :--- |", *rows, "",
        "**태그:** " + " ".join(f"`{t}`" for t in tags), ""])


def main(src: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    blocks = parse(src.read_text(encoding="utf-8"))
    images_dir = src.parent / "images"
    for mode in ("preview", "paste"):
        body, title, tags = render(blocks, images_dir, mode)
        (out / f"{mode}.html").write_text(page(mode, body, title, tags), encoding="utf-8")
    (out / "upload-guide.md").write_text(guide(blocks, title, tags), encoding="utf-8")
    print("만든 파일:", ", ".join(["preview.html", "paste.html", "upload-guide.md"]), "->", out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("사용법: build_preview.py <final.md> <출력 폴더>")
    main(Path(sys.argv[1]), Path(sys.argv[2]))

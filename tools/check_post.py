#!/usr/bin/env python3
"""블로그 글(.md)이 스타일·SEO 가이드의 기계적으로 점검 가능한 규칙을 지키는지 본다.

사용법: python3 tools/check_post.py docs/drafts/<글>.md
점검: 제목 길이, 본문 줄 길이(폭 환산 40자), 5문장 이상 문단, 이모지 개수, 과장 표현,
      이미지 마커 수, 대제목 수, 마무리(정리·격려·댓글)와 태그. 규칙 위반이 있으면 종료 코드 1.
"""
import re
import sys
import unicodedata
from pathlib import Path

MAX_LINE = 40  # 폭 환산 글자 수(스타일 가이드 6장 5번)
SKIP_LINE = re.compile(r"^\s*(#|\||!\[|---|\[IMAGE|\[경험)|https?://")
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")
BANNED = ["무조건", "100%", "반드시 성공", "절대 실패"]


def width(s: str) -> float:
    """한글 등 전각 1, 영문·숫자 0.56, 공백 0.3, 기호 0.35로 폭을 환산한다."""
    t = 0.0
    for c in s:
        if unicodedata.east_asian_width(c) in "WF":
            t += 1.0
        elif c == " ":
            t += 0.3
        elif c in ".,:;!?()'\"·/":
            t += 0.35
        else:
            t += 0.56
    return t


def main(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    problems, notes = [], []

    title = lines[0][2:] if lines and lines[0].startswith("# ") else ""
    if not 25 <= len(title) <= 35:
        problems.append(f"제목 {len(title)}자 (권장 25~35자): {title}")

    in_code, long_lines, paragraphs, cur = False, [], [], []
    for no, ln in enumerate(lines, 1):
        if ln.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not ln.strip():
            if cur:
                paragraphs.append(cur)
                cur = []
            continue
        if SKIP_LINE.match(ln) or "http" in ln or re.match(r"^#\S", ln.strip()):
            if cur:
                paragraphs.append(cur)
                cur = []
            continue
        plain = re.sub(r"^\s*(>\s*|[*\-]\s+|\d+\.\s+)", "", ln)
        plain = re.sub(r"[`*]", "", plain)
        w = width(plain)
        if w > MAX_LINE:
            long_lines.append((no, w, plain))
        if not re.match(r"^\s*(>|[*\-]\s|\d+\.\s|\*\*Q)", ln):
            cur.append(plain)
    if cur:
        paragraphs.append(cur)

    if long_lines:
        problems.append(f"{MAX_LINE}자 초과 줄 {len(long_lines)}개")
        for no, w, plain in long_lines:
            notes.append(f"  {no}행 ({w:.0f}자): {plain[:46]}…")

    for p in paragraphs:
        joined = " ".join(p)
        if len(p) > 4 or len(re.findall(r"[.?!](?=\s|$)", joined)) >= 5:
            problems.append(f"5문장 이상/5줄 이상 문단: {joined[:40]}…")

    emojis = EMOJI.findall(text)
    if not 4 <= len(emojis) <= 6:
        problems.append(f"이모지 {len(emojis)}개 (권장 4~6개)")
    for w_ in BANNED:
        if w_ in text:
            problems.append(f"과장 표현 '{w_}' 포함")

    markers = len(re.findall(r"\[IMAGE:", text))
    if not 5 <= markers <= 10:
        problems.append(f"이미지 마커 {markers}개 (권장 5~10개)")
    h2 = [l for l in lines if l.startswith("## ")]
    if not 3 <= len(h2) <= 7:
        problems.append(f"대제목 {len(h2)}개 (핵심 3~5개 + 준비·마무리 등)")
    if "## " in text and not any("마무리" in l for l in h2):
        problems.append("마무리 섹션이 없음")
    tags = [l for l in lines if re.match(r"^#[^\s#]", l)]
    tagn = len(re.findall(r"#\S+", tags[-1])) if tags else 0
    if not 5 <= tagn <= 10:
        problems.append(f"태그 {tagn}개 (권장 5~10개)")
    if "[경험 보강 필요" in text:
        notes.append("  참고: [경험 보강 필요] 마커가 남아 있음")

    print(f"{path.name}: 공백 제외 {len(re.sub(r'\\s', '', text))}자, 이미지 {markers}개, 이모지 {len(emojis)}개, 태그 {tagn}개")
    print("OK: 모든 점검 통과" if not problems else "문제 " + str(len(problems)) + "건")
    for p in problems:
        print(" -", p)
    for n in notes:
        print(n)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("사용법: check_post.py <글.md>")
    sys.exit(main(Path(sys.argv[1])))

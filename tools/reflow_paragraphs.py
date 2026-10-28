"""문장 하나 = 한 줄로 쓴 본문을, 문단 단위(한 줄 = 한 문단)로 다시 묶고 문단 사이에 빈 줄을 넣는다.
목록·표·제목·코드·인용·이미지 마커·태그 줄은 건드리지 않는다."""
import re, sys
MAX_CHARS, MAX_SENT, SHORT = 170, 3, 60

def is_text(line):
    s = line.strip()
    if not s: return False
    if re.match(r'^(#|\||\* |- |\d+\. |>|```|\[IMAGE|---|!\[)', s): return False
    if re.match(r'^\*\*.*\*\*$', s): return False          # 굵은 소제목 줄(예: **1) ...**, **Q. ...**)
    return True

def sentences(s):
    return len(re.findall(r'[.?!](?=\s|$|["\')])', s)) or 1

src = open(sys.argv[1], encoding='utf-8').read().split('\n')
out, i, in_code = [], 0, False
while i < len(src):
    line = src[i]
    if line.strip().startswith('```'):
        in_code = not in_code; out.append(line); i += 1; continue
    if in_code or not is_text(line):
        out.append(line); i += 1; continue
    block = []
    while i < len(src) and is_text(src[i]) and not src[i].strip().startswith('```'):
        block.append(src[i].strip()); i += 1
    paras, cur = [], ''
    for b in block:
        if cur and len(cur) + 1 + len(b) <= MAX_CHARS and sentences(cur) + sentences(b) <= MAX_SENT:
            cur += ' ' + b
        else:
            if cur: paras.append(cur)
            cur = b
    paras.append(cur)
    # 짧은 문단(한 줄도 안 차는 문장)은 앞 문단에 붙인다
    merged = []
    for p in paras:
        if merged and len(p) < SHORT and len(merged[-1]) + 1 + len(p) <= MAX_CHARS + 60:
            merged[-1] += ' ' + p
        else:
            merged.append(p)
    paras = merged
    # 바로 앞이 굵은 질문 줄(**Q. ...**)이면 붙여 둔다(빈 줄 없이)
    for k, p in enumerate(paras):
        if k: out.append('')
        out.append(p)
print('\n'.join(out), end='')

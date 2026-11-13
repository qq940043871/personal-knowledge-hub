# -*- coding: utf-8 -*-
"""技术库重排收尾机械脚本（默认 dry-run，--apply 才写盘）：
1. 缺 H1 的文件：用文件名补一个 H1（仅 tiny/记录型短文适用，长文说明在报告里）
2. tiny（<1200 字符）文件：折叠 3+ 连续空行、删除 feishu 死链行
3. 所有非导航文件：文末追加《技术知识库 · 卷名》尾注（幂等，已有则跳过）
"""
import io
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
APPLY = "--apply" in sys.argv

HUB = Path(r"D:\ai_person\personal-knowledge-hub")
ROOT = HUB / "library" / "技术"
h1_pat = re.compile(r"(?m)^# \S")
feishu_line = re.compile(r"(?m)^\s*!\[[^\]]*\]\(https?://(?:www\.)?feishu\.cn/file/[^)]+\)\s*\n")

fixed_h1, fixed_blank, dropped_link, added_note = [], [], 0, []

for f in sorted(ROOT.rglob("*.md")):
    rel = f.relative_to(HUB).as_posix()
    name = rel.rsplit("/", 1)[-1]
    vol = rel.split("/")[2]
    is_nav = name == "README.md" or "/" not in rel[len("library/技术/"):]
    text = f.read_text(encoding="utf-8", errors="replace")
    orig = text
    # 1. H1
    if not h1_pat.search(text):
        title = name[:-3].strip() or vol
        text = f"# {title}\n\n" + text
        fixed_h1.append(rel)
    # 2. tiny 机械清理
    if len(text) < 1200 and not is_nav:
        new = feishu_line.sub("", text)
        if new != text:
            dropped_link += len(feishu_line.findall(text))
            text = new
        new = re.sub(r"\n{4,}", "\n\n", text)
        if new != text:
            fixed_blank.append(rel)
            text = new
    # 3. 尾注
    if not is_nav and "本文属《技术知识库" not in text:
        text = text.rstrip("\n") + f"\n\n---\n> 🏷️ 本文属《技术知识库 · {vol}》，重排于 2026-11。\n"
        added_note.append(rel)
    if text != orig and APPLY:
        f.write_text(text, encoding="utf-8", newline="\n")

print(f"H1 补齐: {len(fixed_h1)}", *fixed_h1, sep="\n  - ")
print(f"tiny 空行折叠: {len(fixed_blank)}")
print(f"feishu 死链删除行: {dropped_link}")
print(f"尾注追加: {len(added_note)}")
print("MODE:", "APPLIED" if APPLY else "DRY-RUN")

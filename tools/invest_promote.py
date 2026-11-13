# -*- coding: utf-8 -*-
"""短行提升为小节：短行(<=16字无句末标点)后紧跟以 表现/结果/特点/核心/注意/建议/条件/原则 开头的行 → 提升为 ##
只处理含"本文属《投资知识库"的文件。"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\ai_person\personal-knowledge-hub\library\投资")
VOLS = ["01-我的实盘与成长史", "02-交易心理与悟道", "03-交易系统与实战战法",
        "04-游资与高手实录", "07-新手学习路线"]

NEXT_MARK = ("表现", "结果", "特点", "核心", "注意", "建议", "条件", "原则", "要求", "目的")

def promote(lines):
    out = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if (
            s and len(s) <= 16
            and not s.endswith(("。", "！", "？", "：", ":", "，", ",", "；"))
            and not re.match(r"^#{1,6} ", s)
            and not s.startswith(("|", "!", "- ", "+", "`", ">"))
            and i + 1 < n
            and next((lines[j].strip() for j in range(i + 1, min(i + 4, n)) if lines[j].strip()), "").startswith(NEXT_MARK)
        ):
            if out and out[-1] != "":
                out.append("")
            out.append("## " + s)
            out.append("")
            i += 1
            continue
        out.append(ln)
        i += 1
    return out

count = 0
for vol in VOLS:
    for f in sorted((ROOT / vol).glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "本文属《投资知识库" not in text:
            continue
        body = text.split("本文属《投资知识库")[0]
        footer = text[len(body):]
        new_lines = promote(body.split("\n"))
        new_body = "\n".join(new_lines)
        if new_body != body:
            f.write_text(new_body + footer, encoding="utf-8")
            count += 1
print(f"短行提升: {count} 篇")

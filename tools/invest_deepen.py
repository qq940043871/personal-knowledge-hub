# -*- coding: utf-8 -*-
"""投资知识库规则化深排（只动结构，不动文字）：
1. 超长纯文本段落（>150字）按句号边界拆为 2~3 句一段，句子逐字保留；
2. 独立的编号行（1. / 一、 / 第X章… 短行无句末标点）提升为 ## 小节；
3. 跳过代码块、表格、已有标题、图片行。
只处理含"本文属《投资知识库"的文件（机械规范化过的）。
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\ai_person\personal-knowledge-hub\library\投资")
VOLS = ["01-我的实盘与成长史", "02-交易心理与悟道", "03-交易系统与实战战法",
        "04-游资与高手实录", "07-新手学习路线"]

SENT_END = "。！？；！？"
MAX_CHUNK = 110  # 每段最大字符数


def split_para(para: str) -> list:
    """按句号拆段，句子逐字保留，chunk <= MAX_CHUNK"""
    sents = re.findall(r"[^。！？；]*[。！？；]?", para)
    sents = [s for s in sents if s.strip()]
    if not sents:
        return [para]
    chunks, cur = [], ""
    for s in sents:
        if len(cur) + len(s) <= MAX_CHUNK or not cur:
            cur += s
        else:
            chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    return chunks if len(chunks) > 1 else [para]


def is_heading_like(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 24:
        return False
    if s.endswith(("。", "！", "？", ":", "：", "，", ",")):
        return False
    if re.match(r"^#{1,4} ", s):
        return False
    if re.match(r"^(1[.、)]|[2-9][.、)]|\d{2,}[.、)]|[一二三四五六七八九十]+[、.]|第[一二三四五六七八九十\d]+[章节篇部分条点]|[（(]\d+[)）])\s*\S", s):
        return True
    return False


def process(text: str) -> str:
    lines = text.split("\n")
    out = []
    in_fence = False
    for ln in lines:
        if ln.strip().startswith("```"):
            in_fence = not in_fence
            out.append(ln)
            continue
        if in_fence or ln.strip().startswith("|") or ln.strip().startswith("!["):
            out.append(ln)
            continue
        # 编号行提升为小节
        if is_heading_like(ln):
            out.append("")
            out.append("## " + ln.strip())
            out.append("")
            continue
        out.append(ln)
    # 拆长段落
    paras = "\n".join(out).split("\n\n")
    res = []
    for p in paras:
        stripped = p.strip()
        if len(stripped) > 150 and not any(
            stripped.startswith(x) for x in ("#", "|", "!", ">", "- ", "+", "`", "*")
        ) and stripped.count("。") >= 2:
            res.append("\n\n".join(split_para(stripped)))
        else:
            res.append(p)
    return "\n\n".join(res)


count = 0
for vol in VOLS:
    for f in sorted((ROOT / vol).glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "本文属《投资知识库" not in text:
            continue
        # 只处理正文（页脚之前）
        body = text.split("本文属《投资知识库")[0]
        footer = text[len(body):]
        new_body = process(body)
        if new_body != body:
            f.write_text(new_body + footer, encoding="utf-8")
            count += 1
print(f"规则化深排完成: {count} 篇")

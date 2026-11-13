# -*- coding: utf-8 -*-
"""投资知识库剩余文章的机械规范化（零语义改动）：
- 无 H1 的文件从文件名构造 H1（去序号前缀/广告【】段/_笔记后缀）
- `+ ` 列表统一为 `- `
- 标题/图片/表格/代码块/分割线前后空行规整；压缩连续空行
- 删除机器分隔行"-- 以下为AI生成的图文笔记内容 --"
- 文末统一追加元信息
只处理不含"本文属《投资知识库"的文件（已处理过的不动）。
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\ai_person\personal-knowledge-hub\library\投资")
VOLS = ["01-我的实盘与成长史", "02-交易心理与悟道", "03-交易系统与实战战法",
        "04-游资与高手实录", "06-选股基金与量化", "07-新手学习路线"]


def title_from_name(name: str) -> str:
    t = name[:-3] if name.endswith(".md") else name
    t = re.sub(r"【[^】]*】", "", t)  # 广告段
    t = re.sub(r"^\d+[-.]", "", t)  # 序号前缀
    t = re.sub(r"_笔记$", "", t)
    return t.strip()


def ensure_blank_before(lines, i, need=("##", "###", "####")):
    """i 行是标题/图片/表格/代码/分割线时，若前一行非空则插空行"""
    if i == 0 or lines[i - 1].strip():
        lines.insert(i, "")
        return True
    return False


def normalize(text: str) -> str:
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        # 删机器分隔行
        if ln.strip().startswith("-- 以下为AI生成的图文笔记内容"):
            i += 1
            continue
        # + 列表 → - 列表
        if ln.startswith("+ ") or ln == "+":
            ln = ln.replace("+ ", "- ", 1) if ln.startswith("+ ") else "-"
        # 空行压缩（保留至多 1 个）
        if ln == "" and out and out[-1] == "":
            i += 1
            continue
        out.append(ln)
        i += 1
    lines = out
    # 规整：标题/图片/表格/代码/分割线前后空行
    out = []
    for idx, ln in enumerate(lines):
        s = ln.strip()
        is_heading = s.startswith(("#", "##", "###", "####")) and re.match(r"^#{1,4} \S", s)
        is_img = s.startswith("![")
        is_table = s.startswith("|")
        is_fence = s.startswith("```")
        is_hr = s in ("---", "***", "___")
        if is_heading or is_img or is_table or is_fence or is_hr:
            if out and out[-1] != "":
                out.append("")
        out.append(ln)
    # 文件尾去多余空行
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


count = 0
for vol in VOLS:
    for f in sorted((ROOT / vol).glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "本文属《投资知识库" in text:
            continue
        had_h1 = re.search(r"(?m)^# \S", text) is not None
        text = normalize(text)
        lines = text.rstrip("\n").split("\n")
        if not had_h1:
            title = title_from_name(f.name)
            # 防止文件名构造出空标题
            if not title:
                title = f.stem
            lines.insert(0, f"# {title}")
            text = "\n".join(lines) + "\n"
        # 文末元信息
        footer = f"> 🏷️ 本文属《投资知识库 · {vol}》，重排于 2026-11。"
        if footer not in text:
            text = text.rstrip("\n") + "\n\n---\n" + footer + "\n"
        f.write_text(text, encoding="utf-8")
        count += 1
print(f"机械规范化完成: {count} 篇")

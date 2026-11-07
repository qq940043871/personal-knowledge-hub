# -*- coding: utf-8 -*-
"""腾讯文档导出的 docx -> markdown 保真转换（python-docx，未润色）。

用法: python -I tools/docx2md.py <源目录> <输出目录>
只处理 *.docx；输出同名 .md；标题/段落/列表/表格按序转换。
每篇头部加溯源说明（源文件相对链接 + 在线原稿）。
"""
import sys
from pathlib import Path

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

# 在线原稿链接（来自 腾讯文档导出/导出清单.md）
ONLINE_LINKS = {
    "02-范围管理": "https://docs.qq.com/doc/DSVFxeUJEc3hGZURa",
    "03-进度管理": "https://docs.qq.com/doc/DSURzRm1NS3F0R3pl",
    "04-成本管理": "https://docs.qq.com/doc/DSU5PbGVwb1BtZ0Ru",
    "05-质量管理": "https://docs.qq.com/doc/DSWFsRnZGR2ZaZnZy",
    "06-资源管理": "https://docs.qq.com/doc/DSVlEeGxwSXJTbmFE",
    "07-沟通管理": "https://docs.qq.com/doc/DSW5iY1REQWNCSkNX",
    "08-风险管理": "https://docs.qq.com/doc/DSUdIcXVCamJ4RWtD",
    "09-采购管理": "https://docs.qq.com/doc/DSXhPeFBWV0hGU1hY",
    "10-干系人管理": "https://docs.qq.com/doc/DSXJXSGNObnpFTUpV",
}

HEAD_STYLES = ("heading", "标题")


def iter_blocks(doc):
    """按文档顺序产出段落与表格。"""
    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            yield Paragraph(child, doc)
        elif tag == "tbl":
            yield Table(child, doc)


def para_to_md(p: Paragraph):
    text = p.text.strip()
    if not text:
        return ""
    style = (p.style.name or "").lower()
    for i, h in enumerate(("heading 1", "heading 2", "heading 3",
                           "heading 4", "heading 5", "heading 6"), start=1):
        if style == h:
            return "#" * i + " " + text
    # 中文样式名兜底：标题 1 / 标题 2
    for i in range(1, 7):
        if style == f"标题 {i}":
            return "#" * i + " " + text
    pPr = p._p.pPr
    if pPr is not None and pPr.numPr is not None:
        return "- " + text
    return text


def table_to_md(t: Table):
    rows = []
    for row in t.rows:
        cells = [" ".join(c.text.split()) or " " for c in row.cells]
        rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [" "] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |",
           "| " + " | ".join(["---"] * width) + " |"]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def convert(path: Path, out_dir: Path, rel_to_root: str):
    doc = docx.Document(str(path))
    parts = []
    for block in iter_blocks(doc):
        if isinstance(block, Paragraph):
            md = para_to_md(block)
        else:
            md = table_to_md(block)
        parts.append(md)
    body = "\n\n".join(x for x in parts if x).strip() + "\n"

    stem = path.stem
    online = ONLINE_LINKS.get(stem, "")
    src_link = f"../../../考证/腾讯·职场进阶/项目管理师/软考论文/{path.name}"
    header = (
        f"> 📄 本文由腾讯文档导出的 docx 原样转换（2026-11-07，python-docx，未润色）。\n"
        f"> 原文件：[{src_link.split('/')[-1]}]({src_link})"
        + (f" ｜ [在线原稿]({online})" if online else "")
        + "\n\n"
    )
    out = out_dir / (stem + ".md")
    out.write_text(header + body, encoding="utf-8")
    print(f"转换 {path.name} -> {out.name}（{len(body)} 字符）")


def main():
    src_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(src_dir.glob("*.docx"))
    if not files:
        print("未找到 docx 文件")
        sys.exit(1)
    for f in files:
        convert(f, out_dir, None)
    print(f"完成：{len(files)} 篇 -> {out_dir}")


if __name__ == "__main__":
    main()

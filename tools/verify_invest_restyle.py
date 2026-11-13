# -*- coding: utf-8 -*-
"""投资知识库重排验收：图片引用完整性 / H1 覆盖 / SVG 合法性 / 篇幅塌缩检查。

用法：python -I tools/verify_invest_restyle.py
基线：tools/_restyle_manifest.json（重排前生成）。
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\ai_person\personal-knowledge-hub\library\投资")
MANIFEST = Path(r"D:\ai_person\personal-knowledge-hub\tools\_restyle_manifest.json")
VOLS = ["01-我的实盘与成长史", "02-交易心理与悟道", "03-交易系统与实战战法",
        "04-游资与高手实录", "05-宏观与行业底层逻辑", "06-选股基金与量化", "07-新手学习路线"]

base = json.loads(MANIFEST.read_text(encoding="utf-8"))
img_pat = re.compile(r"!\[[^\]]*\]\([^)]+\)")
svg_pat = re.compile(r"<svg\b.*?</svg>", re.S)

problems = []
stats = {"checked": 0, "h1_missing": [], "img_lost": [], "img_extra": [],
         "svg_bad": [], "shrunk": [], "footer_missing": 0}

for vol in VOLS:
    for f in sorted((ROOT / vol).glob("*.md")):
        rel = str(f)
        text = f.read_text(encoding="utf-8", errors="replace")
        stats["checked"] += 1
        old = base.get(rel)
        if old is None:
            problems.append(f"[基线缺失] {rel}")
            continue
        # 1. H1
        if not re.search(r"(?m)^# \S", text):
            stats["h1_missing"].append(rel)
        # 2. 图片引用：不得丢失；允许出现的既有引用之外的图（不应发生）
        now_imgs = img_pat.findall(text)
        old_set, now_set = set(old["img_refs"]), set(now_imgs)
        lost = old_set - now_set
        if lost:
            stats["img_lost"].append(f"{rel} 丢失{len(lost)}: {sorted(lost)[:2]}")
        extra = now_set - old_set
        if extra:
            stats["img_extra"].append(f"{rel} 多出{len(extra)}")
        # 3. SVG 合法性
        for i, m in enumerate(svg_pat.finditer(text)):
            try:
                ET.fromstring(m.group(0))
            except ET.ParseError as e:
                stats["svg_bad"].append(f"{rel} 第{i+1}张SVG: {e}")
        # 4. 篇幅塌缩（重排后 chars < 基线 60% 视为可疑）
        if len(text) < old["chars"] * 0.6 and old["chars"] > 200:
            stats["shrunk"].append(f"{rel}: {old['chars']} -> {len(text)}")
        # 5. 文末元信息
        if "本文属《投资知识库" not in text:
            stats["footer_missing"] += 1

print(f"检查文件数: {stats['checked']}")
print(f"H1 缺失: {len(stats['h1_missing'])}")
for x in stats["h1_missing"][:20]:
    print("  -", x)
print(f"图片丢失: {len(stats['img_lost'])}")
for x in stats["img_lost"][:20]:
    print("  -", x)
print(f"图片多出: {len(stats['img_extra'])}")
for x in stats["img_extra"][:10]:
    print("  -", x)
print(f"SVG 解析失败: {len(stats['svg_bad'])}")
for x in stats["svg_bad"][:20]:
    print("  -", x)
print(f"篇幅塌缩(<60%): {len(stats['shrunk'])}")
for x in stats["shrunk"][:20]:
    print("  -", x)
print(f"文末元信息缺失: {stats['footer_missing']}")
if problems:
    print("其他问题:", *problems, sep="\n  ")

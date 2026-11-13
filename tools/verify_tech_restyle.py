# -*- coding: utf-8 -*-
"""技术知识库重排验收：图片引用完整性 / H1 覆盖 / SVG 合法性 / 篇幅塌缩 / 尾注。

用法：python -I tools/verify_tech_restyle.py
基线：tools/_tech_restyle_manifest.json（重排前由 tech_restyle_prep.py 生成）。
允许的差异：feishu.cn 死链图片引用被删除（规范 1.3 明确要求）。
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HUB = Path(r"D:\ai_person\personal-knowledge-hub")
ROOT = HUB / "library" / "技术"
MANIFEST = HUB / "tools" / "_tech_restyle_manifest.json"

base = json.loads(MANIFEST.read_text(encoding="utf-8"))
img_pat = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
svg_pat = re.compile(r"<svg\b.*?</svg>", re.S)
feishu_re = re.compile(r"^https?://(?:www\.)?feishu\.cn/file/")

VOLNAME = lambda rel: rel.replace("\\", "/").split("/")[2]

problems = []
stats = {"checked": 0, "h1_missing": [], "img_lost": [], "img_extra": [],
         "svg_bad": [], "svg_many": [], "shrunk": [], "footer_missing": []}

for f in sorted(ROOT.rglob("*.md")):
    rel = f.relative_to(HUB).as_posix()
    b = base.get(rel)
    if b is None:
        problems.append(f"[基线缺失] {rel}")
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    stats["checked"] += 1
    # 1. H1
    if not re.search(r"(?m)^# \S", text):
        stats["h1_missing"].append(rel)
    # 2. 图片引用：非 feishu 引用不得丢失；feishu 死链允许删除
    old_real = [r for r in b["img_refs"] if not feishu_re.match(r)]
    now_imgs = img_pat.findall(text)
    now_set, old_set = set(now_imgs), set(old_real)
    lost = old_set - now_set
    if lost:
        stats["img_lost"].append(f"{rel} 丢失{len(lost)}: {sorted(lost)[:2]}")
    extra = now_set - old_set - {r for r in b["img_refs"]}
    if extra:
        stats["img_extra"].append(f"{rel} 多出{len(extra)}")
    # 3. SVG 合法性
    svgs = list(svg_pat.finditer(text))
    for i, m in enumerate(svgs):
        try:
            ET.fromstring(m.group(0))
        except ET.ParseError as e:
            stats["svg_bad"].append(f"{rel} 第{i+1}张SVG: {e}")
    if len(svgs) > 5:
        stats["svg_many"].append(f"{rel}: {len(svgs)}张")
    # 4. 篇幅塌缩（允许删除 feishu 死链行；重排后 < 预期 60% 且 >200 字符可疑）
    expect = b["chars"] - b["feishu_chars"]
    if len(text) < expect * 0.6 and expect > 200:
        stats["shrunk"].append(f"{rel}: {b['chars']}->{len(text)} (预期≥{int(expect*0.6)})")
    # 5. 尾注（README/卷根导航文件不要求）
    name = rel.rsplit("/", 1)[-1]
    parts = rel.split("/")
    is_nav = name == "README.md" or (len(parts) == 4 and name in ("00-总纲.md", "00-总览.md"))
    if not is_nav and "本文属《技术知识库" not in text:
        stats["footer_missing"].append(rel)

print(f"检查文件数: {stats['checked']}")
for k, label in (("h1_missing", "H1 缺失"), ("img_lost", "图片丢失"),
                 ("img_extra", "图片多出"), ("svg_bad", "SVG 解析失败"),
                 ("svg_many", "SVG 数量异常(>5)"), ("shrunk", "篇幅塌缩(<60%)"),
                 ("footer_missing", "尾注缺失")):
    v = stats[k]
    print(f"{label}: {len(v)}")
    for x in v[:25]:
        print("  -", x)
if problems:
    print("其他问题:", *problems, sep="\n  ")
green = all(len(stats[k]) == 0 for k in stats) and not problems
print("== 验收结果:", "全绿 ✅" if green else "存在问题 ❌")

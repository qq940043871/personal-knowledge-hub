# -*- coding: utf-8 -*-
"""技术库重排准备：基线清单 + 分组分批。

用法：python -I tools/tech_restyle_prep.py
产出：
  tools/_tech_restyle_manifest.json   基线（chars/img_refs/feishu 统计）
  tools/_tech_restyle_batches.json    批次列表（mode + 显式文件路径清单）
  tools/_tech_restyle_report.txt      分组统计
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\ai_person\personal-knowledge-hub\library\技术")
TOOLS = Path(r"D:\ai_person\personal-knowledge-hub\tools")
VOLS = ["17年技术经验总结", "飞书·人工智能", "飞书·飞天闪客", "从0到1设计计算机"]

svg_pat = re.compile(r"<svg\b", re.I)
img_pat = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
feishu_pat = re.compile(r"!\[[^\]]*\]\(https?://(?:www\.)?feishu\.cn/file/[^)]+\)")

# 纯导航文件：不处理（不补图、不加尾注）
def is_excluded(rel_ws: str) -> bool:
    name = rel_ws.rsplit("/", 1)[-1]
    if name == "README.md":
        return True
    parts = rel_ws.split("/")
    if len(parts) == 4 and name in ("00-总纲.md", "00-总览.md"):  # 卷根直下的导航
        return True
    return False

all_files = sorted(p for p in ROOT.rglob("*.md"))
manifest, groups = {}, {"deep17": [], "light17": [], "tiny17": [], "ai": [], "flash": [], "pc": [], "excluded": []}

for f in all_files:
    rel_ws = f.relative_to(ROOT.parent.parent).as_posix()  # library/技术/<卷>/...
    text = f.read_text(encoding="utf-8", errors="replace")
    imgs = img_pat.findall(text)
    fe = feishu_pat.findall(text)
    feishu_chars = sum(len(m.group(0)) for m in feishu_pat.finditer(text))
    manifest[rel_ws] = {
        "chars": len(text),
        "img_refs": imgs,
        "feishu_count": len(fe),
        "feishu_chars": feishu_chars,
    }
    vol = rel_ws.split("/")[2]
    if is_excluded(rel_ws):
        groups["excluded"].append(rel_ws)
        continue
    has_svg = bool(svg_pat.search(text))
    if vol == "17年技术经验总结":
        if has_svg:
            groups["light17"].append(rel_ws)
        elif len(text) < 1200:
            groups["tiny17"].append(rel_ws)
        else:
            groups["deep17"].append(rel_ws)
    elif vol == "飞书·人工智能":
        groups["ai"].append(rel_ws)
    elif vol == "飞书·飞天闪客":
        groups["flash"].append(rel_ws)
    elif vol == "从0到1设计计算机":
        groups["pc"].append(rel_ws)

(TOOLS / "_tech_restyle_manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

# 分批：deep/light/ai/flash 按 mode 决定批大小；超长文件（>30000 字符）独占一批
SIZE = {"deep17": 10, "light17": 20, "ai": 10, "flash": 10, "pc": 8}
MODE = {"deep17": "deep", "light17": "light", "ai": "deep", "flash": "deep", "pc": "light"}
batches = []
for key in ("deep17", "light17", "ai", "flash", "pc"):
    files = sorted(groups[key])
    mode = MODE[key]
    size = SIZE[key]
    big, rest = [], []
    for r in files:
        (big if manifest[r]["chars"] > 30000 else rest).append(r)
    n = 0
    for r in big:
        n += 1
        batches.append({"id": f"{key}-big{n:02d}", "mode": mode, "files": [r]})
    for i in range(0, len(rest), size):
        n += 1
        batches.append({"id": f"{key}-{n:02d}", "mode": mode,
                        "files": rest[i:i + size]})

(TOOLS / "_tech_restyle_batches.json").write_text(
    json.dumps(batches, ensure_ascii=False, indent=1), encoding="utf-8")

lines = ["=== 技术库重排准备报告 ==="]
for k in ("deep17", "light17", "tiny17", "ai", "flash", "pc", "excluded"):
    lines.append(f"{k}: {len(groups[k])} 篇")
lines.append(f"总文件: {len(all_files)}  批次: {len(batches)}")
lines.append(f"feishu 死链总数: {sum(m['feishu_count'] for m in manifest.values())}")
tiny_note = "\n".join(groups["tiny17"][:50])
lines.append("\n--- tiny17 清单（机械处理，不进 agent）---\n" + tiny_note)
lines.append("\n--- excluded 清单 ---\n" + "\n".join(groups["excluded"]))
(TOOLS / "_tech_restyle_report.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))

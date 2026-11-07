# -*- coding: utf-8 -*-
"""library/ 成品层拆分进六大知识库（2026-11-07 第三步重组）。

思路：先按旧布局计算所有受影响 md 的新内容（链接经 MOVE_MAP 重算相对层级），
再执行目录搬移，最后落盘新内容 —— 避免搬移后解析基准错位。
路径口径：一律为仓库根相对（含 library/ 前缀）。

用法: python tools/reorg_library_split.py
"""
import os
import re
from pathlib import Path
from urllib.parse import unquote

WS = Path(__file__).resolve().parent.parent
LIB = WS / "library"

TECH_DIRS = [
    "17年技术经验总结", "AI常用类库指南", "ClaudeCode学习指南", "FFmpeg学习指南",
    "Java框架全景图", "Java避坑指南", "Kafka学习指南", "Linux学习指南",
    "MiniIO学习指南", "Nginx学习指南", "Openclaw学习指南", "OpenCV学习指南",
    "OS_Tutorial", "Redis学习指南", "Zookeeper学习指南", "大模型工具全景图",
    "手写JVM", "手写Web容器", "手写大模型", "手写操作系统", "手写数据库",
    "手写浏览器", "手写消息中间件", "手写游戏引擎", "技术文档体系",
]
KB = "library/"
DIR_MOVES = {KB + d: KB + "技术/" + d for d in TECH_DIRS}
DIR_MOVES.update({
    KB + "实际工作项目": KB + "工作/实际工作项目",
    KB + "码农打怪升级小说": KB + "创作/码农打怪升级小说",
    KB + "考证与项目管理/软考论文": KB + "考证/软考论文",
})
MOC_DIR = KB + "投资/00-七册MOC"
FILE_MOVES = {
    KB + "投资与交易/README.md": KB + "投资/README.md",
    KB + "工作与项目/README.md": KB + "工作/README.md",
    KB + "考证与项目管理/README.md": KB + "考证/README.md",
}
for p in sorted((LIB / "投资与交易").glob("0*.md")):
    if p.name != "README.md":
        FILE_MOVES[KB + f"投资与交易/{p.name}"] = f"{MOC_DIR}/{p.name}"

LINK_RE = re.compile(r"\]\(<?([^)>]*?)>?\)")
MOVE_ROOT = {**DIR_MOVES, **FILE_MOVES}  # 旧根相对 → 新根相对（目录级+文件级）


def build_file_map():
    fmap = {}
    for old, new in DIR_MOVES.items():
        for f in (WS / old).rglob("*"):
            if f.is_file():
                rel = f.relative_to(WS / old).as_posix()
                fmap[f"{old}/{rel}"] = f"{new}/{rel}"
    fmap.update(FILE_MOVES)
    return fmap


def resolve(base: Path, target: str):
    p = (base / target).resolve()
    try:
        return p.relative_to(WS).as_posix()
    except ValueError:
        return None


def map_target(resolved, fmap):
    if resolved is None:
        return None
    if resolved in fmap:
        return fmap[resolved]
    for old, new in MOVE_ROOT.items():
        if resolved == old or resolved.startswith(old + "/"):
            return new + resolved[len(old):]
    return None


def rewrite(md_old_rel: str, text: str, fmap):
    md_new_rel = fmap.get(md_old_rel, md_old_rel)
    new_dir = (WS / md_new_rel).parent
    out, pos, changed = [], 0, 0
    for m in LINK_RE.finditer(text):
        raw = m.group(1)
        if raw.startswith(("http://", "https://", "mailto:", "#")):
            continue
        decoded = unquote(raw)
        resolved = resolve((WS / md_old_rel).parent, decoded)
        new_root = map_target(resolved, fmap)
        if new_root is None:
            continue
        had_angle = text[m.start():m.start() + 3].endswith("(<")
        had_encode = "%" in raw
        new_rel = Path(os.path.relpath(WS / new_root, start=new_dir)).as_posix()
        if had_encode:
            new_rel = new_rel.replace(" ", "%20")
        out.append(text[pos:m.start()])
        out.append("]" + ("(<" + new_rel + ">)" if had_angle else "(" + new_rel + ")"))
        pos = m.end()
        changed += 1
    out.append(text[pos:])
    return "".join(out), md_new_rel, changed


def main():
    fmap = build_file_map()
    print(f"搬移文件 {len(fmap)} 个（目录已展开到文件级）")
    rewritten = {}
    total = 0
    for f in sorted(LIB.rglob("*.md")):
        old_rel = f.relative_to(WS).as_posix()
        text = f.read_text(encoding="utf-8")
        new_text, new_rel, changed = rewrite(old_rel, text, fmap)
        if changed:
            rewritten[old_rel] = (new_rel, new_text)
            total += changed
    print(f"链接重写 {total} 处，涉及 {len(rewritten)} 个文件")
    for old, new in sorted(DIR_MOVES.items(), key=lambda x: -len(x[0])):
        (WS / new).parent.mkdir(parents=True, exist_ok=True)
        (WS / old).rename(WS / new)
    for old, new in FILE_MOVES.items():
        (WS / new).parent.mkdir(parents=True, exist_ok=True)
        (WS / old).rename(WS / new)
    for old_rel, (new_rel, content) in rewritten.items():
        target = WS / new_rel
        if not target.is_file():
            raise SystemExit(f"[中止] 重写目标不存在: {new_rel}")
        target.write_text(content, encoding="utf-8", newline="")
    print(f"[完成] 搬移落盘 + {total} 处链接按新层级写入")


if __name__ == "__main__":
    main()

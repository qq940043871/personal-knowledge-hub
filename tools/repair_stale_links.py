# -*- coding: utf-8 -*-
"""成品拆分后修复"文件搬了但链接没跟着降/升层级"的存量链接。

判定：新位置解析不存在 且 旧位置解析存在 → 按旧目标重算相对层级。
WS 由 __file__ 定位，不依赖 cwd。
"""
import os
import re
from pathlib import Path
from urllib.parse import unquote

WS = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\]\(<?([^)>]*?)>?\)")
KB = "library/"
TECH = ["17年技术经验总结", "AI常用类库指南", "ClaudeCode学习指南", "FFmpeg学习指南",
        "Java框架全景图", "Java避坑指南", "Kafka学习指南", "Linux学习指南",
        "MiniIO学习指南", "Nginx学习指南", "Openclaw学习指南", "OpenCV学习指南",
        "OS_Tutorial", "Redis学习指南", "Zookeeper学习指南", "大模型工具全景图",
        "手写JVM", "手写Web容器", "手写大模型", "手写操作系统", "手写数据库",
        "手写浏览器", "手写消息中间件", "手写游戏引擎", "技术文档体系"]
DIR_MOVES = {KB + d: KB + "技术/" + d for d in TECH}
DIR_MOVES.update({
    KB + "实际工作项目": KB + "工作/实际工作项目",
    KB + "码农打怪升级小说": KB + "创作/码农打怪升级小说",
    KB + "考证与项目管理/软考论文": KB + "考证/软考论文",
})
MOC_FILES = {p.name for p in (WS / "library/投资/00-七册MOC").glob("*.md")}
FILE_MOVES = {KB + f"投资/00-七册MOC/{n}": KB + f"投资与交易/{n}" for n in MOC_FILES}
FILE_MOVES.update({
    KB + "投资/README.md": KB + "投资与交易/README.md",
    KB + "工作/README.md": KB + "工作与项目/README.md",
    KB + "考证/README.md": KB + "考证与项目管理/README.md",
})


def resolve(base, target):
    p = (base / target).resolve()
    try:
        return p.relative_to(WS).as_posix()
    except ValueError:
        return None


def repair(new_rel, old_rel):
    f = WS / new_rel
    text = f.read_text(encoding="utf-8")
    old_dir, new_dir = (WS / old_rel).parent, (WS / new_rel).parent
    out, pos, changed = [], 0, 0
    for m in LINK_RE.finditer(text):
        raw = m.group(1)
        if raw.startswith(("http://", "https://", "mailto:", "#")):
            continue
        decoded = unquote(raw)
        r1 = resolve(new_dir, decoded)
        if r1 and (WS / r1).exists():
            continue
        r0 = resolve(old_dir, decoded)
        if r0 and (WS / r0).exists():
            new_str = Path(os.path.relpath(WS / r0, start=new_dir)).as_posix()
            if "%" in raw:
                new_str = new_str.replace(" ", "%20")
            had = text[m.start():m.start() + 3].endswith("(<")
            out.append(text[pos:m.start()])
            out.append("]" + ("(<" + new_str + ">)" if had else "(" + new_str + ")"))
            pos = m.end()
            changed += 1
            print(f"  {new_rel}: {raw[:40]} → {new_str[:40]}")
    out.append(text[pos:])
    if changed:
        f.write_text("".join(out), encoding="utf-8", newline="")
    return changed


def main():
    n_file = n_link = 0
    for old, new in DIR_MOVES.items():
        for f in (WS / new).rglob("*.md"):
            new_rel = f.relative_to(WS).as_posix()
            old_rel = old + new_rel[len(new):]
            c = repair(new_rel, old_rel)
            if c:
                n_file += 1
                n_link += c
    for new_rel, old_rel in FILE_MOVES.items():
        c = repair(new_rel, old_rel)
        if c:
            n_file += 1
            n_link += c
    print(f"[修复pass] {n_file} 文件 / {n_link} 链接")


if __name__ == "__main__":
    main()

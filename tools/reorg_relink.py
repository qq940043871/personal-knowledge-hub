# -*- coding: utf-8 -*-
"""按 reorg_manifest.json 改写 library/ 与根目录 md 中指向四源备份的链接与文本提及。

用法: python tools/reorg_relink.py
- 链接级: markdown 链接 target 解析到根相对路径 → 查 manifest 文件映射 → 重算相对路径
- 文本级: library/README.md 与 码农打怪升级小说 内的反引号路径提及做整串替换
"""
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

WS = Path(__file__).resolve().parent.parent
META = WS / "_备份元数据"

SRC_PREFIXES = ("语雀备份/", "飞书备份/", "腾讯文档导出/", "为知笔记迁移/")
SRC_ROOTS = ("语雀备份", "飞书备份", "腾讯文档导出", "为知笔记迁移")

# 目录级映射（链接指向目录或文本按目录提及时用；文件级 manifest 优先）
DIR_MAP = {
    "语雀备份/爬坑笔记": None,  # 拆分库无单目录映射，由文件级处理
    "语雀备份/底层逻辑": None,
    "语雀备份/交易系统": None,
    "语雀备份/八位数花园": None,
    "语雀备份/从零开始": None,
    "语雀备份/客户跟踪": "工作/客户跟踪",
    "语雀备份/技术方案": "工作/技术方案",
    "语雀备份/工作-计算机": "技术/语雀·工作与计算机",
    "语雀备份/人工智能": "技术/语雀·人工智能",
    "语雀备份/考试-架构师": "考证/软考-架构师",
    "语雀备份/考试-管理师": "考证/软考-管理师",
    "语雀备份/自媒体学习": "创作/自媒体与股林武侠",
    "语雀备份/README.md": "_备份元数据/语雀-README.md",
    "语雀备份/备份报告.md": "_备份元数据/语雀-备份报告.md",
    "飞书备份/知识库/项目经验/项目经验": "工作/飞书·项目经验",
    "飞书备份/知识库/Agent开发/Agent开发": "技术/飞书·Agent开发",
    "飞书备份/知识库/人生经历/人生经历": "家庭/人生经历",
    "飞书备份/云盘/职业交易员养成之路": "投资/07-新手学习路线/职业交易员养成之路",
    "飞书备份/云盘/像证券交易员一样思考": "投资/07-新手学习路线/像证券交易员一样思考",
    "腾讯文档导出/1工作记录": "工作/腾讯项目文档",
    "腾讯文档导出/3职场进阶": "考证/腾讯·职场进阶",
    "腾讯文档导出/2炒股养家": "投资/01-我的实盘与成长史/账本",
    "腾讯文档导出/README.md": "_备份元数据/腾讯-README.md",
    "腾讯文档导出/导出清单.md": "_备份元数据/腾讯-导出清单.md",
    "为知笔记迁移/工作记录": "工作/为知·工作记录",
    "为知笔记迁移/运维常用": "技术/为知·运维",
    "为知笔记迁移/技术专栏笔记": "技术/为知·技术专栏",
    "为知笔记迁移/微权力下的项目管理": "考证/微权力下的项目管理",
    "为知笔记迁移/项目管理": "考证/项目管理文章",
    "为知笔记迁移/育儿与家庭": "家庭/育儿",
    "为知笔记迁移/个人成长规划": "家庭/个人成长",
    "为知笔记迁移/面试基础整理": "工作/求职与面试",
    "为知笔记迁移/README.md": "_备份元数据/为知-README.md",
}

LINK_RE = re.compile(r"\]\(<?([^)>]*?)>?\)")


def load_map():
    data = json.loads((META / "reorg_manifest.json").read_text(encoding="utf-8"))
    fmap = {e["src"]: e["dst"] for e in data["moves"]}
    return fmap


def resolve(root_rel_candidate, ref_dir: Path):
    """把引用文件目录下的 target 解析成根相对 posix 路径。"""
    p = (ref_dir / root_rel_candidate).resolve()
    try:
        rel = p.relative_to(WS)
    except ValueError:
        return None
    return rel.as_posix()


def map_target(resolved, fmap):
    if resolved is None:
        return None
    if resolved in fmap:
        return fmap[resolved]
    for old, new in DIR_MAP.items():
        if new and (resolved == old or resolved.startswith(old + "/")):
            return new + resolved[len(old):]
    return None


def rewrite_link(ref_dir: Path, new_root_rel, had_angle, had_encode):
    # 从引用文件所在目录重算相对层级（repo 根相对 → 引用者相对）
    new_target = os.path.relpath(WS / new_root_rel, start=ref_dir).replace("\\", "/")
    if had_encode:
        new_target = new_target.replace(" ", "%20")
    return "]" + f"({'<' + new_target + '>' if had_angle else new_target})"


def relink_file(md: Path, fmap, stats):
    text = md.read_text(encoding="utf-8")
    out, pos, changed = [], 0, 0
    for m in LINK_RE.finditer(text):
        raw = m.group(1)
        if not any(p in raw for p in SRC_PREFIXES):
            continue
        decoded = unquote(raw)
        resolved = resolve(decoded, md.parent)
        new_root = map_target(resolved, fmap)
        if new_root is None:
            stats["unmapped"].append(f"{md.relative_to(WS)}: {raw}")
            continue
        had_angle = text[m.start():m.start() + 3].endswith("(<") or "(<" in text[m.start():m.end()]
        had_encode = "%" in raw
        out.append(text[pos:m.start()])
        out.append(rewrite_link(md.parent, new_root, had_angle, had_encode))
        pos = m.end()
        changed += 1
    out.append(text[pos:])
    new_text = "".join(out)
    if changed:
        md.write_text(new_text, encoding="utf-8", newline="")
    stats["links"] += changed
    return changed


def text_replace(md: Path, fmap, stats):
    text = md.read_text(encoding="utf-8")
    new_text = text
    n = 0
    for old in sorted(fmap, key=len, reverse=True):
        if old in new_text:
            n += new_text.count(old)
            new_text = new_text.replace(old, fmap[old])
    # 文本级目录前缀替换（文件级之后的兜底，如反引号里的目录路径）
    for old, new in DIR_MAP.items():
        if new and old in new_text:
            n += new_text.count(old)
            new_text = new_text.replace(old, new)
    if n:
        md.write_text(new_text, encoding="utf-8", newline="")
    stats["text"] += n


def main():
    fmap = load_map()
    stats = {"links": 0, "text": 0, "unmapped": []}
    roots = [WS / "library", WS / "RAG.md", WS / "公众号运营方案.md"]
    for root in roots:
        mds = [root] if root.is_file() else sorted(root.rglob("*.md"))
        for md in mds:
            relink_file(md, fmap, stats)
    # 纯文本提及文件（链接已处理过的跳过重做文本级也无害，替换幂等）
    for md in sorted((WS / "library" / "码农打怪升级小说").rglob("*.md")):
        text_replace(md, fmap, stats)
    text_replace(WS / "library" / "README.md", fmap, stats)
    print(f"链接改写 {stats['links']} 处；文本提及替换 {stats['text']} 处")
    if stats["unmapped"]:
        print(f"\n-- 未映射引用 {len(stats['unmapped'])}（需人工处理）--")
        for u in stats["unmapped"][:30]:
            print("  " + u)
        sys.exit(1)
    print("[完成] 四源引用清零")


if __name__ == "__main__":
    main()

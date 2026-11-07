# -*- coding: utf-8 -*-
"""扫描 library/ 下的文档，生成 index.html 使用的目录索引 tree.json。

只收录浏览器能预览的文档类型（.md / .markdown / .pptx），源码、图片、
隐藏目录与顶层元数据文件（README.md / wiki.md / CLAUDE.md 等）一律忽略。

index.html 的导航只支持三级（分类 / 子目录 / 子子目录），更深的层级会被
折叠成 "父目录/子目录/..." 形式的标签，保证任意深度都不会丢文件。
"""
import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "tree.json"

DOC_EXTS = {".md", ".markdown", ".pptx"}
SKIP_DIRS = {"__pycache__", "node_modules", ".git", ".idea", ".vscode", ".atomcode",
             # 六库中的私有来源子目录(gitignore)不进公开站点树,成品目录正常收录
             "01-我的实盘与成长史", "02-交易心理与悟道", "03-交易系统与实战战法",
             "04-游资与高手实录", "05-宏观与行业底层逻辑", "06-选股基金与量化", "07-新手学习路线",
             "客户跟踪", "技术方案", "腾讯项目文档", "飞书·项目经验", "求职与面试", "为知·工作记录", "飞书周报",
             "飞书·Agent开发", "飞书·Java架构师", "飞书·LLM底层", "飞书·人工智能", "飞书·技术架构",
             "飞书·飞天闪客", "飞书·工程化", "从0到1设计计算机", "语雀·工作与计算机", "语雀·人工智能",
             "为知·技术专栏", "为知·运维", "软考-架构师", "软考-管理师", "腾讯·职场进阶",
             "项目管理文章", "微权力下的项目管理", "自媒体与股林武侠", "_备份元数据"}


def list_dirs(path):
    return sorted(
        d
        for d in os.listdir(path)
        if os.path.isdir(os.path.join(path, d))
        and not d.startswith(".")
        and d not in SKIP_DIRS
    )


def list_docs(path):
    return sorted(
        f
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
        and not f.startswith(".")
        and os.path.splitext(f)[1].lower() in DOC_EXTS
    )


def emit_deep(dir_path, label, out):
    """收集三级及更深目录下的文档，把更深层级折叠进 label。"""
    files = list_docs(dir_path)
    if files:
        out[label] = files
    for sub in list_dirs(dir_path):
        emit_deep(os.path.join(dir_path, sub), f"{label}/{sub}", out)


def build():
    tree = {}
    for folder in list_dirs(BASE):
        folder_path = os.path.join(BASE, folder)
        direct = list_docs(folder_path)
        subs = list_dirs(folder_path)

        if not subs:
            if direct:
                tree[folder] = direct
            continue

        node = {}
        if direct:
            node["_files"] = direct

        for sub in subs:
            sub_path = os.path.join(folder_path, sub)
            sub_files = list_docs(sub_path)
            sub_subs = list_dirs(sub_path)

            if not sub_subs:
                if sub_files:
                    node[sub] = sub_files
                continue

            sub_node = {}
            if sub_files:
                sub_node["_files"] = sub_files
            for sub_sub in sub_subs:
                emit_deep(os.path.join(sub_path, sub_sub), sub_sub, sub_node)
            if sub_node:
                node[sub] = sub_node

        if node:
            tree[folder] = node

    return tree


def main():
    tree = build()
    tmp = OUTPUT.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, OUTPUT)

    folders = len(tree)
    files = 0
    for value in tree.values():
        if isinstance(value, list):
            files += len(value)
            continue
        files += len(value.get("_files", []))
        for key, sub in value.items():
            if key == "_files":
                continue
            if isinstance(sub, list):
                files += len(sub)
            else:
                files += len(sub.get("_files", []))
                for sub_key, sub_files in sub.items():
                    if sub_key != "_files":
                        files += len(sub_files)

    print(f"[build_tree] {folders} folders, {files} documents -> {OUTPUT}")


if __name__ == "__main__":
    main()

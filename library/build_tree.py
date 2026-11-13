# -*- coding: utf-8 -*-
"""扫描 library/ 下的文档，生成 index.html 使用的目录索引 tree.json。

只收录浏览器能预览的文档类型（.md / .markdown / .pptx），源码、图片、
隐藏目录与顶层元数据文件（README.md / wiki.md / CLAUDE.md 等）一律忽略。

跳过名单不再手抄：每个目录都会问一次 `git check-ignore --no-index`，
被 .gitignore（根目录 + library/.gitignore）忽略的目录才不进树。
只有 git 不可用时才退回 FALLBACK_IGNORED_DIRS 里的私有目录兜底。

index.html 的导航只支持三级（分类 / 子目录 / 子子目录），更深的层级会被
折叠成 "父目录/子目录/..." 形式的标签，保证任意深度都不会丢文件。
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "tree.json"

DOC_EXTS = {".md", ".markdown", ".pptx"}

# 纯技术目录，与版本控制无关，永远不收
SKIP_DIRS = {"__pycache__", "node_modules", ".idea", ".vscode", ".atomcode"}

# 兜底名单：仅当 git 不可用（未安装/不在仓库里）时生效，与 .gitignore 的私有目录同步
FALLBACK_IGNORED_DIRS = {"家庭", "隐私", "01-我的实盘与成长史", "客户跟踪"}

_GIT_STATE = None   # None=未探测, True=可用, False=不可用
_GIT_CACHE = {}     # 相对 BASE 的 posix 路径 -> 是否被忽略


def _rel(path):
    return Path(path).relative_to(BASE).as_posix()


def _git_ignored(rels):
    """批量问 git 哪些相对路径被忽略；返回被忽略集合，git 不可用返回 None。"""
    global _GIT_STATE
    if _GIT_STATE is False:
        return None

    todo = [r for r in rels if r not in _GIT_CACHE]
    if todo:
        if _GIT_STATE is None:
            if shutil.which("git") is None:
                _GIT_STATE = False
                return None
            _GIT_STATE = True

        payload = b"\0".join(os.fsencode(r) for r in todo) + b"\0"
        try:
            proc = subprocess.run(
                ["git", "check-ignore", "--no-index", "-z", "--stdin"],
                cwd=str(BASE), input=payload, capture_output=True,
            )
        except OSError:
            _GIT_STATE = False
            return None

        # 0=有命中, 1=无命中; 其他(128 等)说明当前目录不是 git 仓库
        if proc.returncode not in (0, 1):
            _GIT_STATE = False
            return None

        hit = {name.decode("utf-8", "replace")
               for name in proc.stdout.split(b"\0") if name}
        for rel in todo:
            _GIT_CACHE[rel] = rel in hit

    return {rel for rel in rels if _GIT_CACHE.get(rel)}


def list_dirs(path):
    names = sorted(
        d
        for d in os.listdir(path)
        if os.path.isdir(os.path.join(path, d))
        and not d.startswith(".")
    )
    if not names:
        return []

    rels = {name: _rel(os.path.join(path, name)) for name in names}
    ignored = _git_ignored(list(rels.values()))

    keep = []
    for name in names:
        if name in SKIP_DIRS:
            continue
        if ignored is None:
            if name in FALLBACK_IGNORED_DIRS:
                continue
        elif rels[name] in ignored:
            continue
        keep.append(name)
    return keep


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

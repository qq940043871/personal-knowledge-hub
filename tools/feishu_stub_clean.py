# -*- coding: utf-8 -*-
"""飞书备份存根清理工具（默认 dry-run，--apply 才真删）。

判定：
- stub  = 全文只有 markdown 标题行、无正文、<200B 的 .md（导出时空页面的标题壳）
- real  = 其余 .md
- 后缀  = 文件名以 _2.._7 结尾（导出器对同名节点的去重后缀）

规则（保守）：
1. stub + 后缀            -> 删（与同名 base 重复的标题壳，信息在 base/manifest 里）
2. stub + base，存在同名 real -> 删（内容已在 real 版本里）
3. stub + base，无同名 real   -> 保留（墓碑，保住"这页存在过"的记录）
4. real + 后缀，存在同名 real base -> 删（真重复）
5. real + 后缀，无同名 base   -> 保留并在报告中列出（唯一拷贝，人工判断）
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
APPLY = "--apply" in sys.argv
SUFFIX_RE = re.compile(r"^(.*)_([2-7])\.md$")


def is_stub(p: Path) -> bool:
    try:
        if p.stat().st_size > 200:
            return False
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return bool(lines) and all(l.startswith("#") for l in lines)


def main():
    md_files = [p for p in ROOT.rglob("*.md")]
    kinds = {}
    real_names = set()
    for p in md_files:
        rel = p.relative_to(ROOT).as_posix()
        if is_stub(p):
            kinds[rel] = "stub"
        else:
            kinds[rel] = "real"
            real_names.add(p.name)

    to_delete, tombstones, real_dups = [], [], []
    for rel, kind in kinds.items():
        name = Path(rel).name
        m = SUFFIX_RE.match(name)
        if kind == "stub":
            if m:
                to_delete.append(rel)          # 规则1
            elif name in real_names:
                to_delete.append(rel)          # 规则2
            else:
                tombstones.append(rel)         # 规则3
        else:
            if m and (m.group(1) + ".md") in real_names:
                to_delete.append(rel)          # 规则4
            elif m:
                real_dups.append(rel)          # 规则5

    by_space = {}
    for rel in to_delete:
        space = rel.split("/")[1] if rel.startswith("知识库/") else rel.split("/")[0]
        by_space[space] = by_space.get(space, 0) + 1

    print(f"扫描 .md 总数: {len(md_files)}")
    print(f"待删除: {len(to_delete)}  (按空间: {json.dumps(by_space, ensure_ascii=False)})")
    print(f"保留墓碑 stub: {len(tombstones)}")
    print(f"保留唯一 real 后缀文件: {len(real_dups)}")
    for r in real_dups[:20]:
        print(f"  [唯一real后缀] {r}")

    if APPLY:
        import os
        n = 0
        for rel in to_delete:
            os.remove(ROOT / rel)
            n += 1
        out = ROOT / "_stub_cleanup_report.json"
        out.write_text(json.dumps({
            "date": "2026-11-07",
            "deleted": len(to_delete),
            "kept_tombstones": len(tombstones),
            "kept_real_suffixed": len(real_dups),
            "deleted_list": to_delete,
            "tombstone_list": tombstones,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"已删除 {n} 个文件，报告 -> {out}")
    else:
        print("\n[dry-run] 未删除任何文件。确认无误后追加 --apply 执行。")


if __name__ == "__main__":
    main()

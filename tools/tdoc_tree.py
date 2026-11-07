#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""List all Tencent Docs folders (BFS, non-recursive listing per folder)"""
import json
import subprocess
import sys
import os

SKILL = r"C:\Users\qq940\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docs-plugin\5.9.3-wb.42398134.gd4692421.h480e8d1fee0f\skills\tencent-docs"
PY = r"C:\Users\qq940\anaconda3\python.exe"
SCRIPT = os.path.join(SKILL, "tencentdocs.py")


def call(tool, args):
    p = subprocess.run([PY, SCRIPT, "tdoc_call", "tencent-docs", tool, json.dumps(args, ensure_ascii=False)],
                       cwd=SKILL, capture_output=True)
    out = p.stdout.decode("utf-8", "replace")
    try:
        data = json.loads(out)
    except Exception:
        print("RAW:", out[:500], p.stderr.decode("utf-8", "replace")[:500], file=sys.stderr)
        return None
    if "error" in data:
        print("ERR:", json.dumps(data["error"], ensure_ascii=False), file=sys.stderr)
        return None
    res = data.get("result", {})
    sc = res.get("structuredContent")
    if sc is not None:
        return sc
    txt = res.get("content", [{}])[0].get("text", "{}")
    return json.loads(txt)


def list_folder(fid):
    items = []
    start = 0
    while True:
        args = {"start": start}
        if fid:
            args["folder_id"] = fid
        r = call("manage.folder_list", args)
        if not r:
            break
        items.extend(r.get("list") or [])
        if r.get("finish"):
            break
        start += 20
        if start > 4000:
            break
    return items


root = None
all_items = []
queue = [(root, "")]
seen = set()
while queue:
    fid, prefix = queue.pop(0)
    if fid in seen:
        continue
    seen.add(fid)
    for it in list_folder(fid):
        if it.get("is_link"):
            continue
        rec = dict(it)
        rec["folder_path"] = prefix
        all_items.append(rec)
        if it.get("is_folder"):
            queue.append((it["id"], prefix + "/" + it["title"]))

out = r"D:\ai_person\personal-tech-knowledge\.workbuddy\tdoc_manifest.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(all_items, f, ensure_ascii=False, indent=1)

files = [i for i in all_items if not i.get("is_folder")]
print("total items:", len(all_items), "files:", len(files))
from collections import Counter
print(Counter([i.get("ext") or "folder" for i in all_items]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量导出腾讯文档中的"文档(文章)"为 docx"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

SKILL = r"C:\Users\qq940\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docs-plugin\5.9.3-wb.42398134.gd4692421.h480e8d1fee0f\skills\tencent-docs"
PY = r"C:\Users\qq940\anaconda3\python.exe"
SCRIPT = os.path.join(SKILL, "tencentdocs.py")
MANIFEST = r"D:\ai_person\personal-tech-knowledge\.workbuddy\tdoc_manifest.json"
OUTDIR = r"D:\ai_person\personal-tech-knowledge\腾讯文档导出"


def call(tool, args):
    p = subprocess.run([PY, SCRIPT, "tdoc_call", "tencent-docs", tool, json.dumps(args, ensure_ascii=False)],
                       cwd=SKILL, capture_output=True)
    out = p.stdout.decode("utf-8", "replace")
    try:
        data = json.loads(out)
    except Exception:
        return {"error": out[:300]}
    if "error" in data:
        return {"error": json.dumps(data["error"], ensure_ascii=False)}
    res = data.get("result", {})
    sc = res.get("structuredContent")
    if sc is not None:
        return sc
    return json.loads(res.get("content", [{}])[0].get("text", "{}"))


def safe(name):
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name).strip().strip(".")
    return name[:80] or "untitled"


items = json.load(open(MANIFEST, encoding="utf-8"))
docs = [i for i in items if i.get("ext") == "tencentdoc"]
print("docs to export:", len(docs))

results = []
for idx, d in enumerate(docs, 1):
    title = d["title"]
    folder = (d.get("folder_path") or "").strip("/")
    target_dir = os.path.join(OUTDIR, folder) if folder else OUTDIR
    os.makedirs(target_dir, exist_ok=True)
    dest = os.path.join(target_dir, safe(title) + ".docx")
    if os.path.exists(dest) and os.path.getsize(dest) > 2000:
        results.append({"title": title, "path": dest, "status": "skip-exists"})
        print(f"[{idx}/{len(docs)}] skip {title}")
        continue
    r = call("manage.export_file", {"file_id": d["id"]})
    tid = r.get("task_id")
    if not tid:
        results.append({"title": title, "status": "export_fail", "info": r})
        print(f"[{idx}/{len(docs)}] FAIL export {title} :: {r}")
        continue
    url = None
    for _ in range(40):
        time.sleep(3)
        pr = call("manage.export_progress", {"task_id": tid})
        if pr.get("file_url"):
            url = pr["file_url"]
            break
        if pr.get("error"):
            break
    if not url:
        results.append({"title": title, "status": "timeout", "task": tid, "info": pr})
        print(f"[{idx}/{len(docs)}] FAIL poll {title} :: {pr}")
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        size = os.path.getsize(dest)
        results.append({"title": title, "path": dest, "size": size, "status": "ok"})
        print(f"[{idx}/{len(docs)}] ok {title} -> {size} bytes")
    except Exception as e:
        results.append({"title": title, "status": "download_fail", "info": str(e)})
        print(f"[{idx}/{len(docs)}] FAIL download {title} :: {e}")

rp = os.path.join(OUTDIR, "_export_report.json")
with open(rp, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
from collections import Counter
print(Counter(r["status"] for r in results))
print("report:", rp)

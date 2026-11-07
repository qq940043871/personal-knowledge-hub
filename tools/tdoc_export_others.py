#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量导出腾讯文档剩余类型（表格/脑图/流程图/图片）"""
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request

SKILL = r"C:\Users\qq940\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docs-plugin\5.9.3-wb.42398134.gd4692421.h480e8d1fee0f\skills\tencent-docs"
PY = r"C:\Users\qq940\anaconda3\python.exe"
SCRIPT = os.path.join(SKILL, "tencentdocs.py")
MANIFEST = r"D:\ai_person\personal-tech-knowledge\.workbuddy\tdoc_manifest.json"
# DEPRECATED（2026-11-07）：输出目录已随四源重组拆分为 工作/腾讯项目文档、考证/腾讯·职场进阶、投资/01-我的实盘与成长史/账本 及 _备份元数据，本一次性导出工具不再适用。
OUTDIR = r"D:\ai_person\personal-tech-knowledge\腾讯文档导出"
EXT_FALLBACK = {"tencentsheet": ".xlsx", "mind": ".mind", "flowchart": ".flowchart",
                "tencentdoc": ".docx", "jpeg": ".jpg", "png": ".png", "pdf": ".pdf"}


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


def ext_from_url(url, fallback):
    try:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        cd = (q.get("response-content-disposition") or [""])[0]
        m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", cd)
        if m:
            fn = urllib.parse.unquote(m.group(1))
            e = os.path.splitext(fn)[1]
            if e:
                return e
    except Exception:
        pass
    return fallback


items = json.load(open(MANIFEST, encoding="utf-8"))
todo = [i for i in items if not i.get("is_folder") and i.get("ext") != "tencentdoc"]
print("to export:", len(todo))

results = []
for idx, d in enumerate(todo, 1):
    title = d["title"]
    folder = (d.get("folder_path") or "").strip("/")
    target_dir = os.path.join(OUTDIR, folder) if folder else OUTDIR
    os.makedirs(target_dir, exist_ok=True)
    r = call("manage.export_file", {"file_id": d["id"]})
    tid = r.get("task_id")
    if not tid:
        results.append({"title": title, "ext": d.get("ext"), "status": "export_fail", "info": r})
        print(f"[{idx}/{len(todo)}] FAIL export {title} :: {r}")
        continue
    url = None
    pr = {}
    for _ in range(40):
        time.sleep(3)
        pr = call("manage.export_progress", {"task_id": tid})
        if pr.get("file_url"):
            url = pr["file_url"]
            break
        if pr.get("error"):
            break
    if not url:
        results.append({"title": title, "ext": d.get("ext"), "status": "timeout", "info": pr})
        print(f"[{idx}/{len(todo)}] FAIL poll {title} :: {pr}")
        continue
    ext = ext_from_url(url, EXT_FALLBACK.get(d.get("ext"), ".bin"))
    dest = os.path.join(target_dir, safe(title) + ext)
    n = 1
    while os.path.exists(dest):
        n += 1
        dest = os.path.join(target_dir, f"{safe(title)}({n}){ext}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        size = os.path.getsize(dest)
        results.append({"title": title, "ext": d.get("ext"), "path": dest, "size": size, "status": "ok"})
        print(f"[{idx}/{len(todo)}] ok {title}{ext} -> {size} bytes")
    except Exception as e:
        results.append({"title": title, "ext": d.get("ext"), "status": "download_fail", "info": str(e)})
        print(f"[{idx}/{len(todo)}] FAIL download {title} :: {e}")

rp = os.path.join(OUTDIR, "_export_report_others.json")
with open(rp, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
from collections import Counter
print(Counter((r.get("ext"), r["status"]) for r in results))

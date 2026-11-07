#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成导出目录清单 index.md"""
import json
import os

# DEPRECATED（2026-11-07）：输出目录已随四源重组拆分为 工作/腾讯项目文档、考证/腾讯·职场进阶、投资/01-我的实盘与成长史/账本 及 _备份元数据，本一次性导出工具不再适用。
OUTDIR = r"D:\ai_person\personal-tech-knowledge\腾讯文档导出"
MANIFEST = r"D:\ai_person\personal-tech-knowledge\.workbuddy\tdoc_manifest.json"

items = [i for i in json.load(open(MANIFEST, encoding="utf-8")) if not i.get("is_folder")]

rows = []
for d in items:
    folder = (d.get("folder_path") or "").strip("/") or "(根目录)"
    rows.append((folder, d["title"], d.get("ext"), d.get("url")))
rows.sort(key=lambda r: (r[0], r[1]))

lines = ["# 腾讯文档导出清单", "",
         f"导出时间：2026-11-07　|　文件数：36　|　源目录：腾讯文档「我的文档」全量（4 个根文件夹，10 个子文件夹）", "",
         "| 所在文件夹 | 标题 | 类型 | 原链接 |", "| --- | --- | --- | --- |"]
TYPE = {"tencentdoc": "文档 docx", "tencentsheet": "表格 xlsx", "mind": "脑图 mind",
        "flowchart": "流程图 flowchart", "jpeg": "图片(空文件,导出失败)"}
for folder, title, ext, url in rows:
    lines.append(f"| {folder} | {title} | {TYPE.get(ext, ext)} | [打开]({url}) |")

lines += ["", "> 说明：「视频剪辑项目」为历史遗留空文档，正文为空且导出服务报错，未能导出。", ""]
p = os.path.join(OUTDIR, "导出清单.md")
with open(p, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(p, "rows:", len(rows))

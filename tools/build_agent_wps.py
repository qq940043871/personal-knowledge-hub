#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按目录范围把问题清单切分成 agent 工作包,输出 tools/_agent_wps/wpN.json"""
import io
import json
import os
import sys

LIB = 'library'
OUT = 'tools/_agent_wps'
os.makedirs(OUT, exist_ok=True)

SCOPES = [
    ('wp1', ['技术/为知·技术专栏', '技术/为知·运维']),
    ('wp2', ['技术/飞书·Java架构师', '技术/飞书·LLM底层']),
    ('wp3', ['技术/飞书·人工智能', '技术/飞书·飞天闪客', '技术/飞书·Agent开发', '技术/飞书·工程化']),
    ('wp4', ['技术/语雀·工作与计算机', '技术/语雀·人工智能', '技术/17年技术经验总结']),
    ('wp5', ['技术/消息中间件设计', '技术/技术文档体系', '技术/Kafka学习指南', '技术/Nginx学习指南',
             '技术/Redis学习指南', '技术/Linux学习指南', '技术/MiniIO学习指南', '技术/Zookeeper学习指南',
             '技术/OpenCV学习指南', '技术/FFmpeg学习指南', '技术/Java避坑指南', '技术/Java框架全景图',
             '技术/AI常用类库指南', '技术/ClaudeCode学习指南', '技术/Openclaw学习指南',
             '技术/大模型工具全景图', '技术/OS_Tutorial']),
    # wp6 = 技术 下其余全部
    ('wp7', ['投资/01-我的实盘与成长史', '投资/02-交易心理与悟道', '投资/03-交易系统与实战战法']),
    ('wp8', ['投资/04-游资与高手实录', '投资/05-宏观与行业底层逻辑', '投资/06-选股基金与量化']),
    ('wp9', ['投资/07-新手学习路线', '投资/08-fianace-console', '考证']),
    ('wp10', ['工作/客户跟踪']),
    # wp11 = 工作其余 + 家庭 + library 根部文件
]

detail = json.load(io.open('tools/_format_scan2.json', encoding='utf-8'))
quality = json.load(io.open('tools/_quality_scan.json', encoding='utf-8'))

# quality 里的 file 是相对 library 的路径(或根 README/wiki)
qbyfile = {}
for it in quality:
    f = it['file'].replace('\\', '/')
    qbyfile.setdefault(f, []).append({'type': it['type'], 'line': it.get('line', 0), 'detail': it.get('detail', '')})

all_files = []
for dirpath, dirnames, filenames in os.walk(LIB):
    dirnames[:] = [d for d in dirnames if d != '.git']
    for fn in filenames:
        if fn.lower().endswith('.md'):
            all_files.append(os.path.join(dirpath, fn).replace('\\', '/'))

tech_prefix = '技术/'
dir2wp = {}
for name, dirs in SCOPES:
    for d in dirs:
        dir2wp[d + '/'] = name


def assign(rel):
    if rel.startswith(tech_prefix):
        for prefix, wp in dir2wp.items():
            if rel.startswith(prefix):
                return wp
        return 'wp6'
    for prefix, wp in dir2wp.items():
        if rel.startswith(prefix):
            return wp
    return 'wp11'


bywp = {name: [] for name, _ in SCOPES}
bywp['wp6'] = []
bywp['wp11'] = []
for p in all_files:
    rel = p[len(LIB) + 1:]
    wp = assign(rel)
    bywp[wp].append(p)

# 工作包内容
summary = {}
for name, files in bywp.items():
    flagged = {}
    for f in files:
        rel = f[len(LIB) + 1:]
        iss = []
        for it in detail.get(f, []):
            iss.append({'type': it['type'], 'line': it['line'], 'detail': it['detail']})
        for it in qbyfile.get(rel, []):
            if it['type'] != 'stub-tombstone':
                iss.append(it)
        if iss:
            flagged[f] = iss
    data = {'scope_dirs': SCOPES[[n for n, _ in SCOPES].index(name)][1] if name in [n for n, _ in SCOPES] else
            (['技术/其余子目录'] if name == 'wp6' else ['工作其余+家庭+根部']),
            'files': files, 'flagged': flagged}
    with io.open('%s/%s.json' % (OUT, name), 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    summary[name] = {'files': len(files), 'flagged': len(flagged)}

print(json.dumps(summary, ensure_ascii=False, indent=1))

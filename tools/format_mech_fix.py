#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""机械排版修复:仅处理文本区域(代码围栏外)的确定性安全问题。
- BOM 移除
- 行尾空格/制表符移除
- 连续 3+ 空行折叠为 1 个空行;文件尾归一为单个换行
- 有序/无序列表缺空格补空格(排除下一字符为数字或 -)
"""
import io
import os
import re
import sys

ROOTS = sys.argv[1:] or ['library']
FENCE_RE = re.compile(r'^\s*(`{3,}|~{3,})')
ORDERED_RE = re.compile(r'^(\s*\d+)\.(?!\s)(\S)')
UNORDERED_RE = re.compile(r'^(\s*)[-+](?!\s)(?![-+=])(\S)')
stats = {'bom': 0, 'trailing-ws': 0, 'blank-run': 0, 'list-nospace': 0, 'files-changed': 0}


def classify(lines):
    kinds, fence, mark = [], False, ''
    for line in lines:
        m = FENCE_RE.match(line)
        if m:
            if not fence:
                fence, mark = True, m.group(1)[0]
            elif m.group(1)[0] == mark:
                fence = False
            kinds.append('fence')
        else:
            kinds.append('fence' if fence else 'text')
    return kinds


def fix_file(path):
    with io.open(path, 'r', encoding='utf-8-sig', errors='surrogateescape', newline='') as f:
        raw = f.read()
    orig = raw
    if raw.startswith('\ufeff'):
        stats['bom'] += 1
    had_crlf = '\r\n' in raw
    text = raw.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    kinds = classify(lines)
    out = []
    n = len(lines)
    for i, line in enumerate(lines):
        if kinds[i] == 'text':
            fixed = line.rstrip(' \t\u00a0')
            if fixed != line:
                stats['trailing-ws'] += 1
            line = fixed
            m = ORDERED_RE.match(line)
            if m and not m.group(2)[0].isdigit():
                line = m.group(1) + '. ' + m.group(2)
                stats['list-nospace'] += 1
            m = UNORDERED_RE.match(line)
            if m:
                line = m.group(1) + '- ' + m.group(2)
                stats['list-nospace'] += 1
        out.append(line)
    # 折叠连续空行(文本区):3+ 连续空行 -> 1 个
    result = []
    blank = 0
    for i, line in enumerate(out):
        if kinds[i] == 'text' and line.strip() == '':
            blank += 1
            if blank >= 2:
                stats['blank-run'] += 1
                continue
        else:
            blank = 0
        result.append(line)
    # 尾部空行清理:最后一个非空行之后全部去掉
    last_content = -1
    for i in range(len(result) - 1, -1, -1):
        if result[i].strip() != '':
            last_content = i
            break
    result = result[:last_content + 1] if last_content >= 0 else []
    text = '\n'.join(result)
    if text and not text.endswith('\n'):
        text += '\n'
    if had_crlf:
        text = text.replace('\n', '\r\n')
    if text != orig:
        with io.open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        stats['files-changed'] += 1


def walk_md(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != '.git']
        for fn in filenames:
            if fn.lower().endswith('.md'):
                yield os.path.join(dirpath, fn)


for root in ROOTS:
    for p in walk_md(root):
        try:
            fix_file(p)
        except Exception as e:
            print('ERR %s: %s' % (p, e), file=sys.stderr)
print(stats)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""剩余 no-h1 修复:首行纯文本标题(常带前导空格)转 # 标题;结构特殊的输出待人工处理。"""
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
scan = json.load(io.open('tools/_format_scan.json', encoding='utf-8'))
targets = sorted({f for f, iss in scan.items() for it in iss if it['type'] == 'no-h1'})

TITLEISH = re.compile(r'^\s{0,8}([^#>\-\*\+`\|\!\s].{0,90}?)\s*$')
changed = []
manual = []
for path in targets:
    try:
        with io.open(path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
    except OSError as e:
        manual.append((path, 'read-error: %s' % e))
        continue
    idx = next((i for i, l in enumerate(lines) if l.strip()), None)
    if idx is None:
        manual.append((path, 'empty file'))
        continue
    line = lines[idx]
    m = TITLEISH.match(line)
    text = m.group(1).strip() if m else ''
    ok = bool(text) and not re.search(r'[。;；,，]$', text) and not re.match(r'^\d+[\.、]\s*[^ ]', text)
    if not ok:
        manual.append((path, 'first-line: %r' % line[:60]))
        continue
    lines[idx] = '# ' + text
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(lines))
    changed.append((path, text))

print('converted %d:' % len(changed))
for p, t in changed:
    print('  %s -> %s' % (p, t))
print('\nmanual %d:' % len(manual))
for p, why in manual:
    print('  %s | %s' % (p, why))

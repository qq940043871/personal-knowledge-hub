#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""排版细节扫描器:配合 archive-quality-scan.mjs 使用,覆盖其未覆盖的排版问题。
用法: python tools/format_detail_scan.py library > tools/_format_scan.json (stdout 为 JSON)
"""
import io
import json
import os
import re
import sys

ROOTS = sys.argv[1:] or ['library']

FENCE_RE = re.compile(r'^\s*(`{3,}|~{3,})')
HEADING_RE = re.compile(r'^(#{1,6})\s+')
# 常见原始 HTML 标签(排除 SVG 内部标签与 mermaid/svg 代码块内容)
HTML_TAG_RE = re.compile(
    r'</?(?:div|span|br|p|font|center|table|thead|tbody|tr|td|th|img|u|b|s|sub|sup|details|summary|section|aside|video|audio|iframe|style|details)\b',
    re.I)
EMPTY_LINK_RE = re.compile(r'(?<!\!)\[[\s\u00a0\u3000]*\]\([^)]*\)')
ORDERED_NOSPACE_RE = re.compile(r'^\s*(\d+)\.(?!\s)(\S)')
UNORDERED_NOSPACE_RE = re.compile(r'^\s*(-|\+)(?!\s)(?![\-\+=])\S')
BULLET_WORD_RE = re.compile(r'^\s*[-+]\s*$', re.M)
AI_TAIL_PATTERNS = [
    ('ai-tail', re.compile(r'^(以上就是|希望这篇文章|希望本文|希望这份|希望对你|希望对您|希望这些|我们下期(再见|见)|如果这篇文章|如果你也(在|想)|感谢(你|您)的?(阅读|观看|支持)|祝你(学习|工作))')),
    ('ai-edit-leftover', re.compile(r'^(以下是|上面是)(优化|修改|整理|润色|重写|完善)(后|好)?的(版本|文章|内容|稿|文字)')),
]
PLACEHOLDER_RE = re.compile(r'(待补充|待完善|待更新|待定|TODO[:：])')
REPLACEMENT_CH = '�'


def walk_md(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != '.git']
        for fn in filenames:
            if fn.lower().endswith('.md'):
                out.append(os.path.join(dirpath, fn))
    return out


def classify(lines):
    kinds = []
    fence = False
    mark = ''
    mark_len = 0
    for line in lines:
        m = FENCE_RE.match(line)
        if m:
            m0 = m.group(1)
            if not fence:
                fence = True
                mark = m0[0]
                mark_len = len(m0)
            elif m0[0] == mark and len(m0) >= mark_len:
                fence = False
            kinds.append('fence')
            continue
        kinds.append('fence' if fence else 'text')
    return kinds


def scan_file(path):
    with io.open(path, 'r', encoding='utf-8', errors='replace') as f:
        raw = f.read()
    issues = []
    rel = path.replace('\\', '/')

    if raw.startswith('\ufeff'):
        issues.append({'type': 'bom', 'line': 1, 'detail': '文件头 BOM'})

    text = raw

    lines = text.split('\n')
    kinds = classify(lines)

    headings = []  # (level, line_no)
    n_blank = 0
    n_text = 0
    n_trailing_ws = 0
    html_hits = []
    for i, line in enumerate(lines):
        ln = i + 1
        # BOM 占首字符,去掉再判断
        content = line.lstrip('\ufeff')
        if kinds[i] == 'text':
            n_text += 1
            m = HEADING_RE.match(content)
            if m:
                headings.append((len(m.group(1)), ln))
                if len(m.group(1)) == 1 and content.rstrip().rstrip('#').rstrip():
                    pass
            if not content.strip():
                n_blank += 1
            else:
                n_blank = 0
                if content != content.rstrip():
                    n_trailing_ws += 1
                code_stripped = re.sub(r'`[^`\n]*`', '', content)
                for tm in HTML_TAG_RE.finditer(code_stripped):
                    html_hits.append((ln, tm.group(0)))
                if EMPTY_LINK_RE.search(code_stripped):
                    issues.append({'type': 'empty-link', 'line': ln, 'detail': '空链接 []()'})
                om = ORDERED_NOSPACE_RE.match(content)
                if om and not om.group(2)[0].isdigit():
                    issues.append({'type': 'list-nospace', 'line': ln, 'detail': '有序列表缺空格: %s' % content.strip()[:40]})
                um = UNORDERED_NOSPACE_RE.match(content)
                if um:
                    issues.append({'type': 'list-nospace', 'line': ln, 'detail': '无序列表缺空格: %s' % content.strip()[:40]})
                for ptype, pat in AI_TAIL_PATTERNS:
                    if pat.match(content.strip()):
                        issues.append({'type': ptype, 'line': ln, 'detail': content.strip()[:50]})
                pm = PLACEHOLDER_RE.search(code_stripped)
                if pm:
                    issues.append({'type': 'placeholder', 'line': ln, 'detail': pm.group(0)})
                if REPLACEMENT_CH in content:
                    issues.append({'type': 'mojibake', 'line': ln, 'detail': '包含替换符 U+FFFD'})
            if n_blank >= 3:
                issues.append({'type': 'blank-run', 'line': ln, 'detail': '连续 3+ 空行'}) if n_blank == 3 else None
        else:
            n_blank = 0

    if n_text >= 5:
        if n_trailing_ws > max(10, n_text // 3):
            issues.append({'type': 'trailing-ws', 'line': 0, 'detail': '行尾空格 %d/%d 行' % (n_trailing_ws, n_text)})
    if html_hits:
        if len(html_hits) > 8:
            issues.append({'type': 'html-heavy', 'line': html_hits[0][0], 'detail': '原始 HTML 标签 %d 处(如 %s)' % (len(html_hits), html_hits[0][1])})
        else:
            for ln, tag in html_hits[:5]:
                issues.append({'type': 'html-tag', 'line': ln, 'detail': tag})

    h1s = [ln for lv, ln in headings if lv == 1]
    body_chars = sum(len(l) for l in lines)
    if len(h1s) == 0 and body_chars > 300:
        issues.append({'type': 'no-h1', 'line': 0, 'detail': '缺少一级标题'})
    if len(h1s) > 1:
        issues.append({'type': 'multi-h1', 'line': h1s[1], 'detail': '多个一级标题(%d 个)' % len(h1s)})
    prev = None
    for lv, ln in headings:
        if prev is not None and lv > prev + 1:
            issues.append({'type': 'heading-jump', 'line': ln, 'detail': '标题层级从 h%d 跳到 h%d' % (prev, lv)})
            break
        prev = lv

    return issues


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    result = {}
    for root in ROOTS:
        for p in walk_md(root):
            iss = scan_file(p)
            if iss:
                result[p.replace('\\', '/')] = iss
    by_type = {}
    for f, iss in result.items():
        for it in iss:
            by_type.setdefault(it['type'], []).append((f, it))
    print('== format detail scan ==', file=sys.stderr)
    for t, lst in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        print('%s: %d' % (t, len(lst)), file=sys.stderr)
    print('files-with-issues: %d' % len(result), file=sys.stderr)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()

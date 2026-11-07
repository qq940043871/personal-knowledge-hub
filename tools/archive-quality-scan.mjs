#!/usr/bin/env node
// 归档层 markdown 质量扫描器：死链 / 未闭合代码块 / 坏表格 / 乱码 / 过度转义 / 超短文件
// 用法: node tools/archive-quality-scan.mjs <dir> [dir...]
import fs from 'node:fs';
import path from 'node:path';

const roots = process.argv.slice(2);
if (!roots.length) { console.error('usage: node archive-quality-scan.mjs <dir>...'); process.exit(1); }

const IMG_EXT = /\.(png|jpe?g|gif|webp|svg|bmp|ico|avif|mp4|pdf)$/i;
const PLACEHOLDER_RE = /导出失败|空草稿|占位|语雀空文档|lakeboard|空文档|已清理|原地址/;
const issues = [];

function walkMd(dir, out = []) {
  let ents; try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return out; }
  for (const e of ents) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walkMd(p, out);
    else if (/\.md$/i.test(e.name)) out.push(p);
  }
  return out;
}

// 逐行分类：fence / text，并检测未闭合围栏
function classifyLines(lines) {
  const kinds = []; let fence = false, mark = '';
  for (const line of lines) {
    const m = line.match(/^\s*(`{3,}|~{3,})/);
    if (m) {
      if (!fence) { fence = true; mark = m[1][0]; }
      else if (m[1][0] === mark) fence = false;
      kinds.push('fence'); continue;
    }
    kinds.push(fence ? 'fence' : 'text');
  }
  return { kinds, unclosed: fence };
}

const stripInlineCode = (s) => s.replace(/`[^`\n]*`/g, '');
const LINK_RE = /!?\[([^\]\n]*)\]\(\s*<?([^<>()\s]+(?:[ \t][^<>()]*)?)>?(?:[ \t]+"[^"]*")?\s*\)/g;
const HTML_SRC_RE = /<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi;

function scanFile(file, root, nameIndex) {
  const rel = path.relative(root, file);
  let text; try { text = fs.readFileSync(file, 'utf8'); } catch (e) {
    issues.push({ type: 'read-error', file: rel, detail: String(e.message || e) }); return;
  }
  const lines = text.split(/\r?\n/);
  const { kinds, unclosed } = classifyLines(lines);
  if (unclosed) issues.push({ type: 'unclosed-fence', file: rel, line: lines.length, detail: '代码块未闭合' });
  if (text.charCodeAt(0) === 0xFEFF) issues.push({ type: 'bom', file: rel, line: 1, detail: 'UTF-8 BOM' });

  const moj = text.match(/锟斤拷|锟�|\uFFFD|â€[˜œ""]|Ã[\u0080-\u00BF]|ï¼[\u0000-\u00FF]|ã€[\u0000-\u00FF]/g);
  if (moj) issues.push({ type: 'mojibake', file: rel, line: 0, detail: `疑似乱码 ${moj.length} 处，如 ${[...new Set(moj)].slice(0, 3).join(' ')}` });

  // 超短文件：标题壳（墓碑）单列，其余才算质量问题
  const stripped = text.replace(/\s/g, '');
  const nonEmpty = lines.map(l => l.trim()).filter(l => l);
  const isTitleShell = nonEmpty.length > 0 && nonEmpty.every(l => l.startsWith('#'));
  if (isTitleShell) {
    issues.push({ type: 'stub-tombstone', file: rel, line: 1, detail: '标题壳墓碑（存根清理时刻意保留）' });
  } else if (stripped.length < 30 && !PLACEHOLDER_RE.test(text)) {
    issues.push({ type: 'tiny-file', file: rel, line: 1, detail: `有效内容 ${stripped.length} 字符` });
  }

  // 过度转义：只报「破坏渲染」的 \*\* 对与 \` 对（\~ \_ \* \| 等渲染本来就正确，不算问题）
  let escCount = 0; const escSamples = [];
  for (let i = 0; i < lines.length; i++) {
    if (kinds[i] !== 'text') continue;
    const clean = stripInlineCode(lines[i]).replace(/\\`/g, '\u0001');
    const nBold = (clean.match(/\\\*\\\*/g) || []).length;
    const nBt = (clean.match(/\u0001/g) || []).length;
    const n = Math.ceil((nBold % 2 === 0 ? nBold : 0) / 2) + Math.ceil((nBt % 2 === 0 ? nBt : 0) / 2);
    if (n > 0) {
      escCount += n;
      if (escSamples.length < 3) escSamples.push({ line: i + 1, seg: nBold ? '\\*\\*' : '\\`' });
    }
  }
  if (escCount >= 1) issues.push({ type: 'over-escape', file: rel, line: 0, detail: `${escCount} 对未恢复的加粗/代码转义，如 ${escSamples.map(s => `L${s.line}:${s.seg}`).join(' ')}`, count: escCount });

  // 表格检查：仅当行首是 | 或 |…| 网格样式才算表格候选（列表项/正文里的 | 是误报）
  let i = 0;
  const isSep = (s) => /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*:?\s*$/.test(s) && /-/.test(s);
  const isTableRow = (s) => { const t = stripInlineCode(s).trim(); return /^\|/.test(t) && (t.match(/\|/g) || []).length >= 2; };
  while (i < lines.length) {
    if (kinds[i] === 'text' && isTableRow(lines[i])) {
      let j = i; while (j < lines.length && kinds[j] === 'text' && (isTableRow(lines[j]) || isSep(stripInlineCode(lines[j])))) j++;
      const run = lines.slice(i, j);
      if (run.length >= 2 && !isSep(stripInlineCode(run[1]))) {
        const badSep = run.slice(1).some(l => /^[\s|:\-—–]+$/.test(l));
        issues.push({ type: badSep ? 'table-bad-separator' : 'table-no-separator', file: rel, line: i + 1, detail: run[0].trim().slice(0, 60) + ' ⋯ ' + (run[1] || '').trim().slice(0, 40) });
      }
      i = j;
    } else i++;
  }

  // 链接检查（含图片）
  const check = (raw, lineNo) => {
    const t = raw.trim();
    if (/^(https?:|mailto:|data:|about:|#)/i.test(t)) return;
    let target = t.split('#')[0];
    if (!target) return;
    try { target = decodeURIComponent(target); } catch { /* keep raw */ }
    const abs = path.resolve(path.dirname(file), target);
    if (!fs.existsSync(abs)) {
      // 恢复候选：按文件名（含扩展名）在全库索引中找
      const base = path.posix.basename(target).toLowerCase();
      const cands = (nameIndex.get(base) || []).filter(c => path.resolve(c) !== abs);
      issues.push({
        type: IMG_EXT.test(target) ? 'broken-image' : 'broken-link', file: rel, line: lineNo,
        detail: target + (cands.length === 1 ? ` → 唯一候选: ${path.relative(root, cands[0])}` : cands.length > 1 ? ` → ${cands.length} 个候选` : ''),
        target, abs, cands: cands.map(c => path.resolve(c)),
      });
    }
  };
  for (let n = 0; n < lines.length; n++) {
    if (kinds[n] !== 'text') continue;
    const raw = lines[n];
    // HTML 标签内的 src/doc-id 引用单独归类（飞书导出内部引用，本地不可恢复）
    for (const m of raw.matchAll(/<img\b[^>]*?\bsrc\s*=\s*["']([A-Za-z0-9]{20,})["']/gi))
      issues.push({ type: 'feishu-internal-img', file: rel, line: n + 1, detail: m[1] });
    // markdown 链接检测前剥掉 HTML 标签与行内代码段，避免属性值/示例误报
    const noHtml = raw.replace(/<[^>]*>/g, ' ').replace(/`[^`]*`/g, ' ');
    for (const m of noHtml.matchAll(LINK_RE)) check(m[2], n + 1);
  }
}

// 全库文件名索引（用于死链恢复）
const nameIndex = new Map();
for (const root of roots)
  for (const p of walkMd(root)) {
    const k = path.basename(p).toLowerCase();
    if (!nameIndex.has(k)) nameIndex.set(k, []);
    nameIndex.get(k).push(p);
  }

for (const root of roots)
  for (const f of walkMd(root)) scanFile(f, root, nameIndex);

// 汇总
const byType = {};
for (const it of issues) (byType[it.type] ||= []).push(it);
console.log('== 归档层质量扫描 ==');
for (const [t, list] of Object.entries(byType).sort((a, b) => b[1].length - a[1].length))
  console.log(`${t}: ${list.length}`);
console.log('TOTAL:', issues.length);
console.log('---- 明细 ----');
for (const [t, list] of Object.entries(byType).sort((a, b) => b[1].length - a[1].length)) {
  console.log(`\n## ${t} (${list.length})`);
  for (const it of list.slice(0, 60)) console.log(`${it.file}:${it.line}  ${it.detail}`);
  if (list.length > 60) console.log(`… 另有 ${list.length - 60} 条`);
}
fs.writeFileSync('tools/_quality_scan.json', JSON.stringify(issues, null, 1));
console.log('\nJSON → tools/_quality_scan.json');

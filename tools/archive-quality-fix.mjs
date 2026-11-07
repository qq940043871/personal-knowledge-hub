#!/usr/bin/env node
// 归档层质量修复器：--apply 才落盘，默认 dry-run
// 修复项：A) \*\*加粗\*\* 与 \`代码\` 转义残渣  B) 文件尾悬挂 ```  C) memocast/绝对路径丢失图片占位  D) U+FFFD 剥离
import fs from 'node:fs';
import path from 'node:path';

const APPLY = process.argv.includes('--apply');
const roots = ['投资', '工作', '技术', '考证', '家庭', '创作', '_备份元数据', 'library'];

function walkMd(dir, out = []) {
  let ents; try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return out; }
  for (const e of ents) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walkMd(p, out);
    else if (/\.md$/i.test(e.name)) out.push(p);
  }
  return out;
}
const lines_ = (f) => fs.readFileSync(f, 'utf8').split(/\r?\n/);
const stats = { boldFix: 0, codeFix: 0, danglingFence: 0, lostImg: 0, fffd: 0, filesTouched: new Set() };
const log = [];

// ---------- A) 转义残渣：只处理 \*\* 对 与 \` 对，跳过围栏行/行内代码段/$$ 公式 ----------
function unescapeLine(line) {
  if (/\$\$/.test(line)) return { line, a: 0, b: 0 };
  const nBt = (line.match(/\\`/g) || []).length;
  const btFix = nBt > 0 && nBt % 2 === 0;
  // 先把转义反引号换成占位符，避免被切分正则当成真实围栏
  let work = line.replace(/\\`/g, '\u0001');
  const parts = work.split(/(`[^`]*`)/g);
  let a = 0;
  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 1) continue; // 代码段
    const nBold = (parts[i].match(/\\\*\\\*/g) || []).length;
    if (nBold > 0 && nBold % 2 === 0) { parts[i] = parts[i].replace(/\\\*\\\*/g, '**'); a += nBold; }
  }
  work = parts.join('');
  if (nBt > 0) work = work.replace(/\u0001/g, btFix ? '`' : '\\`');
  return { line: work, a, b: btFix ? nBt : 0 };
}

// ---------- 主循环 ----------
for (const root of roots) {
  for (const f of walkMd(root)) {
    const lines = lines_(f);
    let changed = false;

    for (let i = 0; i < lines.length; i++) {
      const { line, a, b } = unescapeLine(lines[i]);
      if (a || b) {
        log.push(`A ${path.relative('.', f)}:${i + 1} 加粗x${a / 2} 代码x${b / 2}`);
        lines[i] = line; changed = true;
        stats.boldFix += a; stats.codeFix += b;
      }
    }

    // B) 文件尾悬挂 ```（未闭合且是最后一行）：连同前一空行删除
    let end = lines.length - 1;
    while (end >= 0 && lines[end].trim() === '') end--;
    if (end >= 0 && lines[end].trim() === '```') {
      // 确认这个 ``` 确实是"开"（之前围栏已配平）
      let open = false;
      for (let i = 0; i < end; i++) if (lines[i].trim().startsWith('```')) open = !open;
      if (!open) {
        log.push(`B ${path.relative('.', f)}:${end + 1} 删尾部悬挂围栏`);
        lines.splice(end); // 删到最后非空围栏行
        while (lines.length && lines[lines.length - 1].trim() === '') lines.pop();
        changed = true; stats.danglingFence++;
      }
    }

    // C) 丢失图片占位（子串替换，保留行内其他文字）
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('memocast://')) {
        lines[i] = lines[i].replace(/!\[\]\(memocast:\/\/[^)]*\)/g, '**〔原图片缺失 —— memocast 图床链接已失效〕**');
        changed = true; stats.lostImg++;
        log.push(`C ${path.relative('.', f)}:${i + 1} memocast图片→占位`);
      }
      if (/!\[\]\(C:\\Users\\[^)]*\)/.test(lines[i])) {
        lines[i] = lines[i].replace(/!\[\]\(C:\\Users\\[^)]*\)/g, '**〔原图片缺失 —— 导出自旧机器绝对路径，文件未随笔记迁移〕**');
        changed = true; stats.lostImg++;
        log.push(`C ${path.relative('.', f)}:${i + 1} 绝对路径图片→占位`);
      }
    }

    // D) U+FFFD 剥离
    const joined = lines.join('\n');
    const nFffd = (joined.match(/\uFFFD/g) || []).length;
    if (nFffd) {
      const cleaned = joined.replace(/\uFFFD/g, '');
      log.push(`D ${path.relative('.', f)} 剥离U+FFFD x${nFffd}`);
      lines.length = 0; lines.push(...cleaned.split('\n'));
      changed = true; stats.fffd += nFffd;
    }

    if (changed && APPLY) fs.writeFileSync(f, lines.join('\n'), 'utf8');
    if (changed) stats.filesTouched.add(path.relative('.', f));
  }
}

console.log(`模式: ${APPLY ? 'APPLY(已落盘)' : 'DRY-RUN(未改动)'}`);
console.log(`\\*\\*加粗恢复: ${stats.boldFix} 处 | 反引号代码恢复: ${stats.codeFix} 处 | 尾部悬挂围栏: ${stats.danglingFence} 个 | 丢失图片占位: ${stats.lostImg} 处 | U+FFFD: ${stats.fffd} 处`);
console.log(`涉及文件: ${stats.filesTouched.size}`);
console.log('---- 明细 ----');
for (const l of log) console.log(l);

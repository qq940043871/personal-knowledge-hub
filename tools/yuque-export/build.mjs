#!/usr/bin/env node
// 语雀导出 JSON -> Markdown 文件树 + 图片本地化
// 用法: node build.mjs <rawDir> <outDir> [--skip-images]
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const rawDir = path.resolve(process.argv[2] || ".");
const outDir = path.resolve(process.argv[3] || ".");
const skipImages = process.argv.includes("--skip-images");

const IMG_EXT_RE = /\.(png|jpe?g|gif|webp|svg|bmp|ico|avif)(?:$|[?#])/i;
const CDN_HOSTS = ["cdn.nlark.com", "cdn.yuque.com"];

const sanitize = (name) =>
  String(name || "")
    .replace(/[\\/:*?"<>|\r\n\t]/g, "-")
    .replace(/\s+/g, " ")
    .replace(/^[.\s-]+|[.\s-]+$/g, "")
    .slice(0, 80) || "未命名";

const report = { books: [], images: { total: 0, ok: 0, fail: 0, failures: [] }, errors: [] };

// ---------- 图片下载 ----------
const imgTasks = [];
function collectImages(md, bookSlug, docSlug) {
  const urls = new Set();
  const push = (u) => {
    if (!u) return;
    const clean = u.trim();
    if (!/^https?:\/\//i.test(clean)) return;
    let host = "";
    try { host = new URL(clean).host; } catch { return; }
    if (!CDN_HOSTS.includes(host)) return;
    urls.add(clean.split("#")[0]);
  };
  // markdown 图片与链接、HTML img 标签
  md.replace(/!\[[^\]]*\]\(([^)\s]+)[^)]*\)/g, (_, u) => { push(u); return _; });
  md.replace(/\[[^\]]*\]\(([^)\s]+)[^)]*\)/g, (_, u) => { push(u); return _; });
  md.replace(/<img[^>]+src=["']([^"']+)["']/g, (_, u) => { push(u); return _; });
  return [...urls];
}

async function downloadImage(url, dest) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const res = await fetch(url, { headers: { "user-agent": "Mozilla/5.0" } });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const buf = Buffer.from(await res.arrayBuffer());
      if (buf.length === 0) throw new Error("empty body");
      fs.writeFileSync(dest, buf);
      return true;
    } catch (e) {
      if (attempt >= 3) { report.images.failures.push({ url, dest, err: String(e.message || e) }); return false; }
      await new Promise(r => setTimeout(r, 800 * attempt));
    }
  }
  return false;
}

// ---------- 主流程 ----------
const files = fs.readdirSync(rawDir).filter(f => f.endsWith(".json")).sort();
if (!files.length) { console.error("no json files in " + rawDir); process.exit(1); }

for (const file of files) {
  const raw = JSON.parse(fs.readFileSync(path.join(rawDir, file), "utf8"));
  const book = raw.book || {};
  const bookName = sanitize(book.name || book.slug || file.replace(/\.json$/, ""));
  const bookDir = path.join(outDir, bookName);
  const imagesDir = path.join(bookDir, "images");
  fs.mkdirSync(bookDir, { recursive: true });
  if (!skipImages) fs.mkdirSync(imagesDir, { recursive: true });

  // docs 索引: doc_id -> md
  const mdById = new Map((raw.docs || []).map(d => [d.doc_id, d]));
  const toc = raw.toc || [];
  const entries = []; // {index,title,relPath}
  let seq = 0;
  const usedNames = new Set();

  for (const node of toc) {
    if (node.type !== "DOC" || !node.doc_id) continue; // TITLE 分组节点跳过
    const doc = mdById.get(node.doc_id);
    seq++;
    const num = String(seq).padStart(3, "0");
    let title = sanitize(node.title || (doc && doc.title) || node.url || "未命名");
    let base = `${num}-${title}`;
    let n = 2;
    while (usedNames.has(base)) base = `${num}-${title}(${n++})`;
    usedNames.add(base);
    const fileName = base + ".md";
    let md = doc && doc.md;
    if (md == null) {
      md = `> ⚠️ 本文档导出失败（doc_id=${node.doc_id}），请到语雀查看：https://www.yuque.com/${book.userSlug || ""}/${book.slugPath || book.slug}/${node.url}`;
      report.errors.push({ book: bookName, doc: node.title, doc_id: node.doc_id, reason: "export null" });
    }
    // 图片本地化
    if (!skipImages) {
      for (const url of collectImages(md, book.slug, node.url)) {
        report.images.total++;
        let ext = (url.match(IMG_EXT_RE) || [])[1];
        if (!ext) {
          try { const p = new URL(url).pathname; const m = p.match(IMG_EXT_RE); ext = m ? m[1] : p.split(".").pop().slice(0, 5); } catch { ext = "png"; }
          if (!/^(png|jpe?g|gif|webp|svg|bmp|ico|avif)$/i.test(ext)) ext = "png";
        }
        ext = ext.toLowerCase().replace("jpeg", "jpg");
        const hash = crypto.createHash("md5").update(url).digest("hex").slice(0, 8);
        let imgName = "";
        try {
          const bn = decodeURIComponent(new URL(url).pathname.split("/").pop() || "img");
          imgName = sanitize(bn.replace(/\.[^.]*$/, "")) + "-" + hash + "." + ext;
        } catch { imgName = hash + "." + ext; }
        const dest = path.join(imagesDir, imgName);
        if (!fs.existsSync(dest)) {
          const ok = await downloadImage(url, dest);
          if (ok) report.images.ok++; else report.images.fail++;
        } else report.images.ok++;
        md = md.split(url).join("images/" + imgName);
      }
    }
    fs.writeFileSync(path.join(bookDir, fileName), md, "utf8");
    entries.push({ num, title, file: fileName });
  }

  // 库内 README：目录清单（按 TOC 顺序含分组层级）
  const lines = [`# ${book.name || bookName}`, "", `> 语雀知识库备份 · 生成于 ${new Date().toLocaleString("zh-CN")} · 共 ${entries.length} 篇文档`, ""];
  let docIdx = 0;
  for (const node of toc) {
    const indent = "  ".repeat(Math.max(0, node.level || 0));
    if (node.type === "TITLE") { lines.push(`${indent}- **${node.title}**`); continue; }
    if (node.type === "DOC" && node.doc_id) {
      const e = entries[docIdx++];
      if (e) lines.push(`${indent}- [${e.title}](./${encodeURIComponent(e.file)})`);
    }
  }
  fs.writeFileSync(path.join(bookDir, "README.md"), lines.join("\n") + "\n", "utf8");

  report.books.push({ name: book.name, slug: book.slug, docs: entries.length, dir: bookName });
  console.log(`[${bookName}] docs=${entries.length}`);
}

fs.writeFileSync(path.join(outDir, "_build_report.json"), JSON.stringify(report, null, 2), "utf8");
console.log(`DONE books=${report.books.length} images ok=${report.images.ok} fail=${report.images.fail} errors=${report.errors.length}`);

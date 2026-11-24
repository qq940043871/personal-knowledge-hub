/* ============================================================
   码潮 CodeTide — app.js
   纯静态博客：文章来自 seed/（meta.json + blocks.jsonl）
   无后端、无登录、无云存储；SPA 路由全部走 location.hash
   ============================================================ */
"use strict";

/* ---------- 1. 全局状态 ---------- */
const PAGE_SIZE = 9;
const SEED_META = "seed/meta.json";
const SEED_BLOCKS = "seed/blocks.jsonl";
let __posts = [];        // 全部文章（含正文），启动时一次性载入
let __loading = null;    // 加载 Promise（只跑一次）

/* ---------- 2. 数据层：seed → 内存 ---------- */
// seed/blocks.jsonl 每行是一块正文：{post, seq, b64}，每块独立 base64，
// 必须「逐块 atob → 拼接字节 → TextDecoder」，不能直接拼 b64 字符串。
function loadPosts() {
  if (__loading) return __loading;
  __loading = (async () => {
    const [metaRes, blocksRes] = await Promise.all([
      fetch(SEED_META, { cache: "no-store" }),
      fetch(SEED_BLOCKS, { cache: "no-store" }),
    ]);
    if (!metaRes.ok) throw new Error(`文章索引加载失败（HTTP ${metaRes.status}）`);
    if (!blocksRes.ok) throw new Error(`文章正文加载失败（HTTP ${blocksRes.status}）`);

    const meta = await metaRes.json();
    const chunkB64 = {}; // post idx -> [b64_chunk, ...]
    (await blocksRes.text()).split("\n").forEach((line) => {
      if (!line.trim()) return;
      try {
        const b = JSON.parse(line);
        if (!chunkB64[b.post]) chunkB64[b.post] = [];
        chunkB64[b.post][b.seq - 1] = b.b64;
      } catch (e) { /* 忽略坏行 */ }
    });

    const decode = (idx) => {
      const parts = (chunkB64[idx] || []).filter(Boolean)
        .map((b64) => Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)));
      const total = parts.reduce((s, p) => s + p.length, 0);
      const all = new Uint8Array(total);
      let offset = 0;
      parts.forEach((p) => { all.set(p, offset); offset += p.length; });
      return new TextDecoder().decode(all);
    };

    // 种子数据不含发布时间，这里按索引生成稳定的展示值（刷新不跳动）
    const BASE = Date.UTC(2026, 10, 21);
    __posts = meta.map((m, i) => {
      let content = "";
      try { content = decode(m.idx); } catch (e) { content = "（正文解码失败）"; }
      return {
        id: m.idx,
        title: m.title || "无标题",
        summary: m.summary || "",
        tags: m.tags || [],
        cover_emoji: m.emoji || "📝",
        cover_hue: m.hue || 210,
        created_at: new Date(BASE - i * 2 * 86400000).toISOString(),
        content,
      };
    });
    return __posts;
  })();
  return __loading;
}

function sortByDateDesc(list) {
  return list.slice().sort((a, b) => (a.created_at < b.created_at ? 1 : a.created_at > b.created_at ? -1 : 0));
}
function currentSorted() {
  return sortByDateDesc(__posts);
}
function findPost(id) {
  return __posts.find((p) => p.id === id) || null;
}
function tagCounts() {
  const counts = {};
  __posts.forEach((p) => (p.tags || []).forEach((t) => { counts[t] = (counts[t] || 0) + 1; }));
  return Object.entries(counts).sort((a, b) => b[1] - a[1]);
}

/* ---------- 3. 小工具 ---------- */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}
function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function toast(msg, type = "") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  $("#toast-box").appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .3s"; }, 2600);
  setTimeout(() => el.remove(), 3000);
}
function coverCss(hue) {
  const h = Number(hue) || 210;
  return `background:linear-gradient(135deg,hsl(${h},72%,38%),hsl(${(h + 42) % 360},80%,52%) 60%,hsl(${(h + 78) % 360},70%,44%))`;
}

/* ---------- 4. Markdown 渲染（marked + DOMPurify + hljs） ---------- */
marked.setOptions({ gfm: true, breaks: true });

function mdToHtml(md) {
  const raw = marked.parse(md || "");
  return DOMPurify.sanitize(raw, { ADD_ATTR: ["target"] });
}
function enhanceMarkdown(container) {
  $$("pre code", container).forEach((el) => {
    try { hljs.highlightElement(el); } catch (e) { /* 语法不支持则跳过 */ }
  });
  $$('a[href^="http"]', container).forEach((a) => { a.target = "_blank"; a.rel = "noopener"; });
}

/* ---------- 5. 路由 ---------- */
const ROUTE_TITLES = { "": "首页", tags: "标签", about: "关于", search: "搜索" };
function parseRoute() {
  const h = location.hash.replace(/^#\/?/, "");
  const parts = h.split("/").filter(Boolean);
  let name = parts[0] || "", arg = decodeURIComponent(parts[1] || "");
  // 纯数字路由（#/2）视为首页分页
  if (/^\d+$/.test(name)) { arg = name; name = ""; }
  return { name, arg, extra: parts[2] || "" };
}
function render() {
  const { name, arg } = parseRoute();
  $$(".nav-link").forEach((el) => {
    el.classList.toggle("active", el.dataset.route === name);
  });
  const app = $("#app");
  const isPost = name === "post";
  $("#read-progress").style.display = isPost ? "block" : "none";
  document.title = `${ROUTE_TITLES[name] || "文章"} · 码潮 CodeTide`;
  switch (name) {
    case "": return pageHome(app, arg);
    case "post": return pagePost(app, Number(arg));
    case "tags": return pageTags(app);
    case "tag": return pageTagFilter(app, arg);
    case "about": return pageAbout(app);
    case "search": return pageSearch(app, arg);
    default: return pageNotFound(app);
  }
}

/* ---------- 6. 列表渲染（首页 / 标签 / 搜索共用） ---------- */
function paintList(posts, page) {
  const area = $("#post-area");
  const pager = $("#pager");
  if (!area) return;
  const total = posts.length;
  const start = (page - 1) * PAGE_SIZE;
  const slice = posts.slice(start, start + PAGE_SIZE);
  if (!total) {
    area.innerHTML = `<div class="empty-state"><div class="es-icon">🏝️</div>
      <p>还没有文章 —— 涨潮之前，海面总是安静的。</p></div>`;
    if (pager) pager.innerHTML = "";
    return;
  }
  if (!slice.length) {
    area.innerHTML = `<div class="empty-state"><div class="es-icon">🌊</div>
      <p>这一页被潮水冲走了。</p>
      <button class="btn btn-primary" onclick="location.hash='#/'">回到首页</button></div>`;
    if (pager) pager.innerHTML = "";
    return;
  }
  area.innerHTML = `<div class="post-grid">${slice.map((p, i) => postCardHtml(p, i)).join("")}</div>`;
  bindCardActions(slice);
  if (pager) renderPager(page, total);
}
function postCardHtml(p, i) {
  return `<article class="post-card" style="animation-delay:${Math.min(i * 60, 480)}ms" data-id="${p.id}">
    <div class="post-cover" style="${coverCss(p.cover_hue)}">
      <span class="cover-tag">${escapeHtml((p.tags || [])[0] || "随笔")}</span>
      <span class="cover-emoji">${escapeHtml(p.cover_emoji || "📝")}</span>
    </div>
    <div class="post-body">
      <div class="post-title">${escapeHtml(p.title)}</div>
      <div class="post-summary">${escapeHtml(p.summary || "（暂无摘要）")}</div>
      <div class="post-meta">
        <span class="meta-item">📅 ${fmtDate(p.created_at)}</span>
        ${(p.tags || []).slice(0, 3).map((t) => `<span class="tag-chip" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</span>`).join("")}
      </div>
    </div></article>`;
}
function bindCardActions(posts) {
  $$(".post-card").forEach((card) => {
    const id = Number(card.dataset.id);
    card.addEventListener("click", (ev) => {
      const tagChip = ev.target.closest(".tag-chip[data-tag]");
      if (tagChip) { ev.stopPropagation(); location.hash = `#/tag/${encodeURIComponent(tagChip.dataset.tag)}`; return; }
      location.hash = `#/post/${id}`;
    });
  });
}
/* 分页：上一页 / 页码(带省略号) / 下一页。容器必须带 .pager 类，否则 CSS 不生效 */
const PAGER_MAX_SLOTS = 7;   // 页码槽位上限（含省略号）
function pagerPages(cur, total) {
  if (total <= PAGER_MAX_SLOTS) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  // 首尾各固定，中间保留 cur 前后各 1 个；靠近两端时内侧补足到 3 个数字，避免只剩 2 个数
  const set = new Set([1, total, cur]);
  if (cur <= 2) { set.add(2); set.add(3); set.add(4); }
  else if (cur >= total - 1) { set.add(total - 1); set.add(total - 2); set.add(total - 3); }
  else { set.add(cur - 1); set.add(cur + 1); }
  const nums = [...set].filter((n) => n >= 1 && n <= total).sort((a, b) => a - b);
  const out = [];
  nums.forEach((n, i) => {
    if (i && n - nums[i - 1] > 1) out.push("…");
    out.push(n);
  });
  return out;
}
function renderPager(page, total) {
  const pager = $("#pager");
  if (!pager) return;
  const pages = Math.ceil(total / PAGE_SIZE);
  if (pages <= 1) { pager.innerHTML = ""; pager.className = ""; return; }

  const clamp = Math.min(Math.max(page, 1), pages);
  const items = pagerPages(clamp, pages);
  const goto = (p) => {
    location.hash = p === 1 ? "#/" : `#/${p}`;
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  let html = `<button class="pg-nav" data-go="${clamp - 1}" ${clamp === 1 ? "disabled" : ""} aria-label="上一页">‹ 上一页</button>`;
  items.forEach((it) => {
    html += it === "…"
      ? `<span class="pg-gap" aria-hidden="true">…</span>`
      : `<button class="pg-num${it === clamp ? " cur" : ""}" data-go="${it}" ${it === clamp ? 'aria-current="page"' : ""}>${it}</button>`;
  });
  html += `<button class="pg-nav" data-go="${clamp + 1}" ${clamp === pages ? "disabled" : ""} aria-label="下一页">下一页 ›</button>`;

  pager.className = "pager";
  pager.innerHTML = html;
  $$("button[data-go]", pager).forEach((b) => {
    b.onclick = () => { if (!b.disabled) goto(Number(b.dataset.go)); };
  });
}

/* ---------- 7. 页面：首页 ---------- */
function pageHome(app, pageStr) {
  const page = Math.max(1, Number(pageStr) || 1);
  const tagSet = new Set();
  __posts.forEach((p) => {
    (p.tags || []).forEach((t) => tagSet.add(t));
  });
  app.innerHTML = `
    <section class="hero page-fade">
      <div class="hero-tagline">🌊 BACKEND · AI · ARCHITECTURE</div>
      <h1>码潮 CodeTide</h1>
      <p>记录每一次技术涨潮：Java 后端、数据库与中间件、系统架构，以及大模型时代的持续修炼。文章以静态数据随站点发布，打开即读。</p>
      <div class="hero-stats">
        <div class="stat-pill"><b>${__posts.length}</b><span>篇文章</span></div>
        <div class="stat-pill"><b>${tagSet.size}</b><span>个标签</span></div>
        <div class="stat-pill"><b>${Math.ceil(__posts.length / PAGE_SIZE)}</b><span>页连载</span></div>
      </div>
    </section>
    <div class="section-head page-fade">
      <h2 id="list-title">最新文章</h2>
      <span class="sub" id="list-count">共 ${__posts.length} 篇 · 第 ${page} 页</span>
    </div>
    <div id="post-area"></div>
    <div id="pager"></div>`;
  paintList(currentSorted(), page);
}

/* ---------- 8. 页面：文章详情 ---------- */
function pagePost(app, id) {
  const post = findPost(id);
  if (!post) {
    app.innerHTML = `<div class="empty-state page-fade"><div class="es-icon">🌊</div>
      <p>这篇文章已随潮水漂走（不存在）。</p>
      <button class="btn btn-primary" onclick="location.hash='#/'">回到首页</button></div>`;
    return;
  }
  const { prev, next } = loadPrevNext(post);
  app.innerHTML = `
    <div class="article-wrap page-fade">
      <span class="back-link" onclick="history.length>1?history.back():location.hash='#/'">← 返回</span>
      <div class="article-cover" style="${coverCss(post.cover_hue)}">
        <span class="cover-emoji">${escapeHtml(post.cover_emoji || "📝")}</span>
      </div>
      <div class="article-head">
        <h1>${escapeHtml(post.title)}</h1>
        <div class="article-meta">
          <span class="m">📅 ${fmtDate(post.created_at)}</span>
          <span class="article-tags">${(post.tags || []).map((t) => `<span class="tag-chip" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</span>`).join("")}</span>
        </div>
      </div>
      <div class="md" id="md-body"></div>
      <div class="article-nav">
        ${prev ? `<div class="an-card" data-goto="${prev.id}"><div class="an-label">← 上一篇</div><div class="an-title">${escapeHtml(prev.title)}</div></div>` : '<div class="an-card an-empty"></div>'}
        ${next ? `<div class="an-card next" data-goto="${next.id}"><div class="an-label">下一篇 →</div><div class="an-title">${escapeHtml(next.title)}</div></div>` : '<div class="an-card next an-empty"></div>'}
      </div>
    </div>`;
  const body = $("#md-body");
  body.innerHTML = mdToHtml(post.content);
  enhanceMarkdown(body);
  $$(".article-tags .tag-chip", app).forEach((c) => {
    c.onclick = () => { location.hash = `#/tag/${encodeURIComponent(c.dataset.tag)}`; };
  });
  $$("[data-goto]", app).forEach((c) => { c.onclick = () => { location.hash = `#/post/${c.dataset.goto}`; window.scrollTo({ top: 0 }); }; });
  window.scrollTo({ top: 0 });
}
function loadPrevNext(post) {
  const arr = sortByDateDesc(__posts);   // 新 → 旧
  const i = arr.findIndex((p) => p.id === post.id);
  if (i < 0) return { prev: null, next: null };
  return { prev: arr[i - 1] || null, next: arr[i + 1] || null };
}

/* ---------- 9. 页面：标签 ---------- */
function pageTags(app) {
  const tags = tagCounts();
  if (!tags.length) {
    app.innerHTML = `<div class="page-fade"><div class="section-head"><h2>标签分类</h2></div>
      <div class="empty-state"><div class="es-icon">🏷️</div><p>还没有任何标签。</p></div></div>`;
    return;
  }
  const max = tags[0][1];
  app.innerHTML = `<div class="page-fade">
    <div class="section-head"><h2>标签分类</h2><span class="sub">共 ${tags.length} 个标签</span></div>
    <div class="tag-cloud">${tags.map(([t, n]) => {
      const scale = 0.85 + 0.55 * (n / max);
      return `<span class="tag-chip" data-tag="${escapeHtml(t)}" style="font-size:${scale.toFixed(2)}em">${escapeHtml(t)}<b> ${n}</b></span>`;
    }).join("")}</div></div>`;
  $$(".tag-cloud .tag-chip", app).forEach((c) => {
    c.onclick = () => { location.hash = `#/tag/${encodeURIComponent(c.dataset.tag)}`; };
  });
}
function pageTagFilter(app, tag) {
  const posts = currentSorted().filter((p) => (p.tags || []).includes(tag));
  app.innerHTML = `<div class="page-fade">
    <div class="section-head"><h2>🏷️ ${escapeHtml(tag)}</h2>
      <span class="sub">共 ${posts.length} 篇 · <a href="#/tags">← 全部标签</a></span></div>
    <div id="post-area"></div><div id="pager" class="pager"></div></div>`;
  if (!posts.length) {
    $("#post-area").innerHTML = `<div class="empty-state"><div class="es-icon">🏝️</div>
      <p>这个标签下还没有文章。</p></div>`;
    return;
  }
  paintList(posts, 1);
}

/* ---------- 10. 页面：关于 ---------- */
function pageAbout(app) {
  app.innerHTML = `
  <div class="about-card page-fade">
    <div class="about-avatar">🧑‍💻</div>
    <h1>关于博主</h1>
    <div class="about-sub">后端工程师 · AI 学习者 · 修炼中</div>
    <p>一名在 Java 后端世界摸爬滚打的工程师，白天和 Spring、MySQL、Kafka 打交道，晚上追大模型的论文和浪潮。
    相信技术是需要"长期修炼"的手艺，所以开了这个博客，把学习笔记、面试复盘和踩坑记录都沉在这里。</p>
    <h3>🧭 这里写什么</h3>
    <ul>
      <li><b>后端八股与原理</b> —— MySQL、JVM、并发、Kafka、Nginx、Linux，问到底层的那种。</li>
      <li><b>系统架构</b> —— 分布式、高并发、稳定性设计的思考与方案沉淀。</li>
      <li><b>AI 学习路线</b> —— 机器学习 / 深度学习 / 大模型 / Agent 的学习记录与实践。</li>
      <li><b>数据结构与算法</b> —— 面试刷题与思维训练。</li>
    </ul>
    <h3>🛠 技术栈</h3>
    <div class="skill-row">
      <span class="tag-chip">Java</span><span class="tag-chip">Spring</span><span class="tag-chip">MySQL</span>
      <span class="tag-chip">Redis</span><span class="tag-chip">Kafka</span><span class="tag-chip">Nginx</span>
      <span class="tag-chip">Linux</span><span class="tag-chip">微服务</span><span class="tag-chip">Python</span>
      <span class="tag-chip">LLM</span><span class="tag-chip">Agent</span><span class="tag-chip">RAG</span>
    </div>
    <h3>📮 找到我</h3>
    <p>文章评论区暂未开放，有交流欲可以直接邮件轰炸。看到必回（忙时随缘）。</p>
    <h3>🌊 关于「码潮」</h3>
    <p>技术的更新像潮水，一波接一波，拦不住也不必拦。与其焦虑被拍在沙滩上，不如学会冲浪。
    这个博客就是我练习冲浪的 beach —— 记录，沉淀，然后再次出发。</p>
  </div>`;
}

/* ---------- 11. 页面：搜索 ---------- */
function pageSearch(app, kw) {
  app.innerHTML = `<div class="page-fade"><div class="section-head"><h2>🔍 「${escapeHtml(kw)}」的搜索结果</h2></div>
    <div id="post-area"></div><div id="pager"></div></div>`;
  const safe = String(kw || "").trim().toLowerCase();
  if (!safe) {
    $("#post-area").innerHTML = '<div class="empty-state"><div class="es-icon">🔍</div><p>请输入有效的搜索关键词。</p></div>';
    return;
  }
  const hits = sortByDateDesc(__posts.filter((p) =>
    (p.title || "").toLowerCase().includes(safe) || (p.summary || "").toLowerCase().includes(safe)
  )).slice(0, 30);
  if (!hits.length) {
    $("#post-area").innerHTML = `<div class="empty-state"><div class="es-icon">🏝️</div>
      <p>没有找到与「${escapeHtml(kw)}」相关的文章。</p></div>`;
    return;
  }
  $("#post-area").innerHTML = `<div class="post-grid">${hits.map((p, i) => postCardHtml(p, i)).join("")}</div>`;
  bindCardActions(hits);
}

/* ---------- 12. 404 ---------- */
function pageNotFound(app) {
  app.innerHTML = `<div class="empty-state page-fade" style="margin-top:40px"><div class="es-icon">🧭</div>
    <p>这片海域还没有航路 —— 页面不存在。</p>
    <button class="btn btn-primary" onclick="location.hash='#/'">回到首页</button></div>`;
}

/* ---------- 13. 启动 ---------- */
function bindChrome() {
  $("#foot-year").textContent = new Date().getFullYear();
  $$(".nav-link").forEach((el) => {
    el.addEventListener("click", () => {
      const r = el.dataset.route;
      location.hash = r ? `#/${r}` : "#/";
    });
  });
  $("#nav-search").addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") {
      const kw = ev.target.value.trim();
      if (kw) { location.hash = `#/search/${encodeURIComponent(kw)}`; ev.target.value = ""; }
    }
  });
  window.addEventListener("scroll", () => {
    const st = window.scrollY, dh = document.documentElement.scrollHeight - innerHeight;
    $("#read-progress").style.width = dh > 0 ? `${(st / dh) * 100}%` : "0%";
    $("#back-top").classList.toggle("show", st > 500);
  }, { passive: true });
}

(async function boot() {
  bindChrome();
  try {
    await loadPosts();
    window.addEventListener("hashchange", render);
    if (!location.hash) location.hash = "#/";
    render();
  } catch (e) {
    console.error("[CodeTide] 初始化失败：", e);
    $("#app").innerHTML = `<div class="empty-state page-fade" style="margin-top:40px">
      <div class="es-icon">⚠️</div>
      <p>文章数据加载失败：${escapeHtml(e.message || "未知错误")}</p>
      <p style="font-size:.9em;opacity:.7">请确认 seed/meta.json 与 seed/blocks.jsonl 能通过 HTTP 访问（不要用 file:// 直接打开）。</p></div>`;
  }
})();

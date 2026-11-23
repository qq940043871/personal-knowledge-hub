# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

命名口径：仓库名、工作区目录名、`README.md` 标题、`index.html` 页标题与 logo、`start.bat` 启动横幅统一为 `personal-knowledge-hub`。旧名 `personal-tech-knowledge` 仅残留在 `library/` 正文的历史说明里，勿据此回改名。

本仓库是**静态内容 + 轻量阅读器 + 一次性维护脚本**，没有构建系统、测试套件、linter 或包管理清单（`requirements.txt` 只有 Flask，仅服务 library 的 Flask 阅读器）。

## 常用命令

```bash
# 门户 + 静态阅读器（推荐）。启动前自动跑 build_tree.py 刷新 tree.json，
# 端口 3005 被占用时会询问是否结束占用进程；优先用缓存的 npx http-server，其次 python。
start.bat

# 仅重建侧边栏索引（新增/删除文档后手动跑）
python library/build_tree.py

# 不用 bat 时，任选一个静态服务器（文档必须是 HTTP 打开，file:// 下 fetch 会失败）
python -m http.server 3005 --bind 127.0.0.1
npx http-server -p 3005 -c-1 -a 127.0.0.1
```

```bash
# Flask 阅读器：只服务 library/ 目录（WORKSPACE_PATH = app.py 所在目录），端口 5000
pip install -r requirements.txt
python library/app.py          # GET /api/files | GET /api/file?path=<相对 library/ 的路径>
```

```bash
# 归档层质量扫描：死链/未闭合围栏/坏表格/乱码/过度转义/超短文件
node tools/archive-quality-scan.mjs library

# 质量修复器：默认 dry-run，加 --apply 才落盘（转义残渣、尾悬挂 ```、丢图占位、U+FFFD）
node tools/archive-quality-fix.mjs --apply

# 查重：md5 精确重复 + minhash 近似重复，参数为仓库根相对目录（可多个，跨目录比对）
python tools/content_dup_scan.py library/技术 --min 0.55 --top 40
```

```bash
# 博客文章数据（站点唯一数据源）：从 library/ 精选文章生成 meta.json + blocks.jsonl（改造标题/导语/截断）
python blog/seed/gen_blocks.py
# 校验 blocks.jsonl 每块 b64 能否干净解码为 UTF-8
python blog/seed/check_b64.py
```

```bash
# 文档格式转换（docx2md 依赖 python-docx，需自行安装，不在 requirements.txt）
python tools/docx2md.py <源目录> <输出目录>
# 语雀导出 JSON → Markdown 文件树 + CDN 图片本地化（可选 --skip-images）
node tools/yuque-export/build.mjs <rawDir> <outDir>
```

`tools/` 下其余脚本（`reorg4sources.py`、`reorg_relink.py`、`reorg_library_split.py`、`repair_stale_links.py`、`cleanup_tech_dups.py`、`feishu_stub_clean.py`、`tdoc_*.py`）是已完成使命的一次性重组/导出工具，多数带 `--plan`/`--apply` 或 dry-run 开关，运行前先读文件头的 DEPRECATED 说明与用法。

## 架构

### 一句话结构

一个暗色门户 `index.html` → 两条访问路径：`library/`（Markdown 知识库 + 静态阅读器）与 `blog/`（纯静态博客 SPA，数据来自 `blog/seed/`，2026-11-23 起无后端）。`tools/` 是维护脚本（2026-11-13 起整体不入库），顶层 `agent/`、`output/` 是本地资产层（不入库）。

### 版本控制三层（改内容前必须确认自己改的是哪层）

| 层 | 内容 | 状态 |
|----|------|------|
| 公开成品 | 根 `index.html`、`library/` 未排除目录、`blog/`、`assets/` | 已跟踪（3001 个文件，其中 md 1639、`library/` 下 2972 个） |
| 本地工具 | 顶层 `tools/` | 2026-11-13 起整体排除（`.gitignore` 的 `tools/` + `git rm -r --cached tools`） |
| 私有来源 | `library/家庭/`、`library/隐私/`、`library/投资/01-我的实盘与成长史/`、`library/工作/客户跟踪/` | `.gitignore` 排除，仅本地存在 |
| 本地资产层 | 顶层 `agent/`、`output/` | 整体排除，历史上从未入库 |

目录被整体排除后 Git 不再递归进入，`!` 否定规则无效——确需入库单个文件只能用 `git add -f <path>`。

私有名单有**两道复制品**，新增或放行私有目录时两处必须同步：根 `.gitignore`、`library/.gitignore`（2026-11-13 新增的第二道防线，防止根文件被编辑器陈旧缓冲区回写覆盖）。第三处不再手抄：`build_tree.py` 运行时对每个目录执行 `git check-ignore --no-index`，被忽略的才不进 `tree.json`（仅 `FALLBACK_IGNORED_DIRS` 在 git 不可用时兜底），因此站点树不会与 gitignore 漂移。

唯一例外是 `library/技术/飞书·人工智能/`：2026-11-12 起已从 `.gitignore` 放行（AI 内容唯一归口，需在阅读器里可浏览、也要随站点发布）。它是「私有来源里被提升为公开成品」的唯一案例。

### library/：内容布局与索引管线

当前是**四公开库 + 两私有库**：`技术/ 投资/ 工作/ 考证/` 为成品公开库，`家庭/`、`隐私/` 整库私有。`创作/` 已于 2026-11-13 下线（小说与股林武侠素材归入本地资产层 `output/novels/`）。成品目录遵循编号约定：`00-总览/`、`01-基础/`、`02-进阶/`、`99-参考速查.md`。

`技术/` 现已收敛为四个顶层目录：`17年技术经验总结/`（15 个编号分册，是主要成品区）、`从0到1设计计算机/`、`飞书·飞天闪客/`、`飞书·人工智能/`。原先散在 `技术/` 下的「手写」系列、中间件学习指南、Java 框架全景图等已全部并入 `17年技术经验总结/13-手写系列-原理`、`11-Linux学习指南`、`12-Java框架全景图` 等分册——**旧路径（如 `技术/Linux学习指南/`）已不存在**，别按历史记忆找目录。

导航不硬编码：`build_tree.py` 扫描磁盘，只收录 `.md/.markdown/.pptx`，跳过隐藏目录与顶层元数据文件，输出 `tree.json`（生成产物，`start.bat` 每次启动重建，写临时文件后 `os.replace` 原子替换）。数据形态是三层嵌套：`{分类: [files] | {子目录: [files] | {子子目录: [files]}}}`，目录直属文件用特殊键 `_files` 承载；更深的层级被**折叠**进 `父/子` 标签键（`emit_deep`）。`library/index.html` 按这个形状硬编码三段循环渲染并 `fetch(path)` 取正文。

### 三套互不共享代码的阅读器

改渲染、导航或样式通常要改三处，不要假设有共享模块：

1. `library/index.html` + `library/tree.json`：纯静态，`marked` + `highlight.js`（CDN）。
2. `library/python.html` + `library/app.py`：Flask，前端走 `/api/files`、`/api/file`；后端用 `Path.resolve()` + `is_relative_to(root)` 阻断 `../` 逃逸。
3. `library/技术/17年技术经验总结/09-技术知识库/index.html` + `md-viewer.html?file=pages/...`：自包含站点（原 `hello_my_profile`），iframe 式导航。

三者的共同限制：Markdown 正文被渲染进阅读器页面本身，没有 `<base>` 或 URL 重写，因此正文里的**相对图片/链接按阅读器页面所在目录解析，而非按 .md 所在目录**——归档层里大量 `![](images/xxx.png)` 形式的相对图在静态阅读器中会裂图，成品库因此多用内联 SVG。

### blog/：纯静态 SPA（无构建、无后端）

`blog/index.html` 是外壳与全部样式，`blog/app.js` 是唯一逻辑文件，通过 CDN 引入 marked、DOMPurify、highlight.js。

**2026-11-23 已彻底下线云端**：删除 WorkBuddy Cloud SDK 依赖、云数据库（posts 表）、邮箱认证（密码/OTP/注册/重置）、云存储（图片与附件上传、签名 URL）、写文章/编辑/我的文章/删除/阅读计数，同时删除 `blog/.wbapp_*.genie`、`gen_seed.py`、`post_*.b64`、`seed_posts.jsonl`、`split_96.json`。现在只有一个数据源：`blog/seed/`。

- **数据层**：`loadPosts()` 启动时一次性 fetch `seed/meta.json` + `seed/blocks.jsonl`，解码后放进内存数组 `__posts`（含正文），之后所有列表/筛选/搜索都是内存操作，**不再有查询器抽象**（原来的 `postsQuery()` / `localPosts()` 已删）。正文按 400 字符切块、逐块独立 base64，解码是「每块独立 atob → 拼接字节 → TextDecoder」，**不能直接拼 b64 字符串**。
- **展示字段**：种子数据不含发布时间与阅读数，`loadPosts()` 用索引生成稳定值（`views = 100 + (i*137)%1900`，`created_at` 从 `2026-11-21` 起每篇减 2 天），刷新不跳动，别改成 `Math.random()`。
- **路由**：`location.hash` 手写路由表（`#/`、`#/post/:id`、`#/tags`、`#/tag/:t`、`#/about`、`#/search/:kw`，纯数字 hash 视作首页分页）。所有 HTML 都经 `escapeHtml`。
- **部署**：仓库根有 `.nojekyll`（关掉 Jekyll，避免 `library/` 里含 `{{ }}` 的 md 被 Liquid 处理），`seed/` 目录名不带下划线也是为了绕开 Jekyll 的 `_` 前缀排除规则。GitHub Pages 上 `/blog/` 即可直接打开，无 CORS 依赖。

### tools/：一次性脚本的约定

`tools/` 自 2026-11-13 起**整体不入库**（`.gitignore` 有 `tools/`，历史文件已 `git rm -r --cached`），脚本只在本机跑、产物落到 `library/` 或 `output/`，因此改脚本不需要提交。

绝大多数脚本用 `WS = Path(__file__).resolve().parent.parent` 定位仓库根，不依赖 cwd；路径口径是**仓库根相对（含 `library/` 前缀）**。重组管线有严格顺序：`reorg4sources.py --plan`（产出 `library/_备份元数据/reorg_manifest.json` 全文件级清单）→ `--apply` → `reorg_relink.py`（按 manifest 改写链接）→ `reorg_library_split.py`（成品拆进六库，先算新内容再搬目录）→ `repair_stale_links.py`（修"文件搬了链接没跟着改"的存量链接）。删除类脚本一律「先 grep 全库入链、有入链则记录并改写」再动手。

### 内嵌子项目：library/投资/08-fianace-console/

投资交易工作站静态原型，纯 CDN（Tailwind + Font Awesome + Chart.js），零构建。`index.html` 是外壳（顶栏 + 可折叠侧栏 + `<iframe id="mainFrame">`），子页用 `parent.loadPage('module/page.html')` 导航，Tab 容器页用 `switchTab()` 加**目录相对**路径加载内层 iframe。每个 `.html` 都配一份同名 `.md`（页面概述/功能需求/页面结构/技术实现）。组件自己的 `CLAUDE.md` 与 `start.bat`（端口 3004）在该目录内，改动前先读它。

**涨跌配色是 A 股口径：红涨 `#DC2626`、绿跌 `#10B981`**，与欧美相反。已知文件名怪癖（`mainipulation_process.html`、`tongce_medical.html`）不要顺手"修正"。

### 内容规范

- 中文写作，实用直给，结构走「场景 → 原因分析 → 解决」，第二人称「你」。
- 文档体系原遵循 Divio 四象限（`library/技术/技术文档体系/DOC_SYSTEM.md` 等），该目录已在 2026-11-13 重组中移除；现在只保留本条约定，无独立规范文件可引。
- 分类导航入口是 `library/wiki.md`（**内容已严重滞后**：技术类链接都还是 `技术/xxx学习指南/` 这类已不存在的路径），库总说明是 `library/README.md`，两者统计口径均以根 `README.md` 与磁盘现状为准。

## 已知待办与坑

- 根 `index.html` 有 4 处链接指向 `library/17年技术经验总结/09-技术知识库/...`，但实际路径是 `library/技术/17年技术经验总结/09-技术知识库/...`（成品拆分进六库后的残留死链）。
- ~~`SKIP_DIRS` 与 gitignore 漂移~~（2026-11-13 已修）：`build_tree.py` 改为运行时 `git check-ignore --no-index` 判定，`SKIP_DIRS` 只留 `__pycache__`/`node_modules` 之类的技术目录，私有目录由 gitignore 单一来源决定。修复后 `tree.json` 从 984 篇回到 **1643 篇**（4 个公开库：技术/投资/工作/考证；同日清理 `工作/基础学习` 9 篇冗余文档后为 1634 篇），原先白丢的约 660 篇公开文档已回到侧边栏。git 不可用时退回 `FALLBACK_IGNORED_DIRS`（`家庭`/`隐私`/`01-我的实盘与成长史`/`客户跟踪`）兜底，新增私有目录时记得同步这两处。
- `blog/seed/meta.json` + `blocks.jsonl` 是生成产物，但 2026-11-23 起是博客**唯一**数据源，必须入库（`.gitignore` 中原有的忽略规则已删除）。改完 `library/` 内容后要重跑 `gen_blocks.py` 才会反映到 blog。
- 博客部署到 GitHub Pages 只依赖两条：仓库根有 `.nojekyll`（否则 Jekyll 会处理 `library/` 下含 `{{ }}` 的 md，并会排除 `_` 前缀路径）；`seed/` 目录名保持无下划线前缀。云端 CORS 已不再是问题（后端已下线）。
- `library/tree.json` 是生成产物，不要手改；`build_tree.py` 只认 `.md/.markdown/.pptx`，新增其他类型不会出现在侧边栏。
- `library/wiki.md` 是分类导航索引，但其中的技术类链接全部指向重构前的旧路径，直接点击会 404；引用前先核对磁盘。
